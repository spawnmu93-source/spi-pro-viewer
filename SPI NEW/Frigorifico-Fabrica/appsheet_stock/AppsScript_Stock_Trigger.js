/**
 * =============================================================================
 * SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - GOOGLE APPS SCRIPT WEBHOOK & ENGINE
 * Módulo: AppsScript_Stock_Trigger.js (Conector Python Edge -> Google Sheets -> AppSheet)
 * =============================================================================
 * Instrucciones:
 * 1. Abre tu hoja "SPI_Control_Stock_AppSheet" en Google Sheets.
 * 2. Ve a Extensiones > Apps Script.
 * 3. Pega este código completo y guarda con el nombre "SPI_Stock_Backend".
 * 4. Haz clic en "Implementar" > "Nueva implementación" > Tipo: "Aplicación web".
 *    - Ejecutar como: "Yo" (tu cuenta)
 *    - Quién tiene acceso: "Cualquiera"
 * 5. Copia la URL generada y colócala en config_parametros.py (API_CENTRAL_URL).
 * =============================================================================
 */

const SHEET_CAMARAS = "Camaras_Depositos";
const SHEET_STOCK_MR = "Stock_Medias_Reses";
const SHEET_KARDEX = "Movimientos_Kardex";
const SHEET_AUDITORIAS = "Auditorias_Stock";

/**
 * Endpoint GET: Consulta de estado de cámaras y stock en tiempo real
 */
function doGet(e) {
  try {
    const action = (e && e.parameter && e.parameter.action) ? e.parameter.action : "getStatus";
    const ss = SpreadsheetApp.getActiveSpreadsheet();

    if (action === "getCamaras") {
      const sheet = ss.getSheetByName(SHEET_CAMARAS);
      const data = sheet.getDataRange().getValues();
      const headers = data[0];
      const camaras = [];
      for (let i = 1; i < data.length; i++) {
        const row = {};
        for (let j = 0; j < headers.length; j++) {
          row[headers[j]] = data[i][j];
        }
        camaras.push(row);
      }
      return jsonResponse({ success: true, camaras: camaras });
    }

    return jsonResponse({
      status: "ONLINE",
      timestamp: new Date().toISOString(),
      service: "SPI Google Sheets / AppSheet Stock Bridge"
    });
  } catch (err) {
    return jsonResponse({ success: false, error: err.toString() });
  }
}

/**
 * Endpoint POST: Recepción de pesajes y eventos desde Python Edge (Terminal de Faena / Gancho)
 */
function doPost(e) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const rawData = e.postData.contents;
    const body = JSON.parse(rawData);

    // Si viene como lote de eventos desde sync_worker.py
    const items = Array.isArray(body) ? body : [body];
    let insertedMR = 0;
    let insertedKardex = 0;

    const wsStock = ss.getSheetByName(SHEET_STOCK_MR);
    const wsKardex = ss.getSheetByName(SHEET_KARDEX);

    items.forEach(item => {
      const payload = item.payload || item;
      const eventType = item.event_type || item.tipo_evento || "INGRESO_MEDIA_RES_CAMARA";

      if (eventType === "INGRESO_MEDIA_RES_CAMARA" || eventType === "MEDIA_RES") {
        const idMR = payload.lote || payload.lote_media_res || `MR-${payload.lado || "A"}-${Date.now()}`;
        const numAnimal = payload.numero_animal || 1;
        const lado = payload.lado || "IZQ";
        const tropa = payload.tropa || payload.tropa_actual || payload.id_tropa_fk || "TRP-2026-00412";
        const depCod = payload.deposito_codigo || "CO1";
        const tipoAnimal = payload.tipo_animal || "MEI";
        const fechaFaena = Utilities.formatDate(new Date(), "GMT-3", "yyyy-MM-dd");
        const pesoCaliente = parseFloat(payload.peso_kg || payload.peso_gancho_caliente_kg || 0.0);
        
        let estSanitario = "APTA";
        let dpMotivo = "";
        let dpKilos = 0.0;
        if (payload.decomiso_total) {
          estSanitario = "DECOMISO_TOTAL";
        } else if (payload.decomiso_parcial) {
          estSanitario = "DECOMISO_PARCIAL";
          dpMotivo = payload.decomiso_parcial.motivo || "";
          dpKilos = parseFloat(payload.decomiso_parcial.kilos || 0.0);
        }

        const capturaManual = payload.captura_manual ? "SI" : "NO";
        const autorizadoPor = payload.autorizado_por || "";
        const nowIso = Utilities.formatDate(new Date(), "GMT-3", "yyyy-MM-dd HH:mm:ss");

        // 1. Agregar a Stock_Medias_Reses
        wsStock.appendRow([
          idMR,
          numAnimal,
          lado,
          tropa,
          depCod,
          tipoAnimal,
          fechaFaena,
          pesoCaliente,
          "", // Peso_Frio_Kg
          "", // Merma_Oreo_Kg (calculada en Sheets / AppSheet)
          "", // Merma_Oreo_Pct
          estSanitario,
          dpMotivo,
          dpKilos,
          `=H${wsStock.getLastRow() + 1}-N${wsStock.getLastRow() + 1}`, // Kilos_Netos_Aptos
          "EN_OREO",
          capturaManual,
          autorizadoPor,
          nowIso
        ]);
        insertedMR++;

        // 2. Agregar a Movimientos_Kardex
        const idMov = "MOV-" + Utilities.formatDate(new Date(), "GMT-3", "yyyyMMdd-HHmmss-") + Math.floor(Math.random() * 1000);
        wsKardex.appendRow([
          idMov,
          nowIso,
          idMR,
          "1. INGRESO_FAENA",
          "PALCO_GANCHO",
          depCod,
          pesoCaliente,
          payload.operario_nombre || "Operario Gancho",
          `Ingreso automático desde palco de faena. Autorizado: ${autorizadoPor || 'N/A'}`
        ]);
        insertedKardex++;
      }
    });

    return jsonResponse({
      success: true,
      medias_registradas: insertedMR,
      movimientos_kardex: insertedKardex,
      message: "Sincronizado exitosamente con Google Sheets y disponible en AppSheet."
    });

  } catch (error) {
    return jsonResponse({ success: false, error: error.toString() });
  }
}

/**
 * Helper para formatear respuesta JSON
 */
function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Trigger automático para verificar saturación de cámaras (opcional)
 */
function verificarCapacidadCamaras() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ws = ss.getSheetByName(SHEET_CAMARAS);
  const data = ws.getDataRange().getValues();

  for (let i = 1; i < data.length; i++) {
    const cod = data[i][0];
    const nombre = data[i][1];
    const capMax = data[i][3];
    const stockActual = data[i][5];

    if (capMax > 0 && stockActual >= capMax) {
      Logger.log(`[ALERTA] Cámara ${nombre} (${cod}) saturada al 100%: ${stockActual}/${capMax} MR.`);
      // Opcional: Enviar email automático si se desea:
      // MailApp.sendEmail("auditor@frigorifico.com", `Alerta: ${nombre} Saturada`, `Stock: ${stockActual}/${capMax}`);
    }
  }
}

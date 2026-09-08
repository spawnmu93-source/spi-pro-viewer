/**
 * ============================================================================
 * SCRIPT PARA CREAR LOS 4 FORMULARIOS GOOGLE FORMS AUTOMÁTICAMENTE
 * Sistema de Producción Integral (SPI)
 * 
 * Genera con 1 solo clic los 4 formularios específicos:
 * 1. Frigorífico - Responsable (Jefe de Planta / Veterinario)
 * 2. Frigorífico - Operario (Pesador de Gancho / Playa de Faena)
 * 3. Fábrica - Responsable (Maestro Chacinero / Jefe de Calidad)
 * 4. Fábrica - Operario (Pesador de Batea / Embutidor)
 * ============================================================================
 * 
 * INSTRUCCIONES DE USO EN 1 MINUTO:
 * 1. Abre en tu navegador: https://script.new (inicia sesión con Google/Gmail).
 * 2. Borra el código existente y PEGA TODO EL CONTENIDO de este archivo.
 * 3. Presiona el botón "Ejecutar" (Run ▶️) en la barra superior.
 * 4. Acepta los permisos de Google (Revisar permisos -> Avanzado -> Ir a...).
 * 5. ¡LISTO! En segundos el script crea los 4 formularios en tu Google Drive y
 *    te muestra en pantalla los 4 enlaces listos para mandar por WhatsApp.
 * ============================================================================
 */

function crearLos4FormulariosSPI() {
  Logger.log('🚀 INICIANDO CREACIÓN DE LOS 4 FORMULARIOS SPI...');
  
  var links = [];
  
  // ==========================================================================
  // FORMULARIO 1: FRIGORÍFICO - RESPONSABLE
  // ==========================================================================
  var f1 = FormApp.create('SPI - 1. Frigorífico (Responsable / Calidad / SENASA)');
  f1.setDescription(
    'Cuestionario de definición para Responsables de Frigorífico, Jefes de Faena y Médicos Veterinarios SENASA.\n' +
    'Objetivo: Definir reglas de negocio, filtros sanitarios, límites de bloqueo vs permisivos y KPIs.'
  );
  f1.setProgressBar(true);

  f1.addTextItem().setTitle('Nombre y Apellido:').setRequired(true);
  f1.addTextItem().setTitle('Puesto / Función exacta:').setRequired(true);

  // Sección: DT-e y Recepción
  f1.addPageBreakItem().setTitle('RECEPCIÓN DE TROPA Y DOCUMENTACIÓN SENASA');
  f1.addMultipleChoiceItem()
    .setTitle('1. Si los kilos vivos de báscula difieren > 2% del DT-e:')
    .setChoiceValues([
      '🔴 Bloqueo duro: No permitir iniciar faena sin autorización explícita de supervisor.',
      '🟡 Alerta blanda: Mostrar advertencia visual pero permitir descargar a corrales.',
      '🟢 Registro silencioso: Registrar para informe gerencial sin frenar la descarga.'
    ]).setRequired(true);

  f1.addMultipleChoiceItem()
    .setTitle('2. Tiempo de descanso en corrales previo a faena (2 a 4 horas):')
    .setChoiceValues([
      'Obligatorio: El sistema no debe permitir habilitar la tropa antes del descanso mínimo.',
      'Sugerencia: Mostrar tiempo transcurrido pero dejar inicio a criterio del jefe de faena.'
    ]).setRequired(true);

  // Sección: Inspección Sanitaria SENASA
  f1.addPageBreakItem().setTitle('INSPECCIÓN SANITARIA Y DECOMISOS (SENASA)');
  f1.addMultipleChoiceItem()
    .setTitle('3. Mecánica de Aprobación Sanitaria en línea de faena:')
    .setChoiceValues([
      'Aprobación por Excepción (Recomendada): Toda res se asume APTA en balanza a menos que el veterinario marque decomiso.',
      'Bloqueo Unitario: La balanza NO pesa ni imprime etiqueta si el veterinario no dio "Apto" previo a cada res.',
      'Carga Posterior: Se faena continuo y las actas de decomiso se cargan al final de la tropa desde planilla.'
    ]).setRequired(true);

  f1.addMultipleChoiceItem()
    .setTitle('4. Decomiso Total (ej. sospecha triquinosis/ictericia):')
    .setChoiceValues([
      'Imprimir etiqueta roja de "DECOMISO SANITARIO" para identificar la res enviada a digestor.',
      'No imprimir nada físico y dar de baja automática en el sistema.',
      'Generar acta SENASA individual en PDF en el momento exacto del decomiso.'
    ]).setRequired(true);

  f1.addMultipleChoiceItem()
    .setTitle('5. Decomiso Parcial (vísceras rojas, cabezas, órganos):')
    .setChoiceValues([
      'La canal continúa como apta y solo se registran los kilos/órganos decomisados.',
      'Se debe descontar el peso del órgano del rendimiento oficial de la canal.'
    ]).setRequired(true);

  // Sección: Oreado y Desposte
  f1.addPageBreakItem().setTitle('OREADO, MERMAS Y DESPOSTE DE PLANTA');
  f1.addMultipleChoiceItem()
    .setTitle('6. Pesaje en frío a las 24 horas (Control de Merma de Cámara):')
    .setChoiceValues([
      'Se pesan el 100% de las medias reses al salir de cámara.',
      'Se pesa solo una muestra representativa (ej. 10 reses por tropa).',
      'Se pesa el camión completo cargado en báscula de salida.'
    ]).setRequired(true);

  f1.addMultipleChoiceItem()
    .setTitle('7. Re-impresión de etiquetas de media res dañadas:')
    .setChoiceValues([
      'Controlada: Requiere clave/PIN de supervisor para evitar duplicación de canales.',
      'Libre: Cualquier operario puede volver a imprimir la etiqueta en su puesto.'
    ]).setRequired(true);

  f1.addParagraphTextItem().setTitle('Comentarios u observaciones para Frigorífico (Responsable):');

  links.push({
    formulario: '1. Frigorífico - Responsable',
    editUrl: f1.getEditUrl(),
    viewUrl: f1.getPublishedUrl()
  });

  // ==========================================================================
  // FORMULARIO 2: FRIGORÍFICO - OPERARIO
  // ==========================================================================
  var f2 = FormApp.create('SPI - 2. Frigorífico (Operario de Balanza y Playa)');
  f2.setDescription(
    'Cuestionario para el Operario de Balanza de Gancho, Playa de Faena y Cámaras.\n' +
    'Objetivo: Conocer cómo es el trabajo físico real en la línea, uso de pantallas con guantes y velocidad de trabajo.'
  );
  f2.setProgressBar(true);

  f2.addTextItem().setTitle('Nombre y Apellido:').setRequired(true);
  f2.addTextItem().setTitle('Puesto de trabajo en faena (ej. Pesador de gancho, Desposte, etc.):').setRequired(true);

  f2.addPageBreakItem().setTitle('DINÁMICA DE PESAJE EN EL GANCHO AÉREO');
  f2.addMultipleChoiceItem()
    .setTitle('1. ¿Cómo pasa la media res por la balanza de gancho?')
    .setChoiceValues([
      'Se detiene completamente la roldana sobre la celda de carga para pesar.',
      'Pasa al paso (en movimiento continuo sobre la noria riel).'
    ]).setRequired(true);

  f2.addMultipleChoiceItem()
    .setTitle('2. ¿Cuánto tiempo tienes aproximadamente para pesar cada media res?')
    .setChoiceValues([
      'Menos de 10 segundos (ritmo muy rápido).',
      'Entre 10 y 25 segundos.',
      'Más de 30 segundos (ritmo tranquilo).'
    ]).setRequired(true);

  f2.addMultipleChoiceItem()
    .setTitle('3. ¿Cómo prefieres indicar si la res es Lado Izquierdo (IZQ) o Derecho (DER)?')
    .setChoiceValues([
      'Que el sistema alterne solo (primero IZQ, luego DER automáticamente).',
      'Presionar yo mismo un botón grande en la pantalla para confirmar el lado.'
    ]).setRequired(true);

  f2.addPageBreakItem().setTitle('PANTALLA, GUANTES Y ETIQUETAS');
  f2.addMultipleChoiceItem()
    .setTitle('4. ¿Qué guantes usas habitualmente al operar la pantalla?')
    .setChoiceValues([
      'Guantes de nitrilo / látex fino.',
      'Guantes térmicos o de goma gruesa.',
      'Guante de malla de acero en una mano.',
      'Sin guantes al momento de tocar la pantalla.'
    ]).setRequired(true);

  f2.addMultipleChoiceItem()
    .setTitle('5. Si la impresora Zebra se queda sin papel en mitad de la faena:')
    .setChoiceValues([
      'Prefiero que el sistema me deje seguir pesando y guarde las etiquetas para imprimirlas todas juntas al cambiar el rollo.',
      'Prefiero que se frene el pesaje hasta cambiar el rollo para no confundir las reses.'
    ]).setRequired(true);

  f2.addMultipleChoiceItem()
    .setTitle('6. Inicio de sesión / Identificación de operario:')
    .setChoiceValues([
      'Prefiero poner mi PIN una sola vez al inicio del turno y que quede abierto.',
      'Prefiero escanear un código de barras en mi credencial para abrir mi sesión rápida.'
    ]).setRequired(true);

  f2.addParagraphTextItem().setTitle('¿Qué cosas te molestan o te hacen perder tiempo de los sistemas que usas hoy?');

  links.push({
    formulario: '2. Frigorífico - Operario',
    editUrl: f2.getEditUrl(),
    viewUrl: f2.getPublishedUrl()
  });

  // ==========================================================================
  // FORMULARIO 3: FÁBRICA - RESPONSABLE
  // ==========================================================================
  var f3 = FormApp.create('SPI - 3. Fábrica de Chacinados (Responsable / Maestro Chacinero)');
  f3.setDescription(
    'Cuestionario de definición para Maestro Chacinero, Jefe de Fábrica y Responsables de Calidad.\n' +
    'Objetivo: Definir formulación de recetas, mermas de secado, tolerancias y control de puntos críticos.'
  );
  f3.setProgressBar(true);

  f3.addTextItem().setTitle('Nombre y Apellido:').setRequired(true);
  f3.addTextItem().setTitle('Puesto / Rol en Fábrica:').setRequired(true);

  f3.addPageBreakItem().setTitle('RECETAS Y TOLERANCIAS DE FORMULACIÓN');
  f3.addMultipleChoiceItem()
    .setTitle('1. Rigidez en el pesaje de ingredientes (ej. 70% Magro y 30% Tocino):')
    .setChoiceValues([
      '🔴 Bloqueo duro: No permitir procesar la batea si el desvío supera el ±1% de la receta teórica.',
      '🟡 Alerta suave: Avisar del desvío en pantalla, recalcular el costo/rendimiento real y permitir embutir.',
      '🟢 Permisivo: Registrar lo que realmente pesaron sin exigir concordancia estricta con la receta.'
    ]).setRequired(true);

  f3.addMultipleChoiceItem()
    .setTitle('2. Uso del Tocino Industrial (Lote Fijo 00049):')
    .setChoiceValues([
      'Todo el tocino dorsal propio debe ingresar y consumirse bajo el lote fijo 00049.',
      'Podemos tener diferentes lotes de tocino según la fecha o el proveedor.'
    ]).setRequired(true);

  f3.addPageBreakItem().setTitle('PUNTOS CRÍTICOS Y CONTROL DE SECADO');
  f3.addMultipleChoiceItem()
    .setTitle('3. Temperatura máxima de masa durante picado/mezclado:')
    .setChoiceValues([
      '🔴 Bloquear embutido si la masa supera los 6.0 °C (exigir enfriado con escarcha/hielo).',
      '🟡 Emitir advertencia visual de masa caliente pero permitir que el Maestro decida si embute.',
      '🟢 No bloquear; solo guardar el dato para control bromatológico.'
    ]).setRequired(true);

  f3.addMultipleChoiceItem()
    .setTitle('4. Control de merma en salames y secos (Objetivo 35% - 38% a 20-30 días):')
    .setChoiceValues([
      'Pesamos carros completos periódicamente para verificar la curva de secado.',
      'Pesamos ristras testigo marcadas con precinto como patrón del lote.',
      'El punto final lo determina el Maestro Fiambrero por tacto, dureza y aroma.'
    ]).setRequired(true);

  f3.addMultipleChoiceItem()
    .setTitle('5. Acción si a día 25 la merma está fuera de rango (< 30% o > 42%):')
    .setChoiceValues([
      'Bloquear el lote para despacho hasta que Calidad dé el visto bueno.',
      'Notificar por alerta en AppSheet al Maestro Chacinero para ajuste de secadero sin bloquear.'
    ]).setRequired(true);

  f3.addParagraphTextItem().setTitle('Comentarios u observaciones para Fábrica (Responsable):');

  links.push({
    formulario: '3. Fábrica - Responsable',
    editUrl: f3.getEditUrl(),
    viewUrl: f3.getPublishedUrl()
  });

  // ==========================================================================
  // FORMULARIO 4: FÁBRICA - OPERARIO
  // ==========================================================================
  var f4 = FormApp.create('SPI - 4. Fábrica de Chacinados (Operario de Batea y Embutido)');
  f4.setDescription(
    'Cuestionario para el Operario de Balanza Moretti, Picado, Mezclado y Embutido.\n' +
    'Objetivo: Diseñar una pantalla simple, rápida y fácil de usar mientras se trabaja con carnes y especias.'
  );
  f4.setProgressBar(true);

  f4.addTextItem().setTitle('Nombre y Apellido:').setRequired(true);
  f4.addTextItem().setTitle('Sector de trabajo (ej. Pesaje de batea, Cutter, Embutidora):').setRequired(true);

  f4.addPageBreakItem().setTitle('DINÁMICA DE PESAJE EN BALANZA MORETTI');
  f4.addMultipleChoiceItem()
    .setTitle('1. ¿Cómo pesas habitualmente los ingredientes?')
    .setChoiceValues([
      'Peso todo adentro del mismo recipiente o batea grande, usando el botón de TARA entre ingrediente e ingrediente.',
      'Peso cada ingrediente por separado en tachos o cajones individuales y luego vuelco a la máquina.'
    ]).setRequired(true);

  f4.addMultipleChoiceItem()
    .setTitle('2. ¿Cómo mides la temperatura de la carne picada/masa hoy en día?')
    .setChoiceValues([
      'Con un termómetro pincha-carne con aguja digital.',
      'Con una pistola láser infrarroja.',
      'La máquina mezcladora/cutter tiene su propio reloj de temperatura.',
      'No medimos temperatura con termómetro; nos guiamos por el frío al tacto.'
    ]).setRequired(true);

  f4.addPageBreakItem().setTitle('PANTALLA TÁCTIL Y RITMO DE TRABAJO');
  f4.addMultipleChoiceItem()
    .setTitle('3. ¿Cómo tienes las manos habitualmente al momento de confirmar un pesaje?')
    .setChoiceValues([
      'Con grasa, restos de carne o agua (necesito botones muy grandes para tocar con nudillo o codo).',
      'Uso guantes limpios o me saco el guante para tocar la pantalla.'
    ]).setRequired(true);

  f4.addMultipleChoiceItem()
    .setTitle('4. Al terminar de embutir chacinados frescos (chorizos):')
    .setChoiceValues([
      'Pesamos todo el lote completo de ristras juntas.',
      'Pesamos cajón por cajón a medida que vamos llenando.',
      'Contamos solo las unidades/ristras sin volver a pesar.'
    ]).setRequired(true);

  f4.addParagraphTextItem().setTitle('¿Qué sugerencia tienes para que el nuevo programa no te haga perder tiempo en la fábrica?');

  links.push({
    formulario: '4. Fábrica - Operario',
    editUrl: f4.getEditUrl(),
    viewUrl: f4.getPublishedUrl()
  });

  // ==========================================================================
  // SALIDA CON ENLACES EN EL LOG
  // ==========================================================================
  Logger.log('==================================================================');
  Logger.log('🎉 ¡LOS 4 FORMULARIOS FUERON CREADOS CON ÉXITO EN TU DRIVE!');
  Logger.log('==================================================================');
  for (var i = 0; i < links.length; i++) {
    Logger.log('');
    Logger.log('📌 ' + links[i].formulario.toUpperCase());
    Logger.log('   ✏️ Link para EDITAR: ' + links[i].editUrl);
    Logger.log('   📱 Link para MANDAR POR WHATSAPP: ' + links[i].viewUrl);
  }
  Logger.log('==================================================================');
}

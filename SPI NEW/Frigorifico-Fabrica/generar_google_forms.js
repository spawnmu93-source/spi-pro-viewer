/**
 * ============================================================================
 * SCRIPT PARA CREAR EL FORMULARIO GOOGLE FORMS AUTOMÁTICAMENTE
 * Sistema de Producción Integral (SPI) - Módulos Frigorífico y Fábrica
 * ============================================================================
 * 
 * INSTRUCCIONES DE USO EN 1 MINUTO:
 * 1. Abre tu navegador y ve a: https://script.new (inicia sesión con tu cuenta de Google).
 * 2. Borra el código que aparece por defecto y PEGA TODO EL CONTENIDO de este archivo.
 * 3. Haz clic en el botón "Ejecutar" (Run) con el icono de Play ▶️ arriba.
 * 4. Acepta los permisos que te solicite Google (Revisar permisos -> Avanzado -> Ir a...).
 * 5. ¡LISTO! El script creará automáticamente el formulario en tu Google Drive y
 *    mostrará en el registro de ejecución los enlaces para editarlo y para enviarlo por WhatsApp.
 * ============================================================================
 */

function crearFormularioOperativoSPI() {
  // 1. Crear el formulario con título y descripción
  var form = FormApp.create('SPI - Cuestionario Operativo (Frigorífico y Fábrica)');
  form.setDescription(
    'Cuestionario para definir los flujos reales de trabajo, qué procesos deben ser bloqueantes y cuáles flexibles.\n' +
    'Dirigido a: Responsables de Frigorífico, Faena, SENASA/Calidad y Fábrica de Chacinados.\n' +
    'Objetivo: Diseñar el software exactamente a la medida de la planta.'
  );
  form.setProgressBar(true);

  // --------------------------------------------------------------------------
  // SECCIÓN 0: IDENTIFICACIÓN DEL RESPONSABLE
  // --------------------------------------------------------------------------
  var sec0 = form.addSectionHeaderItem();
  sec0.setTitle('DATOS DEL RESPONSABLE');
  sec0.setHelpText('Por favor ingresa tus datos para asociar tus respuestas a tu sector.');

  var nombre = form.addTextItem();
  nombre.setTitle('Nombre y Apellido:').setRequired(true);

  var rol = form.addMultipleChoiceItem();
  rol.setTitle('Rol / Puesto en la empresa:')
     .setChoiceValues([
       'Responsable de Frigorífico / Faena',
       'Médico Veterinario Inspector (SENASA / Calidad)',
       'Maestro Fiambrero / Jefe de Fábrica de Chacinados',
       'Supervisor de Planta / Mantenimiento',
       'Gerencia de Operaciones'
     ])
     .setRequired(true);

  // --------------------------------------------------------------------------
  // SECCIÓN 1: FRIGORÍFICO - RECEPCIÓN Y CORRALES
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 1: FRIGORÍFICO - RECEPCIÓN Y CORRALES');

  var q1_1 = form.addMultipleChoiceItem();
  q1_1.setTitle('1.1. Si los kilos de báscula viva difieren > 2% de los declarados en el DT-e SENASA:');
  q1_1.setChoiceValues([
    'Bloquear la tropa (No permitir faenar sin clave de supervisor)',
    'Alerta blanda (Aviso visual en pantalla pero permite descargar a corrales)',
    'Registro silencioso (No frena la operación, solo reporta a gerencia)'
  ]);

  var q1_2 = form.addMultipleChoiceItem();
  q1_2.setTitle('1.2. Control de tiempo de descanso de animales en corrales (2 a 4 horas):');
  q1_2.setChoiceValues([
    'Obligatorio: El sistema no debe permitir noquear cerdos antes del tiempo mínimo',
    'Recomendación: Mostrar aviso pero permitir faenar si hay urgencia',
    'Libre: El inicio de faena lo decide el jefe de faena sin intervención del sistema'
  ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 2: INSPECCIÓN SANITARIA Y SENASA
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 2: INSPECCIÓN VETERINARIA Y SENASA');

  var q2_1 = form.addMultipleChoiceItem();
  q2_1.setTitle('2.1. ¿Cómo debe ser la mecánica de aprobación sanitaria en la balanza de gancho?');
  q2_1.setChoiceValues([
    'Aprobación por Excepción (Recomendada): Toda res que llega se considera APTA por defecto a menos que el veterinario accione un decomiso.',
    'Bloqueo Unitario: La balanza NO pesa ni imprime etiqueta si el veterinario no dio "Apto" previo a cada res.',
    'Carga Posterior: Se faena continuo y las actas de decomiso se cargan al final de la tropa desde una planilla.'
  ]);

  var q2_2 = form.addMultipleChoiceItem();
  q2_2.setTitle('2.2. Ante un DECOMISO TOTAL (ej. Triquinosis / Cisticercosis):');
  q2_2.setChoiceValues([
    'Imprimir etiqueta roja de "DECOMISO SANITARIO" para identificar la res en digestor',
    'No imprimir ninguna etiqueta y marcar la res como baja directa en el sistema',
    'Generar automáticamente el acta oficial SENASA en PDF'
  ]);

  var q2_3 = form.addMultipleChoiceItem();
  q2_3.setTitle('2.3. Cuando ocurre un DECOMISO PARCIAL (pulmón, hígado, cabeza):');
  q2_3.setChoiceValues([
    'La media res sigue su curso y solo se anotan los kilos/órganos decomisados',
    'Se debe descontar el peso del órgano del rendimiento oficial de la canal'
  ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 3: PESAJE AL GANCHO Y TIPIFICACIÓN
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 3: PESAJE AL GANCHO Y ETIQUETADO ZEBRA');

  var q3_1 = form.addMultipleChoiceItem();
  q3_1.setTitle('3.1. Dinámica de pesaje en riel aéreo (Balanza Systel):');
  q3_1.setChoiceValues([
    'La media res se detiene completamente sobre la celda de carga para estabilizar',
    'El pesaje es al paso (en movimiento continuo sobre la noria)'
  ]);

  var q3_2 = form.addCheckboxItem();
  q3_2.setTitle('3.2. Parámetros de calidad que se miden en el pesaje (marca todos los que apliquen):');
  q3_2.setChoiceValues([
    'Espesor de grasa dorsal (milímetros)',
    'Porcentaje de carne magra estimado (%)',
    'pH de la carne a 45 minutos',
    'Conformación visual de la res',
    'Ninguno (solo nos interesa el peso neto al gancho)'
  ]);

  var q3_3 = form.addMultipleChoiceItem();
  q3_3.setTitle('3.3. Si la impresora Zebra se queda sin papel o se traba en plena faena:');
  q3_3.setChoiceValues([
    'Frenar el pesaje inmediatamente hasta que se solucione la impresora',
    'Seguir pesando normalmente, guardar las etiquetas en cola y sacarlas todas juntas al recargar rollo'
  ]);

  var q3_4 = form.addMultipleChoiceItem();
  q3_4.setTitle('3.4. Re-impresión de etiquetas dañadas de media res:');
  q3_4.setChoiceValues([
    'Libre: Cualquier operario puede volver a imprimir la etiqueta',
    'Controlada: Requiere autorización con PIN de supervisor para evitar clonación de lotes'
  ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 4: CÁMARAS Y DESPOSTE DE FRIGORÍFICO
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 4: OREADO Y DESPOSTE DE FAENA');

  var q4_1 = form.addMultipleChoiceItem();
  q4_1.setTitle('4.1. Pesaje en frío a las 24 horas (Control de Merma de Oreado):');
  q4_1.setChoiceValues([
    'Se pesan el 100% de las medias reses al salir de cámara',
    'Se pesa solo una muestra representativa (ej. 10 medias reses)',
    'Se pesa el camión completo cargado de despacho'
  ]);

  var q4_2 = form.addMultipleChoiceItem();
  q4_2.setTitle('4.2. Tocino Dorsal para Fábrica de Chacinados (Lote Fijo 00049):');
  q4_2.setChoiceValues([
    'Se junta en cajones/bins y se pesa el lote consolidado al final del turno',
    'Se pesa cajón por cajón a medida que sale de las mesas de desposte'
  ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 5: FÁBRICA DE CHACINADOS
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 5: FÁBRICA DE CHACINADOS Y EMBUTIDOS');

  var q5_1 = form.addMultipleChoiceItem();
  q5_1.setTitle('5.1. Rigidez en el pesaje de la receta (ej. 70% Magro y 30% Tocino):');
  q5_1.setChoiceValues([
    'Estricto: Bloquear el embutido si el operario se desvía más de ±1% de la fórmula',
    'Alerta suave: Avisar del desvío, recalcular el rendimiento real y permitir embutir',
    'Permisivo: Registrar lo que pesaron sin validar contra la receta teórica'
  ]);

  var q5_2 = form.addMultipleChoiceItem();
  q5_2.setTitle('5.2. Control de TEMPERATURA DE MASA durante el mezclado/picado:');
  q5_2.setChoiceValues([
    'Bloquear el embutido si la masa supera los 6.0 °C hasta que se agregue escarcha/hielo',
    'Mostrar cartel de advertencia de masa caliente, pero dejar que el Maestro Chacinero decida si sigue',
    'No bloquear; solo anotar la temperatura para registro bromatológico'
  ]);

  var q5_3 = form.addMultipleChoiceItem();
  q5_3.setTitle('5.3. Control de Secado en Salames (Merma objetivo 35% - 38% en 20-30 días):');
  q5_3.setChoiceValues([
    'Pesamos carros completos periódicamente',
    'Pesamos ristras testigo marcadas con precinto',
    'El punto se determina por tacto y textura del Maestro Fiambrero'
  ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 6: MATRIZ DE DECISIÓN "BLOQUEAR VS. PERMITIR"
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 6: MATRIZ DE FRICCIÓN (¿QUÉ DEBE BLOQUEAR LA PANTALLA?)');

  var grid = form.addGridItem();
  grid.setTitle('Para cada situación, selecciona qué nivel de control prefieres:')
      .setRows([
        '1. Balanza se desconecta durante el turno',
        '2. Rendimiento de faena da inferior al 79.5%',
        '3. Temperatura de masa en fábrica supera 6.0°C',
        '4. Merma de secado de salames fuera de rango',
        '5. Despacho de mercadería con alerta sanitaria',
        '6. Se solicita usar pesaje manual por rotura de balanza'
      ])
      .setColumns([
        '🔴 Bloqueo Duro (Requiere PIN)',
        '🟡 Advertencia Blanda (Deja seguir)',
        '🟢 Silencioso (Solo reporte)'
      ]);

  // --------------------------------------------------------------------------
  // SECCIÓN 7: COMENTARIOS Y CASOS ESPECIALES
  // --------------------------------------------------------------------------
  form.addPageBreakItem().setTitle('SECCIÓN 7: COMENTARIOS Y CASOS PARTICULARES');

  var com = form.addParagraphTextItem();
  com.setTitle('Comentarios adicionales o particularidades de su planta:')
     .setHelpText('Cuéntanos cualquier detalle de su día a día que quieran que el software contemple.');

  // Finalización
  Logger.log('===============================================================');
  Logger.log('✅ ¡FORMULARIO CREADO CON ÉXITO EN TU GOOGLE DRIVE!');
  Logger.log('🔗 Link para EDITAR el formulario: ' + form.getEditUrl());
  Logger.log('📱 Link para ENVIAR por WhatsApp: ' + form.getPublishedUrl());
  Logger.log('===============================================================');
}

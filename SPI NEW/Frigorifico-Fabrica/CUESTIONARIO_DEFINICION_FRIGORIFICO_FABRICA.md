# 📋 CUESTIONARIO OPERATIVO Y DE DEFINICIÓN FINA
## SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - MÓDULOS FRIGORÍFICO Y FÁBRICA

> **Dirigido a:**  
> - Responsable de Frigorífico / Jefe de Planta de Faena  
> - Médico Veterinario Inspector (SENASA / Calidad)  
> - Maestro Fiambrero / Jefe de Producción de Fábrica de Chacinados  
> - Responsable de Control de Calidad y Auditoría  
> - Gerencia de Operaciones  
>
> **Objetivo de este Cuestionario:**  
> Diseñar la programación del sistema **exactamente a la medida de la realidad operativa de la planta**, eliminando trabas burocráticas innecesarias y estableciendo con precisión:
> 1. Dónde el software debe ser **estricto y bloqueante** (para proteger la sanidad, la inocuidad y la trazabilidad legal).
> 2. Dónde el software debe ser **ágil y permisivo** (para no frenar la línea de producción ni generar cuellos de botella con pantallas lentas).
> 3. Cómo se mueve físicamente la mercadería y la información en el día a día.

---

## 📌 GUÍA RÁPIDA: LOS 3 NIVELES DE CONTROL EN PROGRAMACIÓN
Al responder cada punto, por favor considerar qué nivel de limitación prefieren que aplique el sistema:

* 🔴 **BLOQUEO DURO (Hard Stop):** La pantalla se congela o no permite continuar el proceso bajo ninguna circunstancia a menos que se cumpla la condición o un supervisor ingrese un PIN de desbloqueo.
* 🟡 **ADVERTENCIA BLANDA (Soft Warning):** El sistema muestra un cartel llamativo en amarillo y emite un sonido, pero permite que el operario presione *"Continuar de todos modos"*, dejando registrado quién lo autorizó.
* 🟢 **REGISTRO SILENCIOSO (Audit Log):** La pantalla no interrumpe al operario en absoluto; registra el desvío en segundo plano para que la gerencia y calidad lo vean en su reporte diario.

---

# SECCIÓN A: FRIGORÍFICO Y LÍNEA DE FAENA

## 1. Recepción de Tropas y Báscula de Camiones
1. **Llegada y Documentación:**
   - ¿El ingreso de la tropa con el DT-e de SENASA se registra en el momento exacto en que llega el camión o se hace una carga previa/posterior desde la oficina?
   - ¿Qué datos del DT-e son indispensables para ustedes al momento de descargar los animales? (Nro DT-e, cabezas declaradas, kilos origen, RENSPA, transportista).
2. **Pesaje Vivo en Báscula:**
   - ¿Tienen báscula propia de camiones integrada o el peso vivo se digita a partir del ticket impreso de la balanza puente?
   - Si los kilos pesados difieren significativamente de los declarados en el DT-e (ej. más del 2% de merma de viaje):
     - [ ] **Bloquear la tropa:** No permitir faenar hasta que el supervisor lo autorice.
     - [ ] **Alerta blanda:** Mostrar advertencia en pantalla pero permitir ingresar la tropa a corrales.
     - [ ] **Solo registrar:** Calcular la merma en el reporte sin avisos en planta.
3. **Manejo en Corrales:**
   - ¿Es obligatorio para ustedes que el sistema valide un tiempo mínimo de descanso de los animales (ej. 2 a 4 horas) antes de habilitar el noqueo?
   - ¿O prefieren que el inicio de faena sea libre según la urgencia del día?

---

## 2. Inspección Sanitaria Veterinaria y SENASA (Dinámica Real)
*Este es un punto crítico para calibrar la fluidez del software:*

1. **Ubicación y Método del Veterinario:**
   - ¿Cómo trabaja físicamente el veterinario en la línea?
     - [ ] Puesto fijo con pantalla/tablet donde aprueba o decomisa en tiempo real.
     - [ ] Trabaja al pie de la noria inspeccionando y anota en planilla papel, cargándose al final de la jornada.
     - [ ] Trabaja sobre la línea pero solo interviene cuando hay un problema (inspección por excepción).
2. **Mecánica de Aprobación Sanitaria:**
   - **Opción A (Bloqueo Unitario):** El operario de la balanza de gancho no puede pesar ni etiquetar ninguna media res si el veterinario no le dio "Aprobado" previamente en el sistema.
   - **Opción B (Aprobación por Defecto / Excepción - RECOMENDADA EN FAENA RÁPIDA):** Toda res que llega a la balanza se considera "Apta" por defecto. Si el veterinario detecta una patología, marca el gancho o acciona un botón/tarjeta de decomiso que desvía la canal al digestor y bloquea su etiqueta apta.
   - ¿Cuál de estas opciones se adapta mejor a la velocidad de su faena?
3. **Tipos de Decomisos y su Impacto:**
   - Cuando hay un **decomiso parcial** (ej. pulmón, hígado, cabeza):
     - ¿Afecta el pesaje de la media res o solo se registra la cantidad/kilos de menudencias descartadas?
   - Cuando hay un **decomiso total** (ej. triquinosis, ictericia generalizada):
     - ¿La res completa va a digestor? ¿Debe el sistema imprimir una etiqueta especial de color o alerta de *"NO APTO - DECOMISO"* para que no se mezcle físicamente en la cámara?
4. **Actas de Decomiso SENASA:**
   - ¿Las actas oficiales se deben generar en PDF automáticamente por cada animal decomisado, o se emite un acta resumen al finalizar la tropa con el total de kilos y motivos?

---

## 3. Pesaje al Gancho Aéreo y Tipificación (Balanza Systel)
1. **Dinámica del Gancho:**
   - ¿La media res se pesa detenida en el tramo de balanza o pasa en movimiento continuo sobre el riel?
   - ¿Cuánto tiempo aproximado permanece la media res en la zona de pesaje? (segundos).
   - ¿Tienen tara fija calibrada para las roldanas/ganchos o varía según el tipo de gancho?
2. **Tipificación de Calidad:**
   - ¿Qué parámetros de tipificación miden actualmente al momento del pesaje?
     - [ ] Espesor de grasa dorsal (en milímetros).
     - [ ] Porcentaje de magro estimado (% de carne magra).
     - [ ] pH de la carne (a 45 minutos post-sangrado).
     - [ ] Conformación visual de la canal.
     - [ ] Ninguno (solo se registra el peso neto).
   - Si se miden: ¿Quién y cómo ingresa estos datos? (¿El mismo pesador mediante pantalla táctil, un segundo operario, o se mide solo a una muestra de animales?).
   - ¿Es obligatorio ingresar la grasa/magro para imprimir la etiqueta, o puede quedar vacío si la línea viene muy rápida?
3. **Identificación de Lado (Media Res Izquierda vs Derecha):**
   - ¿Desean que el sistema alterne automáticamente `IZQ` y `DER` en cada pesada, o el operario debe presionar un botón para confirmar el lado?
   - ¿Qué sucede si una media res se cae o se retira de la línea? ¿Cómo prefieren corregir la numeración?

---

## 4. Etiquetado Físico con Impresora Zebra (ZPL)
1. **Colocación de la Etiqueta:**
   - ¿En qué parte física de la media res se coloca la etiqueta? (Pierna, falda, gancho).
   - ¿Usan etiquetas autoadhesivas comunes, térmicas reforzadas para humedad/grasa, o tarjetas plásticas colgantes abrochadas?
2. **Manejo de Errores e Impresión:**
   - Si la impresora Zebra se queda sin papel o se traba en plena faena:
     - ¿El sistema debe **frenar el pesaje** hasta que se solucione?
     - ¿O debe **guardar los pesajes en cola** y permitir imprimir el lote de etiquetas juntas cuando se recargue el rollo?
   - **Re-impresión de Etiquetas dañadas:**  
     - ¿Cualquier operario puede re-imprimir una etiqueta de media res o debe requerir contraseña de supervisor para evitar duplicación de códigos?

---

## 5. Cámaras de Oreado, Desposte de Planta y Tocino Industrial
1. **Control de Merma de Cámara (Oreado 24 horas):**
   - Al día siguiente de la faena: ¿Vuelven a pesar todas las medias reses frías al salir de la cámara para calcular la merma exacta de oreado, o solo hacen un pesaje global por camión/muestreo?
   - ¿Cuál consideran que es la merma máxima normal tolerada en su cámara fría? (Valor de referencia: 1.5% a 2.0%).
2. **Desposte en Frigorífico y Generación de Tocino (Lote Fijo `00049`):**
   - Las medias reses que no se despachan enteras a carnicerías y se despostan en planta:
     - ¿Hasta qué nivel de detalle quieren registrarlas? (¿Cortes mayores como Jamón/Paleta/Carré, o corte por corte?).
   - **El Tocino Dorsal para Fábrica:**
     - ¿Cómo se junta físicamente el tocino que sale de las mesas de desposte? (Cajones plásticos, bins de 300 kg, carritos).
     - ¿En qué momento se le asigna el lote fijo `00049`? ¿Se pesa cajón por cajón o se hace un pesaje total del día antes de mandarlo a la fábrica de chacinados?

---

# SECCIÓN B: FÁBRICA DE CHACINADOS Y EMBUTIDOS

## 6. Recepción de Materias Primas y Formulación
1. **Abastecimiento de Carne y Grasas:**
   - ¿La carne que entra a fábrica proviene 100% del desposte propio o compran también recortes de terceros con otros números de lote?
   - ¿Cómo se identifica la carne magra que ingresa a batea? (¿Viene con la etiqueta del frigorífico con código de barras o se vuelca en masa?).
2. **Gestión de Recetas:**
   - ¿Quién tiene autorización para crear o modificar los porcentajes de una receta (Salame, Chorizo, Morcilla, Bondiola)?
   - **Flexibilidad en la Formulación:**
     - Si la receta teórica dice *"70% Magro y 30% Tocino"*, pero en planta el operario puso *68% y 32%*:
       - [ ] **Bloquear:** No permitir procesar la masa si el desvío supera el ±1%.
       - [ ] **Alerta suave:** Mostrar aviso del desvío, recalcular el costo/rendimiento y permitir embutir.
       - [ ] **Permisivo total:** Registrar los kilos reales pesados sin exigir concordancia exacta con la receta teórica.
3. **Manejo del Tocino Industrial (`00049`):**
   - ¿Todo el tocino utilizado en embutidos debe provenir obligatoriamente del lote `00049` o pueden convivir otros lotes de grasa?

---

## 7. Pesaje en Batea y Mezclado (Balanza Moretti)
1. **Dinámica de Pesaje:**
   - ¿El operario pesa ingrediente por ingrediente arriba de la misma balanza de plataforma (usando tara acumulativa), o pesan cada cosa por separado en tachos y luego vuelcan a la mezcladora?
   - ¿Qué capacidad máxima y precisión tiene la balanza Moretti utilizada?
2. **Control de Temperatura de Masa (Punto Crítico Bromatológico):**
   - ¿Cómo miden actualmente la temperatura de la masa durante el picado/mezclado?
     - [ ] Termómetro pincha-carne manual digital (el operario lee la aguja/pantalla y la digita).
     - [ ] Sensor infrarrojo / pistola láser.
     - [ ] Sensor integrado en la máquina cutter/mezcladora.
   - **Límites Térmicos:**
     - ¿A qué temperatura consideran que la masa está en riesgo de "empaste" o deterioro de grasa? (Normalmente > 4°C a 6°C).
     - Si la temperatura supera el límite seguro:
       - ¿Quieren que el sistema **bloquee el embutido** hasta que se enfríe con escarcha de hielo?
       - ¿O prefieren que solo emita una advertencia sin frenar a los operarios?

---

## 8. Embutido, Destino y Control de Mermas (Secadero)
1. **Productos Frescos (Chorizos, Salchichas parrillera):**
   - Una vez embutida la masa: ¿Se pesan todas las ristras juntas o por cajón antes de entrar a cámara de frío?
   - ¿Necesitan que el sistema calcule el rendimiento inmediato de la masa fresca ($\text{Kilos obtenidos} \div \text{Kilos masa cargada}$)?
2. **Productos Secos-Curados (Salames, Salamines, Bondiolas):**
   - **Pesaje inicial:** ¿Se pesa la totalidad de los carros que entran a estufa/secadero o se toma una muestra de ristras testigo (patrón)?
   - **Control periódico durante los 20-30 días de secado:**
     - ¿Cada cuántos días se controla el secado? (ej. días 7, 14, 21, 28).
     - ¿Quién realiza este control y dónde lo anota hoy en día?
   - **Merma de Salida (Objetivo 35% - 38%):**
     - Si un lote de salames llega al día 25 con una merma del 42% (muy seco) o del 28% (falto de secado):
       - ¿Qué acción debe tomar el sistema? (¿Alerta al Maestro Chacinero, aviso en AppSheet, bloqueo de despacho hasta evaluación de calidad?).

---

# SECCIÓN C: MATRIZ DE DECISIÓN "BLOQUEAR VS. PERMITIR"
*Por favor marquen con una cruz (X) en cada fila cómo desean que se comporte el sistema:*

| Situación Operativa | 🔴 Bloquear Pantalla (No avanza sin PIN) | 🟡 Advertir y Permitir (Aviso visual/sonoro) | 🟢 Silencioso (Solo reporte gerencial) |
|---|:---:|:---:|:---:|
| **1. Kilos báscula vivos difieren > 2% del DT-e SENASA** | [ ] | [ ] | [ ] |
| **2. Media res llega a balanza sin aprobación SENASA explícita** | [ ] | [ ] | [ ] |
| **3. Peso de balanza oscila o no estabiliza en 3 segundos** | [ ] | [ ] | [ ] |
| **4. Se solicita re-imprimir una etiqueta de media res ya emitida**| [ ] | [ ] | [ ] |
| **5. Rendimiento de faena de la tropa da inferior al 79.5%** | [ ] | [ ] | [ ] |
| **6. Kilos de carne en batea difieren > 2% de la receta teórica** | [ ] | [ ] | [ ] |
| **7. Temperatura de masa de chacinado supera los 4.5 °C** | [ ] | [ ] | [ ] |
| **8. Temperatura de masa de chacinado supera los 6.0 °C** | [ ] | [ ] | [ ] |
| **9. Merma de secado de salames fuera del rango 35%-38%** | [ ] | [ ] | [ ] |
| **10. Se intenta despachar mercadería de un lote con alerta sanitaria**| [ ] | [ ] | [ ] |
| **11. Balanza pierde conexión serie RS-232 durante el turno** | [ ] | [ ] | [ ] |
| **12. Impresora Zebra se queda sin papel o cinta ribbon** | [ ] | [ ] | [ ] |

---

# SECCIÓN D: CONTINGENCIAS, HARDWARE Y USUARIOS EN PLANTA

## 9. Entorno de Trabajo y Operarios
1. **Uso de Pantallas en Planta:**
   - ¿Qué tipo de guantes utilizan los operarios en los puestos de balanza? (Látex fino, nitrilo, guantes térmicos gruesos, guantes de malla de acero).
   - ¿Hay salpicaduras directas de agua/grasa en el puesto de la balanza durante el trabajo o la limpieza con hidrolavadora?
2. **Identificación y Turnos:**
   - ¿Cada operario debe ingresar su PIN personal cada vez que realiza una pesada, o el puesto queda logueado para todo el turno de trabajo?
   - Si se turnan los descansos: ¿Cómo prefieren cambiar de usuario de forma rápida? (Lector de código de barras en credencial, botón táctil con foto, PIN numérico simple de 4 dígitos).

## 10. Contingencias y Modo de Emergencia
1. **Falla de Balanza Automática:**
   - Si por un desperfecto eléctrico la balanza no transmite datos por RS-232:
     - ¿Desean tener habilitado un botón de *"Carga Manual de Kilos"* en la pantalla?
     - Si se habilita: ¿Debe requerir clave de supervisor para evitar que los operarios anoten pesos a mano por comodidad?
2. **Corte Total de Red / Sin Sincronización:**
   - Si la planta trabaja todo el día sin internet:
     - Las terminales operan 100% desconectadas gracias al buffer local. ¿Hay alguna información que sea crítica recibir de la oficina central durante el turno o el trabajo de faena es autosuficiente?

---

# SECCIÓN E: ALERTAS, NOTIFICACIONES Y DESTINATARIOS

Por favor indicar **quién y por qué medio** debe recibir cada aviso importante:

| Evento / Alerta Crítica | ¿Quién debe enterarse? (Puesto/Nombre) | ¿Por qué canal? (Pantalla planta / App móvil / WhatsApp / Email) |
|---|---|---|
| **Decomiso Total SENASA (> 2 cerdos)** | | |
| **Rendimiento de Tropa por debajo del 79%** | | |
| **Masa de Chacinados recalentada (> 5.5°C)** | | |
| **Lote de Salames con hongo/secado desparejo** | | |
| **Falla en cámara de frío (Temp > 4°C)** | | |
| **Cierre de Tropa completado (Resumen final)**| | |
| **Cierre de Bachada completado (Rendimiento)** | | |

---

## 📝 ESPACIO PARA COMENTARIOS LIBRES DE LOS RESPONSABLES:
*(Por favor indicar aquí cualquier particularidad de su trabajo diario que sientan que los sistemas tradicionales no contemplan, cosas que les molesten de otros programas que hayan usado, o ideas que crean que agilizarían su jornada).*

- **Comentarios Frigorífico:**  
  ___________________________________________________________________________________________________  
  ___________________________________________________________________________________________________  

- **Comentarios Fábrica de Chacinados:**  
  ___________________________________________________________________________________________________  
  ___________________________________________________________________________________________________  

---

*Cuestionario generado para el Sistema de Producción Integral (SPI). Una vez completado por los responsables de área, se utilizará para parametrizar las validaciones y los flujos definitivos en el código.*

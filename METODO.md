# METODOLOGÍA Y REGLAS DE DISEÑO VISUAL — SISTEMA DE PRODUCCIÓN INTEGRAL (SPI)

Este documento define las reglas de diseño ergonómico, arquitectura de interfaces (Tkinter / CustomTkinter) y el protocolo de control de calidad previo a la entrega para terminales industriales en planta.

---

## 🎯 OBJETIVO
Garantizar que ninguna actualización o modificación de pantalla produzca regresiones visuales (botones fuera de pantalla, desbordes por alertas dinámicas, menús táctiles bloqueados o textos ilegibles para los operarios).

---

## 🖥️ 1. Entorno de Operación y Resoluciones Críticas
Las terminales de planta funcionan en modo Kiosco sin bordes de ventana (`overrideredirect`), operadas con pantallas táctiles, a menudo con guantes, humedad y a distancia de lectura de ~1 metro.

Las dos resoluciones mandatorias de diseño son:
- **Terminal Vertical:** `768 x 1366 px`
- **Terminal Horizontal:** `1366 x 768 px`

> ⚠️ **REGLA ABSOLUTA:** Jamás diseñar ni validar asumiendo pantallas Full HD (1920x1080). Toda vista debe ser probada en las resoluciones mínimas industriales indicadas arriba.

---

## 📐 2. Reglas Arquitectónicas de Layout (Tkinter / CustomTkinter)

### Regla 1: Anclaje Inferior Primero (`Bottom-First Anchoring`)
En pantallas con formularios y acciones finales:
- **Toda botonera de acción (`FINALIZAR`, `CANCELAR`, `REGISTRAR`) debe empaquetarse ANTES que el contenido expandible**, utilizando:
  ```python
  frame_acciones.pack(side="bottom", fill="x", padx=..., pady=...)
  ```
- El contenido central (tablas, listados, formularios) se empaqueta **después**:
  ```python
  frame_central.pack(side="top", fill="both", expand=True)
  ```
*¿Por qué?* Si se empaqueta primero el contenido central con `expand=True`, cualquier alerta dinámica o aumento de filas empujará la botonera inferior fuera de la pantalla, dejando la terminal inoperable.

---

### Regla 2: Altura Adaptativa de Tablas y Listados
- Ningún `Treeview` o contenedor de lista debe tener una altura fija sobredimensionada que robe espacio a los controles.
- La altura debe ser dinámica en función del contenido real:
  ```python
  filas_reales = len(elementos)
  tree.configure(height=max(min(filas_reales, MAX_VISIBLES), MIN_FILAS))
  ```
- Si la lista supera la altura máxima permitida, debe poseer scrollbar vertical táctil ancho.

---

### Regla 3: Espacio Reservado para Alertas y Notificaciones
- Los banners de aviso, error o alerta de tolerancia (ej. desvíos de peso) **no deben expandir agresivamente la ventana**.
- Deben tener una altura compacta (1 o 2 líneas como máximo) o tener un espacio reservado previamente en el layout para que su aparición no mueva bruscamente los botones inferiores.

---

### Regla 4: Prohibición de Dropdowns Nativos en Pantallas Táctiles
- **QUEDA TERMINANTEMENTE PROHIBIDO el uso de `CTkComboBox` o menús emergentes (`TrackPopupMenu` de Windows)** en terminales táctiles Kiosco.
- *Causa:* Los drivers táctiles de Windows HID y el modo sin bordes suelen inhibir la captura de eventos del mouse, provocando que los dropdowns se congelen o no se desplieguen.
- *Solución estándar:* **Botoneras directas de selección táctil** (botones de selección inmediata visibles) o ventanas modales táctiles dedicadas con botones de gran formato.

---

### Regla 5: Límite Estricto de Columnas en Botoneras Táctiles (Máximo 3 Columnas)
- **Las cuadrículas de botones de opciones y cortes resultantes NUNCA deben superar las 3 columnas** (`num_cols <= 3`).
- *Causa:* En terminales verticales (768 px de ancho total), usar 4 o más columnas reduce el ancho útil de cada botón por debajo del umbral mínimo de usabilidad (~200 px). Esto genera:
  1. Truncamiento de los nombres de los cortes o productos (texto cortado o ilegible).
  2. Aumento de toques erróneos accidentales al operar con guantes o dedos húmedos.
- *Configuración obligatoria:* Configurar la grilla en **2 o 3 columnas** como máximo, asegurando una altura ergonómica de 45px - 50px por botón.

---

## 👆 3. Ergonomía Táctil y Legibilidad

| Elemento | Medida Mínima | Justificación |
| :--- | :--- | :--- |
| **Columnas en Botoneras Táctiles** | `Máximo 3 columnas` | Previene truncamiento de nombres y asegura ancho táctil para pulsar con guantes. |
| **Altura de Botón Táctil** | `50px - 65px` (o `45px` en grillas compactas) | Permite pulsación rápida y certera con guantes o dedos húmedos. |
| **Separación entre Botones** | `10px - 14px` | Previene toques dobles o accidentales entre botones críticos. |
| **Tipografía Operativa (Totales / Kilos)** | `18pt - 24pt` (Bold) | Legibilidad inmediata a más de 1 metro de distancia. |
| **Tipografía de Etiquetas / Instrucciones** | `14pt - 16pt` | Claridad bajo iluminación variable de planta frigorífica. |
| **Contraste de Colores** | Alto contraste | Fondo oscuro (#1A1A1A / #242424) con textos blanco puro o celeste nítido. Prohibido texto gris oscuro sobre fondo negro. |

---

## 🛡️ 4. La Línea de Verificación Previa a la Entrega

Antes de compilar, generar instaladores o hacer `push` a producción, se debe verificar y cumplir estrictamente el siguiente criterio de control:

```text
«VERIFICACIÓN DE PEOR ESCENARIO: En la resolución estricta de terminal (768x1366 / 1366x768), 
activar simultáneamente todos los elementos dinámicos (banner de alerta desplegado + cantidad 
máxima de filas en tabla); se aprueba la entrega ÚNICAMENTE si el 100% de la botonera inferior 
de acción permanece visible, accesible y con textos legibles a 1 metro de distancia sin requerir 
desplazamiento.»
```

---

## 📋 5. Checklist Rápido de Pre-Release

- [ ] ¿La botonera de acciones está anclada con `side="bottom"` antes de los componentes dinámicos?
- [ ] ¿Las cuadrículas de selección táctil (cortes/opciones) respetan el límite estricto de no más de 3 columnas?
- [ ] ¿Se verificó en resolución `768x1366` (vertical) y `1366x768` (horizontal)?
- [ ] ¿Se probó la vista con una alerta de error/tolerancia activada al mismo tiempo que la tabla llena?
- [ ] ¿Todos los botones principales tienen al menos 50px de alto y espacio suficiente para dedos con guantes?
- [ ] ¿Se eliminaron combos o desplegables en favor de botones directos o pop-ups modales?
- [ ] ¿El instalador Inno Setup incluye la última versión compilada y versionada (`config.py` / `APP_VERSION`)?

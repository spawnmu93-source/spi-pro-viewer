# PLAN DE IMPLEMENTACIÓN TÉCNICO SEGMENTADO: FRIGORÍFICO Y FÁBRICA
**Sistema de Producción Integral (SPI)**  
*Alcance:* Construcción integral del software de planta (Edge Industrial) y módulos de gestión móvil.  
*Estrategia:* Desarrollo segmentado por capas independientes (Hardware $\rightarrow$ Buffer Offline $\rightarrow$ UI Táctil $\rightarrow$ Sync $\rightarrow$ AppSheet) con arquitectura parametrizada adaptable a las respuestas de los 4 cuestionarios.

---

## 1. ESTRATEGIA DE CONSTRUCCIÓN DESACOPLADA Y PARAMETRIZADA

Para poder avanzar de inmediato en la programación de los módulos sin depender de los tiempos de respuesta de los 4 formularios, el código se estructura con un módulo de configuración central: `config_parametros.py`.

En este archivo se concentran las variables de comportamiento:
- Modos de bloqueo: `BLOQUEO_SENASA_ESTRICTO = False` (o `True` según respuesta).
- Tolerancia de báscula viva: `TOLERANCIA_DTE_PCT = 2.0`.
- Límites de temperatura de masa: `TEMP_MASA_ALERTA = 4.0`, `TEMP_MASA_BLOQUEO = 6.0`.
- Modo de alternancia de lado: `ALTERNANCIA_LADO_AUTO = True`.

> **Ventaja Clave:** Toda la arquitectura, conexiones seriales RS-232, buffers SQLite, pantallas táctiles y sincronización se programan y prueban con solidez técnica. Cuando los responsables de planta completen los formularios, solo se ajustarán los valores de este archivo sin tocar una sola línea del motor central.

---

## 2. ARQUITECTURA GENERAL Y SEGMENTACIÓN POR PARTES

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ARQUITECTURA DE DESARROLLO SPI                        │
├─────────────────────────┬─────────────────────────┬─────────────────────────┤
│ PARTE 1: HARDWARE CORE  │ PARTE 2: PERSISTENCIA   │ PARTE 3: UI FRIGORÍFICO │
│ - scale_driver.py       │ - local_db.py           │ - terminal_frigorifico  │
│ - zebra_printer.py      │ - SQLite WAL Mode       │ - Display 72px Systel   │
│ - Mocks de Balanza/ZPL  │ - Idempotency Keys      │ - Etiqueta Media Res    │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ PARTE 4: UI FÁBRICA     │ PARTE 5: SYNC ASÍNCRONO │ PARTE 6: APPSHEET CORE  │
│ - terminal_fabrica.py   │ - sync_worker.py        │ - Frigorífico DT-e/SENASA│
│ - Moretti Batea + Temp  │ - HTTPS + JWT           │ - Fábrica Recetas/Estufa│
│ - Etiqueta Bachada      │ - evento_lote (JSONB)   │ - Actas SENASA PDF      │
├─────────────────────────┴─────────────────────────┴─────────────────────────┤
│ PARTE 7: SUITE DE TESTING E2E, FAILOVER Y SIMULACIÓN OFFLINE                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### PARTE 1: CAPA DE HARDWARE INDUSTRIAL Y EMULADORES (PYTHON)
* **Objetivo:** Comunicar de forma confiable las balanzas y las impresoras térmicas.
* **Tecnologías y Librerías:** Python 3.10+, `pyserial`, `socket`, `threading`, `re`.
* **Componentes a programar:**
  1. `scale_driver.py`: Driver serial multi-protocolo para balanzas **Systel** (Cuora gancho aéreo) y **Moretti** (LAP batea/plataforma). Hilo daemon continuo no bloqueante, filtro debounce de peso estable (< 50ms) y auto-reconexión cíclica ante desconexión física de cable.
  2. `zebra_printer.py`: Motor ZPL-II parametrizable para etiquetas de Canal (100x75mm), Bachada (100x50mm) y Decomiso (75x50mm). Soporte para envío directo TCP (puerto 9100) y puerto serie.
  3. `mock_hardware.py`: Emuladores de balanzas por puerto virtual y receptor gráfico de tramas ZPL para programar y probar sin necesidad de tener las balanzas físicas conectadas en el escritorio.

---

### PARTE 2: PERSISTENCIA LOCAL OFFLINE-FIRST (SQLITE WAL)
* **Objetivo:** Garantizar que si se corta la red o internet en planta, el operario continúe pesando y emitiendo etiquetas sin bloqueos de pantalla ni pérdida de registros.
* **Tecnologías y Librerías:** `sqlite3`, `uuid`, WAL mode (Write-Ahead Logging).
* **Componentes a programar:**
  1. `local_db.py`: Inicializador del buffer local en cada terminal de planta.
  2. Tablas locales: `pending_weights`, `pending_labels`, `config_local`.
  3. Generación de `idempotency_key` (UUIDv4) por cada pesaje para garantizar cero duplicaciones al subir los datos a la nube.

---

### PARTE 3: TERMINAL TÁCTIL DE PLANTA - FRIGORÍFICO
* **Objetivo:** Interfaz gráfica industrial para el pesador de gancho en la línea de faena.
* **Tecnologías y Librerías:** Python, `customtkinter` (Dark Theme según `Visual del programa.md`), `Pillow`.
* **Componentes a programar:**
  1. `terminal_frigorifico.py`: Pantalla táctil Kiosk optimizada para resoluciones estándar (1280x800 y 1920x1080).
  2. Display gigante de balanza Systel: números monoespaciados de 72px que cambian a verde esmeralda (`#10B981`) al estabilizar el peso.
  3. Botones táctiles de gran tamaño ($\ge 54\text{ px}$) operables con guantes húmedos/grasos.
  4. Selector de lado (`IZQ` / `DER`) con alternancia automática configurable.
  5. Campos de tipificación rápida: Espesor de grasa dorsal (mm), % de magro y pH 45min.
  6. Disparo automático de impresión ZPL de la media res.

---

### PARTE 4: TERMINAL TÁCTIL DE PLANTA - FÁBRICA DE CHACINADOS
* **Objetivo:** Interfaz gráfica táctil para pesaje de batea en báscula Moretti y mezclado de masa.
* **Tecnologías y Librerías:** Python, `customtkinter`, `Pillow`.
* **Componentes a programar:**
  1. `terminal_fabrica.py`: Interfaz táctil de planta para batea y cutter.
  2. Pesaje asistido paso a paso: Carne Magra $\rightarrow$ Tocino Industrial `00049` $\rightarrow$ Sales de Cura y Condimentos.
  3. Botón de tara automática en pantalla.
  4. Semáforo visual de temperatura de masa:
     - 🟢 Verde: $< 4.0^\circ\text{C}$ (Temperatura ideal).
     - 🟡 Ámbar: $4.0^\circ\text{C} - 6.0^\circ\text{C}$ (Advertencia preventiva).
     - 🔴 Rojo: $> 6.0^\circ\text{C}$ (Riesgo de empaste / bloqueo configurable).
  5. Generación de lote de bachada y emisión de etiqueta ZPL de lote.

---

### PARTE 5: DEMONIO DE SINCRONIZACIÓN ASÍNCRONO (SYNC WORKER)
* **Objetivo:** Subir los registros locales de SQLite a la base de datos central PostgreSQL de forma transparente y sin interrumpir la interfaz de usuario.
* **Tecnologías y Librerías:** Python, `requests`, `urllib3`, `psycopg2`, `jwt`.
* **Componentes a programar:**
  1. `sync_worker.py`: Demonio en segundo plano que monitorea la cola en `local_db.py`.
  2. Detección activa de conectividad (ping de enlace).
  3. Envío en lotes de hasta 50 pesajes hacia PostgreSQL mediante HTTPS con autenticación JWT y TLS 1.2+.
  4. Inserción idempotente con `ON CONFLICT (idempotency_key) DO NOTHING`.
  5. Inserción automática en el Event Log inmutable `evento_lote` (JSONB).

---

### PARTE 6: CONFIGURACIÓN Y BLUEPRINTS DE GOOGLE APPSHEET
* **Objetivo:** Módulos de gestión móvil en tablets para inspectores veterinarios, jefes de faena y maestros fiambreros.
* **Tecnologías:** Google AppSheet, PostgreSQL Connector, Plantillas PDF HTML.
* **Componentes a programar:**
  1. `appsheet_frigorifico_spec.md`:
     - Carga de Tropa con DT-e de SENASA y datos de origen.
     - Interfaz de Dictamen Sanitario Veterinario (Aprobado, Decomiso Parcial, Decomiso Total).
     - Generación automática de Actas de Decomiso oficiales en PDF.
  2. `appsheet_fabrica_spec.md`:
     - Catálogo maestro de recetas y formulaciones.
     - Planificador de órdenes de bachada.
     - Registro móvil de control de estufas y curvas de secado de salames (días 7, 14, 21, 28).

---

### PARTE 7: SUITE DE TESTING E2E, FAILOVER Y SIMULACIÓN OFFLINE
* **Objetivo:** Certificar la robustez del sistema antes de llevarlo a la planta real.
* **Tecnologías:** `pytest`, emuladores virtuales de hardware.
* **Componentes a programar:**
  1. `test_hardware_drivers.py`: Pruebas de parseo de tramas Systel y Moretti con ruido e interferencias.
  2. `test_offline_failover_e2e.py`: Simulación de desconexión de red durante 50 pesajes consecutivos, validando persistencia local en SQLite y sincronización íntegra sin duplicados al reconectar.

---

## 3. HOJA DE RUTA Y ORDEN DE EJECUCIÓN PROPUESTO

Podemos avanzar paso a paso de manera ordenada:
* **Paso 1:** Capa de Hardware Core y Mocks (`scale_driver.py`, `zebra_printer.py`, `mock_hardware.py`).
* **Paso 2:** Persistencia Local Offline (`local_db.py` con SQLite WAL e idempotencia).
* **Paso 3:** Terminal Táctil Frigorífico (`terminal_frigorifico.py` con Display Systel gigante y ZPL).
* **Paso 4:** Terminal Táctil Fábrica (`terminal_fabrica.py` con batea Moretti y control térmico).
* **Paso 5:** Demonio de Sincronización (`sync_worker.py` hacia PostgreSQL y `evento_lote`).
* **Paso 6:** Blueprints de AppSheet para gestión móvil (SENASA, Recetas y Actas PDF).
* **Paso 7:** Pruebas integrales de carga y failover de red.

---

*Documento técnico de implementación segmentada para Frigorífico y Fábrica en el ecosistema SPI.*

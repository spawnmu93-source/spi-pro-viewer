# 🏭 ESPECIFICACIÓN INTEGRAL: MÓDULOS FRIGORÍFICO Y FÁBRICA DE CHACINADOS
**Sistema de Producción Integral (SPI)**  
*Ubicación:* `\SPI NEW\Frigorifico-Fabrica\`  
*Versión:* 2.0 Enterprise  
*Hardware Asociado:* Balanzas Systel (Gancho) y Moretti (Plataforma/Batea) + Impresoras Zebra ZPL-II  
*Software:* Google AppSheet (Gestión y Dictamen) + Python Desktop (Terminales Edge) + PostgreSQL Central  

---

## 📑 ÍNDICE DE CONTENIDOS
1. [Diagramas de Flujo de Procesos de Punta a Punta](#1-diagramas-de-flujo-de-procesos-de-punta-a-punta)
   - 1.1 Flujo Operativo Frigorífico (Faena, Inspección SENASA y Desposte)
   - 1.2 Flujo Operativo Fábrica de Chacinados (Materia Prima, Mezclado, Embutido y Secado)
   - 1.3 Malla de Trazabilidad Cruzada Frigorífico $\rightarrow$ Fábrica
2. [Arquitectura de Datos y Cómo Viaja la Información](#2-arquitectura-de-datos-y-cómo-viaja-la-información)
   - 2.1 La Ruta del Dato (Hardware Serial $\rightarrow$ Edge $\rightarrow$ Buffer $\rightarrow$ Cloud $\rightarrow$ Zebra)
   - 2.2 Tramas Físicas RS-232 (Systel & Moretti)
   - 2.3 Buffer Local SQLite WAL (Esquema y Registro Ejemplo)
   - 2.4 Payload JSON de Sincronización HTTPS/REST con Idempotencia
   - 2.5 Registro Inmutable en `evento_lote` (JSONB)
   - 2.6 Corriente de Impresión Zebra ZPL-II (Canal y Bachada)
3. [Reglas de Negocio, Roles y Matriz de Permisos](#3-reglas-de-negocio-roles-y-matriz-de-permisos)
   - 3.1 Roles Operativos y de Sistema
   - 3.2 Matriz de Control de Acceso (RBAC)
   - 3.3 Reglas Operativas Inquebrantables
4. [Tablero de KPIs, Umbrales y Fórmulas Matemáticas](#4-tablero-de-kpis-umbrales-y-fórmulas-matemáticas)
   - 4.1 KPIs de Frigorífico
   - 4.2 KPIs de Fábrica de Chacinados
5. [Sistema de Alertas, Disparadores y Notificaciones](#5-sistema-de-alertas-disparadores-y-notificaciones)
   - 5.1 Niveles de Severidad y Canales
   - 5.2 Matriz de Disparadores y Acciones Automáticas
   - 5.3 Ejemplos Visuales de Alertas en Terminales y Móvil

---

## 1. DIAGRAMAS DE FLUJO DE PROCESOS DE PUNTA A PUNTA

### 1.1 Flujo Operativo Frigorífico (Faena, Inspección SENASA y Tipificación)

```mermaid
flowchart TD
    subgraph Recepcion["1. RECEPCIÓN Y CORRALES"]
        A["Arribo Camión con Tropa"] --> B["Control Documental DT-e SENASA"]
        B --> C["Pesaje Bruto en Báscula de Camión (kg Vivo)"]
        C --> D["Descanso en Corrales (2 a 4 horas con aspersión)"]
    end

    subgraph Faena["2. LÍNEA DE FAENA"]
        D --> E["Noqueo, Degüello y Sangrado"]
        E --> F["Escaldado, Depilado y Eviscerado"]
        F --> G{"Inspección Sanitaria Veterinaria SENASA"}
    end

    subgraph Dictamen["3. DICTAMEN VETERINARIO"]
        G -->|Aprobado Total| H["División en Medias Reses (IZQ / DER)"]
        G -->|Decomiso Parcial| I["Extirpación de Vísceras/Órganos Afectados"]
        I --> J["Emisión Acta Decomiso Parcial PDF"]
        J --> H
        G -->|Decomiso Total / Triquinosis| K["Baja Sanitaria Inmediata a Digestor / Horno"]
        K --> L["Emisión Acta Decomiso Total SENASA"]
        L --> M["Bloqueo y Cierre de Tropa"]
    end

    subgraph PesajeCanal["4. PESAJE Y TIPIFICACIÓN (TERMINAL PYTHON)"]
        H --> N["Gancho Aéreo (Balanza Systel RS-232)"]
        N --> O["Captura Automática de Peso Caliente (< 50ms)"]
        O --> P["Medición Espesor Grasa Dorsal (mm) + % Magro + pH 45min"]
        P --> Q["Generación de Lote Media Res:\nMR-[LADO]-[ID_TROPA]-[SEC]"]
        Q --> R["Disparo de Impresión Etiqueta Zebra ZPL (100x75mm)"]
        R --> S["Buffer Local SQLite + Inserción en evento_lote"]
    end

    subgraph Camara["5. OREADO Y DESPACHO"]
        S --> T["Ingreso a Cámara Fría (0°C a 4°C por 24hs)"]
        T --> U["Pesaje Gancho Frío (Cálculo Merma Oreado)"]
        U --> V{"Destino Canal"}
        V -->|Despacho Sucursales| W["Remito Tango REI (Transporte Frío)"]
        V -->|Desposte Interno / Fábrica| X["Sala de Desposte (Tocino 00049 + Magro)"]
    end
```

---

### 1.2 Flujo Operativo Fábrica de Chacinados (Elaboración, Embutido y Curado)

```mermaid
flowchart TD
    subgraph RecepcionMP["1. INGRESO Y RECONCILIACIÓN DE MATERIA PRIMA"]
        A1["Recepción de Cortes de Cerdo (Magro)"] --> B1["Validación Lote Origen de Media Res"]
        A2["Recepción Tocino Dorsal (Lote Fijo 00049)"] --> B1
        A3["Especias, Sales de Cura y Tripas"] --> B2["Validación Lote Proveedor y Vencimiento"]
        B1 & B2 --> C1["Almacenamiento en Cámara de Materia Prima (0°C - 2°C)"]
    end

    subgraph Planificacion["2. SELECCIÓN DE RECETA Y FORMULACIÓN (APPSHEET)"]
        C1 --> D1["Maestro Fiambrero Selecciona Receta:\n(ej. Salame Milán / Chorizo Parrillero)"]
        D1 --> E1["Ingreso de Kilos a Producir (ej. 200 kg)"]
        E1 --> F1["Cálculo Automático por Fórmulas:\n- Magro Requerido: 140 kg (70%)\n- Tocino 00049: 40 kg (20%)\n- Condimentos/Sal: 20 kg (10%)"]
        F1 --> G1["Generación de ID Bachada:\nBACH-[RECETA]-[YYMMDD]-[SEC]"]
    end

    subgraph PesajeMezclado["3. PESAJE Y MEZCLADO (TERMINAL PYTHON BÁSCULA MORETTI)"]
        G1 --> H1["Colocación de Batea en Balanza Moretti RS-232"]
        H1 --> I1["Pesaje Asistido con Validación de Tolerancia (±0.5%)"]
        I1 --> J1["Picado en Cutter / Mezcladora Industrial"]
        J1 --> K1{"Control de Temperatura de Masa"}
        K1 -->|Temp <= 4°C| L1["Masa Homogénea Conforme"]
        K1 -->|Temp > 6°C| M1["ALERTA CRÍTICA: Bloqueo de Embutido\n(Adición de escarcha / enfriamiento forzado)"]
        M1 --> L1
    end

    subgraph Embutido["4. EMBUTIDO Y TIPIFICACIÓN"]
        L1 --> N1["Embutido en Tripa (Natural / Colágeno) y Atado"]
        N1 --> O1["Pesaje de Masa Fresca Terminada + Conteo Ristras"]
        O1 --> P1{"Tipo de Proceso de Receta"}
    end

    subgraph Finalizacion["5. DESTINO DEL PRODUCTO"]
        P1 -->|Fresco: Chorizo / Salchicha| Q1["Pesaje Final de Lote"]
        Q1 --> R1["Impresión Etiqueta Zebra ZPL Bachada (100x50mm)"]
        R1 --> S1["Cámara de Producto Terminado Fresco"]

        P1 -->|Seco-Curado: Salame / Bondiola| T1["Estufado Inicial (22°C - 24°C, 48hs)"]
        T1 --> U1["Cámara de Secado (12°C - 14°C, 20 a 30 días)"]
        U1 --> V1["Pesajes Semanales de Control de Merma"]
        V1 --> W1{"¿Alcanzó Merma Objetivo (35% - 38%)?"}
        W1 -->|No / Falta Secado| U1
        W1 -->|Sí / Conforme| X1["Cepillado / Empaque Final"]
        X1 --> R1
    end
```

---

### 1.3 Malla de Trazabilidad Cruzada Frigorífico $\rightarrow$ Fábrica

```mermaid
graph LR
    subgraph OrigenFrigorifico["FRIGORÍFICO"]
        TRP["Tropa: TRP-2026-00412\n(DT-e SENASA)"] --> MR1["Media Res DER: MR-DER-00412-01\n(42.50 kg - Magro 58%)"]
        TRP --> MR2["Media Res IZQ: MR-IZQ-00412-01\n(42.30 kg - Magro 58%)"]
        MR1 & MR2 --> DESP["Desposte Primario"]
        DESP --> REC_MAG["Recortes Magros\nLote: LOT-20260904-MAGRO"]
        DESP --> TOC["Tocino Dorsal Industrial\nLote Fijo: 00049"]
    end

    subgraph InsumosExternos["PROVEEDORES"]
        ESP["Especias / Sal de Cura\nLote: PROV-ESP-8821"]
        TRIP["Tripa Calibre 45\nLote: PROV-TRP-3310"]
    end

    subgraph DestinoFabrica["FÁBRICA DE CHACINADOS"]
        REC_MAG & TOC & ESP & TRIP --> BACH["Bachada: BACH-SALMIL-260904-01\n(Salame Milán - 150 kg)"]
        BACH --> EVENT["evento_lote (Blockchain-like Event Log)\nTrazabilidad Ascendente Inmediata"]
    end
```

---

## 2. ARQUITECTURA DE DATOS Y CÓMO VIAJA LA INFORMACIÓN

### 2.1 La Ruta del Dato (Data Journey)

```
[ Balanza Física ] 
       │  (Trama RS-232 pura cada 100ms)
       ▼
[ scale_driver.py ] 
       │  (Filtro de debounce, validación checksum, extracción float)
       ▼
[ Terminal UI Python ] 
       │  (Muestra display gigante 72px verde, valida operario y corte)
       ▼
[ local_db.py (SQLite WAL) ]  ◄─── ¡PUNTO SEGURO OFFLINE!
       │  (Transacción local inmediata < 10ms, asigna idempotency_key)
       ├──► Dispara [ zebra_printer.py ] ──► [ Impresora Zebra (ZPL) ]
       │
       ▼  (En segundo plano por sync_worker.py)
[ HTTPS POST /api/v1/sync ] 
       │  (Header Authorization: Bearer JWT, Payload comprimido)
       ▼
[ PostgreSQL Central ]
       ├──► INSERT INTO faena_medias_reses / chacinados_bachadas
       └──► INSERT INTO evento_lote (Inmutable JSONB)
```

---

### 2.2 Tramas Físicas RS-232

#### Balanza Systel (Gancho Aéreo / Línea de Faena)
* **Baudrate:** 9600 bps, 8 bits de datos, sin paridad (8N1).
* **Modo:** Transmisión continua (Continuous Broadcast).
* **Estructura de Trama:**
  ```text
  [STX] [ESTADO] [SIGNO] [PESO_NETO_6] [TARA_6] [ETX]
  Hex: \x02  'S'     '+'    '008450'      '000000' \x03
  ```
  - `\x02`: Start of Text.
  - `ESTADO`: `'S'` (Estable), `'M'` (En movimiento/Inestable), `'O'` (Sobrecarga).
  - `SIGNO`: `'+'` o `'-'`.
  - `PESO_NETO`: 6 caracteres ASCII (`008450` = $84.50\text{ kg}$).
  - `\x03`: End of Text.

#### Balanza Moretti (Plataforma / Batea de Fábrica)
* **Baudrate:** 9600 bps, 8N1.
* **Modo:** Polling (Pregunta/Respuesta con código ASCII `ENQ` `\x05`) o continuo.
* **Estructura de Trama:**
  ```text
  [STX] 'P' '+' '0' '4' '5' '.' '2' '5' '0' 'k' 'g' [CR] [LF] [ETX]
  ```
  - Parseo regex unificado en Python: `r'([+-]?\d+\.?\d*)\s*kg'`

---

### 2.3 Buffer Local SQLite WAL (`local_db.py`)

Si la planta pierde internet o cae el switch, la terminal no se bloquea. Escribe en su base local con `journal_mode=WAL`:

```sql
-- Estructura local en cada terminal de planta:
CREATE TABLE IF NOT EXISTS pending_sync_queue (
    id_local INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT UNIQUE NOT NULL,
    entity_type TEXT NOT NULL, -- 'FAENA_MEDIA_RES' o 'CHACINADOS_BACHADA'
    payload_json TEXT NOT NULL,
    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
    intentos INTEGER DEFAULT 0,
    ultimo_error TEXT,
    sincronizado INTEGER DEFAULT 0 -- 0=Pendiente, 1=Sincronizado
);
```

#### Ejemplo de Registro Insertado en SQLite Local:
```json
{
  "id_local": 412,
  "idempotency_key": "c7a8b091-e45f-4a11-b921-729f81d59302",
  "entity_type": "FAENA_MEDIA_RES",
  "payload_json": "{\"id_tropa_fk\":\"TRP-2026-00412\",\"lado\":\"DER\",\"peso_gancho_caliente_kg\":42.50,\"espesor_grasa_dorsal_mm\":14.2,\"porcentaje_magro_estimado\":58.4,\"ph_45min\":6.20,\"temperatura_camara_c\":3.5,\"lote_media_res\":\"MR-DER-00412-01\",\"operario_id\":4}",
  "creado_en": "2026-09-04 09:12:45",
  "intentos": 0,
  "sincronizado": 0
}
```

---

### 2.4 Payload JSON de Sincronización HTTPS/REST con Idempotencia

El hilo en segundo plano (`sync_worker.py`) toma los registros pendientes y los envía por HTTPS al backend central:

```http
POST /api/v1/sync/faena HTTP/1.1
Host: spi-cloud.empresa.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "sync_batch_id": "BATCH-EDGE-TERM01-202609040915",
  "terminal_id": "TERM-FRIG-01",
  "timestamp_envio": "2026-09-04T09:15:02Z",
  "records": [
    {
      "idempotency_key": "c7a8b091-e45f-4a11-b921-729f81d59302",
      "tropa_dte": "TRP-2026-00412",
      "lado": "DER",
      "peso_gancho_caliente_kg": 42.50,
      "espesor_grasa_dorsal_mm": 14.2,
      "porcentaje_magro_estimado": 58.4,
      "ph_45min": 6.20,
      "temperatura_camara_c": 3.5,
      "lote_media_res": "MR-DER-00412-01",
      "aprobacion_veterinaria_senasa": true,
      "operario_id": 4,
      "fecha_hora_captura": "2026-09-04T09:12:45Z"
    }
  ]
}
```

#### Respuesta Idempotente del Servidor:
```json
{
  "status": "SUCCESS",
  "processed": 1,
  "duplicates_ignored": 0,
  "server_timestamp": "2026-09-04T09:15:03.112Z"
}
```

---

### 2.5 Registro Inmutable en `evento_lote` (JSONB)

Cada inserción crea un evento transaccional que no puede ser modificado ni borrado:

```json
{
  "id_evento": 98402,
  "lote": "MR-DER-00412-01",
  "tipo_evento": "PESAJE",
  "ubicacion": "FRIGORIFICO_LINEA_GANCHO_01",
  "id_operario_fk": 4,
  "payload_json": {
    "tropa_senasa": "TRP-2026-00412",
    "balanza_modelo": "Systel Cuora Gancho Serial",
    "peso_kg": 42.50,
    "tipificacion": {
      "grasa_mm": 14.2,
      "magro_pct": 58.4,
      "ph": 6.20
    },
    "sensor_camara_temp_c": 3.5,
    "etiqueta_zpl_emitida": true,
    "hash_seguridad_trama": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "idempotency_key": "c7a8b091-e45f-4a11-b921-729f81d59302",
  "fecha_hora": "2026-09-04 09:12:45.321"
}
```

---

### 2.6 Corriente de Impresión Zebra ZPL-II

#### Etiqueta Media Res Frigorífico (100mm x 75mm - 203 DPI)
```zpl
^XA
^PW812
^LL609
^CF0,30
^FO50,40^FD*** SISTEMA DE PRODUCCION INTEGRAL ***^FS
^FO50,80^GB712,3,3^FS
^CF0,45
^FO50,105^FDLOTE MEDIA RES:^FS
^CF0,55
^FO50,155^FDMR-DER-00412-01^FS
^CF0,35
^FO50,230^FDTROPA DT-e: TRP-2026-00412^FS
^FO50,275^FDPESO GANCHO: 42.50 kg  [LADO: DER]^FS
^FO50,320^FDTIP: GRASA 14.2mm | MAGRO 58.4%^FS
^FO50,365^FDFECHA: 04/09/2026 09:12  OP: 004^FS
^BY3,2,80
^FO50,420^BCN,80,Y,N,N^FDMR-DER-00412-01^FS
^FO620,400^BQN,2,5^FDQA,https://spi.empresa.com/t?l=MR-DER-00412-01^FS
^XZ
```

#### Etiqueta Bachada Fábrica de Chacinados (100mm x 50mm - 203 DPI)
```zpl
^XA
^PW812
^LL406
^CF0,28
^FO40,30^FDSPI - FABRICA DE CHACINADOS^FS
^FO40,65^GB732,2,2^FS
^CF0,40
^FO40,85^FDSALAME MILAN SECO^FS
^CF0,48
^FO40,135^FDLOTE: BACH-SALMIL-260904-01^FS
^CF0,30
^FO40,195^FDPESO: 150.00 kg | RISTRAS: 120 un^FS
^FO40,235^FDTOCINO: LOTE 00049 | ELAB: 04/09/2026^FS
^BY2,2,65
^FO40,285^BCN,65,Y,N,N^FDBACH-SALMIL-260904-01^FS
^XZ
```

---

## 3. REGLAS DE NEGOCIO, ROLES Y MATRIZ DE PERMISOS

### 3.1 Roles Operativos y de Sistema

| Rol | Alcance y Responsabilidad | Dispositivo Habitual |
|---|---|---|
| **VETERINARIO_SENASA** | Inspección antemortem y postmortem, dictamen de decomisos, aprobación sanitaria de canales. | Tablet Rugerizada (AppSheet) |
| **OPERARIO_FAENA** | Operación de noqueo, enganche, captura de peso en balanza Systel y etiquetado físico. | Terminal Industrial Táctil (Python Desktop) |
| **MAESTRO_CHACINERO** | Selección de recetas, cálculo de ingredientes, control de picado, pesaje en Moretti y embutido. | Terminal Táctil Fábrica + Tablet AppSheet |
| **SUPERVISOR_PLANTA** | Apertura/cierre de tropas, control de cámaras frías, anulación justificada de lotes y monitoreo de mermas. | PC Oficina / Tablet AppSheet |
| **AUDITOR_CALIDAD** | Muestreos de pH, control microbiológico, calibración de balanzas y auditoría de consistencia de stock. | Móvil / Web AppSheet |

---

### 3.2 Matriz de Control de Acceso (RBAC)

| Módulo / Acción | VETERINARIO_SENASA | OPERARIO_FAENA | MAESTRO_CHACINERO | SUPERVISOR_PLANTA | AUDITOR_CALIDAD |
|---|:---:|:---:|:---:|:---:|:---:|
| **Crear Tropa / DT-e** | ❌ | ❌ | ❌ | 🟢 **SÍ** | 👁️ Solo Lectura |
| **Dictaminar SENASA / Decomiso** | 🟢 **SÍ (Exclusivo)** | ❌ | ❌ | 👁️ Solo Lectura | 👁️ Solo Lectura |
| **Captura Peso Gancho RS-232** | ❌ | 🟢 **SÍ** | ❌ | 🟢 SÍ (Supervisor) | ❌ |
| **Re-impresión Etiqueta Canal** | ❌ | 🟡 Con PIN Supervisor | ❌ | 🟢 **SÍ** | ❌ |
| **Crear/Modificar Recetas** | ❌ | ❌ | 🟡 Propone | 🟢 **SÍ (Aprueba)** | 👁️ Solo Lectura |
| **Pesaje Bachada Moretti** | ❌ | ❌ | 🟢 **SÍ** | 🟢 SÍ | ❌ |
| **Registro Control de Merma Secado**| ❌ | ❌ | 🟢 **SÍ** | 🟢 SÍ | 🟢 **SÍ** |
| **Anular Sesión / Registro** | ❌ | ❌ | ❌ | 🟡 **SÍ (Soft-Delete)**| ❌ |
| **Ver Event Log Histórico** | 👁️ Solo Lectura | ❌ | 👁️ Solo Lectura | 🟢 **SÍ** | 🟢 **SÍ** |

---

### 3.3 Reglas Operativas Inquebrantables
1. **Regla de Inmutabilidad de Pesaje:** Una vez capturado el peso por el puerto serie y generado el registro en `faena_medias_reses` o `chacinados_bachadas`, **el valor de kilos no puede ser editado por nadie** (ni siquiera por el administrador). Si hubo un error operativo (ej. se pesó con una cadena encima), se debe anular la media res con motivo auditado en `evento_lote` y generar una nueva lectura.
2. **Regla del Bloqueo por Dictamen SENASA:** Ninguna media res puede recibir etiqueta ZPL de canal ni ser enviada a cámara de oreado si el campo `aprobacion_veterinaria_senasa` se encuentra en `false` o nulo.
3. **Regla de Temperatura de Masa en Chacinados:** Si el sensor de temperatura en batea registra $> 6.0^\circ\text{C}$, el sistema **bloquea la generación de la bachada** e impide la impresión de la etiqueta hasta que se registre una corrección térmica ($< 4.0^\circ\text{C}$) avalada por el Maestro Chacinero.
4. **Regla del Tocino `00049`:** Todo sobrante de tocino dorsal apto originado en el desposte de faena debe registrarse bajo el código de subproducto central y lote `00049`, garantizando su absorción estandarizada en las recetas de fábrica.

---

## 4. TABLERO DE KPIS, UMBRALES Y FÓRMULAS MATEMÁTICAS

### 4.1 KPIs de Frigorífico

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              KPIS FRIGORÍFICO                               │
├───────────────────────────────┬───────────────────────────────┬─────────────┤
│ KPI                           │ FÓRMULA MATEMÁTICA            │ META / UMBRAL│
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 1. Merma Transporte Pie (%)   │ ((Kg Granja - Kg Báscula)     │ <= 1.2 %    │
│                               │   / Kg Granja) * 100          │             │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 2. Rendimiento de Faena (%)   │ (Sum(Kg Medias Reses Caliente)│ 80.5 - 82.5%│
│                               │   / Kg Vivo Báscula) * 100    │             │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 3. Merma Cámara Oreado (%)    │ ((Kg Caliente - Kg Frío 24h)  │ <= 1.8 %    │
│                               │   / Kg Caliente) * 100        │             │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 4. Índice de Decomiso (%)     │ (Cabezas Decomisadas Totales  │ <= 0.5 %    │
│                               │   / Total Cabezas Tropa) * 100│             │
└───────────────────────────────┴───────────────────────────────┴─────────────┘
```

---

### 4.2 KPIs de Fábrica de Chacinados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                KPIS FÁBRICA                                 │
├───────────────────────────────┬───────────────────────────────┬─────────────┤
│ KPI                           │ FÓRMULA MATEMÁTICA            │ META / UMBRAL│
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 1. Rendimiento Chacinado      │ (Kg Producto Embutido Term.   │ 99.0 -      │
│    Fresco (%)                 │   / Kg Masa Formulada) * 100  │   102.0 %   │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 2. Merma Secado Salames (%)   │ ((Kg Masa Embutida Inicial    │ 35.0 -      │
│                               │   - Kg Seco Final) / Kg Masa) │    38.0 %   │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 3. Cumplimiento de Receta     │ (|Kg Reales - Kg Teóricos|    │ <= 0.5 %    │
│    (Desvío Ingredientes)      │   / Kg Teóricos) * 100        │ por ingr.   │
├───────────────────────────────┼───────────────────────────────┼─────────────┤
│ 4. Adopción Tocino 00049      │ (Kg Tocino 00049 Utilizados   │ 100 %       │
│                               │   / Total Tocino Formulado)   │             │
└───────────────────────────────┴───────────────────────────────┴─────────────┘
```

---

## 5. SISTEMA DE ALERTAS, DISPARADORES Y NOTIFICACIONES

### 5.1 Niveles de Severidad y Canales de Transmisión

```mermaid
flowchart LR
    A["EVENTO DETECTADO"] --> B{"Nivel de Severidad"}
    
    B -->|INFO| C["🟢 Nivel Informativo\n- Toast en UI Táctil (3s)\n- Badge en Dashboard"]
    B -->|WARNING| D["🟡 Advertencia Operativa\n- Sonido Beep Doble en Terminal\n- Notificación Push en AppSheet\n- Registro en Log"]
    B -->|CRITICAL| E["🔴 Bloqueante / Sanitario\n- Bloqueo de UI (Requiere PIN Supervisor)\n- Alerta Push Inmediata a Gerencia\n- Notificación WhatsApp/Email Automática"]
```

---

### 5.2 Matriz de Disparadores y Acciones Automáticas

| Código Alerta | Módulo | Condición de Disparo (Trigger) | Nivel | Acción Automática del Sistema |
|---|---|---|:---:|---|
| `ALT-FRIG-01` | Frigorífico | Merma de transporte pie $> 2.0\%$ | 🟡 **WARNING** | Notifica a Supervisor en AppSheet; marca tropa con bandera amarilla para revisión de báscula de camión. |
| `ALT-FRIG-02` | Frigorífico | Rendimiento de faena $< 79.5\%$ | 🟡 **WARNING** | Alerta al Jefe de Faena; genera reporte de comparación de lote de engorde origen. |
| `ALT-FRIG-03` | Frigorífico | Decomiso total SENASA $> 2$ cabezas en la misma tropa | 🔴 **CRITICAL** | Bloqueo preventivo de la tropa; notificación inmediata por correo/WhatsApp al Veterinario Jefe y Dirección. |
| `ALT-FRIG-04` | Frigorífico | Desconexión física de balanza Systel RS-232 | 🔴 **CRITICAL** | Modal rojo en terminal táctil: *"Balanza Desconectada - Verifique cable COM"*; bloquea botón de captura. |
| `ALT-FAB-01` | Fábrica | Temperatura de masa en mezcladora $> 4.0^\circ\text{C}$ | 🟡 **WARNING** | Advertencia en pantalla: *"Masa caliente. Incorpore escarcha de hielo antes de continuar."* |
| `ALT-FAB-02` | Fábrica | Temperatura de masa $> 6.0^\circ\text{C}$ | 🔴 **CRITICAL** | **Bloqueo total de embutido**. Requiere validación de Maestro Chacinero para desestimar o tratar masa. |
| `ALT-FAB-03` | Fábrica | Merma de secado en cámara a día 25 es $< 30\%$ o $> 42\%$ | 🟡 **WARNING** | Alerta en AppSheet: *"Posible exceso de humedad o desecamiento acelerado en Cámara 2"*. Notifica a mantenimiento térmico. |
| `ALT-SYNC-01` | Edge | Cola offline en SQLite tiene $> 50$ registros pendientes | 🟡 **WARNING** | Badge amarillo en header: *"🟡 52 registros en buffer local. Verifique enlace de red."* |

---

### 5.3 Ejemplos Visuales de Alertas en Terminales y Móvil

#### A. Toast de Alerta en Terminal Táctil Python (Dark UI):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠️ ADVERTENCIA: PESO INESTABLE EN BALANZA CUORA GANCHO                     │
│ La res continúa oscilando. Espere la estabilización del indicador verde.    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### B. Modal Bloqueante de Decomiso Sanitario SENASA (Terminal / AppSheet):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔴 DICTAMEN SENASA: DECOMISO TOTAL POR SOSPECHA DE TRIQUINOSIS              │
│                                                                             │
│ Tropa: TRP-2026-00412  |  Animal Nro: 042  |  Hora: 09:14:22                │
│ Veterinario Dictaminante: Dr. Roberto Gómez (Mat. SENASA 8821)             │
│                                                                             │
│ ACCIÓN: La canal ha sido desviada al digestor de desnaturalización.         │
│ Esta canal NO generará etiquetas de media res apta.                         │
│                                                                             │
│ [ 📄 IMPRIMIR ACTA OFICIAL SENASA (PDF) ]       [ ✔️ ENTENDIDO Y CONTINUAR ] │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Este documento define con total precisión los flujos, paquetes de datos, reglas y alertas operativas para la construcción del MVP de Frigorífico y Fábrica en el ecosistema SPI.*

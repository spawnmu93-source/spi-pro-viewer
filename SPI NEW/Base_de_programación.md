# Base de programación

> **Nota de Alcance y Estrategia Híbrida (MVP vs Fase 2):**  
> Conforme al análisis de viabilidad técnica aprobado en [Viabilidad_de_AppSheets.md](Viabilidad_de_AppSheets.md), la fase inicial del **MVP productivo utiliza Google AppSheet** para la captura móvil en campo (Granja, Auditorías y Logística), reduciendo el tiempo de desarrollo inicial de 4 meses a solo 3 semanas.  
> La arquitectura nativa en **Android Studio (Kotlin + Room)** detallada en el presente documento constituye la especificación de referencia para la **Fase 2 de escalamiento**, en caso de requerir aplicaciones nativas dedicadas a futuro.

## Visión general y objetivos
Este documento describe la viabilidad y la arquitectura de alto nivel para la construcción de los módulos de captura y auditoría en los diferentes sectores productivos de la empresa (Granja, Frigorífico, Fábrica y Locales).  Se busca una solución **offline‑first** que permita trabajar sin conexión y sincronizar los datos con una base central cuando haya conectividad.

---

## Visión arquitectónica
> *Diagrama de arquitectura (placeholder)*

```mermaid
flowchart LR
    subgraph Offline
        A[App Android (Granja)] --> B[SQLite/Room]
        C[App Python (Frigorífico/Fábrica/Locales)] --> D[SQLite]
    end
    subgraph Sync
        B -->|Sync API| E[Backend (PostgreSQL)]
        D -->|Sync API| E
    end
    E --> F[Audit Service]
    F --> G[Data Lineage Store]
```

---

## Diseño del módulo Android (Granja)
- **Framework**: Android Studio con Kotlin.
- **Almacenamiento offline**: **Room** (capa de abstracción sobre SQLite) – recomendado por su manejo de migraciones y su integración con LiveData/Flow, lo que simplifica la actualización de UI y la sincronización posterior.
- **Captura de datos**: formularios UI que registran lote, paso, operador, timestamps y datos de sensor.
- **Sincronización**: cliente **Retrofit** que consume una **API REST JSON** protegida con **JWT**. La sincronización se ejecuta en fondo cuando el dispositivo detecta conectividad.
- **Auditoría**: eventos generados como **JSON blobs** y almacenados localmente; se envían en lotes al endpoint `/audit`.

---

## Diseño de la terminal Python (Frigorífico, Fábrica y Locales)
- **Entorno**: Python 3.9+ (compatible Windows y Linux).
- **Almacenamiento offline**: **SQLite** vía el módulo estándar `sqlite3`. Es ligero, portátil y permite transacciones para resolver conflictos al sincronizar.
- **Interfaz**: aplicación de consola con menús textuales; se pueden usar bibliotecas como `curses` o `prompt_toolkit` para una UI más amigable.
- **Sincronización**: uso de la librería **requests** contra la misma **API REST JSON** con autenticación **JWT**.
- **Auditoría**: generación de **JSON blobs** que se guardan en una tabla `audit_events` local y se envían en lotes al backend.

---

## Capa de auditoría compartida
- **Formato**: blobs JSON que incluyen `timestamp`, `user_id`, `action`, `entity_id` y `payload`.
- **Almacenamiento local**: tabla `audit_events` en cada base SQLite (Android y Python).
- **Envío**: endpoint `POST /audit` que recibe un array de eventos y los persiste en la base central.
- **Ventaja**: permite rastrear cualquier cambio y reconstruir el historial completo.

---

## Estrategia de sincronización offline‑first
1. **Cola de cambios**: cada operación de escritura se registra en una tabla `pending_sync`.
2. **Detección de conectividad**: en Android se usa `ConnectivityManager`; en Python se verifica mediante una petición ping a la API.
3. **Envió en lotes**: cuando hay conectividad, los registros pendientes se envían mediante la API REST. En caso de error se reintenta con back‑off exponencial.
4. **Resolución de conflictos**: política **"last‑write‑wins"** con timestamps UTC; los registros conflictivos se marcan para revisión manual.

---

## Modelo de trazabilidad y linaje de datos
Se captura la siguiente información en cada registro operativo:
- `lot_id` (identificador del lote origen)
- `step_id` (identificador del proceso, p. ej. "recepción", "desposte")
- `operator_id` (quién realizó la acción)
- `device_id` (identificador del terminal que registró la operación)
- `timestamp` (UTC)
- `data_payload` (detalles específicos del paso)

**Modelo inmutable**: en lugar de actualizar filas, se inserta una nueva fila por cada evento, garantizando un historial completo. El registro de auditoría refuerza esta inmutabilidad.

---

## Hoja de ruta de implementación y próximos pasos
| Fase | Actividad | Responsable | Duración estimada |
|------|-----------|-------------|-------------------|
| 1 | Definir especificaciones finales (API, esquemas) | Arquitectura | 1 semana |
| 2 | Implementar API backend (endpoints `/ingest`, `/audit`, `/status`) | Backend | 2 semanas |
| 3 | Desarrollar módulo Android (UI, Room, Sync) | móvil | 3 semanas |
| 4 | Desarrollar terminales Python (UI consola, SQLite, Sync) | backend | 3 semanas |
| 5 | Pruebas integradas (sincronización, auditoría, trazabilidad) | QA | 2 semanas |
| 6 | Despliegue piloto en Granja y Frigorífico | Operaciones | 1 semana |
| 7 | Retroalimentación y ajustes | Todos | 1‑2 semanas |

---

## Preguntas abiertas (para referencia futura) 
- **Versión mínima del SDK Android**: 21 (Lollipop) – suficiente para la mayoría de dispositivos; se puede elevar a 23 si se usan componentes Jetpack modernos.
- **Preferencias de diagramas**: se incluyen diagramas Mermaid directamente en este documento, facilitando su edición y visualización.

*Este documento sirve como base para el desarrollo posterior y será actualizado a medida que se avance en cada fase.*

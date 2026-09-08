"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - BUFFER LOCAL OFFLINE-FIRST (SQLITE)
Persistencia transaccional de alta velocidad con Journal Mode WAL
=============================================================================
Garantías:
1. Resiliencia total: Si se corta la red o la luz, las pesadas no se pierden.
2. Idempotencia: Cada pesaje genera un UUIDv4 inmutable.
3. Concurrencia limpia: WAL mode permite lecturas concurrentes de la UI
   mientras el demonio de sincronización (sync_worker) sube datos en background.
=============================================================================
"""

import sys
import os
import sqlite3
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from config_parametros import SQLITE_DB_PATH
except ImportError:
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spi_local_buffer.db")


class LocalDatabase:
    """Gestor del buffer local SQLite en cada terminal industrial."""

    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión con WAL mode y timeout de espera."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self):
        """Crea las tablas locales si no existen."""
        with self._get_connection() as conn:
            # Tabla de pesajes y eventos pendientes de sincronizar
            conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_sync_queue (
                id_local INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT UNIQUE NOT NULL,
                modulo TEXT NOT NULL,
                tipo_registro TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                creado_en TEXT NOT NULL,
                sincronizado INTEGER DEFAULT 0,
                intentos_sync INTEGER DEFAULT 0,
                ultimo_error TEXT,
                sincronizado_en TEXT
            );
            """)

            # Tabla de cola de impresión ZPL de respaldo
            conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_labels_queue (
                id_label INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_etiqueta TEXT NOT NULL,
                zpl_code TEXT NOT NULL,
                estado TEXT DEFAULT 'PENDIENTE',
                creado_en TEXT NOT NULL,
                impreso_en TEXT,
                error_msg TEXT
            );
            """)

            # Tabla de configuración y caché local
            conn.execute("""
            CREATE TABLE IF NOT EXISTS local_cache (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            );
            """)

            # Índices de rendimiento
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sync_status ON pending_sync_queue(sincronizado);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_labels_status ON pending_labels_queue(estado);")
            conn.commit()

    # -----------------------------------------------------------------------
    # REGISTRO DE TRANSACCIONES DE PESAJE
    # -----------------------------------------------------------------------
    def save_weight_record(
        self,
        modulo: str,
        tipo_registro: str,
        data: Dict[str, Any],
        custom_idempotency_key: Optional[str] = None
    ) -> str:
        """
        Guarda un registro de pesaje en el buffer local de manera atómica.
        Retorna el idempotency_key asignado.
        """
        idempotency_key = custom_idempotency_key or str(uuid.uuid4())
        data["idempotency_key"] = idempotency_key
        payload_str = json.dumps(data, ensure_ascii=False)
        ahora = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO pending_sync_queue 
                (idempotency_key, modulo, tipo_registro, payload_json, creado_en, sincronizado)
                VALUES (?, ?, ?, ?, ?, 0);
            """, (idempotency_key, modulo, tipo_registro, payload_str, ahora))
            conn.commit()

        return idempotency_key

    # -----------------------------------------------------------------------
    # CONSULTA Y ACTUALIZACIÓN DE MEDIAS RESES POR TROPA
    # -----------------------------------------------------------------------
    def get_media_res_records_by_tropa(self, tropa: str) -> List[Dict[str, Any]]:
        """Obtiene todos los pesajes de media res pertenecientes a una tropa específica."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id_local, idempotency_key, modulo, tipo_registro, payload_json, creado_en
                FROM pending_sync_queue
                WHERE modulo = 'FRIGORIFICO' 
                  AND tipo_registro IN ('INGRESO_MEDIA_RES_CAMARA', 'MEDIA_RES')
                ORDER BY id_local ASC;
            """).fetchall()
            
            result = []
            for r in rows:
                p = json.loads(r["payload_json"])
                if p.get("id_tropa_fk") == tropa or p.get("tropa") == tropa or tropa in str(p.get("lote_media_res", "")):
                    item = dict(r)
                    item["payload"] = p
                    result.append(item)
            return result

    def update_media_res_record(self, idempotency_key: str, update_data: Dict[str, Any]) -> bool:
        """
        Actualiza el payload JSON de un pesaje local (ej. marcar EM anulado, o DP decomiso parcial)
        y lo marca pendiente de sincronización.
        """
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT payload_json FROM pending_sync_queue WHERE idempotency_key = ?;
            """, (idempotency_key,)).fetchone()
            if not row:
                return False
            payload = json.loads(row["payload_json"])
            payload.update(update_data)
            payload["actualizado_en"] = datetime.datetime.now().isoformat()
            nuevo_json = json.dumps(payload, ensure_ascii=False)
            conn.execute("""
                UPDATE pending_sync_queue
                SET payload_json = ?, sincronizado = 0
                WHERE idempotency_key = ?;
            """, (nuevo_json, idempotency_key))
            conn.commit()
            return True

    # -----------------------------------------------------------------------
    # GESTIÓN DE COLA DE ETIQUETAS ZPL
    # -----------------------------------------------------------------------
    def enqueue_label(self, tipo_etiqueta: str, zpl_code: str) -> int:
        """Encola una etiqueta cuando la impresora física no responde."""
        ahora = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO pending_labels_queue (tipo_etiqueta, zpl_code, estado, creado_en)
                VALUES (?, ?, 'PENDIENTE', ?);
            """, (tipo_etiqueta, zpl_code, ahora))
            conn.commit()
            return cur.lastrowid

    def get_pending_labels(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM pending_labels_queue 
                WHERE estado = 'PENDIENTE' 
                ORDER BY id_label ASC LIMIT ?;
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    def mark_label_printed(self, id_label: int):
        ahora = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE pending_labels_queue 
                SET estado = 'IMPRESO', impreso_en = ? 
                WHERE id_label = ?;
            """, (ahora, id_label))
            conn.commit()

    # -----------------------------------------------------------------------
    # MÉTODOS PARA EL SINCRONIZADOR (SYNC WORKER)
    # -----------------------------------------------------------------------
    def get_pending_sync_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene un lote de registros pendientes para enviar al servidor."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT id_local, idempotency_key, modulo, tipo_registro, payload_json, creado_en, intentos_sync
                FROM pending_sync_queue
                WHERE sincronizado = 0
                ORDER BY id_local ASC
                LIMIT ?;
            """, (limit,)).fetchall()
            
            result = []
            for r in rows:
                item = dict(r)
                item["payload"] = json.loads(item["payload_json"])
                result.append(item)
            return result

    def mark_as_synced(self, idempotency_keys: List[str]):
        """Marca una lista de registros como subidos exitosamente a PostgreSQL."""
        if not idempotency_keys:
            return
        ahora = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            placeholders = ",".join("?" for _ in idempotency_keys)
            conn.execute(f"""
                UPDATE pending_sync_queue
                SET sincronizado = 1, sincronizado_en = ?
                WHERE idempotency_key IN ({placeholders});
            """, [ahora] + idempotency_keys)
            conn.commit()

    def record_sync_error(self, idempotency_key: str, error_msg: str):
        """Incrementa el contador de intentos y registra el último error."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE pending_sync_queue
                SET intentos_sync = intentos_sync + 1, ultimo_error = ?
                WHERE idempotency_key = ?;
            """, (error_msg[:255], idempotency_key))
            conn.commit()

    # -----------------------------------------------------------------------
    # MÉTRICAS Y ESTADO DEL BUFFER
    # -----------------------------------------------------------------------
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas para el header visual de la pantalla (Badges)."""
        with self._get_connection() as conn:
            pending_sync = conn.execute("SELECT COUNT(*) FROM pending_sync_queue WHERE sincronizado = 0;").fetchone()[0]
            total_sync = conn.execute("SELECT COUNT(*) FROM pending_sync_queue WHERE sincronizado = 1;").fetchone()[0]
            pending_labels = conn.execute("SELECT COUNT(*) FROM pending_labels_queue WHERE estado = 'PENDIENTE';").fetchone()[0]

            return {
                "pending_sync_count": pending_sync,
                "total_synced_count": total_sync,
                "pending_labels_count": pending_labels,
                "is_clean": (pending_sync == 0 and pending_labels == 0)
            }


# ---------------------------------------------------------------------------
# PRUEBA STANDALONE DEL BUFFER LOCAL
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Probando LocalDatabase SQLite WAL...")
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_spi_buffer.db")
    db = LocalDatabase(db_path=test_db_path)

    # 1. Guardar pesaje de prueba
    test_payload = {
        "id_tropa_fk": "TRP-2026-00412",
        "lado": "DER",
        "peso_gancho_caliente_kg": 42.50,
        "operario_id": 4
    }
    key = db.save_weight_record("FRIGORIFICO", "MEDIA_RES", test_payload)
    print(f"[OK] Pesaje guardado con idempotency_key: {key}")

    # 2. Consultar pendientes
    pending = db.get_pending_sync_records(limit=10)
    print(f"[OK] Registros pendientes en cola: {len(pending)}")

    # 3. Marcar sincronizado
    db.mark_as_synced([key])
    stats = db.get_buffer_stats()
    print(f"[OK] Estadísticas del buffer: Pendientes: {stats['pending_sync_count']} | Sincronizados: {stats['total_synced_count']}")

    # Limpieza de archivo de prueba
    try:
        os.remove(test_db_path)
    except Exception:
        pass
    print("[OK] Prueba de LocalDatabase completada con éxito.")

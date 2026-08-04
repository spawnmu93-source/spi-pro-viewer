import os
import datetime
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="SPI - Sistema de Producción Integral API",
    description="API REST local para interactuar con la base de datos PostgreSQL de la granja.",
    version="1.0.0"
)

# Habilitar CORS para permitir llamadas desde cualquier IP en la red local de la granja
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir la carpeta de la app de Stock
static_stock_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static_stock")
os.makedirs(static_stock_dir, exist_ok=True)
app.mount("/stock", StaticFiles(directory=static_stock_dir, html=True), name="stock")

# Crear credentials.json desde Variable de Entorno si no existe físicamente (Para Deploy en Nube/Render)
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
env_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON") or os.environ.get("CREDENTIALS.JSON") or os.environ.get("CREDENTIALS_JSON")
if not os.path.exists(CREDENTIALS_FILE) and env_creds:
    try:
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            f.write(env_creds)
        print("Creado credentials.json a partir de la variable de entorno de Render")
    except Exception as e:
        print(f"Error al escribir credentials.json: {e}")

# Configuración de la Base de Datos (Editar con las credenciales del servidor)
DB_CONFIG = {
    "host": "localhost",
    "database": "spi_db",
    "user": "postgres",
    "password": "your_password_here", # Reemplazar con la contraseña maestra configurada
    "port": 5432
}

# Inicializar Pool de Conexiones
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,  # Mínimo 1, Máximo 10 conexiones activas
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )
except Exception as e:
    err_info = repr(e)
    print(f"AVISO: Base de datos PostgreSQL no conectada ({err_info}). Servidor backend y Web App activos normalmente.")
    connection_pool = None

def get_db():
    """Dependency para obtener una conexión del pool y cerrarla al terminar."""
    if not connection_pool:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El pool de conexiones a la base de datos no está inicializado."
        )
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

# --- Modelos de Datos Pydantic para Validaciones ---

class LoginRequest(BaseModel):
    pin: str

class CerdadLoteInput(BaseModel):
    id: str
    raza: str
    edad: int
    fecha_nacimiento: Optional[str] = None # Formato "DD/MM/YYYY"

class NuevoLoteRequest(BaseModel):
    lote_id: str
    cerdas: List[CerdadLoteInput]
    operario: str

class AltaPlantelInput(BaseModel):
    id: str
    raza: str
    edad: int
    peso: float
    tfi: str
    tfd: str
    celo: int
    lote: str
    fecha_nacimiento: Optional[str] = None # Formato "DD/MM/YYYY"

class AltaPlantelRequest(BaseModel):
    cerdas: List[AltaPlantelInput]
    operario: str
    fecha_movimiento: Optional[str] = None # Formato "DD/MM/YYYY"

class ActualizarCelosRequest(BaseModel):
    ids_cerdas: List[str]
    operario: str
    fecha_movimiento: Optional[str] = None # Formato "DD/MM/YYYY"

class BajasRequest(BaseModel):
    ids_pesos: Dict[str, str] # { "IDCerda": "Peso" }
    ids_edades: Dict[str, str] # { "IDCerda": "Edad" }
    categoria: str # 'Muerte', 'Descarte', 'Venta'
    motivo: str
    operario: str
    destino: Optional[str] = ""
    fecha_movimiento: Optional[str] = None

class SolicitudModificacionInput(BaseModel):
    id_solicitud: str
    operario: str
    tipo_movimiento: str
    id_cerda: str
    datos_originales: str # JSON string con datos originales
    estado: str = "Pendiente"

class LoggerRequest(BaseModel):
    nivel: str
    usuario: str
    evento: str

# --- Funciones de Utilidad ---

def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """Parsea fecha del formato 'DD/MM/YYYY' a date objeto para PostgreSQL."""
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        try:
            # Fallback en caso de que venga con formato ISO
            return datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

def format_timestamp(ts: Optional[datetime.datetime]) -> Optional[str]:
    if not ts: return None
    return ts.strftime("%d/%m/%Y %H:%M:%S")

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "ONLINE", "service": "SPI Server Backend", "time": datetime.datetime.now()}

@app.post("/auth/login")
def login(payload: LoginRequest, db=Depends(get_db)):
    """Verifica el PIN del usuario y retorna el nombre de usuario."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT usuario FROM cachorras_usuarios WHERE pin = %s", (payload.pin.strip(),))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="PIN incorrecto.")
        return {"usuario": user["usuario"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/mails")
def get_mails(db=Depends(get_db)):
    """Obtiene los destinatarios de correos configurados."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT usuario, mail FROM mails_corpo")
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/lotes")
def get_lotes(db=Depends(get_db)):
    """Obtiene todas las cerdas activas de los lotes (no procesadas o eliminadas)."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT lote as "Lote", id_cerda as "IDCerda", raza as "Raza", edad_ingreso as "Edad", 
                   timestamp_ingreso as "Timestamp", operario as "Operario", fecha_nacimiento as "FechaNacimiento"
            FROM cachorras_lotes 
            WHERE is_deleted = FALSE
        """)
        records = cursor.fetchall()
        for r in records:
            r["Timestamp"] = format_timestamp(r["Timestamp"])
            if r["FechaNacimiento"]:
                r["FechaNacimiento"] = r["FechaNacimiento"].strftime("%d/%m/%Y")
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/lotes")
def registrar_lote(payload: NuevoLoteRequest, db=Depends(get_db)):
    """Inserta masivamente cerdas a un lote de origen."""
    cursor = db.cursor()
    try:
        for c in payload.cerdas:
            fnac = parse_date(c.fecha_nacimiento)
            cursor.execute("""
                INSERT INTO cachorras_lotes (id_cerda, lote, raza, edad_ingreso, fecha_nacimiento, operario, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (id_cerda) DO UPDATE 
                SET lote = EXCLUDED.lote, raza = EXCLUDED.raza, edad_ingreso = EXCLUDED.edad_ingreso, 
                    fecha_nacimiento = EXCLUDED.fecha_nacimiento, operario = EXCLUDED.operario, 
                    is_deleted = FALSE, timestamp_ingreso = CURRENT_TIMESTAMP, synced_to_sheets = FALSE
            """, (c.id, payload.lote_id, c.raza, c.edad, fnac, payload.operario))
        db.commit()
        return {"status": "SUCCESS", "message": f"Se registraron {len(payload.cerdas)} cerdas en el Lote {payload.lote_id}."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/plantel")
def get_plantel(db=Depends(get_db)):
    """Obtiene todas las cerdas activas en el plantel."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id_cerda as "IDCerda", raza as "Raza", edad as "Edad", peso as "Peso", 
                   tfi as "TFI", tfd as "TFD", numero_de_celo as "Numero de Celo", 
                   lote_origen as "LoteOrigen", timestamp_alta as "Timestamp", 
                   operario as "Operario", fecha_nacimiento as "FechaNacimiento"
            FROM cachorras_plantel
            WHERE is_deleted = FALSE
        """)
        records = cursor.fetchall()
        for r in records:
            r["Timestamp"] = format_timestamp(r["Timestamp"])
            if r["FechaNacimiento"]:
                r["FechaNacimiento"] = r["FechaNacimiento"].strftime("%d/%m/%Y")
            # Convertir decimales a flotantes/strings para compatibilidad con JSON
            r["Peso"] = float(r["Peso"]) if r["Peso"] else ""
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/plantel/alta")
def alta_plantel(payload: AltaPlantelRequest, db=Depends(get_db)):
    """Da de alta cerdas en el plantel (primer celo) y las purga de Lotes."""
    cursor = db.cursor()
    try:
        fecha_mov = parse_date(payload.fecha_movimiento) or datetime.datetime.now().date()
        
        # Validar duplicados en Plantel Activo
        ids_migrar = [c.id for c in payload.cerdas]
        cursor.execute("SELECT id_cerda FROM cachorras_plantel WHERE id_cerda = ANY(%s) AND is_deleted = FALSE", (ids_migrar,))
        duplicados = [row[0] for row in cursor.fetchall()]
        if duplicados:
            raise HTTPException(status_code=400, detail=f"Las siguientes cerdas ya existen en el Plantel: {duplicados}")

        for c in payload.cerdas:
            fnac = parse_date(c.fecha_nacimiento)
            
            # 1. Insertar en Plantel
            cursor.execute("""
                INSERT INTO cachorras_plantel (id_cerda, raza, edad, peso, tfi, tfd, numero_de_celo, lote_origen, operario, fecha_nacimiento, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (id_cerda) DO UPDATE 
                SET raza = EXCLUDED.raza, edad = EXCLUDED.edad, peso = EXCLUDED.peso, tfi = EXCLUDED.tfi, 
                    tfd = EXCLUDED.tfd, numero_de_celo = EXCLUDED.numero_de_celo, lote_origen = EXCLUDED.lote_origen, 
                    operario = EXCLUDED.operario, fecha_nacimiento = EXCLUDED.fecha_nacimiento, 
                    is_deleted = FALSE, timestamp_alta = CURRENT_TIMESTAMP, synced_to_sheets = FALSE
            """, (c.id, c.raza, c.edad, c.peso, c.tfi, c.tfd, c.celo, c.lote, payload.operario, fnac))
            
            # 2. Registrar movimiento de celo
            cursor.execute("""
                INSERT INTO cachorras_registro_celo (id_cerda, raza, edad, peso, tfi, tfd, numero_de_celo, operario, lote_origen, motivo, fecha_nacimiento, fecha_movimiento, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Primer Celo', %s, %s, FALSE)
            """, (c.id, c.raza, c.edad, c.peso, c.tfi, c.tfd, c.celo, payload.operario, c.lote, fnac, fecha_mov))
            
            # 3. Borrado lógico de Lotes (Doble Purga)
            cursor.execute("""
                UPDATE cachorras_lotes 
                SET is_deleted = TRUE, synced_to_sheets = FALSE 
                WHERE id_cerda = %s
            """, (c.id,))
            
        db.commit()
        return {"status": "SUCCESS", "message": f"Alta en Plantel y purga de Lotes completada para {len(payload.cerdas)} cerdas."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/plantel/celos")
def registrar_celos(payload: ActualizarCelosRequest, db=Depends(get_db)):
    """Suma un celo masivamente a las cerdas indicadas."""
    cursor = db.cursor()
    try:
        fecha_mov = parse_date(payload.fecha_movimiento) or datetime.datetime.now().date()
        ids_actualizados = []
        ids_conflictos = []

        for id_cerda in payload.ids_cerdas:
            # Obtener datos actuales de la cerda
            cursor.execute("""
                SELECT raza, edad, peso, tfi, tfd, numero_de_celo, lote_origen, timestamp_alta, fecha_nacimiento 
                FROM cachorras_plantel 
                WHERE id_cerda = %s AND is_deleted = FALSE
            """, (id_cerda,))
            row = cursor.fetchone()
            
            if not row:
                ids_conflictos.append(id_cerda)
                continue
                
            raza, edad_original, peso, tfi, tfd, celo_actual, lote_orig, timestamp_alta, fnac = row
            nuevo_celo = celo_actual + 1
            
            # Calcular edad actual en base al nacimiento o ingreso
            edad_actual = edad_original
            if fnac:
                edad_actual = (datetime.datetime.now().date() - fnac).days
            
            # 1. Actualizar el Plantel
            cursor.execute("""
                UPDATE cachorras_plantel 
                SET numero_de_celo = %s, edad = %s, operario = %s, timestamp_alta = CURRENT_TIMESTAMP, synced_to_sheets = FALSE
                WHERE id_cerda = %s AND is_deleted = FALSE
            """, (nuevo_celo, edad_actual, payload.operario, id_cerda))
            
            # 2. Registrar el nuevo Celo en el Histórico
            cursor.execute("""
                INSERT INTO cachorras_registro_celo (id_cerda, raza, edad, peso, tfi, tfd, numero_de_celo, operario, lote_origen, motivo, fecha_nacimiento, fecha_movimiento, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            """, (id_cerda, raza, edad_actual, peso, tfi, tfd, nuevo_celo, payload.operario, lote_orig, f"Actualización a Celo {nuevo_celo}", fnac, fecha_mov))
            
            ids_actualizados.append(id_cerda)
            
        db.commit()
        return {
            "status": "SUCCESS" if not ids_conflictos else "PARTIAL",
            "message": f"Se actualizaron {len(ids_actualizados)} cerdas.",
            "conflictos": ids_conflictos
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/plantel/bajas")
def procesar_bajas(payload: BajasRequest, db=Depends(get_db)):
    """Registra la baja masiva de cerdas moviéndolas a Muertes, Descartes o Ventas."""
    cursor = db.cursor()
    try:
        fecha_mov = parse_date(payload.fecha_movimiento) or datetime.datetime.now().date()
        tabla_destino = ""
        if payload.categoria == "Muerte":
            tabla_destino = "cachorras_muertes"
        elif payload.categoria == "Descarte":
            tabla_destino = "cachorras_descartes"
        else:
            tabla_destino = "cachorras_ventas"
            
        bajas_realizadas = []
        
        for id_cerda, peso_nuevo_str in payload.ids_pesos.items():
            # Intentar leer del Plantel
            cursor.execute("""
                SELECT raza, edad, peso, tfi, tfd, numero_de_celo, lote_origen, fecha_nacimiento 
                FROM cachorras_plantel 
                WHERE id_cerda = %s AND is_deleted = FALSE
            """, (id_cerda,))
            row = cursor.fetchone()
            
            es_del_plantel = True
            if not row:
                # Si no está en Plantel, podría estar en Lotes sin registrar celo
                cursor.execute("""
                    SELECT raza, edad_ingreso, fecha_nacimiento, lote 
                    FROM cachorras_lotes 
                    WHERE id_cerda = %s AND is_deleted = FALSE
                """, (id_cerda,))
                row = cursor.fetchone()
                es_del_plantel = False
                
            if not row:
                continue # Cerda inexistente
                
            if es_del_plantel:
                raza, edad_original, peso_original, tfi, tfd, celo, lote_origen, fnac = row
            else:
                raza, edad_original, fnac, lote_origen = row
                peso_original, tfi, tfd, celo = None, "", "", 0
                
            # Validar peso final
            peso_final = float(peso_nuevo_str) if (peso_nuevo_str and peso_nuevo_str.strip() != "") else (float(peso_original) if peso_original else None)
            
            # Calcular edad
            edad_actual = int(payload.ids_edades.get(id_cerda, edad_original))
            if fnac:
                edad_actual = (datetime.datetime.now().date() - fnac).days
                
            # 1. Insertar en la tabla histórica correspondiente
            cursor.execute(f"""
                INSERT INTO {tabla_destino} (id_cerda, raza, edad, peso, tfi, tfd, numero_de_celo, operario, lote_origen, motivo, destino, fecha_nacimiento, fecha_movimiento, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            """, (id_cerda, raza, edad_actual, peso_final, tfi, tfd, celo, payload.operario, lote_origen, payload.motivo, payload.destino, fnac, fecha_mov))
            
            # 2. Purgar (borrado lógico) de su tabla origen
            if es_del_plantel:
                cursor.execute("UPDATE cachorras_plantel SET is_deleted = TRUE, synced_to_sheets = FALSE WHERE id_cerda = %s", (id_cerda,))
            else:
                cursor.execute("UPDATE cachorras_lotes SET is_deleted = TRUE, synced_to_sheets = FALSE WHERE id_cerda = %s", (id_cerda,))
                
            # 3. Si es Descarte, reingresa a Lotes bajo la categoría "Descartes"
            if payload.categoria == "Descarte":
                cursor.execute("""
                    INSERT INTO cachorras_lotes (id_cerda, lote, raza, edad_ingreso, fecha_nacimiento, operario, is_deleted, synced_to_sheets)
                    VALUES (%s, 'Descartes', %s, %s, %s, %s, FALSE, FALSE)
                    ON CONFLICT (id_cerda) DO UPDATE 
                    SET lote = 'Descartes', raza = EXCLUDED.raza, edad_ingreso = EXCLUDED.edad_ingreso, 
                        fecha_nacimiento = EXCLUDED.fecha_nacimiento, operario = EXCLUDED.operario, 
                        is_deleted = FALSE, timestamp_ingreso = CURRENT_TIMESTAMP, synced_to_sheets = FALSE
                """, (id_cerda, raza, edad_actual, fnac, payload.operario))
                
            bajas_realizadas.append(id_cerda)
            
        db.commit()
        return {"status": "SUCCESS", "message": f"Se procesó la baja de {len(bajas_realizadas)} cerdas como {payload.categoria}."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/modificaciones")
def crear_solicitud_modificacion(payload: List[SolicitudModificacionInput], db=Depends(get_db)):
    """Crea una solicitud de modificación en la tabla modificaciones local."""
    cursor = db.cursor()
    try:
        for s in payload:
            cursor.execute("""
                INSERT INTO cachorras_modificaciones (id_solicitud, operario, tipo_movimiento, id_cerda, datos_originales, estado, synced_to_sheets)
                VALUES (%s, %s, %s, %s, %s, %s, FALSE)
            """, (s.id_solicitud, s.operario, s.tipo_movimiento, s.id_cerda, s.datos_originales, s.estado))
        db.commit()
        return {"status": "SUCCESS", "id_solicitud": payload[0].id_solicitud}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.get("/modificaciones")
def leer_solicitudes(db=Depends(get_db)):
    """Lee todas las solicitudes del historial local."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT id_solicitud, timestamp, operario, tipo_movimiento, id_cerda, datos_originales, estado, timestamp_resolucion FROM cachorras_modificaciones")
        records = cursor.fetchall()
        for r in records:
            r["timestamp"] = format_timestamp(r["timestamp"])
            r["timestamp_resolucion"] = format_timestamp(r["timestamp_resolucion"])
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/logger")
def log_event(payload: LoggerRequest, db=Depends(get_db)):
    """Registra eventos en la bitácora del sistema."""
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO cachorras_logger (nivel, usuario, evento, synced_to_sheets)
            VALUES (%s, %s, %s, FALSE)
        """, (payload.nivel, payload.usuario, payload.evento))
        db.commit()
        return {"status": "SUCCESS"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# --- ENDPOINTS PARA EL DAEMON DE SINCRONIZACIÓN CLOUD ---

@app.get("/sync/pending")
def get_pending_syncs(db=Depends(get_db)):
    """Retorna todas las filas pendientes de sincronizar agrupadas por tabla."""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    tables = {
        "cachorras_usuarios": "usuario",
        "mails_corpo": "id",
        "cachorras_lotes": "id_cerda",
        "cachorras_plantel": "id_cerda",
        "cachorras_registro_celo": "id",
        "cachorras_muertes": "id",
        "cachorras_descartes": "id",
        "cachorras_ventas": "id",
        "cachorras_modificaciones": "id_solicitud",
        "cachorras_logger": "id"
    }
    
    pending_data = {}
    try:
        for table, pk in tables.items():
            cursor.execute(f"SELECT * FROM {table} WHERE synced_to_sheets = FALSE")
            rows = cursor.fetchall()
            if rows:
                # Limpieza de tipos de fecha a strings JSON serializables
                for r in rows:
                    for k, v in r.items():
                        if isinstance(v, (datetime.date, datetime.datetime)):
                            r[k] = v.isoformat()
                        elif isinstance(v, float) or hasattr(v, 'as_tuple'): # Decimal a float
                            r[k] = float(v) if v is not None else None
                pending_data[table] = rows
        return pending_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

class ConfirmSyncRequest(BaseModel):
    table_pks: Dict[str, List[Any]] # { "nombre_tabla": [pk1, pk2, ...] }

@app.post("/sync/confirm")
def confirm_sync(payload: ConfirmSyncRequest, db=Depends(get_db)):
    """Marca registros específicos como ya sincronizados en Google Sheets."""
    cursor = db.cursor()
    tables_pks_map = {
        "cachorras_usuarios": "usuario",
        "mails_corpo": "id",
        "cachorras_lotes": "id_cerda",
        "cachorras_plantel": "id_cerda",
        "cachorras_registro_celo": "id",
        "cachorras_muertes": "id",
        "cachorras_descartes": "id",
        "cachorras_ventas": "id",
        "cachorras_modificaciones": "id_solicitud",
        "cachorras_logger": "id"
    }
    
    try:
        for table, pks in payload.table_pks.items():
            if table not in tables_pks_map:
                continue
            pk_col = tables_pks_map[table]
            cursor.execute(
                f"UPDATE {table} SET synced_to_sheets = TRUE WHERE {pk_col} = ANY(%s)",
                (pks,)
            )
        db.commit()
        return {"status": "SUCCESS", "message": "Estado de sincronización actualizado en base de datos local."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

# --- Modelos de Datos Pydantic para App de Stock ---

class StockLoginRequest(BaseModel):
    pin: str

class GeminiOCRRequest(BaseModel):
    image: str

class RegistrarStockRequest(BaseModel):
    local: str
    codigo: str
    descripcion: str
    peso: float
    lote: str
    fecha: str
    operario: str

class RecordLoteItem(BaseModel):
    codigo: str
    descripcion: str
    peso: float
    lote: str

class RegistrarStockLoteRequest(BaseModel):
    local: str
    fecha: str
    operario: str
    registros: List[RecordLoteItem]

class SaveTangoRequest(BaseModel):
    rows: List[Dict[str, Any]]

# --- Endpoints para App de Stock (Google Sheets y Gemini) ---

@app.post("/api/stock/gemini-ocr")
def gemini_ocr(payload: GeminiOCRRequest):
    """Procesa la imagen de la etiqueta utilizando Gemini 1.5 Flash (Multimodal) para máxima precisión."""
    import google.generativeai as genai
    import base64
    import json
    
    # Intentar obtener la API KEY desde variables de entorno o desde config.json
    api_key = os.environ.get("GEMINI_API_KEY")
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if not api_key and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                api_key = config.get("gemini_api_key")
        except Exception:
            pass
            
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Falta la clave GEMINI_API_KEY. Agrégala en variables de entorno o en el config.json del servidor."
        )
        
    try:
        # Configurar biblioteca generativa
        genai.configure(api_key=api_key)
        
        # Decodificar imagen base64
        header, encoded = payload.image.split(",", 1) if "," in payload.image else ("", payload.image)
        img_bytes = base64.b64decode(encoded)
        
        # Inicializar modelo con salida estructurada JSON nativa
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Enviar imagen y prompt estructurado simple
        contents = [
            {
                "mime_type": "image/jpeg",
                "data": img_bytes
            },
            "Analiza esta etiqueta de carne de desposte. Extrae los siguientes campos en formato JSON:\n"
            "{\n"
            "  \"corte\": \"Nombre del corte (ej. TOCINO, PECHITO)\",\n"
            "  \"lote\": \"Número de lote (entero bajo LOTE, ej. 527266248)\",\n"
            "  \"peso\": \"Peso en kilos (decimal bajo KILOS, ej. 6.8)\"\n"
            "}"
        ]
        
        response = model.generate_content(contents)
        text_response = response.text.strip()
        parsed_data = json.loads(text_response)
        return parsed_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Formato no estructurado devuelto por la IA: {text_response}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el motor generativo de Gemini: {str(e)}")

@app.post("/api/stock/login")
def stock_login(payload: StockLoginRequest):
    """Valida el PIN directamente consultando la hoja 'Users' en Google Sheets en tiempo real."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    SHEET_NAME = 'Users'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        records = sheet.get_all_values()
        
        if len(records) > 1:
            headers = [str(h).lower().strip() for h in records[0]]
            user_idx = -1
            pin_idx = -1
            
            for idx, h in enumerate(headers):
                if "usuari" in h:
                    user_idx = idx
                if "cont" in h or "pin" in h:
                    pin_idx = idx
                    
            if user_idx != -1 and pin_idx != -1:
                pin_clean = str(payload.pin).strip()
                for row in records[1:]:
                    if len(row) > max(user_idx, pin_idx):
                        u_val = str(row[user_idx]).strip()
                        p_val = str(row[pin_idx]).strip()
                        if p_val == pin_clean:
                            return {"usuario": u_val}
        raise HTTPException(status_code=401, detail="PIN incorrecto.")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Google Sheets: {e}")

@app.get("/api/stock/operarios")
def get_stock_operarios():
    """Obtiene la lista de operarios leyendo directamente la hoja 'Users' de Google Sheets."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    SHEET_NAME = 'Users'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        records = sheet.get_all_values()
        
        operarios = []
        if len(records) > 1:
            headers = [str(h).lower().strip() for h in records[0]]
            user_idx = -1
            for idx, h in enumerate(headers):
                if "usuari" in h:
                    user_idx = idx
                    break
            if user_idx != -1:
                for row in records[1:]:
                    if len(row) > user_idx:
                        u_val = str(row[user_idx]).strip()
                        if u_val and u_val not in operarios:
                            operarios.append(u_val)
        return operarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Google Sheets: {e}")

@app.get("/api/stock/cortes")
def get_stock_cortes():
    """Parsea CODIGOS.csv y devuelve la lista de cortes que empiezan con '0103'."""
    import csv
    cortes = []
    csv_path = os.path.join(os.path.dirname(__file__), "CODIGOS.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=500, detail="No se encontró el archivo CODIGOS.csv en el servidor.")
        
    try:
        # Intentar con UTF-8
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        code = row[0].strip()
                        desc = row[1].strip()
                        if code.startswith("0103"):
                            cortes.append({"codigo": code, "descripcion": desc})
        except UnicodeDecodeError:
            # Fallback a latin-1
            with open(csv_path, mode='r', encoding='latin-1') as f:
                reader = csv.reader(f, delimiter=';')
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        code = row[0].strip()
                        desc = row[1].strip()
                        if code.startswith("0103"):
                            cortes.append({"codigo": code, "descripcion": desc})
        return cortes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer cortes: {e}")

@app.post("/api/stock/registrar")
def registrar_stock(payload: RegistrarStockRequest):
    """Guarda una carga de stock en la pestaña correspondiente (Stock Local 1/2/3) de Google Sheets."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    local_clean = payload.local.strip()
    if local_clean not in ["Local 1", "Local 2", "Local 3"]:
        raise HTTPException(status_code=400, detail="El local especificado no es válido (Debe ser Local 1, Local 2 o Local 3).")
        
    sheet_name = f"Stock {local_clean}"
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        try:
            ws = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
            
        vals = ws.get_all_values()
        headers = ["Fecha", "Operario", "Código", "Descripción", "Peso (KG)", "Lote"]
        
        if not vals or len(vals) == 0 or (len(vals) == 1 and (not vals[0] or vals[0] == [""] or len([x for x in vals[0] if x.strip()]) == 0)):
            ws.update(range_name="A1:F1", values=[headers])
            
        fecha_registro = payload.fecha.strip() if payload.fecha else datetime.datetime.now().strftime("%d/%m/%Y")
        
        row_data = [
            fecha_registro,
            payload.operario.strip(),
            payload.codigo.strip(),
            payload.descripcion.strip(),
            f"{payload.peso:.2f}",
            payload.lote.strip()
        ]
        
        ws.append_row(row_data)
        return {"status": "SUCCESS", "message": f"Registro guardado con éxito en {sheet_name}."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de sincronización con Google Sheets: {e}")

@app.post("/api/stock/registrar-lote")
def registrar_stock_lote(payload: RegistrarStockLoteRequest):
    """Guarda un lote de cargas de stock en la pestaña correspondiente de Google Sheets en una sola llamada."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    local_clean = payload.local.strip()
    if local_clean not in ["Local 1", "Local 2", "Local 3"]:
        raise HTTPException(status_code=400, detail="El local especificado no es válido (Debe ser Local 1, Local 2 o Local 3).")
        
    sheet_name = f"Stock {local_clean}"
    
    if not payload.registros or len(payload.registros) == 0:
        raise HTTPException(status_code=400, detail="La lista de registros está vacía.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        try:
            ws = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
            
        vals = ws.get_all_values()
        headers = ["Fecha", "Operario", "Código", "Descripción", "Peso (KG)", "Lote"]
        
        if not vals or len(vals) == 0 or (len(vals) == 1 and (not vals[0] or vals[0] == [""] or len([x for x in vals[0] if x.strip()]) == 0)):
            ws.update(range_name="A1:F1", values=[headers])
            
        fecha_registro = payload.fecha.strip() if payload.fecha else datetime.datetime.now().strftime("%d/%m/%Y")
        
        rows_to_append = []
        for reg in payload.registros:
            rows_to_append.append([
                fecha_registro,
                payload.operario.strip(),
                reg.codigo.strip(),
                reg.descripcion.strip(),
                f"{reg.peso:.2f}",
                reg.lote.strip()
            ])
            
        ws.append_rows(rows_to_append)
        return {"status": "SUCCESS", "message": f"Se guardaron {len(rows_to_append)} registros con éxito en {sheet_name}."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de sincronización con Google Sheets: {e}")

def normalize_code(code_val):
    s = str(code_val).strip()
    if s.isdigit():
        return f"{int(s):08d}"
    return s

def run_recalculate_consistency_and_yields(spreadsheet):
    """Recalcula las hojas 'Consistencia Stock' y 'Rendimiento Despiece' en Google Sheets."""
    from collections import defaultdict
    try:
        # 1. Recalcular Consistencia Stock
        try:
            rt_sheet = spreadsheet.worksheet("RTANGOSTOCK")
            rt_rows = rt_sheet.get_all_records()
        except Exception as e:
            print(f"Error al leer RTANGOSTOCK para recálculo: {e}")
            rt_rows = []
            
        tango_data = {}
        for r in rt_rows:
            dep = r.get('Depósito', '').strip()
            code = normalize_code(r.get('Cód. Artículo', ''))
            desc = r.get('Desc. artículo', '').strip()
            comp_type = r.get('Tipo comprobante', '').strip()
            
            # Cantidad en control de stock viene dividida por 1000 para pasar de gramos/milésimas a KG
            try:
                qty_raw = r.get('Cantidad control stock', 0)
                qty = float(qty_raw) / 1000.0
            except:
                qty = 0.0
            
            if not dep or not code:
                continue
                
            key = (dep, code)
            if key not in tango_data:
                tango_data[key] = { 'REI': 0.0, 'REM': 0.0, 'DEC': 0.0, 'DON': 0.0, 'desc': desc }
            
            if comp_type in tango_data[key]:
                tango_data[key][comp_type] += qty
            else:
                tango_data[key][comp_type] = qty
                
        reconciliation_results = []
        yield_results = []
        
        for local_num in [1, 2, 3]:
            local_name_tango = f"Local comercial {local_num}"
            tab_name_despiece = f"Local {local_num}"
            tab_name_stock = f"Stock Local {local_num}"
            
            # Leer despieces
            despiece_in = {}
            despiece_out = {}
            despiece_groups = defaultdict(list)
            try:
                # Intenta abrir 'Local X' o fallback 'Local comercial X'
                try:
                    d_sheet = spreadsheet.worksheet(tab_name_despiece)
                except:
                    d_sheet = spreadsheet.worksheet(f"Local comercial {local_num}")
                    
                d_rows = d_sheet.get_all_values()
                for r in d_rows:
                    if len(r) >= 5:
                        mtype_raw = r[1].strip().lower()
                        if 'egr' in mtype_raw or 'sal' in mtype_raw:
                            mtype = 'Egreso'
                        elif 'ing' in mtype_raw or 'ent' in mtype_raw:
                            mtype = 'Ingreso'
                        else:
                            mtype = r[1].strip().capitalize()
                            
                        cut_name = r[2].strip()
                        code = normalize_code(r[3])
                        try:
                            weight = float(r[4].replace(',', '.'))
                        except:
                            weight = 0.0
                        
                        if code != "01030073": # Ignorar merma para acumulados de stock
                            if mtype == "Ingreso":
                                despiece_in[code] = despiece_in.get(code, 0.0) + weight
                            elif mtype == "Egreso":
                                despiece_out[code] = despiece_out.get(code, 0.0) + weight
                                
                        operator = r[5].strip() if len(r) > 5 and r[5].strip() else "Operador"
                        lote = r[6].strip() if len(r) > 6 and r[6].strip() else "SIN-LOTE"
                        timestamp = r[0].strip() if r[0].strip() else "FECHA-SN"
                        
                        despiece_groups[(timestamp, operator)].append({
                            'type': mtype,
                            'cut': cut_name,
                            'code': code,
                            'weight': weight,
                            'lote': lote
                        })
            except Exception as e:
                print(f"Error leyendo despiece de Local {local_num}: {e}")
                
            # Procesar rendimientos despiece
            for (ts, oper), items in despiece_groups.items():
                egresos = [it for it in items if it['type'] == 'Egreso']
                ingresos = [it for it in items if it['type'] == 'Ingreso']
                
                if egresos:
                    mother = egresos[0]
                    mother_cut = mother['cut']
                    mother_weight = mother['weight']
                    mother_lote = mother['lote']
                    
                    if mother_weight > 0:
                        merma_item = [it for it in ingresos if it['code'] == '01030073']
                        merma_weight = merma_item[0]['weight'] if merma_item else 0.0
                        useful_results = [it for it in ingresos if it['code'] != '01030073']
                        useful_weight_sum = sum(it['weight'] for it in useful_results)
                        calc_merma = round(mother_weight - useful_weight_sum, 3)
                        final_merma = merma_weight if merma_weight > 0 else max(0.0, calc_merma)
                        merma_pct = round((final_merma / mother_weight) * 100.0, 2)
                        
                        for res in useful_results:
                            yield_results.append([
                                local_name_tango, ts, oper, mother_lote, mother_cut, mother_weight,
                                res['lote'], res['cut'], res['weight'], f"{round((res['weight']/mother_weight)*100, 2)}%",
                                final_merma, f"{merma_pct}%"
                            ])
                        if not useful_results:
                            yield_results.append([
                                local_name_tango, ts, oper, mother_lote, mother_cut, mother_weight,
                                "", "SÓLO DECOMISO/MERMA", 0.0, "0.0%", final_merma, f"{merma_pct}%"
                            ])
                            
            # Leer stock físico
            stock_counts = {}
            try:
                s_sheet = spreadsheet.worksheet(tab_name_stock)
                s_rows = s_sheet.get_all_values()
                if len(s_rows) > 1:
                    for r in s_rows[1:]:
                        if len(r) > 4:
                            code = normalize_code(r[2])
                            try:
                                weight = float(r[4])
                            except:
                                weight = 0.0
                            stock_counts[code] = weight
            except Exception as e:
                pass
                
            # Consolidar códigos de artículo
            all_codes = set()
            item_descs = {}
            for (dep, code), data in tango_data.items():
                if dep == local_name_tango:
                    all_codes.add(code)
                    item_descs[code] = data['desc']
            for code in despiece_in:
                all_codes.add(code)
            for code in despiece_out:
                all_codes.add(code)
            for code in stock_counts:
                all_codes.add(code)
                
            for code in sorted(list(all_codes)):
                desc = item_descs.get(code, f"Producto {code}")
                t_info = tango_data.get((local_name_tango, code), { 'REI': 0.0, 'REM': 0.0, 'DEC': 0.0, 'DON': 0.0 })
                rei = t_info.get('REI', 0.0)
                rem = t_info.get('REM', 0.0)
                dec = t_info.get('DEC', 0.0)
                don = t_info.get('DON', 0.0)
                
                d_in = despiece_in.get(code, 0.0)
                d_out = despiece_out.get(code, 0.0)
                phys_final = stock_counts.get(code, None)
                stock_ini = 0.0
                
                stock_teorico = stock_ini + rei + rem + dec + don + d_in - d_out
                
                if phys_final is not None:
                    diff = phys_final - stock_teorico
                    if abs(diff) < 0.01:
                        estado = "OK"
                    elif diff > 0:
                        estado = "Sobrante"
                    else:
                        estado = "Faltante"
                else:
                    diff = ""
                    estado = "Sin Conteo"
                    
                reconciliation_results.append([
                    local_name_tango, code, desc, stock_ini, round(rei, 3), round(rem, 3), round(dec + don, 3),
                    round(d_in, 3), round(d_out, 3), round(stock_teorico, 3),
                    phys_final if phys_final is not None else "", round(diff, 3) if diff != "" else "", estado
                ])
                
        # Guardar en sheets
        # 1. Consistencia Stock
        try:
            ws_cons = spreadsheet.worksheet("Consistencia Stock")
            spreadsheet.del_worksheet(ws_cons)
        except:
            pass
        ws_cons = spreadsheet.add_worksheet(title="Consistencia Stock", rows=str(len(reconciliation_results) + 50), cols="15")
        headers_cons = [
            'Sucursal', 'Código', 'Producto', 'Stock Inicial', 'Ingresos (Tango REI)', 
            'Ventas (Tango REM)', 'Ajustes (Tango DEC/DON)', 'Transf. Entradas (Despiece)', 
            'Transf. Salidas (Despiece)', 'Stock Teórico', 'Stock Físico Real', 'Diferencia', 'Estado'
        ]
        ws_cons.update(range_name="A1", values=[headers_cons] + reconciliation_results)
        
        # 2. Rendimiento Despiece
        try:
            ws_yield = spreadsheet.worksheet("Rendimiento Despiece")
            spreadsheet.del_worksheet(ws_yield)
        except:
            pass
        ws_yield = spreadsheet.add_worksheet(title="Rendimiento Despiece", rows=str(len(yield_results) + 50), cols="15")
        headers_yield = [
            'Sucursal', 'Fecha/Hora', 'Operario', 'Lote Madre', 'Corte Madre', 'Peso Madre (KG)',
            'Lote Resultante', 'Producto Resultante', 'Peso Resultante (KG)', 'Rendimiento (%)',
            'Merma Registrada (KG)', 'Merma (%)'
        ]
        ws_yield.update(range_name="A1", values=[headers_yield] + yield_results)
        
    except Exception as e:
        print(f"Error durante el recálculo automático: {e}")

@app.get("/api/stock/reporte-consistencia")
def get_reporte_consistencia():
    """Retorna los datos de la hoja 'Consistencia Stock' de Google Sheets."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        try:
            ws = spreadsheet.worksheet("Consistencia Stock")
        except gspread.exceptions.WorksheetNotFound:
            run_recalculate_consistency_and_yields(spreadsheet)
            ws = spreadsheet.worksheet("Consistencia Stock")
            
        records = ws.get_all_records()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener consistencia de stock: {e}")

@app.get("/api/stock/reporte-rendimiento")
def get_reporte_rendimiento():
    """Retorna los datos de la hoja 'Rendimiento Despiece' de Google Sheets."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Recalcular automáticamente para incluir las últimas entradas de Local 1, Local 2 y Local 3
        try:
            run_recalculate_consistency_and_yields(spreadsheet)
        except Exception as err:
            print(f"Aviso al recalcular rendimientos: {err}")

        ws = spreadsheet.worksheet("Rendimiento Despiece")
        records = ws.get_all_records()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener rendimiento de despiece: {e}")

@app.post("/api/stock/save-tango")
def save_tango_data(payload: SaveTangoRequest):
    """Guarda las filas de Tango en RTANGOSTOCK, y luego recalcula consistencia y rendimientos."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
    SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=500, detail="Falta el archivo credentials.json en el servidor.")
        
    if not payload.rows:
        raise HTTPException(status_code=400, detail="La lista de filas de Tango está vacía.")
        
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        try:
            ws = spreadsheet.worksheet("RTANGOSTOCK")
            spreadsheet.del_worksheet(ws)
        except:
            pass
            
        ws = spreadsheet.add_worksheet(title="RTANGOSTOCK", rows=str(len(payload.rows) + 100), cols="15")
        
        headers = [
            'Fecha de Comprobante', 'Origen del movimiento', 'Tipo comprobante', 'Comprobante',
            'Cód. Artículo', 'Desc. artículo', 'U.M. control stock', 'Cantidad control stock',
            'Depósito', 'Depósito destino'
        ]
        
        rows_to_write = []
        for r in payload.rows:
            rows_to_write.append([
                str(r.get('Fecha de Comprobante', '')),
                str(r.get('Origen del movimiento', '')),
                str(r.get('Tipo comprobante', '')),
                str(r.get('Comprobante', '')),
                str(r.get('Cód. Artículo', '')),
                str(r.get('Desc. artículo', '')),
                str(r.get('U.M. control stock', '')),
                str(r.get('Cantidad control stock', 0)),
                str(r.get('Depósito', '')),
                str(r.get('Depósito destino', ''))
            ])
            
        ws.update(range_name="A1", values=[headers] + rows_to_write)
        
        # Disparar el recálculo automático de consistencia y rendimientos
        run_recalculate_consistency_and_yields(spreadsheet)
        
        return {"status": "SUCCESS", "message": f"Se importaron {len(rows_to_write)} registros de Tango y se recalcularon los análisis."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar datos de Tango y recalcular: {e}")

if __name__ == "__main__":
    import uvicorn
    # Corre localmente en el puerto 8000. 
    # El parámetro host="0.0.0.0" permite conexiones desde cualquier IP de la red de la granja.
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

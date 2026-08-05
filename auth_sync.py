import csv
import os
import sys
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import socket
from datetime import datetime
from procesador_datos import ProcesadorDatos

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    appdata = os.getenv('APPDATA')
    if not appdata:
        data_dir = os.path.join(os.path.expanduser("~"), ".spi_despiece")
    else:
        data_dir = os.path.join(appdata, "SPI-Despiece")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

BASE_PATH = get_base_path()
DATA_DIR = get_data_dir()
SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
SHEET_NAME = 'Users'
CREDENTIALS_FILE = os.path.join(BASE_PATH, 'credentials.json')
CSV_FILE = os.path.join(DATA_DIR, 'HDContent1 - Users.csv')
CSV_DECOMISOS = os.path.join(DATA_DIR, 'HDContent1 - Decomisos.csv')

def is_connected():
    try:
        host = socket.gethostbyname("www.google.com")
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except:
        return False

def sync_users_from_sheets():
    """Descarga los usuarios desde Google Sheets si hay internet y actualiza el CSV."""
    if not is_connected():
        return False, "Modo OFFLINE: Sin conexión a internet."
    
    if not os.path.exists(CREDENTIALS_FILE):
        return False, f"Modo OFFLINE: Falta {CREDENTIALS_FILE}"
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        
        # Acceder por ID y Hoja
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        records = sheet.get_all_values()
        
        if len(records) > 1: # Require at least a header row and one user row
            with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Usuario", "Contraseña"])
                
                # Assume headers are the first row
                headers = [str(h).lower().strip() for h in records[0]]
                
                # Find the indices for user and password columns
                user_idx = -1
                pin_idx = -1
                
                for idx, h in enumerate(headers):
                    if "usuari" in h:
                        user_idx = idx
                    if "cont" in h or "pin" in h:
                        pin_idx = idx
                        
                # Proceed only if both columns were found
                if user_idx != -1 and pin_idx != -1:
                    for row in records[1:]: # Skip header
                        if len(row) > max(user_idx, pin_idx):
                            u_val = str(row[user_idx]).strip()
                            p_val = str(row[pin_idx]).strip()
                            if u_val and p_val:
                                writer.writerow([u_val, p_val])
                        
        return True, "Usuarios sincronizados con éxito (ONLINE)."
    except Exception as e:
        return False, f"Error al sincronizar: {e}"

def load_local_users():
    """Lee el CSV y devuelve un diccionario { 'PIN': 'Nombre de Usuario' }."""
    if not os.path.exists(CSV_FILE):
        default_file = os.path.join(BASE_PATH, 'HDContent1 - Users.csv')
        if os.path.exists(default_file):
            import shutil
            try:
                shutil.copy(default_file, CSV_FILE)
            except Exception as e:
                print(f"Error al copiar archivo de usuarios por defecto: {e}")
                
    users = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    pin = str(row[1]).strip()
                    nombre = row[0].strip()
                    users[pin] = nombre
    return users

def sync_decomisos_from_sheets():
    """Descarga los motivos de decomiso desde la hoja Contenidos (Columna K) y actualiza el CSV."""
    if not is_connected():
        return False, "Modo OFFLINE: Sin conexión a internet para decomisos."
    
    if not os.path.exists(CREDENTIALS_FILE):
        return False, f"Modo OFFLINE: Falta {CREDENTIALS_FILE}"
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SHEET_ID).worksheet('Contenidos')
        records = sheet.get_all_values()
        
        decomisos_validos = []
        if len(records) > 1:
            for row in records[1:]: # Saltar fila 1
                if len(row) > 10:
                    motivo = str(row[10]).strip()
                    if motivo: # Ignorar vacíos
                        decomisos_validos.append(motivo)
                        
            if decomisos_validos:
                with open(CSV_DECOMISOS, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Motivos de Decomiso"])
                    for motivo in decomisos_validos:
                        writer.writerow([motivo])
                        
        return True, "Decomisos sincronizados con éxito (ONLINE)."
    except Exception as e:
        return False, f"Error al sincronizar decomisos: {e}"

def load_local_decomisos():
    """Lee el CSV local y devuelve una lista de strings con los motivos."""
    import shutil
    if not os.path.exists(CSV_DECOMISOS):
        # Intentar migrar desde Descartes legacy
        legacy_path = os.path.join(DATA_DIR, 'HDContent1 - Descartes.csv')
        if os.path.exists(legacy_path):
            try:
                shutil.copy(legacy_path, CSV_DECOMISOS)
            except Exception:
                pass
        else:
            default_file = os.path.join(BASE_PATH, 'HDContent1 - Decomisos.csv')
            if not os.path.exists(default_file):
                default_file_legacy = os.path.join(BASE_PATH, 'HDContent1 - Descartes.csv')
                if os.path.exists(default_file_legacy):
                    default_file = default_file_legacy
            if os.path.exists(default_file):
                try:
                    shutil.copy(default_file, CSV_DECOMISOS)
                except Exception as e:
                    print(f"Error al copiar decomisos por defecto: {e}")
                
    decomisos = []
    if os.path.exists(CSV_DECOMISOS):
        with open(CSV_DECOMISOS, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if row:
                    motivo = str(row[0]).strip()
                    if motivo:
                        decomisos.append(motivo)
    return decomisos

def load_local_config():
    """Carga la configuración local del archivo config.json."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('local_activo', 'Local 2')  # Por defecto Local 2
        except Exception as e:
            print(f"Error al cargar config.json: {e}")
    return 'Local 2'

def save_local_config(local_name):
    """Guarda la configuración del local en config.json."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    data = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error al leer config.json existente: {e}")
    data['local_activo'] = local_name
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar config.json: {e}")
        return False

def load_scale_divisor():
    """Carga el divisor de la balanza desde config.json. Por defecto 1000.0."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return float(data.get('divisor_balanza', 1000.0))
        except Exception as e:
            print(f"Error al cargar divisor_balanza: {e}")
    return 1000.0

def save_scale_divisor(divisor_val):
    """Guarda el divisor de la balanza en config.json."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    data = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error al leer config.json existente para divisor: {e}")
    data['divisor_balanza'] = float(divisor_val)
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar divisor_balanza: {e}")
        return False

def load_permitir_manual():
    """Carga si el control manual está permitido desde config.json. Por defecto True."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return bool(data.get('permitir_control_manual', True))
        except Exception as e:
            print(f"Error al cargar permitir_control_manual: {e}")
    return True

def save_permitir_manual(permitir_bool):
    """Guarda la opción de permitir control manual en config.json."""
    config_file = os.path.join(DATA_DIR, 'config.json')
    data = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error al leer config.json existente para permitir_control_manual: {e}")
    data['permitir_control_manual'] = bool(permitir_bool)
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar permitir_control_manual: {e}")
        return False

def generar_lote_resultante(lote_origen):
    ahora = datetime.now()
    dia_num = ahora.isoweekday() # Lunes = 1, Martes = 2, ..., Domingo = 7
    num_semana = ahora.isocalendar()[1]
    yy = ahora.strftime("%y")
    lote_str = str(lote_origen).strip()
    
    # Extraer y preservar sufijos conocidos (-J para Blanda, -P para Pulpa de Paleta)
    sufijo = ""
    if lote_str.endswith("-J"):
        sufijo = "-J"
        lote_str = lote_str[:-2]
    elif lote_str.endswith("-P"):
        sufijo = "-P"
        lote_str = lote_str[:-2]
        
    ultimos_4 = lote_str[-4:] if len(lote_str) >= 4 else lote_str
    return f"{dia_num}{num_semana}{yy}{ultimos_4}{sufijo}"

def push_despiece_to_sheets(corte_madre, peso_madre, resultantes, operador, lote, callback_error=None):
    """Sincroniza el despiece en una sola hoja por local (ej. Local 1, Local 2), diferenciando ingresos y egresos con la columna Movimiento."""
    if not is_connected():
        return False, "Sin conexión."
    
    if not os.path.exists(CREDENTIALS_FILE):
        return False, "Falta credenciales."
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        local_activo = load_local_config()
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        filas_a_agregar = []
        
        # 1. Registrar Egreso (Corte Madre)
        codigo_madre = ProcesadorDatos().obtener_codigo(corte_madre)
        # Columnas: Timestamp, Movimiento, Corte, CODIGO, Peso, Operador, Lote, Motivo Decomiso
        filas_a_agregar.append([
            ahora, 
            "Egreso", 
            corte_madre, 
            codigo_madre, 
            f"{peso_madre:.2f}", 
            operador, 
            lote, 
            ""  # Motivo Decomiso vacío para egresos
        ])
        
        # 2. Registrar Ingresos (Cortes Resultantes)
        if resultantes:
            # Agrupar por (descripción + motivo + es_decomiso) para sumatoria
            sumatoria = {}
            for c in resultantes:
                desc = c.get('descripcion', 'Desconocido')
                motivo = c.get('motivo_decomiso', '')
                es_dec = c.get('es_decomiso', False)
                clave = (desc, motivo, es_dec)
                peso = c.get('peso', 0.0)
                sumatoria[clave] = sumatoria.get(clave, 0.0) + peso
            
            for (desc, motivo, es_dec), peso_total in sumatoria.items():
                # Obtener código para la descripción
                codigo_res = ProcesadorDatos().obtener_codigo(desc)
                movimiento = "Decomiso" if es_dec else "Ingreso"
                
                # Caso especial: Si el corte resultante es TOCINO, el lote queda fijo en "00049"
                if str(desc).strip().upper() == "TOCINO":
                    lote_destino = "00049"
                else:
                    lote_destino = generar_lote_resultante(lote)
                
                # Columnas: Timestamp, Movimiento, Corte, CODIGO, Peso, Operador, Lote, Motivo Decomiso
                filas_a_agregar.append([
                    ahora, 
                    movimiento, 
                    desc, 
                    codigo_res, 
                    f"{peso_total:.2f}", 
                    operador, 
                    lote_destino, 
                    motivo
                ])
                
        # 3. Escribir todas las filas en la hoja correspondiente al local activo
        if filas_a_agregar:
            try:
                ws_local = spreadsheet.worksheet(local_activo)
                ws_local.append_rows(filas_a_agregar)
            except Exception as e:
                print(f"Error al escribir en la hoja {local_activo}: {e}")
                raise e
        
        return True, "Sincronización Cloud exitosa."
    except Exception as e:
        error_msg = f"Error Cloud: {e}"
        if callback_error:
            callback_error(error_msg)
        return False, error_msg

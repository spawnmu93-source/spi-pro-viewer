"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - CONFIGURACIÓN CENTRAL DE PLANTA
Módulos: Frigorífico (Faena) y Fábrica de Chacinados
=============================================================================
Este archivo concentra todos los parámetros, umbrales y banderas de comportamiento
operativo del software. Permite ajustar la rigidez del sistema (bloquear vs. advertir)
sin modificar el código fuente de los drivers ni de las interfaces gráficas.
"""

import os

# ---------------------------------------------------------------------------
# 1. AMBIENTE Y PERSISTENCIA LOCAL
# ---------------------------------------------------------------------------
VERSION_SISTEMA = "2.0.0-MVP"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "spi_local_buffer.db")

# Endpoint central PostgreSQL / API REST
API_CENTRAL_URL = os.environ.get("SPI_API_URL", "https://api-spi.empresa.com/v1")
API_TOKEN_JWT = os.environ.get("SPI_JWT_TOKEN", "mock_jwt_token_spi_2026")
TERMINAL_ID_DEFAULT = os.environ.get("SPI_TERMINAL_ID", "TERM-PLANTA-01")

# ---------------------------------------------------------------------------
# 2. HARDWARE: BALANZAS RS-232
# ---------------------------------------------------------------------------
# Balanza de Gancho Aéreo en Faena (Systel Cuora)
BALANZA_GANCHO_PORT = os.environ.get("BALANZA_GANCHO_PORT", "COM3")
BALANZA_GANCHO_BAUD = 9600
BALANZA_GANCHO_PROTOCOL = "SYSTEL"  # Opciones: "SYSTEL", "MORETTI", "MOCK"

# Balanza de Batea / Plataforma en Fábrica (Moretti LAP)
BALANZA_BATEA_PORT = os.environ.get("BALANZA_BATEA_PORT", "COM4")
BALANZA_BATEA_BAUD = 9600
BALANZA_BATEA_PROTOCOL = "MORETTI"  # Opciones: "MORETTI", "SYSTEL", "MOCK"

# Parámetros de Estabilización de Peso
PESO_MINIMO_VALIDO_KG = 1.0       # Ignora lecturas menores a 1 kg (ruido de cables)
DEBOUNCE_LECTURAS_CONSECUTIVAS = 3 # Cantidad de lecturas iguales consecutivas para peso estable
TOLERANCIA_ESTABILIDAD_KG = 0.05   # Margen de ±50g para considerar lecturas idénticas
TIMEOUT_LECTURA_SERIAL_SEG = 1.0   # Timeout de comunicación serie

# ---------------------------------------------------------------------------
# 3. HARDWARE: IMPRESORAS ZEBRA ZPL-II
# ---------------------------------------------------------------------------
ZEBRA_IP = os.environ.get("ZEBRA_IP", "192.168.1.200")
ZEBRA_PORT = int(os.environ.get("ZEBRA_PORT", 9100))
ZEBRA_DPI = 203  # 8 dots/mm

# Medidas de etiquetas
ETIQUETA_CANAL_ANCHO_MM = 100
ETIQUETA_CANAL_ALTO_MM = 75

ETIQUETA_BACHADA_ANCHO_MM = 100
ETIQUETA_BACHADA_ALTO_MM = 50

# ---------------------------------------------------------------------------
# 4. PARÁMETROS OPERATIVOS: FRIGORÍFICO Y FAENA
# ---------------------------------------------------------------------------
# Granjas de Origen Exclusivas
GRANJA_ULAPES_RENSPA = "11.012.0.00435/00"
GRANJA_CHEPES_RENSPA = "11.016.0.00312/00"
GRANJAS_HABILITADAS = [
    f"Granja Ulapes - RENSPA {GRANJA_ULAPES_RENSPA}",
    f"Granja Chepes - RENSPA {GRANJA_CHEPES_RENSPA}"
]

# Cámaras de Oreo y Frigoríficas de Planta
CAMARAS_PLANTA = {
    "Cámara de Oreo 1": {"capacidad_max_mr": 400, "tipo": "OREADO", "temp_objetivo_c": 2.0, "codigo": "CO1"},
    "Cámara de Oreo 2": {"capacidad_max_mr": 400, "tipo": "OREADO", "temp_objetivo_c": 2.0, "codigo": "CO2"},
    "Cámara Frigorífica 1": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C1"},
    "Cámara Frigorífica 2": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C2"},
    "Cámara Frigorífica 3": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C3"},
    "Cámara Frigorífica 4": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C4"},
    "Cámara Frigorífica 5": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C5"},
    "Cámara Frigorífica 6": {"capacidad_max_mr": 700, "tipo": "FRIGORIFICA", "temp_objetivo_c": 1.0, "codigo": "C6"},
}
LISTA_CAMARAS_NOMBRES = list(CAMARAS_PLANTA.keys())

# Mapeo de Códigos de Depósito Rápidos de Planta
DEPOSITOS_MAP = {
    "C1": "Cámara Frigorífica 1",
    "C2": "Cámara Frigorífica 2",
    "C3": "Cámara Frigorífica 3",
    "C4": "Cámara Frigorífica 4",
    "C5": "Cámara Frigorífica 5",
    "C6": "Cámara Frigorífica 6",
    "CO1": "Cámara de Oreo 1",
    "CO2": "Cámara de Oreo 2",
}
DEPOSITOS_INVERSO_MAP = {v: k for k, v in DEPOSITOS_MAP.items()}
LISTA_CODIGOS_DEPOSITOS = ["C1", "C2", "C3", "C4", "C5", "C6", "CO1", "CO2"]

# Categorías / Tipos de Animal Oficiales
TIPOS_ANIMAL = [
    {"codigo": "MEI", "descripcion": "MACHO ENTERO INMUNOCASTRADO", "label": "MEI - MACHO ENTERO INMUNOCASTRADO"},
    {"codigo": "CAP", "descripcion": "CAPÓN", "label": "CAP - CAPÓN"},
    {"codigo": "SAN", "descripcion": "SANITARIAS", "label": "SAN - SANITARIAS"},
    {"codigo": "CER", "descripcion": "CERDAS", "label": "CER - CERDAS"},
    {"codigo": "CACH", "descripcion": "CACHORRAS", "label": "CACH - CACHORRAS"},
    {"codigo": "LECH", "descripcion": "LECHÓN", "label": "LECH - LECHÓN"},
]
LISTA_TIPOS_ANIMAL_LABELS = [t["label"] for t in TIPOS_ANIMAL]
LISTA_TIPOS_ANIMAL_CODIGOS = [t["codigo"] for t in TIPOS_ANIMAL]
TIPO_ANIMAL_DEFAULT = "MEI"

# Motivos Oficiales de Decomiso Parcial (DP) SENASA
MOTIVOS_DECOMISO_PARCIAL = [
    {"codigo": "CO", "descripcion": "FRACTURA DE COLUMNA", "label": "CO - FRACTURA DE COLUMNA"},
    {"codigo": "CA", "descripcion": "FRACTURA DE CADERA", "label": "CA - FRACTURA DE CADERA"},
    {"codigo": "AB", "descripcion": "ABSCESO", "label": "AB - ABSESO"},
    {"codigo": "HE", "descripcion": "HEMATOMAS", "label": "HE - HEMATOMAS"},
]
LISTA_MOTIVOS_DP_LABELS = [m["label"] for m in MOTIVOS_DECOMISO_PARCIAL]
MOTIVOS_DP_MAP = {m["codigo"]: m["descripcion"] for m in MOTIVOS_DECOMISO_PARCIAL}

# Recepción e Ingreso de Hacienda
TOLERANCIA_DTE_CABEZAS_DIF = 0     # Si difiere en cabezas, activa protocolo de discrepancia
HORAS_MINIMAS_DESCANSO_CORRAL = 2.5 # Horas recomendadas antes del noqueo

# Aprobación Sanitaria SENASA
# Si es True: La balanza exige aprobación previa unitaria del veterinario.
# Si es False (Recomendado): Aprobación por excepción (toda res se asume apta salvo decomiso).
BLOQUEO_SENASA_ESTRICTO = False

# Alternancia automática de media res (primero IZQ, luego DER automáticamente)
ALTERNANCIA_LADO_AUTOMATICA = True

# Re-impresión de etiquetas emitidas
# Si es True: Requiere PIN de supervisor para volver a imprimir una etiqueta ya emitida.
REIMPRESION_REQUIERE_SUPERVISOR = True

# KPIs y Alertas de Faena
RENDIMIENTO_FAENA_OBJETIVO_MIN_PCT = 79.5  # % mínimo de rendimiento de canal caliente
RENDIMIENTO_FAENA_OBJETIVO_MAX_PCT = 83.0  # % máximo
MERMA_OREADO_CAMARA_MAX_PCT = 2.0          # % máximo tolerable a 24 horas

# ---------------------------------------------------------------------------
# 5. PARÁMETROS OPERATIVOS: FÁBRICA DE CHACINADOS
# ---------------------------------------------------------------------------
# Lote Maestro Fijo de Tocino Industrial proveniente de desposte
LOTE_FIJO_TOCINO_INDUSTRIAL = "00049"

# Temperatura de Masa de Picado / Batea (Puntos Críticos Bromatológicos)
TEMP_MASA_IDEAL_MAX_C = 4.0   # 🟢 Verde: Por debajo de este valor la masa es perfecta
TEMP_MASA_ALERTA_C = 5.0      # 🟡 Ámbar: Se recomienda incorporar escarcha de hielo
TEMP_MASA_BLOQUEO_C = 6.0     # 🔴 Rojo: Peligro de empaste de grasa. Bloqueo de embutido

# Tolerancia en formulación de ingredientes respecto a receta teórica
TOLERANCIA_DESVIO_RECETA_PCT = 1.5 # ±1.5% antes de alertar

# Curva de Merma de Secado de Salames (a día 20 - 30)
MERMA_SECADO_MIN_PCT = 32.0   # Menos de esto: Falto de secado
MERMA_SECADO_OBJETIVO_PCT = 35.0 # Punto óptimo comercial
MERMA_SECADO_MAX_PCT = 40.0   # Más de esto: Desecamiento excesivo

# ---------------------------------------------------------------------------
# 6. SINCRONIZACIÓN Y RESILIENCIA OFFLINE
# ---------------------------------------------------------------------------
MAX_REGISTROS_POR_LOTE_SYNC = 50
INTERVALO_SYNC_SEGUNDOS = 5
MAX_REINTENTOS_EXPONENCIAL = 8

"""
SCRIPT DE RECUPERACIÓN Y REENVÍO DE CSVs LOCALES A GOOGLE SHEETS
Sistema de Producción Integral (SPI Despiece / Combos)

Permite seleccionar uno o varios archivos CSV locales generados por SPI,
parsear sus registros de despiece o combo, y enviarlos a la hoja correspondiente
en Google Sheets utilizando las credenciales oficiales del sistema.
"""

import os
import sys
import csv
import json
import threading
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Google Sheets
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSPREAD_DISPONIBLE = True
except ImportError:
    GSPREAD_DISPONIBLE = False

# UI
try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox, ttk
    import tkinter as tk
    CTK_DISPONIBLE = True
except ImportError:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    CTK_DISPONIBLE = False

# Importar utilidades locales del proyecto si existen
try:
    from auth_sync import generar_lote_resultante, load_local_config
    from procesador_datos import ProcesadorDatos
except ImportError:
    def generar_lote_resultante(lote_origen):
        ahora = datetime.now()
        dia_num = ahora.isoweekday()
        num_semana = ahora.isocalendar()[1]
        yy = ahora.strftime("%y")
        lote_str = str(lote_origen).strip()
        sufijo = ""
        if lote_str.endswith("-J"):
            sufijo = "-J"
            lote_str = lote_str[:-2]
        elif lote_str.endswith("-P"):
            sufijo = "-P"
            lote_str = lote_str[:-2]
        ultimos_4 = lote_str[-4:] if len(lote_str) >= 4 else lote_str
        return f"{dia_num}{num_semana}{yy}{ultimos_4}{sufijo}"

    def load_local_config():
        return "LOCAL 1"

    class ProcesadorDatos:
        def obtener_codigo(self, corte_nombre):
            return ""

SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SHEET_ID = '1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY'
LOCALES_DISPONIBLES = ["LOCAL 1", "LOCAL 2", "LOCAL 3", "LOCAL PRUEBAS"]


def buscar_credenciales() -> str:
    """Busca credentials.json en rutas de desarrollo y carpetas de instalación."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_appdata = os.getenv('LOCALAPPDATA', '')

    candidatos = [
        os.path.join(base_dir, 'credentials.json'),
        os.path.join(base_dir, '_internal', 'credentials.json'),
        os.path.join(local_appdata, 'SPI - Despiece Horizontal', '_internal', 'credentials.json'),
        os.path.join(local_appdata, 'SPI - Despiece', '_internal', 'credentials.json'),
        os.path.join(local_appdata, 'SPI - Despiece Horizontal', 'credentials.json'),
        os.path.join(local_appdata, 'SPI - Despiece', 'credentials.json'),
    ]

    for p in candidatos:
        if os.path.exists(p):
            return p
    return ""


def buscar_directorio_csv() -> str:
    """Detecta la carpeta de almacenamiento de CSVs del usuario."""
    user_home = os.path.expanduser("~")
    candidatos = [
        os.path.join(user_home, "OneDrive", "Documentos", "SPI-Despiece"),
        os.path.join(user_home, "OneDrive", "Documents", "SPI-Despiece"),
        os.path.join(user_home, "Documentos", "SPI-Despiece"),
        os.path.join(user_home, "Documents", "SPI-Despiece"),
        os.path.join(user_home, "SPI-Despiece"),
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return candidatos[0]


def formatear_marca_temporal(ts_raw: str) -> str:
    """Convierte cualquier fecha/hora del CSV a formato DD/MM/YYYY HH:MM:SS."""
    ts_str = str(ts_raw).strip()
    if not ts_str:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S"
    ]
    for fmt in formatos:
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            pass
    return ts_str


def parsear_csv(ruta_csv: str) -> Dict[str, Any]:
    """
    Parsea un archivo CSV (Despiece o Combo) y extrae las filas listas para Google Sheets.
    Retorna un diccionario con metadatos y la lista de filas con estructura:
    ['Marca Temporal', 'Proceso', 'Corte', 'Codigo', 'Peso', 'Operario', 'Lote', 'Motivo D']
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No existe el archivo: {ruta_csv}")

    with open(ruta_csv, mode='r', encoding='utf-8', errors='ignore') as f:
        lineas = list(csv.reader(f, delimiter=';'))

    # Limpiar líneas vacías
    filas_validas = [r for r in lineas if r and any(str(c).strip() for c in r)]
    if not filas_validas:
        raise ValueError("El archivo CSV está completamente vacío.")

    # Detectar si es COMBO o DESPIECE
    es_combo = any(len(r) > 0 and r[0].strip().upper() == 'COMBO_ARMADO' for r in filas_validas)
    proc = ProcesadorDatos()

    filas_sheets = []
    resumen = {
        "archivo": os.path.basename(ruta_csv),
        "ruta": ruta_csv,
        "tipo": "COMBO" if es_combo else "DESPIECE",
        "lote": "",
        "operador": "",
        "timestamp": "",
        "descripcion_principal": "",
        "peso_total": 0.0,
        "filas_a_enviar": 0,
        "detalle_filas": []
    }

    if es_combo:
        # Formato COMBO_ARMADO
        combo_header = None
        ingredientes = []

        for r in filas_validas:
            tipo_reg = r[0].strip().upper()
            if tipo_reg == 'COMBO_ARMADO':
                combo_header = r
            elif tipo_reg == 'INGREDIENTE_COMBO':
                ingredientes.append(r)

        if not combo_header:
            raise ValueError("Estructura de Combo inválida: falta encabezado COMBO_ARMADO.")

        # [TIPO, CODIGO, DESCRIPCION, PESO REAL, BANDEJAS, OPERADOR, TIMESTAMP, LOTE, DIFERENCIA]
        c_cod = combo_header[1].strip() if len(combo_header) > 1 else ""
        c_nom = combo_header[2].strip() if len(combo_header) > 2 else "Combo"
        c_peso_str = combo_header[3].strip() if len(combo_header) > 3 else "0.0"
        c_bandejas = combo_header[4].strip() if len(combo_header) > 4 else "1"
        c_operador = combo_header[5].strip() if len(combo_header) > 5 else ""
        c_ts_raw = combo_header[6].strip() if len(combo_header) > 6 else ""
        c_lote = combo_header[7].strip() if len(combo_header) > 7 else ""

        if not c_cod:
            c_cod = proc.obtener_codigo(c_nom)

        c_ts = formatear_marca_temporal(c_ts_raw)
        peso_total_ing = 0.0

        # 1. Egresos: Ingredientes pesados
        for ing in ingredientes:
            # [TIPO, CODIGO, DESCRIPCION, PESO REAL, PESO ESPERADO, OPERADOR, TIMESTAMP, LOTE, DESVIO %]
            i_cod = ing[1].strip() if len(ing) > 1 else ""
            i_nom = ing[2].strip() if len(ing) > 2 else ""
            try:
                i_peso = float(ing[3].strip().replace(',', '.'))
            except (ValueError, IndexError):
                i_peso = 0.0
            i_op = ing[5].strip() if len(ing) > 5 and ing[5].strip() else c_operador
            i_ts = formatear_marca_temporal(ing[6].strip() if len(ing) > 6 else c_ts_raw)
            i_lote = ing[7].strip() if len(ing) > 7 and ing[7].strip() else c_lote
            i_desvio = ing[8].strip() if len(ing) > 8 else ""

            if not i_cod:
                i_cod = proc.obtener_codigo(i_nom)

            peso_total_ing += i_peso
            nota_desvio = f"Consumo Combo ({i_desvio})" if i_desvio else "Consumo Combo"

            filas_sheets.append([
                i_ts,
                "Egreso",
                i_nom,
                i_cod,
                f"{i_peso:.2f}",
                i_op,
                i_lote,
                nota_desvio
            ])

        # 2. Ingreso: Combo terminado
        try:
            bandejas_num = int(round(float(c_bandejas.replace(',', '.'))))
        except ValueError:
            bandejas_num = 1

        lote_combo_dest = generar_lote_resultante(c_lote)
        filas_sheets.append([
            c_ts,
            "Ingreso",
            c_nom,
            c_cod,
            f"{peso_total_ing:.2f}",
            c_operador,
            lote_combo_dest,
            f"Producción {bandejas_num} bandejas"
        ])

        resumen["lote"] = c_lote
        resumen["operador"] = c_operador
        resumen["timestamp"] = c_ts
        resumen["descripcion_principal"] = f"{c_nom} ({bandejas_num} bandejas)"
        resumen["peso_total"] = peso_total_ing

    else:
        # Formato DESPIECE TRADICIONAL
        origen_row = None
        resultantes = []

        for r in filas_validas:
            tipo_reg = r[0].strip().upper()
            if tipo_reg == 'ORIGEN':
                origen_row = r
            elif tipo_reg in ('DESTINO', 'DECOMISO'):
                resultantes.append(r)

        if not origen_row:
            raise ValueError("Estructura de Despiece inválida: no se encontró registro ORIGEN.")

        # [ORIGEN, CODIGO, DESCRIPCION, PESO, CANTIDAD, OPERADOR, TIMESTAMP, LOTE, MOTIVO]
        o_cod = origen_row[1].strip() if len(origen_row) > 1 else ""
        o_corte = origen_row[2].strip() if len(origen_row) > 2 else ""
        try:
            o_peso = float(origen_row[3].strip().replace(',', '.'))
        except (ValueError, IndexError):
            o_peso = 0.0
        o_op = origen_row[5].strip() if len(origen_row) > 5 else ""
        o_ts_raw = origen_row[6].strip() if len(origen_row) > 6 else ""
        o_lote = origen_row[7].strip() if len(origen_row) > 7 else ""

        # Si origen no tenía timestamp u operador, tomar del primer resultante
        if not o_ts_raw and resultantes and len(resultantes[0]) > 6:
            o_ts_raw = resultantes[0][6].strip()
        if not o_op and resultantes and len(resultantes[0]) > 5:
            o_op = resultantes[0][5].strip()

        o_ts = formatear_marca_temporal(o_ts_raw)
        if not o_cod:
            o_cod = proc.obtener_codigo(o_corte)

        # 1. Registrar Egreso (Corte Madre)
        filas_sheets.append([
            o_ts,
            "Egreso",
            o_corte,
            o_cod,
            f"{o_peso:.2f}",
            o_op,
            o_lote,
            ""
        ])

        # 2. Registrar Ingresos y Decomisos agrupados
        # [tipo, codigo, descripcion, peso, cantidad, operador, timestamp, lote_destino, motivo]
        sumatoria = {}
        for res in resultantes:
            t_reg = res[0].strip().upper()
            es_dec = (t_reg == 'DECOMISO')
            desc = res[2].strip() if len(res) > 2 else "Corte"
            try:
                p_val = float(res[3].strip().replace(',', '.'))
            except (ValueError, IndexError):
                p_val = 0.0
            r_op = res[5].strip() if len(res) > 5 and res[5].strip() else o_op
            r_ts = formatear_marca_temporal(res[6].strip() if len(res) > 6 and res[6].strip() else o_ts_raw)
            motivo_dec = res[8].strip() if len(res) > 8 else ""

            clave = (desc, motivo_dec, es_dec, r_op, r_ts)
            sumatoria[clave] = sumatoria.get(clave, 0.0) + p_val

        for (desc, motivo_dec, es_dec, r_op, r_ts), p_total in sumatoria.items():
            movimiento = "Decomiso" if es_dec else "Ingreso"
            cod_res = proc.obtener_codigo(desc)
            if str(desc).strip().upper() == "TOCINO":
                lote_destino = "00049"
            else:
                lote_destino = generar_lote_resultante(o_lote)

            filas_sheets.append([
                r_ts,
                movimiento,
                desc,
                cod_res,
                f"{p_total:.2f}",
                r_op,
                lote_destino,
                motivo_dec
            ])

        resumen["lote"] = o_lote
        resumen["operador"] = o_op
        resumen["timestamp"] = o_ts
        resumen["descripcion_principal"] = f"{o_corte} ({o_peso:.2f} kg)"
        resumen["peso_total"] = o_peso

    resumen["filas_a_enviar"] = len(filas_sheets)
    resumen["detalle_filas"] = filas_sheets
    return resumen


def enviar_filas_a_google_sheets(
    local_destino: str,
    filas: List[List[Any]],
    creds_path: str,
    callback_log=None
) -> Tuple[bool, str]:
    """Envía un lote de filas a la pestaña de Google Sheets del local indicado."""
    if not GSPREAD_DISPONIBLE:
        return False, "Las librerías 'gspread' u 'oauth2client' no están instaladas en Python."

    if not os.path.exists(creds_path):
        return False, f"Archivo de credenciales no encontrado: {creds_path}"

    try:
        if callback_log:
            callback_log(f"Autenticando con Google Sheets ({os.path.basename(creds_path)})...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Buscar pestaña del local de forma insensible a mayúsculas
        ws_local = None
        for ws in spreadsheet.worksheets():
            if ws.title.strip().upper() == local_destino.strip().upper():
                ws_local = ws
                break

        if not ws_local:
            if callback_log:
                callback_log(f"Creando nueva pestaña para '{local_destino}'...")
            ws_local = spreadsheet.add_worksheet(title=local_destino, rows="1000", cols="10")
            headers = ['Marca Temporal', 'Proceso', 'Corte', 'Codigo', 'Peso', 'Operario', 'Lote', 'Motivo D']
            ws_local.append_row(headers)

        if callback_log:
            callback_log(f"Insertando {len(filas)} filas en la hoja '{ws_local.title}'...")

        ws_local.append_rows(filas)
        return True, f"Se enviaron con éxito {len(filas)} filas a '{ws_local.title}'."
    except Exception as e:
        return False, f"Error al enviar a Sheets: {e}"


# =============================================================================
# INTERFAZ GRÁFICA (GUI)
# =============================================================================
class AppRecuperadorCSV(ctk.CTk if CTK_DISPONIBLE else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SPI - Recuperador y Reenvío de CSVs a Google Sheets")
        self.geometry("980x720")
        self.minsize(850, 600)

        if CTK_DISPONIBLE:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")

        self.creds_path = buscar_credenciales()
        self.dir_defecto = buscar_directorio_csv()
        self.archivos_cargados = []  # Lista de resúmenes de parseo

        self.construir_ui()
        self.verificar_credenciales_inicio()

    def construir_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10) if CTK_DISPONIBLE else tk.Frame(self, bg="#1E293B")
        header.pack(fill="x", padx=15, pady=(15, 10))

        lbl_t = ctk.CTkLabel(
            header,
            text="📤 Reenvío de CSVs a Google Sheets",
            font=ctk.CTkFont(size=22, weight="bold") if CTK_DISPONIBLE else ("Arial", 16, "bold"),
            text_color="#38BDF8" if CTK_DISPONIBLE else "white"
        )
        lbl_t.pack(anchor="w", padx=15, pady=(10, 2))

        lbl_desc = ctk.CTkLabel(
            header,
            text="Seleccione los archivos CSV que no llegaron a destino y reenvíelos a la hoja del local correspondiente.",
            font=ctk.CTkFont(size=12) if CTK_DISPONIBLE else ("Arial", 10),
            text_color="#94A3B8"
        )
        lbl_desc.pack(anchor="w", padx=15, pady=(0, 10))

        # 2. Configuración de Destino (Local) y Credenciales
        cfg_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10) if CTK_DISPONIBLE else tk.Frame(self, bg="#1E293B")
        cfg_frame.pack(fill="x", padx=15, pady=5)

        row_cfg = ctk.CTkFrame(cfg_frame, fg_color="transparent") if CTK_DISPONIBLE else tk.Frame(cfg_frame)
        row_cfg.pack(fill="x", padx=15, pady=10)

        lbl_loc = ctk.CTkLabel(row_cfg, text="Destino (Local):", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_loc.pack(side="left", padx=(0, 10))

        local_predeterminado = load_local_config() if load_local_config() in LOCALES_DISPONIBLES else LOCALES_DISPONIBLES[0]
        self.combo_local = ctk.CTkComboBox(
            row_cfg,
            values=LOCALES_DISPONIBLES,
            width=200,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="readonly"
        ) if CTK_DISPONIBLE else ttk.Combobox(row_cfg, values=LOCALES_DISPONIBLES, state="readonly")
        self.combo_local.set(local_predeterminado)
        self.combo_local.pack(side="left", padx=(0, 20))

        self.lbl_creds_status = ctk.CTkLabel(
            row_cfg,
            text="Verificando credenciales...",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_creds_status.pack(side="left", padx=10)

        # 3. Botonera de Selección de Archivos
        btn_bar = ctk.CTkFrame(self, fg_color="transparent") if CTK_DISPONIBLE else tk.Frame(self)
        btn_bar.pack(fill="x", padx=15, pady=5)

        btn_sel_archivos = ctk.CTkButton(
            btn_bar,
            text="📄 SELECCIONAR CSVs ESPECÍFICOS",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            command=self.seleccionar_archivos_dialog
        )
        btn_sel_archivos.pack(side="left", padx=(0, 10))

        btn_sel_carpeta = ctk.CTkButton(
            btn_bar,
            text="📁 CARGAR CARPETA SPI-DESPIECE",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            height=38,
            command=self.cargar_desde_carpeta_default
        )
        btn_sel_carpeta.pack(side="left", padx=(0, 10))

        btn_limpiar = ctk.CTkButton(
            btn_bar,
            text="🧹 LIMPIAR LISTA",
            font=ctk.CTkFont(size=12),
            fg_color="#475569",
            hover_color="#334155",
            width=110,
            height=38,
            command=self.limpiar_lista
        )
        btn_limpiar.pack(side="right")

        # 4. Tabla de Archivos (Treeview)
        frame_tree = ctk.CTkFrame(self, fg_color="transparent") if CTK_DISPONIBLE else tk.Frame(self)
        frame_tree.pack(fill="both", expand=True, padx=15, pady=5)

        cols = ("archivo", "tipo", "descripcion", "lote", "operador", "fecha", "filas", "estado")
        self.tree = ttk.Treeview(frame_tree, columns=cols, show="headings", height=8)
        self.tree.heading("archivo", text="ARCHIVO")
        self.tree.heading("tipo", text="TIPO")
        self.tree.heading("descripcion", text="DESCRIPCIÓN")
        self.tree.heading("lote", text="LOTE")
        self.tree.heading("operador", text="OPERADOR")
        self.tree.heading("fecha", text="FECHA/HORA")
        self.tree.heading("filas", text="FILAS")
        self.tree.heading("estado", text="ESTADO")

        self.tree.column("archivo", width=140)
        self.tree.column("tipo", width=90, anchor="center")
        self.tree.column("descripcion", width=180)
        self.tree.column("lote", width=100, anchor="center")
        self.tree.column("operador", width=120)
        self.tree.column("fecha", width=140, anchor="center")
        self.tree.column("filas", width=60, anchor="center")
        self.tree.column("estado", width=130, anchor="center")

        scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 5. Botón de Envío y Consola de Log
        bottom_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10) if CTK_DISPONIBLE else tk.Frame(self, bg="#1E293B")
        bottom_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        row_send = ctk.CTkFrame(bottom_frame, fg_color="transparent") if CTK_DISPONIBLE else tk.Frame(bottom_frame)
        row_send.pack(fill="x", padx=15, pady=10)

        self.btn_enviar = ctk.CTkButton(
            row_send,
            text="🚀 ENVIAR ARCHIVOS A GOOGLE SHEETS",
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=46,
            command=self.iniciar_envio_hilo
        )
        self.btn_enviar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.lbl_resumen_envio = ctk.CTkLabel(
            row_send,
            text="0 archivos seleccionados",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_resumen_envio.pack(side="right")

        # Consola de texto en tiempo real
        self.txt_log = ctk.CTkTextbox(
            bottom_frame,
            height=120,
            font=("Consolas", 12),
            fg_color="#0F172A",
            text_color="#E2E8F0"
        ) if CTK_DISPONIBLE else tk.Text(bottom_frame, height=6, bg="#0F172A", fg="#E2E8F0", font=("Consolas", 10))
        self.txt_log.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def log(self, mensaje: str):
        if CTK_DISPONIBLE:
            self.txt_log.insert("end", mensaje + "\n")
            self.txt_log.see("end")
        else:
            self.txt_log.insert(tk.END, mensaje + "\n")
            self.txt_log.see(tk.END)

    def verificar_credenciales_inicio(self):
        if not self.creds_path:
            self.lbl_creds_status.configure(text="❌ credentials.json NO encontrado.", text_color="#EF4444")
            self.log("⚠️ No se encontró 'credentials.json'. Colóquelo en la misma carpeta del script.")
        else:
            self.lbl_creds_status.configure(
                text=f"✅ Credenciales OK ({os.path.basename(self.creds_path)})",
                text_color="#10B981"
            )
            self.log(f"Credenciales detectadas en: {self.creds_path}")

    def seleccionar_archivos_dialog(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar archivos CSV para sincronizar",
            initialdir=self.dir_defecto if os.path.exists(self.dir_defecto) else os.getcwd(),
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if rutas:
            self.agregar_archivos(list(rutas))

    def cargar_desde_carpeta_default(self):
        if not os.path.exists(self.dir_defecto):
            # Preguntar al usuario por la carpeta
            carpeta = filedialog.askdirectory(title="Seleccionar carpeta con archivos CSV de SPI")
            if not carpeta:
                return
            self.dir_defecto = carpeta

        csvs = [os.path.join(self.dir_defecto, f) for f in os.listdir(self.dir_defecto) if f.lower().endswith(".csv")]
        if not csvs:
            messagebox.showinfo("Sin archivos", f"No se encontraron archivos .csv en:\n{self.dir_defecto}")
            return

        # Ordenar por fecha de modificación más reciente
        csvs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        self.agregar_archivos(csvs)

    def agregar_archivos(self, lista_rutas: List[str]):
        rutas_existentes = {a["ruta"] for a in self.archivos_cargados}
        nuevos = 0

        for ruta in lista_rutas:
            if ruta in rutas_existentes:
                continue
            try:
                parsed = parsear_csv(ruta)
                parsed["item_id"] = len(self.archivos_cargados)
                self.archivos_cargados.append(parsed)
                rutas_existentes.add(ruta)

                icono_tipo = "📦 Combo" if parsed["tipo"] == "COMBO" else "🥩 Despiece"
                self.tree.insert("", "end", iid=str(parsed["item_id"]), values=(
                    parsed["archivo"],
                    icono_tipo,
                    parsed["descripcion_principal"],
                    parsed["lote"],
                    parsed["operador"],
                    parsed["timestamp"],
                    parsed["filas_a_enviar"],
                    "⏳ Pendiente"
                ))
                nuevos += 1
            except Exception as e:
                self.log(f"⚠️ Error al leer {os.path.basename(ruta)}: {e}")

        total_filas = sum(a["filas_a_enviar"] for a in self.archivos_cargados)
        self.lbl_resumen_envio.configure(text=f"{len(self.archivos_cargados)} archivos ({total_filas} filas)")
        self.log(f"Se cargaron {nuevos} archivos nuevos para procesar.")

    def limpiar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.archivos_cargados.clear()
        self.lbl_resumen_envio.configure(text="0 archivos seleccionados")
        self.log("Lista de archivos reiniciada.")

    def iniciar_envio_hilo(self):
        if not self.archivos_cargados:
            messagebox.showwarning("Aviso", "No hay ningún archivo CSV cargado en la lista.")
            return

        if not self.creds_path:
            messagebox.showerror("Error", "No se encontró el archivo de credenciales 'credentials.json'.")
            return

        local = self.combo_local.get().strip()
        if not local:
            messagebox.showwarning("Aviso", "Seleccione el Local de destino.")
            return

        confirma = messagebox.askyesno(
            "Confirmar Envío",
            f"¿Desea enviar {len(self.archivos_cargados)} archivos a la pestaña '{local}' de Google Sheets?\n\n"
            f"Total de registros a insertar: {sum(a['filas_a_enviar'] for a in self.archivos_cargados)}"
        )
        if not confirma:
            return

        self.btn_enviar.configure(state="disabled")
        threading.Thread(target=self.proceso_envio_worker, args=(local,), daemon=True).start()

    def proceso_envio_worker(self, local_destino: str):
        self.log(f"\n==========================================")
        self.log(f"🚀 INICIANDO ENVÍO A HOJA '{local_destino}'")
        self.log(f"==========================================")

        exitos = 0
        fallos = 0

        for item in self.archivos_cargados:
            item_id = str(item["item_id"])
            archivo = item["archivo"]
            filas = item["detalle_filas"]

            self.tree.set(item_id, "estado", "🔄 Enviando...")
            self.log(f"• Procesando {archivo} ({item['tipo']} | Lote: {item['lote']})...")

            ok, msj = enviar_filas_a_google_sheets(
                local_destino=local_destino,
                filas=filas,
                creds_path=self.creds_path,
                callback_log=self.log
            )

            if ok:
                exitos += 1
                self.tree.set(item_id, "estado", "✅ Enviado OK")
                self.log(f"  -> {archivo}: {msj}")
            else:
                fallos += 1
                self.tree.set(item_id, "estado", "❌ Error")
                self.log(f"  -> {archivo} FALLÓ: {msj}")

        self.btn_enviar.configure(state="normal")
        self.log(f"\n🏁 FINALIZADO: {exitos} archivos enviados exitosamente. {fallos} fallos.")

        if fallos == 0:
            messagebox.showinfo(
                "Sincronización Completa",
                f"¡Todos los archivos ({exitos}) se enviaron con éxito a la hoja '{local_destino}' en Google Sheets!"
            )
        else:
            messagebox.showwarning(
                "Finalizado con Alertas",
                f"Se enviaron {exitos} archivos pero {fallos} tuvieron errores. Revise la consola inferior para detalles."
            )


# =============================================================================
# MODO LÍNEA DE COMANDOS (CLI)
# =============================================================================
def ejecutar_cli(args):
    print("==================================================")
    print(" SPI - Reenvío de CSVs a Google Sheets (Modo CLI)")
    print("==================================================")

    creds = buscar_credenciales()
    if not creds:
        print("❌ Error: No se encontró 'credentials.json'.")
        sys.exit(1)

    local = args.local.strip() if args.local else load_local_config()
    archivos = []

    if args.archivos:
        for a in args.archivos:
            if os.path.isfile(a):
                archivos.append(a)
    elif args.dir:
        if os.path.isdir(args.dir):
            archivos = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if f.lower().endswith(".csv")]
    elif args.auto:
        d = buscar_directorio_csv()
        if os.path.isdir(d):
            archivos = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".csv")]
            archivos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            archivos = archivos[:args.limite] if args.limite else archivos

    if not archivos:
        print("⚠️ No se encontraron archivos CSV para procesar.")
        sys.exit(0)

    print(f"Destino: Hoja '{local}'")
    print(f"Archivos encontrados: {len(archivos)}\n")

    for f in archivos:
        try:
            parsed = parsear_csv(f)
            print(f"• Enviando {parsed['archivo']} ({parsed['tipo']} | Lote: {parsed['lote']}) -> {parsed['filas_a_enviar']} filas...")
            ok, msj = enviar_filas_a_google_sheets(local, parsed["detalle_filas"], creds, callback_log=print)
            if ok:
                print(f"  ✅ OK: {msj}")
            else:
                print(f"  ❌ Error: {msj}")
        except Exception as e:
            print(f"  ❌ Error al parsear {os.path.basename(f)}: {e}")

    print("\nProceso finalizado.")


def main():
    parser = argparse.ArgumentParser(description="Recuperador y reenvío de CSVs de SPI a Google Sheets.")
    parser.add_argument("archivos", nargs="*", help="Rutas de archivos CSV a procesar.")
    parser.add_argument("--local", default="", help="Local de destino (LOCAL 1, LOCAL 2, LOCAL 3, LOCAL PRUEBAS).")
    parser.add_argument("--dir", default="", help="Directorio con archivos CSV.")
    parser.add_argument("--auto", action="store_true", help="Procesa automáticamente los CSVs de la carpeta predeterminada.")
    parser.add_argument("--limite", type=int, default=10, help="Límite de archivos recientes a procesar con --auto.")
    parser.add_argument("--gui", action="store_true", help="Fuerza abrir la interfaz gráfica.")

    args = parser.parse_args()

    # Si se pasan parámetros de CLI (archivos, --auto o --dir) y no se forzó --gui, correr en CLI
    if (args.archivos or args.dir or args.auto) and not args.gui:
        ejecutar_cli(args)
    else:
        app = AppRecuperadorCSV()
        app.mainloop()


if __name__ == '__main__':
    main()

"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - PANEL MAESTRO DE CONTROL
=============================================================================
Interfaz gráfica unificada para lanzamiento, supervisión y acceso rápido
a todos los subsistemas del proyecto SPI:
  1. SPI Despiece (Horizontal y Vertical con Combos y Balanza)
  2. Servidor Central & Control de Stock (FastAPI + Web App)
  3. SPI Cachorras (Gestión de Granja y Genética Porcina)
  4. Terminales Industriales (Frigorífico Faena y Fábrica Chacinados)
  5. Diagnóstico de Hardware y Herramientas de Mantenimiento
=============================================================================
"""

import os
import sys
import subprocess
import webbrowser
import threading
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image

# Configuración visual global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1YYjZD_0lUIljt4fSCAgYF_hkYT3cyN4NRAXKUTulQwY/edit"
STOCK_WEB_URL = "http://localhost:8000"

# Paleta de Colores Industrial Dark
C_BG = "#0B0F19"
C_PANEL = "#111827"
C_CARD = "#1E293B"
C_CARD_HOVER = "#243248"
C_BORDER = "#334155"
C_TEXT = "#F8FAFC"
C_TEXT_MUTED = "#94A3B8"
C_PRIMARY = "#2563EB"
C_PRIMARY_HOVER = "#1D4ED8"
C_SUCCESS = "#10B981"
C_SUCCESS_HOVER = "#059669"
C_WARNING = "#F59E0B"
C_WARNING_HOVER = "#D97706"
C_PURPLE = "#8B5CF6"
C_PURPLE_HOVER = "#7C3AED"
C_CYAN = "#06B6D4"
C_CYAN_HOVER = "#0891B2"
C_DANGER = "#EF4444"

class PanelControlSPI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SPI - Panel Maestro de Control & Lanzamiento")
        self.geometry("1120x760")
        self.minsize(980, 680)
        self.configure(fg_color=C_BG)

        # Icono si existe
        icon_path = os.path.join(BASE_DIR, "SPI_HD.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self._active_processes = []
        self._setup_ui()
        self._check_system_health()

    def _setup_ui(self):
        # -------------------------------------------------------------
        # 1. ENCABEZADO PRINCIPAL (HEADER)
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=0, height=80)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        # Contenedor para logo y textos
        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=25, pady=10)

        # Logo si existe
        logo_path = os.path.join(BASE_DIR, "Logo cerdos MINI.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                logo_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
                lbl_logo = ctk.CTkLabel(header_inner, image=logo_ctk, text="")
                lbl_logo.pack(side="left", padx=(0, 15))
            except Exception:
                pass

        # Textos de título
        title_box = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_box.pack(side="left", fill="y", justify="center")

        lbl_title = ctk.CTkLabel(
            title_box,
            text="SISTEMA DE PRODUCCIÓN INTEGRAL (SPI)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=C_TEXT
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="Panel Maestro de Módulos, Despiece, Control de Stock y Faena",
            font=ctk.CTkFont(size=12),
            text_color=C_TEXT_MUTED
        )
        lbl_sub.pack(anchor="w")

        # Botón para abrir Documentación / Mapa
        btn_mapa = ctk.CTkButton(
            header_inner,
            text="📖 Mapa del Sistema",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C_CARD,
            hover_color=C_BORDER,
            text_color=C_TEXT,
            width=150,
            height=36,
            command=self._abrir_mapa_sistema
        )
        btn_mapa.pack(side="right", padx=5)

        btn_sheets = ctk.CTkButton(
            header_inner,
            text="📊 Google Sheets",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0F9D58",
            hover_color="#0B8043",
            text_color=C_TEXT,
            width=140,
            height=36,
            command=lambda: webbrowser.open(SHEETS_URL)
        )
        btn_sheets.pack(side="right", padx=5)

        # -------------------------------------------------------------
        # 2. CONTENIDO PRINCIPAL SCROLLABLE CON TARJETAS
        # -------------------------------------------------------------
        self.scroll_content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_content.pack(fill="both", expand=True, padx=25, pady=15)

        # Configurar 2 columnas
        self.scroll_content.grid_columnconfigure(0, weight=1, uniform="col")
        self.scroll_content.grid_columnconfigure(1, weight=1, uniform="col")

        # Tarjeta 1: SPI Despiece
        self._crear_tarjeta_despiece(row=0, col=0)

        # Tarjeta 2: Servidor Central & Stock
        self._crear_tarjeta_servidor_stock(row=0, col=1)

        # Tarjeta 3: SPI Cachorras (Granja)
        self._crear_tarjeta_cachorras(row=1, col=0)

        # Tarjeta 4: Terminales Industriales (Frigorífico & Fábrica)
        self._crear_tarjeta_industrial(row=1, col=1)

        # Sección inferior: Herramientas, Diagnóstico y Carpetas
        self._crear_seccion_herramientas()

        # -------------------------------------------------------------
        # 3. BARRA DE ESTADO INFERIOR
        # -------------------------------------------------------------
        status_bar = ctk.CTkFrame(self, fg_color=C_PANEL, height=32, corner_radius=0)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            status_bar,
            text="Listo. Seleccione un módulo para iniciar.",
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_MUTED
        )
        self.lbl_status.pack(side="left", padx=20)

        self.lbl_health = ctk.CTkLabel(
            status_bar,
            text="Verificando integridad...",
            font=ctk.CTkFont(size=11),
            text_color=C_SUCCESS
        )
        self.lbl_health.pack(side="right", padx=20)

    # -----------------------------------------------------------------
    # TARJETAS DE SUBSISTEMAS
    # -----------------------------------------------------------------
    def _crear_tarjeta_despiece(self, row, col):
        card = ctk.CTkFrame(self.scroll_content, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Título y Badge
        top_box = ctk.CTkFrame(card, fg_color="transparent")
        top_box.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top_box,
            text="🥩 SPI Despiece (Planta Principal)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C_TEXT
        ).pack(side="left")

        badge = ctk.CTkLabel(
            top_box,
            text="PRODUCCIÓN",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#1E3A8A",
            text_color="#93C5FD",
            corner_radius=6,
            padx=8,
            pady=2
        )
        badge.pack(side="right")

        desc = (
            "Transformación de cortes primarios y secundarios, balanza digital Systel, "
            "gestión de bandejas de COMBOS con validación estricta de tolerancias y "
            "sincronización automática a Google Sheets."
        )
        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_MUTED,
            justify="left",
            wraplength=460
        ).pack(fill="x", padx=16, pady=(0, 14))

        # Botones de Acción
        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        btn_horiz = ctk.CTkButton(
            btn_box,
            text="▶ Despiece Horizontal (Recomendado)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C_PRIMARY,
            hover_color=C_PRIMARY_HOVER,
            height=38,
            command=lambda: self._lanzar_script("main_horizontal.py", "SPI Despiece Horizontal")
        )
        btn_horiz.pack(fill="x", pady=4)

        btn_vert = ctk.CTkButton(
            btn_box,
            text="▶ Despiece Vertical",
            font=ctk.CTkFont(size=12),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=32,
            command=lambda: self._lanzar_script("main.py", "SPI Despiece Vertical")
        )
        btn_vert.pack(fill="x", pady=4)

    def _crear_tarjeta_servidor_stock(self, row, col):
        card = ctk.CTkFrame(self.scroll_content, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        top_box = ctk.CTkFrame(card, fg_color="transparent")
        top_box.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top_box,
            text="🌐 Servidor Central & Stock Web",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C_TEXT
        ).pack(side="left")

        badge = ctk.CTkLabel(
            top_box,
            text="API / WEB",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#064E3B",
            text_color="#6EE7B7",
            corner_radius=6,
            padx=8,
            pady=2
        )
        badge.pack(side="right")

        desc = (
            "Servidor backend FastAPI (REST API y WebSockets) junto con la Web App "
            "React/Vite para consulta de existencias, recepción de pesajes, control de stock "
            "en tiempo real y sincronización en la nube."
        )
        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_MUTED,
            justify="left",
            wraplength=460
        ).pack(fill="x", padx=16, pady=(0, 14))

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        btn_server = ctk.CTkButton(
            btn_box,
            text="▶ Iniciar Servidor FastAPI & Web App",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C_SUCCESS,
            hover_color=C_SUCCESS_HOVER,
            height=38,
            command=self._iniciar_servidor_y_navegador
        )
        btn_server.pack(fill="x", pady=4)

        btn_web = ctk.CTkButton(
            btn_box,
            text="🌐 Abrir Panel Web en Navegador (Port 8000)",
            font=ctk.CTkFont(size=12),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=32,
            command=lambda: webbrowser.open(STOCK_WEB_URL)
        )
        btn_web.pack(fill="x", pady=4)

    def _crear_tarjeta_cachorras(self, row, col):
        card = ctk.CTkFrame(self.scroll_content, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        top_box = ctk.CTkFrame(card, fg_color="transparent")
        top_box.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top_box,
            text="🐖 SPI Cachorras (Granja Porcina)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C_TEXT
        ).pack(side="left")

        badge = ctk.CTkLabel(
            top_box,
            text="GRANJA",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#78350F",
            text_color="#FDE68A",
            corner_radius=6,
            padx=8,
            pady=2
        )
        badge.pack(side="right")

        desc = (
            "Gestión integral del ciclo productivo en granja: control de cachorras, "
            "trazabilidad genética, servicio/inseminación, control de preñez, partos y "
            "destetes con base de datos SQLite integrada."
        )
        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_MUTED,
            justify="left",
            wraplength=460
        ).pack(fill="x", padx=16, pady=(0, 14))

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        cachorras_dir = os.path.join(BASE_DIR, "SPI - Cachorras")
        btn_cach = ctk.CTkButton(
            btn_box,
            text="▶ Iniciar SPI Cachorras (Desktop)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C_WARNING,
            hover_color=C_WARNING_HOVER,
            height=38,
            command=lambda: self._lanzar_script("main.py", "SPI Cachorras", cwd=cachorras_dir)
        )
        btn_cach.pack(fill="x", pady=4)

        movil_dir = os.path.join(BASE_DIR, "SPI Cachorras Movil")
        btn_movil = ctk.CTkButton(
            btn_box,
            text="📱 Explorar Código App Móvil Android",
            font=ctk.CTkFont(size=12),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=32,
            command=lambda: self._abrir_carpeta(movil_dir)
        )
        btn_movil.pack(fill="x", pady=4)

    def _crear_tarjeta_industrial(self, row, col):
        card = ctk.CTkFrame(self.scroll_content, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        top_box = ctk.CTkFrame(card, fg_color="transparent")
        top_box.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            top_box,
            text="🏭 SPI New (Frigorífico & Fábrica)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=C_TEXT
        ).pack(side="left")

        badge = ctk.CTkLabel(
            top_box,
            text="EDGE INDUSTRIAL",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#581C87",
            text_color="#E9D5FF",
            corner_radius=6,
            padx=8,
            pady=2
        )
        badge.pack(side="right")

        desc = (
            "Terminales táctiles industriales para planta: Faena con pesaje al gancho "
            "aéreo + impresión Zebra ZPL, y Fábrica para pesaje de batea con semáforo "
            "térmico de masa (< 4°C) y gestión de lotes fijos."
        )
        ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=C_TEXT_MUTED,
            justify="left",
            wraplength=460
        ).pack(fill="x", padx=16, pady=(0, 14))

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 16))

        edge_dir = os.path.join(BASE_DIR, "SPI NEW", "Frigorifico-Fabrica", "python_edge")
        btn_frig = ctk.CTkButton(
            btn_box,
            text="▶ Terminal Frigorífico (Gancho Faena)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C_PURPLE,
            hover_color=C_PURPLE_HOVER,
            height=38,
            command=lambda: self._lanzar_script("terminal_frigorifico.py", "Terminal Frigorífico", cwd=edge_dir)
        )
        btn_frig.pack(fill="x", pady=4)

        btn_fab = ctk.CTkButton(
            btn_box,
            text="▶ Terminal Fábrica (Batea Chacinados)",
            font=ctk.CTkFont(size=12),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=32,
            command=lambda: self._lanzar_script("terminal_fabrica.py", "Terminal Fábrica", cwd=edge_dir)
        )
        btn_fab.pack(fill="x", pady=4)

    # -----------------------------------------------------------------
    # SECCIÓN DE HERRAMIENTAS Y UTILIDADES
    # -----------------------------------------------------------------
    def _crear_seccion_herramientas(self):
        tools_card = ctk.CTkFrame(self.scroll_content, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        tools_card.grid(row=2, column=0, columnspan=2, padx=10, pady=(15, 10), sticky="nsew")

        lbl_tools = ctk.CTkLabel(
            tools_card,
            text="🛠️ Herramientas de Mantenimiento, Diagnóstico y Carpetas del Sistema",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=C_TEXT
        )
        lbl_tools.pack(anchor="w", padx=16, pady=(12, 10))

        bar = ctk.CTkFrame(tools_card, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 14))

        btn_balanza = ctk.CTkButton(
            bar,
            text="⚖️ Diagnóstico Balanza",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C_CYAN,
            hover_color=C_CYAN_HOVER,
            text_color="#0F172A",
            height=34,
            command=lambda: self._lanzar_script("test_serial_gui.py", "Diagnóstico de Balanza")
        )
        btn_balanza.pack(side="left", padx=4, expand=True, fill="x")

        btn_tests = ctk.CTkButton(
            bar,
            text="🧪 Suite de Tests",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            height=34,
            command=self._ejecutar_tests_dialog
        )
        btn_tests.pack(side="left", padx=4, expand=True, fill="x")

        btn_informes = ctk.CTkButton(
            bar,
            text="📁 Informes & Hardware",
            font=ctk.CTkFont(size=11),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=34,
            command=lambda: self._abrir_carpeta(os.path.join(BASE_DIR, "Informes"))
        )
        btn_informes.pack(side="left", padx=4, expand=True, fill="x")

        btn_csvs = ctk.CTkButton(
            bar,
            text="📂 CSVs Históricos",
            font=ctk.CTkFont(size=11),
            fg_color=C_BORDER,
            hover_color=C_CARD_HOVER,
            height=34,
            command=lambda: self._abrir_carpeta(os.path.join(BASE_DIR, "Muestras_CSVs_Historicos"))
        )
        btn_csvs.pack(side="left", padx=4, expand=True, fill="x")

    # -----------------------------------------------------------------
    # CONTROLADORES Y LANZADORES
    # -----------------------------------------------------------------
    def _lanzar_script(self, script_name, display_name, cwd=None):
        target_dir = cwd if cwd else BASE_DIR
        script_full_path = os.path.join(target_dir, script_name)

        if not os.path.exists(script_full_path):
            messagebox.showerror("Archivo No Encontrado", f"No se encontró el script:\n{script_full_path}")
            return

        try:
            self._set_status(f"Iniciando {display_name}...")
            # Popen independiente para no congelar la GUI
            proc = subprocess.Popen([sys.executable, script_name], cwd=target_dir)
            self._active_processes.append(proc)
            self._set_status(f"{display_name} en ejecución (PID: {proc.pid})")
        except Exception as e:
            messagebox.showerror("Error de Lanzamiento", f"Error al iniciar {display_name}:\n{str(e)}")
            self._set_status(f"Error al iniciar {display_name}")

    def _iniciar_servidor_y_navegador(self):
        self._lanzar_script("server.py", "Servidor Central FastAPI")
        # Abrir navegador luego de 2 segundos en un hilo
        def abrir_web():
            import time
            time.sleep(1.8)
            webbrowser.open(STOCK_WEB_URL)
        threading.Thread(target=abrir_web, daemon=True).start()

    def _ejecutar_tests_dialog(self):
        self._set_status("Ejecutando Suite de Tests...")
        def correr():
            try:
                res = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "tests", "-v"],
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True
                )
                salida = res.stderr if res.stderr else res.stdout
                if res.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo("Tests Aprobados", f"¡Todos los tests pasaron exitosamente!\n\n{salida[:500]}..."))
                    self.after(0, lambda: self._set_status("Tests completados: 100% OK"))
                else:
                    self.after(0, lambda: messagebox.showwarning("Fallos en Tests", f"Hubo tests fallidos:\n\n{salida}"))
                    self.after(0, lambda: self._set_status("Tests completados con advertencias"))
            except Exception as ex:
                self.after(0, lambda: messagebox.showerror("Error", f"Error al correr tests: {str(ex)}"))
                self.after(0, lambda: self._set_status("Error en ejecución de tests"))
        threading.Thread(target=correr, daemon=True).start()

    def _abrir_carpeta(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                pass
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
            self._set_status(f"Carpeta abierta: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{path}\n\nDetalle: {str(e)}")

    def _abrir_mapa_sistema(self):
        mapa_path = os.path.join(BASE_DIR, "MAPA_DEL_SISTEMA.md")
        if os.path.exists(mapa_path):
            try:
                os.startfile(mapa_path)
                self._set_status("Abriendo MAPA_DEL_SISTEMA.md")
                return
            except Exception:
                pass
        messagebox.showinfo("Mapa del Sistema", f"El archivo se encuentra en:\n{mapa_path}")

    def _set_status(self, text):
        self.lbl_status.configure(text=text)

    def _check_system_health(self):
        criticos = [
            ("CODIGOS.csv", os.path.join(BASE_DIR, "CODIGOS.csv")),
            ("cortes_madre_y_resultantes.csv", os.path.join(BASE_DIR, "cortes_madre_y_resultantes.csv")),
            ("credentials.json", os.path.join(BASE_DIR, "credentials.json")),
            ("combos_config.py", os.path.join(BASE_DIR, "combos_config.py")),
            ("procesador_datos.py", os.path.join(BASE_DIR, "procesador_datos.py")),
            ("auth_sync.py", os.path.join(BASE_DIR, "auth_sync.py")),
        ]
        faltantes = [nom for nom, path in criticos if not os.path.exists(path)]
        if faltantes:
            self.lbl_health.configure(
                text=f"⚠️ Faltan archivos: {', '.join(faltantes[:2])}",
                text_color=C_WARNING
            )
        else:
            self.lbl_health.configure(
                text="● Archivos Críticos: OK | Entorno Python: Listo",
                text_color=C_SUCCESS
            )

if __name__ == "__main__":
    app = PanelControlSPI()
    app.mainloop()

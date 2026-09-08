"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - TERMINAL TÁCTIL DE FRIGORÍFICO
Módulo de Faena: Pesaje al Gancho Aéreo, Tipificación y Etiquetado ZPL
=============================================================================
Diseñado según especificación 'Visual del programa.md':
- Dark Mode Industrial (#0B0F19, #0F172A, #1E293B)
- Display de balanza gigante (72px monoespaciado) con cambio de color verde (#10B981)
- Botones de gran formato (>= 54px) glove-friendly
- Integración nativa con ScaleDriver (Systel), ZebraPrinter y LocalDatabase (SQLite WAL)
=============================================================================
"""

import sys
import os
import time
import datetime
import customtkinter as ctk

# Asegurar importación de módulos hermanos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware"))

from config_parametros import (
    BALANZA_GANCHO_PORT,
    BALANZA_GANCHO_BAUD,
    BALANZA_GANCHO_PROTOCOL,
    ALTERNANCIA_LADO_AUTOMATICA
)
from hardware.scale_driver import ScaleDriver
from hardware.zebra_printer import ZebraPrinter
from local_db import LocalDatabase
from auth_session import LoginPinModal, SupervisorAuthModal, CargaManualPesoModal, SessionManager, get_current_timestamp_iso

# Configuración visual global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_BG = "#0B0F19"
COLOR_CARD = "#0F172A"
COLOR_CARD_BORDER = "#1E293B"
COLOR_GREEN = "#10B981"
COLOR_YELLOW = "#F59E0B"
COLOR_RED = "#EF4444"
COLOR_BLUE = "#38BDF8"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"


class TerminalFrigorifico(ctk.CTk):
    """Interfaz táctil de faena para puesto de balanza de gancho aéreo."""

    def __init__(self):
        super().__init__()

        self.title("SPI - Terminal de Faena // Balanza de Gancho")
        self.geometry("1280x800")
        self.minsize(1024, 720)
        self.configure(fg_color=COLOR_BG)

        # Servicios de Backend / Hardware
        self.db = LocalDatabase()
        self.printer = ZebraPrinter(mock_mode=True)
        self.scale = ScaleDriver(
            port=BALANZA_GANCHO_PORT,
            baudrate=BALANZA_GANCHO_BAUD,
            protocol=BALANZA_GANCHO_PROTOCOL,
            mock_mode=True  # Inicia en modo Mock para simulación; cambia con hardware real
        )
        self.scale.start()

        # Estado operativo y usuario de sesión
        user = SessionManager.get_current_user()
        self.operario_id = user["id"]
        self.operario_nombre = user["nombre"]
        self.operario_legajo = user["legajo"]
        self.tropa_actual = "TRP-2026-00412"
        self.cabezas_faenadas = 42
        self.cabezas_totales_tropa = 108
        self.lado_actual = "IZQ"
        self.secuencia_media_res = 1
        self.ultima_media_res = None

        # Construir Interfaz de Usuario
        self._build_header()
        self._build_main_layout()
        self._build_footer()

        # Iniciar loop de refresco de balanza (100ms)
        self._poll_scale_data()

        # Manejo de cierre seguro
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -----------------------------------------------------------------------
    # 1. HEADER BAR INDUSTRIAL
    # -----------------------------------------------------------------------
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=64)
        self.header_frame.pack(fill="x", side="top")

        # Título y Sector
        title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="🥩 SPI // FRIGORÍFICO - LÍNEA DE FAENA",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#A5B4FC"
        )
        title_lbl.pack(side="left", padx=20, pady=12)

        # Indicadores de Hardware en Header
        self.status_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.status_container.pack(side="right", padx=20)

        # Badge Balanza
        self.lbl_scale_status = ctk.CTkLabel(
            self.status_container,
            text="⚖️ BALANZA: OK",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_GREEN,
            fg_color="#064E3B",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.lbl_scale_status.pack(side="left", padx=6)

        # Badge Impresora Zebra
        self.lbl_zebra_status = ctk.CTkLabel(
            self.status_container,
            text="🖨️ ZEBRA: LISTA",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_BLUE,
            fg_color="#082F49",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.lbl_zebra_status.pack(side="left", padx=6)

        # Badge Buffer Offline
        self.lbl_buffer_status = ctk.CTkLabel(
            self.status_container,
            text="💾 OFFLINE: 0",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
            fg_color="#1E293B",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.lbl_buffer_status.pack(side="left", padx=6)

        # Botón Operario con Login PIN Modal
        self.btn_operario = ctk.CTkButton(
            self.status_container,
            text=f"👤 {self.operario_nombre} ({self.operario_legajo})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT,
            fg_color="#312E81",
            hover_color="#4338CA",
            corner_radius=6,
            height=30,
            command=self._abrir_login_modal
        )
        self.btn_operario.pack(side="left", padx=6)

    # -----------------------------------------------------------------------
    # 2. CUERPO PRINCIPAL (SPLIT 55% / 45%)
    # -----------------------------------------------------------------------
    def _build_main_layout(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=16, pady=12)

        # Panel Izquierdo: Display de Balanza y Confirmación (55%)
        self.left_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=14)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Panel Derecho: Tropa, Tipificación e Historial (45%)
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=14)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self._build_scale_panel()
        self._build_control_panel()

    # -----------------------------------------------------------------------
    # PANEL IZQUIERDO: DISPLAY DE BALANZA SYSTEL
    # -----------------------------------------------------------------------
    def _build_scale_panel(self):
        # Título de panel
        p_title = ctk.CTkLabel(
            self.left_frame,
            text="LECTURA EN LÍNEA DE GANCHO AÉREO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        p_title.pack(anchor="w", padx=24, pady=(20, 8))

        # Display Digital Gigante (Tarjeta Oscura con borde)
        self.display_card = ctk.CTkFrame(self.left_frame, fg_color="#060911", border_color="#334155", border_width=2, corner_radius=16)
        self.display_card.pack(fill="x", padx=24, pady=10)

        # Texto de Peso Monoespaciado de 72px
        self.lbl_weight = ctk.CTkLabel(
            self.display_card,
            text="0.00",
            font=ctk.CTkFont(family="Consolas", size=84, weight="bold"),
            text_color=COLOR_YELLOW
        )
        self.lbl_weight.pack(pady=(16, 0))

        # Unidad "kg" y Estado de Estabilidad
        unit_box = ctk.CTkFrame(self.display_card, fg_color="transparent")
        unit_box.pack(pady=(0, 16))

        self.lbl_stability = ctk.CTkLabel(
            unit_box,
            text="🟡 INESTABLE (EN MOVIMIENTO)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_YELLOW
        )
        self.lbl_stability.pack(side="left", padx=10)

        lbl_kg = ctk.CTkLabel(
            unit_box,
            text="KILOGRAMOS NETO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_kg.pack(side="left", padx=10)

        # Selector Táctil de Lado (IZQ / DER)
        lado_box = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        lado_box.pack(fill="x", padx=24, pady=10)

        lado_lbl = ctk.CTkLabel(lado_box, text="Lado de Media Res:", font=ctk.CTkFont(size=14, weight="bold"))
        lado_lbl.pack(side="left")

        self.btn_lado_izq = ctk.CTkButton(
            lado_box,
            text="IZQUIERDA (IZQ)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#4338CA" if self.lado_actual == "IZQ" else "#1E293B",
            command=lambda: self._set_lado("IZQ")
        )
        self.btn_lado_izq.pack(side="left", padx=10, expand=True, fill="x")

        self.btn_lado_der = ctk.CTkButton(
            lado_box,
            text="DERECHA (DER)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#4338CA" if self.lado_actual == "DER" else "#1E293B",
            command=lambda: self._set_lado("DER")
        )
        self.btn_lado_der.pack(side="left", padx=10, expand=True, fill="x")

        # BOTÓN GIGANTE DE CONFIRMACIÓN Y DISPARO ZPL (Glove-Friendly >= 54px)
        self.btn_confirmar = ctk.CTkButton(
            self.left_frame,
            text="⚖️ CONFIRMAR PESAJE E IMPRIMIR CANAL",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=68,
            fg_color=COLOR_GREEN,
            hover_color="#059669",
            command=self._confirmar_pesaje
        )
        self.btn_confirmar.pack(fill="x", padx=24, pady=(16, 6))

        # Botón Contingencia Manual (Balanza Rota / Autorización Supervisor)
        self.btn_carga_manual = ctk.CTkButton(
            self.left_frame,
            text="⚠️ CARGA MANUAL (BALANZA DAÑADA / AUTORIZAR)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            fg_color="#854D0E",
            hover_color="#A16207",
            command=self._iniciar_flujo_carga_manual
        )
        self.btn_carga_manual.pack(fill="x", padx=24, pady=(0, 10))

        # Botón Secundario de Decomiso Sanitario
        self.btn_decomiso = ctk.CTkButton(
            self.left_frame,
            text="⚠️ REGISTRAR DECOMISO SANITARIO SENASA",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            fg_color="#7F1D1D",
            hover_color=COLOR_RED,
            command=self._abrir_modal_decomiso
        )
        self.btn_decomiso.pack(fill="x", padx=24, pady=(0, 16))

    # -----------------------------------------------------------------------
    # PANEL DERECHO: DATOS DE TROPA, TIPIFICACIÓN E HISTORIAL
    # -----------------------------------------------------------------------
    def _build_control_panel(self):
        # Tarjeta de Tropa Actual
        tropa_box = ctk.CTkFrame(self.right_frame, fg_color="#1E293B", corner_radius=10)
        tropa_box.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            tropa_box,
            text=f"TROPA ACTIVA: {self.tropa_actual}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        self.lbl_tropa_progreso = ctk.CTkLabel(
            tropa_box,
            text=f"Canales Faenadas: {self.cabezas_faenadas} de {self.cabezas_totales_tropa} animales",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_tropa_progreso.pack(anchor="w", padx=14, pady=(0, 10))

        # Tipificación Rápida de Calidad
        tip_title = ctk.CTkLabel(
            self.right_frame,
            text="TIPIFICACIÓN SANITARIA Y DE CALIDAD",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        tip_title.pack(anchor="w", padx=20, pady=(10, 6))

        tip_grid = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        tip_grid.pack(fill="x", padx=20, pady=4)

        # Campo 1: Grasa Dorsal
        ctk.CTkLabel(tip_grid, text="Grasa Dorsal (mm):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.txt_grasa = ctk.CTkEntry(tip_grid, width=120, height=36, font=ctk.CTkFont(size=14))
        self.txt_grasa.insert(0, "14.2")
        self.txt_grasa.grid(row=0, column=1, sticky="e", padx=(10, 0), pady=4)

        # Campo 2: % Magro Estimado
        ctk.CTkLabel(tip_grid, text="Carne Magra (%):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.txt_magro = ctk.CTkEntry(tip_grid, width=120, height=36, font=ctk.CTkFont(size=14))
        self.txt_magro.insert(0, "58.4")
        self.txt_magro.grid(row=1, column=1, sticky="e", padx=(10, 0), pady=4)

        # Campo 3: pH 45min
        ctk.CTkLabel(tip_grid, text="pH 45 minutos:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", pady=4)
        self.txt_ph = ctk.CTkEntry(tip_grid, width=120, height=36, font=ctk.CTkFont(size=14))
        self.txt_ph.insert(0, "6.20")
        self.txt_ph.grid(row=2, column=1, sticky="e", padx=(10, 0), pady=4)

        # Historial de Últimas Pesadas
        hist_title = ctk.CTkLabel(
            self.right_frame,
            text="HISTORIAL RECIENTE DE LA JORNADA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        hist_title.pack(anchor="w", padx=20, pady=(16, 6))

        self.hist_box = ctk.CTkTextbox(self.right_frame, height=130, font=ctk.CTkFont(family="Consolas", size=12), fg_color="#060911")
        self.hist_box.pack(fill="x", padx=20, pady=4)
        self.hist_box.insert("end", "[10:35:12] MR-DER-00412-41:  42.50 kg | Magro: 58.4% | OK\n")
        self.hist_box.insert("end", "[10:34:40] MR-IZQ-00412-41:  42.20 kg | Magro: 58.0% | OK\n")
        self.hist_box.insert("end", "[10:33:55] MR-DER-00412-40:  44.10 kg | Magro: 57.5% | OK\n")
        self.hist_box.configure(state="disabled")

        # Botón de Re-impresión de Última Etiqueta
        self.btn_reimprimir = ctk.CTkButton(
            self.right_frame,
            text="🔄 Re-imprimir Última Etiqueta Emitida",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._reimprimir_ultima
        )
        self.btn_reimprimir.pack(fill="x", padx=20, pady=(10, 16))

    # -----------------------------------------------------------------------
    # 3. FOOTER
    # -----------------------------------------------------------------------
    def _build_footer(self):
        self.footer_frame = ctk.CTkFrame(self, fg_color="#060911", height=32, corner_radius=0)
        self.footer_frame.pack(fill="x", side="bottom")

        self.lbl_footer_msg = ctk.CTkLabel(
            self.footer_frame,
            text="Sistema Listo. Esperando peso estable en celda de carga de gancho...",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_footer_msg.pack(side="left", padx=20, pady=4)

        lbl_version = ctk.CTkLabel(
            self.footer_frame,
            text="SPI v2.0 Enterprise | Offline-First (SQLite WAL)",
            font=ctk.CTkFont(size=11),
            text_color="#475569"
        )
        lbl_version.pack(side="right", padx=20, pady=4)

    # -----------------------------------------------------------------------
    # LOGICA OPERATIVA Y ENLACE DE HARDWARE
    # -----------------------------------------------------------------------
    def _poll_scale_data(self):
        """Consulta el estado del ScaleDriver cada 100ms."""
        status = self.scale.get_status()
        peso = status["weight_kg"]
        estable = status["is_stable"]

        # Actualizar display de peso
        self.lbl_weight.configure(text=f"{peso:6.2f}")

        if estable and peso > 1.0:
            self.lbl_weight.configure(text_color=COLOR_GREEN)
            self.lbl_stability.configure(text="🟢 PESO ESTABLE", text_color=COLOR_GREEN)
            self.display_card.configure(border_color=COLOR_GREEN)
        elif peso > 1.0:
            self.lbl_weight.configure(text_color=COLOR_YELLOW)
            self.lbl_stability.configure(text="🟡 INESTABLE (OSCILANDO)", text_color=COLOR_YELLOW)
            self.display_card.configure(border_color=COLOR_YELLOW)
        else:
            self.lbl_weight.configure(text_color="#64748B")
            self.lbl_stability.configure(text="⚪ BALANZA EN CERO", text_color="#64748B")
            self.display_card.configure(border_color="#334155")

        # Actualizar estado de buffers en header
        stats = self.db.get_buffer_stats()
        self.lbl_buffer_status.configure(text=f"💾 OFFLINE: {stats['pending_sync_count']}")

        # Re-programar chequeo en 100ms
        self.after(100, self._poll_scale_data)

    def _abrir_login_modal(self):
        def on_logged(user):
            self.operario_id = user["id"]
            self.operario_nombre = user["nombre"]
            self.operario_legajo = user["legajo"]
            self.btn_operario.configure(text=f"👤 {self.operario_nombre} ({self.operario_legajo})")
            self._set_footer_msg(f"✅ Sesión iniciada: {self.operario_nombre} ({user['rol']}) a las {user['login_timestamp']}")
        LoginPinModal(self, on_success_callback=on_logged)

    def _set_lado(self, lado: str):
        self.lado_actual = lado
        self.btn_lado_izq.configure(fg_color="#4338CA" if lado == "IZQ" else "#1E293B")
        self.btn_lado_der.configure(fg_color="#4338CA" if lado == "DER" else "#1E293B")

    def _iniciar_flujo_carga_manual(self):
        """Inicia el protocolo de contingencia por balanza de gancho rota o descalibrada."""
        desc = (
            f"Desbloquear carga manual de peso para la canal actual (Tropa: {self.tropa_actual}, "
            f"Lado: {self.lado_actual}) por falla en balanza Systel."
        )
        SupervisorAuthModal(
            self,
            accion_descripcion=desc,
            on_authorized_callback=self._on_supervisor_manual_autorizado
        )

    def _on_supervisor_manual_autorizado(self, supervisor: Dict[str, Any]):
        """Abre teclado numérico de peso tras validar PIN de Administrador o Supervisor."""
        CargaManualPesoModal(
            self,
            supervisor_autorizante=supervisor,
            on_confirm_callback=self._on_peso_manual_confirmado
        )

    def _on_peso_manual_confirmado(self, peso: float, motivo: str, supervisor: Dict[str, Any]):
        """Ejecuta la captura oficial manual con firma del supervisor autorizante."""
        nom_sup = f"{supervisor['nombre']} ({supervisor['legajo']})"
        self._ejecutar_captura_oficial(
            peso=peso,
            captura_manual=True,
            autorizado_por=nom_sup,
            motivo_contingencia=motivo
        )

    def _confirmar_pesaje(self):
        """Ejecuta la captura oficial desde balanza física."""
        st = self.scale.get_status()
        peso = st["weight_kg"]

        if peso < 1.0:
            self._set_footer_msg("❌ Error: No hay carga sobre el gancho para pesar.", is_error=True)
            return

        self._ejecutar_captura_oficial(peso=peso, captura_manual=False)

    def _ejecutar_captura_oficial(
        self,
        peso: float,
        captura_manual: bool = False,
        autorizado_por: str = "",
        motivo_contingencia: str = ""
    ):
        # Generar código de lote de media res
        ahora = datetime.datetime.now()
        ahora_iso = get_current_timestamp_iso()
        lote_media_res = f"MR-{self.lado_actual}-{self.tropa_actual.replace('TRP-', '')}-{self.cabezas_faenadas:02d}"

        # Obtener tipificación
        try:
            grasa = float(self.txt_grasa.get())
            magro = float(self.txt_magro.get())
            ph = float(self.txt_ph.get())
        except ValueError:
            grasa, magro, ph = 14.0, 58.0, 6.2

        # 1. Guardar en SQLite Local Buffer (Garantía Offline)
        registro = {
            "id_tropa_fk": self.tropa_actual,
            "lado": self.lado_actual,
            "peso_gancho_caliente_kg": peso,
            "espesor_grasa_dorsal_mm": grasa,
            "porcentaje_magro_estimado": magro,
            "ph_45min": ph,
            "lote_media_res": lote_media_res,
            "aprobacion_veterinaria_senasa": True,
            "captura_manual": captura_manual,
            "autorizado_por": autorizado_por,
            "motivo_contingencia": motivo_contingencia,
            "operario_id": self.operario_id,
            "operario_nombre": self.operario_nombre,
            "operario_legajo": self.operario_legajo,
            "timestamp_captura_iso": ahora_iso,
            "timestamp": ahora.isoformat()
        }
        idempotency_key = self.db.save_weight_record("FRIGORIFICO", "MEDIA_RES", registro)

        # 2. Generar e Imprimir Etiqueta ZPL
        zpl = self.printer.build_media_res_zpl(
            lote_media_res=lote_media_res,
            tropa_dte=self.tropa_actual,
            lado=self.lado_actual,
            kilos=peso,
            grasa_mm=grasa,
            magro_pct=magro,
            operario_id=self.operario_id,
            fecha_hora=ahora.strftime("%d/%m/%Y %H:%M"),
            captura_manual=captura_manual,
            autorizado_por=autorizado_por
        )
        res_print = self.printer.send_zpl(zpl)

        # Si falla el envío físico a Zebra, encolar en SQLite
        if not res_print["success"]:
            self.db.enqueue_label("CANAL_100x75", zpl)

        self.ultima_media_res = {"lote": lote_media_res, "zpl": zpl}

        # 3. Actualizar Historial en Pantalla
        tag_man = " [MANUAL]" if captura_manual else ""
        self.hist_box.configure(state="normal")
        self.hist_box.insert("1.0", f"[{ahora.strftime('%H:%M:%S')}] {lote_media_res}: {peso:6.2f} kg{tag_man} | Magro: {magro}% | OK\n")
        self.hist_box.configure(state="disabled")

        # 4. Alternancia Automática de Lado si está activada
        if ALTERNANCIA_LADO_AUTOMATICA:
            nuevo_lado = "DER" if self.lado_actual == "IZQ" else "IZQ"
            self._set_lado(nuevo_lado)
            if nuevo_lado == "IZQ":
                self.cabezas_faenadas += 1
                self.lbl_tropa_progreso.configure(
                    text=f"Canales Faenadas: {self.cabezas_faenadas} de {self.cabezas_totales_tropa} animales"
                )

        if captura_manual:
            self._set_footer_msg(f"⚠️ [MANUAL] Pesaje capturado: {lote_media_res} ({peso:.2f} kg) autorizado por {autorizado_por}.")
        else:
            self._set_footer_msg(f"✅ Pesaje capturado: {lote_media_res} ({peso:.2f} kg) | Etiqueta ZPL emitida.")

    def _abrir_modal_decomiso(self):
        """Modal de decomiso sanitario SENASA."""
        st = self.scale.get_status()
        peso = st["weight_kg"]

        modal = ctk.CTkToplevel(self)
        modal.title("Dictamen Sanitario SENASA - Decomiso")
        modal.geometry("520x400")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal,
            text="🔴 REGISTRO DE DECOMISO SANITARIO",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_RED
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            modal,
            text=f"Tropa: {self.tropa_actual} | Peso: {peso:.2f} kg",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXT_MUTED
        ).pack(pady=4)

        ctk.CTkLabel(modal, text="Motivo del Decomiso:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=30, pady=(10, 2))
        combo_motivo = ctk.CTkComboBox(modal, values=["Sospecha Triquinosis", "Ictericia Generalizada", "Abscesos Múltiples", "Neumonía Severa", "Contaminación Gastrointestinal"], width=300)
        combo_motivo.pack(anchor="w", padx=30, pady=4)

        ctk.CTkLabel(modal, text="Destino Final:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=30, pady=(10, 2))
        combo_destino = ctk.CTkComboBox(modal, values=["DIGESTOR SANITARIO", "HORNO PIROLÍTICO / CREMATORIO", "DESNATURALIZACIÓN QUÍMICA"], width=300)
        combo_destino.pack(anchor="w", padx=30, pady=4)

        def ejecutar_decomiso():
            motivo = combo_motivo.get()
            destino = combo_destino.get()

            # Guardar en SQLite
            self.db.save_weight_record("FRIGORIFICO", "DECOMISO", {
                "tropa": self.tropa_actual,
                "motivo": motivo,
                "destino": destino,
                "peso_kg": peso,
                "veterinario": "DR. SENASA (MAT 8821)",
                "operario_id": self.operario_id,
                "operario_nombre": self.operario_nombre,
                "operario_legajo": self.operario_legajo,
                "timestamp_captura_iso": get_current_timestamp_iso()
            })

            # Imprimir etiqueta roja ZPL
            zpl_dec = self.printer.build_decomiso_zpl(self.tropa_actual, motivo, destino)
            self.printer.send_zpl(zpl_dec)

            modal.destroy()
            self._set_footer_msg(f"⚠️ Decomiso registrado: {motivo} -> {destino}", is_error=True)

        ctk.CTkButton(modal, text="CONFIRMAR DECOMISO SANITARIO", fg_color=COLOR_RED, hover_color="#B91C1C", height=44, command=ejecutar_decomiso).pack(fill="x", padx=30, pady=(24, 10))

    def _reimprimir_ultima(self):
        if not self.ultima_media_res:
            self._set_footer_msg("⚠️ No hay etiqueta previa en la memoria para re-imprimir.", is_error=True)
            return
        self.printer.send_zpl(self.ultima_media_res["zpl"])
        self._set_footer_msg(f"🔄 Etiqueta re-impresa: {self.ultima_media_res['lote']}")

    def _set_footer_msg(self, msg: str, is_error: bool = False):
        color = COLOR_RED if is_error else COLOR_GREEN
        self.lbl_footer_msg.configure(text=msg, text_color=color)

    def _on_close(self):
        self.scale.stop()
        self.destroy()


if __name__ == "__main__":
    app = TerminalFrigorifico()
    app.mainloop()

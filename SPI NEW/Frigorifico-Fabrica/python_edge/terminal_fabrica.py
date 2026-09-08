"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - TERMINAL TÁCTIL DE FÁBRICA
Módulo de Chacinados: Pesaje Asistido de Batea, Control Térmico y ZPL
=============================================================================
Diseñado según especificación 'Visual del programa.md':
- Dark Mode Industrial (#0B0F19, #0F172A, #1E293B)
- Integración con Balanza Moretti LAP (Plataforma / Batea)
- Semáforo Térmico de Masa (< 4°C Verde, 4-6°C Ámbar, > 6°C Rojo)
- Adopción estandarizada del Lote Fijo Tocino Industrial 00049
- Generación de Bachada y Etiqueta Térmica Zebra ZPL (100x50mm)
=============================================================================
"""

import sys
import os
import time
import datetime
import customtkinter as ctk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware"))

from config_parametros import (
    BALANZA_BATEA_PORT,
    BALANZA_BATEA_BAUD,
    BALANZA_BATEA_PROTOCOL,
    LOTE_FIJO_TOCINO_INDUSTRIAL,
    TEMP_MASA_IDEAL_MAX_C,
    TEMP_MASA_ALERTA_C,
    TEMP_MASA_BLOQUEO_C
)
from hardware.scale_driver import ScaleDriver
from hardware.zebra_printer import ZebraPrinter
from local_db import LocalDatabase
from auth_session import LoginPinModal, SupervisorAuthModal, CargaManualPesoModal, SessionManager, get_current_timestamp_iso

# Paleta Cromática Dark UI
ctk.set_appearance_mode("dark")
COLOR_BG = "#0B0F19"
COLOR_CARD = "#0F172A"
COLOR_CARD_BORDER = "#1E293B"
COLOR_GREEN = "#10B981"
COLOR_YELLOW = "#F59E0B"
COLOR_RED = "#EF4444"
COLOR_BLUE = "#38BDF8"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"


class TerminalFabrica(ctk.CTk):
    """Interfaz táctil para el Maestro Chacinero y pesador de batea en Fábrica."""

    def __init__(self):
        super().__init__()

        self.title("SPI - Terminal de Fábrica // Pesaje de Batea y Bachadas")
        self.geometry("1280x800")
        self.minsize(1024, 720)
        self.configure(fg_color=COLOR_BG)

        # Servicios
        self.db = LocalDatabase()
        self.printer = ZebraPrinter(mock_mode=True)
        self.scale = ScaleDriver(
            port=BALANZA_BATEA_PORT,
            baudrate=BALANZA_BATEA_BAUD,
            protocol=BALANZA_BATEA_PROTOCOL,
            mock_mode=True
        )
        self.scale.start()

        # Datos Operativos y Usuario de Sesión
        user = SessionManager.get_current_user()
        self.operario_id = user["id"]
        self.operario_nombre = user["nombre"]
        self.operario_legajo = user["legajo"]
        self.receta_actual = "Salame Milán Seco (Formulación 150 kg)"
        self.kilos_formulados = 150.0
        self.kilos_magro_req = 105.0  # 70%
        self.kilos_tocino_req = 30.0  # 20%
        self.kilos_especias_req = 15.0 # 10%

        # Estado del pesaje acumulativo
        self.peso_tara_acumulado = 0.0
        self.paso_actual = 1  # 1=Magro, 2=Tocino 00049, 3=Especias/Sal
        self.temp_masa_actual = 3.5
        self.ultima_bachada = None

        # Layout
        self._build_header()
        self._build_main_layout()
        self._build_footer()

        # Polling de balanza y refresco de interfaz
        self._poll_scale_data()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -----------------------------------------------------------------------
    # 1. HEADER BAR
    # -----------------------------------------------------------------------
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=64)
        self.header_frame.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="🌭 SPI // FÁBRICA DE CHACINADOS - BATEA Y MEZCLADO",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#FDE047"
        )
        title_lbl.pack(side="left", padx=20, pady=12)

        self.status_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.status_container.pack(side="right", padx=20)

        self.lbl_scale_status = ctk.CTkLabel(
            self.status_container,
            text="⚖️ BÁSCULA MORETTI: OK",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_GREEN,
            fg_color="#064E3B",
            corner_radius=6,
            padx=10,
            pady=4
        )
        self.lbl_scale_status.pack(side="left", padx=6)

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

        self.btn_operario = ctk.CTkButton(
            self.status_container,
            text=f"👤 {self.operario_nombre} ({self.operario_legajo})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT,
            fg_color="#854D0E",
            hover_color="#A16207",
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

        # Izquierda: Display de Balanza Moretti + Botones de Acción
        self.left_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=14)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Derecha: Pasos de la Receta + Control Térmico de Masa
        self.right_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=14)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        self._build_scale_panel()
        self._build_recipe_panel()

    # -----------------------------------------------------------------------
    # PANEL IZQUIERDO: DISPLAY BÁSCULA MORETTI
    # -----------------------------------------------------------------------
    def _build_scale_panel(self):
        p_title = ctk.CTkLabel(
            self.left_frame,
            text="PESAJE DE BATEA EN BÁSCULA DE PLATAFORMA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        p_title.pack(anchor="w", padx=24, pady=(20, 8))

        # Display Digital Gigante
        self.display_card = ctk.CTkFrame(self.left_frame, fg_color="#060911", border_color="#334155", border_width=2, corner_radius=16)
        self.display_card.pack(fill="x", padx=24, pady=10)

        self.lbl_weight = ctk.CTkLabel(
            self.display_card,
            text="0.00",
            font=ctk.CTkFont(family="Consolas", size=84, weight="bold"),
            text_color=COLOR_YELLOW
        )
        self.lbl_weight.pack(pady=(16, 0))

        unit_box = ctk.CTkFrame(self.display_card, fg_color="transparent")
        unit_box.pack(pady=(0, 16))

        self.lbl_stability = ctk.CTkLabel(
            unit_box,
            text="🟡 INESTABLE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_YELLOW
        )
        self.lbl_stability.pack(side="left", padx=10)

        self.lbl_tara_info = ctk.CTkLabel(
            unit_box,
            text="TARA ACTUAL: 0.00 kg",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_BLUE
        )
        self.lbl_tara_info.pack(side="left", padx=10)

        # Fila de Botones Rápidos (TARA y CERO)
        btn_row = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=8)

        self.btn_tara = ctk.CTkButton(
            btn_row,
            text="🎯 FIJAR TARA DE BATEA",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self._fijar_tara
        )
        self.btn_tara.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_reset_tara = ctk.CTkButton(
            btn_row,
            text="BORRAR TARA",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            fg_color="#334155",
            hover_color="#475569",
            command=self._borrar_tara
        )
        self.btn_reset_tara.pack(side="left", expand=True, fill="x", padx=(6, 0))

        # BOTÓN GIGANTE DE CONFIRMACIÓN DE BACHADA
        self.btn_confirmar_bachada = ctk.CTkButton(
            self.left_frame,
            text="🥩 CONFIRMAR BACHADA E IMPRIMIR ZPL",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=68,
            fg_color=COLOR_GREEN,
            hover_color="#059669",
            command=self._confirmar_bachada
        )
        self.btn_confirmar_bachada.pack(fill="x", padx=24, pady=(16, 6))

        # Botón Contingencia Manual por Falla de Balanza Moretti
        self.btn_carga_manual = ctk.CTkButton(
            self.left_frame,
            text="⚠️ CARGA MANUAL DE BATEA (BALANZA DAÑADA / AUTORIZAR)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            fg_color="#854D0E",
            hover_color="#A16207",
            command=self._iniciar_flujo_carga_manual
        )
        self.btn_carga_manual.pack(fill="x", padx=24, pady=(0, 16))

    # -----------------------------------------------------------------------
    # PANEL DERECHO: RECETA PASO A PASO + CONTROL TÉRMICO
    # -----------------------------------------------------------------------
    def _build_recipe_panel(self):
        # Cabecera de Receta
        rec_box = ctk.CTkFrame(self.right_frame, fg_color="#1E293B", corner_radius=10)
        rec_box.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            rec_box,
            text=f"RECETA: {self.receta_actual}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FDE047"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            rec_box,
            text="Lote Maestro Tocino: 00049 | Masa Total Programada: 150.0 kg",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # SEMÁFORO TÉRMICO DE MASA (Punto Crítico)
        temp_title = ctk.CTkLabel(
            self.right_frame,
            text="CONTROL DE TEMPERATURA DE MASA (CRÍTICO)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        temp_title.pack(anchor="w", padx=20, pady=(8, 4))

        self.temp_card = ctk.CTkFrame(self.right_frame, fg_color="#064E3B", corner_radius=10, height=60)
        self.temp_card.pack(fill="x", padx=20, pady=4)

        self.lbl_temp_val = ctk.CTkLabel(
            self.temp_card,
            text=f"🌡️ {self.temp_masa_actual:4.1f} °C  -  TEMPERATURA ÓPTIMA (CONFORME)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_GREEN
        )
        self.lbl_temp_val.pack(pady=12)

        # Botones de Simulación de Temperatura (+ / -)
        temp_ctrl_box = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        temp_ctrl_box.pack(fill="x", padx=20, pady=4)
        ctk.CTkButton(temp_ctrl_box, text="❄️ Bajar Temp (-0.5°C)", height=32, command=lambda: self._ajustar_temp(-0.5)).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(temp_ctrl_box, text="🔥 Subir Temp (+0.5°C)", height=32, command=lambda: self._ajustar_temp(+0.5)).pack(side="left", expand=True, fill="x", padx=2)

        # Pasos de Formulación Asistida
        pasos_title = ctk.CTkLabel(
            self.right_frame,
            text="DETALLE DE FORMULACIÓN CARGADA EN BATEA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        pasos_title.pack(anchor="w", padx=20, pady=(14, 4))

        self.pasos_box = ctk.CTkTextbox(self.right_frame, height=130, font=ctk.CTkFont(family="Consolas", size=12), fg_color="#060911")
        self.pasos_box.pack(fill="x", padx=20, pady=4)
        self.pasos_box.insert("end", f"1. [MAGRO CERDO]      Teorico: {self.kilos_magro_req:5.1f} kg (70%)  | Real: 105.0 kg [OK]\n")
        self.pasos_box.insert("end", f"2. [TOCINO LOTE 00049] Teorico: {self.kilos_tocino_req:5.1f} kg (20%)  | Real:  30.0 kg [OK]\n")
        self.pasos_box.insert("end", f"3. [ESPECIAS / SAL]   Teorico: {self.kilos_especias_req:5.1f} kg (10%)  | Real:  15.0 kg [OK]\n")
        self.pasos_box.insert("end", "─────────────────────────────────────────────────────────────\n")
        self.pasos_box.insert("end", "TOTAL MASA EN BATEA: 150.0 kg  |  Ristras estimadas: 120 un\n")
        self.pasos_box.configure(state="disabled")

    # -----------------------------------------------------------------------
    # 3. FOOTER
    # -----------------------------------------------------------------------
    def _build_footer(self):
        self.footer_frame = ctk.CTkFrame(self, fg_color="#060911", height=32, corner_radius=0)
        self.footer_frame.pack(fill="x", side="bottom")

        self.lbl_footer_msg = ctk.CTkLabel(
            self.footer_frame,
            text="Fábrica de Chacinados: Listo para formular y pesar en batea.",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_footer_msg.pack(side="left", padx=20, pady=4)

        lbl_version = ctk.CTkLabel(
            self.footer_frame,
            text="SPI Fábrica v2.0 | Control Térmico Activo",
            font=ctk.CTkFont(size=11),
            text_color="#475569"
        )
        lbl_version.pack(side="right", padx=20, pady=4)

    # -----------------------------------------------------------------------
    # LÓGICA DE BÁSCULA Y TEMPERATURA
    # -----------------------------------------------------------------------
    def _poll_scale_data(self):
        status = self.scale.get_status()
        peso_bruto = status["weight_kg"]
        peso_neto = max(0.0, peso_bruto - self.peso_tara_acumulado)
        estable = status["is_stable"]

        self.lbl_weight.configure(text=f"{peso_neto:6.2f}")

        if estable and peso_neto > 1.0:
            self.lbl_weight.configure(text_color=COLOR_GREEN)
            self.lbl_stability.configure(text="🟢 ESTABLE", text_color=COLOR_GREEN)
            self.display_card.configure(border_color=COLOR_GREEN)
        elif peso_neto > 1.0:
            self.lbl_weight.configure(text_color=COLOR_YELLOW)
            self.lbl_stability.configure(text="🟡 INESTABLE", text_color=COLOR_YELLOW)
            self.display_card.configure(border_color=COLOR_YELLOW)
        else:
            self.lbl_weight.configure(text_color="#64748B")
            self.lbl_stability.configure(text="⚪ EN CERO", text_color="#64748B")
            self.display_card.configure(border_color="#334155")

        stats = self.db.get_buffer_stats()
        self.lbl_buffer_status.configure(text=f"💾 OFFLINE: {stats['pending_sync_count']}")

        self.after(100, self._poll_scale_data)

    def _fijar_tara(self):
        status = self.scale.get_status()
        self.peso_tara_acumulado = status["weight_kg"]
        self.lbl_tara_info.configure(text=f"TARA ACTUAL: {self.peso_tara_acumulado:6.2f} kg")
        self._set_footer_msg(f"🎯 Tara fijada en {self.peso_tara_acumulado:.2f} kg.")

    def _borrar_tara(self):
        self.peso_tara_acumulado = 0.0
        self.lbl_tara_info.configure(text="TARA ACTUAL: 0.00 kg")
        self._set_footer_msg("Borrada la tara de batea.")

    def _ajustar_temp(self, delta: float):
        self.temp_masa_actual = round(max(0.0, min(15.0, self.temp_masa_actual + delta)), 1)

        if self.temp_masa_actual <= TEMP_MASA_IDEAL_MAX_C:
            self.temp_card.configure(fg_color="#064E3B")
            self.lbl_temp_val.configure(text=f"🌡️ {self.temp_masa_actual:4.1f} °C  -  TEMPERATURA ÓPTIMA (CONFORME)", text_color=COLOR_GREEN)
            self.btn_confirmar_bachada.configure(state="normal", fg_color=COLOR_GREEN)
        elif self.temp_masa_actual <= TEMP_MASA_BLOQUEO_C:
            self.temp_card.configure(fg_color="#78350F")
            self.lbl_temp_val.configure(text=f"⚠️ {self.temp_masa_actual:4.1f} °C  -  ADVERTENCIA: INCORPORAR ESCARCHA", text_color=COLOR_YELLOW)
            self.btn_confirmar_bachada.configure(state="normal", fg_color=COLOR_YELLOW)
        else:
            self.temp_card.configure(fg_color="#7F1D1D")
            self.lbl_temp_val.configure(text=f"🔴 {self.temp_masa_actual:4.1f} °C  -  BLOQUEO: MASA MUY CALIENTE", text_color="#FCA5A5")
            self.btn_confirmar_bachada.configure(state="disabled", fg_color="#334155")
            self._set_footer_msg("🔴 Bloqueo bromatológico: La masa superó 6°C. Enfríe antes de continuar.", is_error=True)

    def _abrir_login_modal(self):
        def on_logged(user):
            self.operario_id = user["id"]
            self.operario_nombre = user["nombre"]
            self.operario_legajo = user["legajo"]
            self.btn_operario.configure(text=f"👤 {self.operario_nombre} ({self.operario_legajo})")
            self._set_footer_msg(f"✅ Sesión iniciada: {self.operario_nombre} ({user['rol']}) a las {user['login_timestamp']}")
        LoginPinModal(self, on_success_callback=on_logged)

    def _iniciar_flujo_carga_manual(self):
        """Inicia el protocolo de contingencia por báscula Moretti de batea averiada."""
        desc = (
            f"Desbloquear carga manual de peso para la bachada de {self.receta_actual} "
            f"por contingencia en báscula de batea."
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
        """Ejecuta la confirmación de la bachada con pesaje manual firmado por supervisor."""
        nom_sup = f"{supervisor['nombre']} ({supervisor['legajo']})"
        self._ejecutar_confirmacion_bachada(
            peso_real=peso,
            captura_manual=True,
            autorizado_por=nom_sup,
            motivo_contingencia=motivo
        )

    def _confirmar_bachada(self):
        self._ejecutar_confirmacion_bachada(peso_real=self.kilos_formulados, captura_manual=False)

    def _ejecutar_confirmacion_bachada(
        self,
        peso_real: float,
        captura_manual: bool = False,
        autorizado_por: str = "",
        motivo_contingencia: str = ""
    ):
        if self.temp_masa_actual > TEMP_MASA_BLOQUEO_C:
            self._set_footer_msg("❌ No se puede confirmar bachada con temperatura > 6.0 °C.", is_error=True)
            return

        ahora = datetime.datetime.now()
        ahora_iso = get_current_timestamp_iso()
        lote_bachada = f"BACH-SALMIL-{ahora.strftime('%y%m%d')}-01"
        kilos_totales = peso_real
        unidades_estimadas = int(round((kilos_totales / 150.0) * 120))

        # Guardar en SQLite Local
        registro_bachada = {
            "id_bachada": lote_bachada,
            "receta": "Salame Milán Seco",
            "kilos_totales": kilos_totales,
            "unidades_ristras": unidades_estimadas,
            "temperatura_masa_c": self.temp_masa_actual,
            "lote_tocino_industrial": LOTE_FIJO_TOCINO_INDUSTRIAL,
            "captura_manual": captura_manual,
            "autorizado_por": autorizado_por,
            "motivo_contingencia": motivo_contingencia,
            "operario_id": self.operario_id,
            "operario_nombre": self.operario_nombre,
            "operario_legajo": self.operario_legajo,
            "timestamp_captura_iso": ahora_iso,
            "timestamp": ahora.isoformat()
        }
        idempotency_key = self.db.save_weight_record("FABRICA", "BACHADA", registro_bachada)

        # Imprimir Etiqueta ZPL Bachada (100x50mm)
        zpl = self.printer.build_bachada_zpl(
            nombre_producto="SALAME MILAN SECO",
            lote_bachada=lote_bachada,
            kilos=kilos_totales,
            unidades=unidades_estimadas,
            lote_tocino=LOTE_FIJO_TOCINO_INDUSTRIAL,
            fecha_elab=ahora.strftime("%d/%m/%Y")
        )
        res_print = self.printer.send_zpl(zpl)
        if not res_print["success"]:
            self.db.enqueue_label("BACHADA_100x50", zpl)

        if captura_manual:
            self._set_footer_msg(f"⚠️ [MANUAL] Bachada confirmada: {lote_bachada} ({kilos_totales:.1f} kg) autorizada por {autorizado_por}.")
        else:
            self._set_footer_msg(f"✅ Bachada confirmada: {lote_bachada} ({kilos_totales:.1f} kg) | Etiqueta ZPL emitida.")

    def _set_footer_msg(self, msg: str, is_error: bool = False):
        color = COLOR_RED if is_error else COLOR_GREEN
        self.lbl_footer_msg.configure(text=msg, text_color=color)

    def _on_close(self):
        self.scale.stop()
        self.destroy()


if __name__ == "__main__":
    app = TerminalFabrica()
    app.mainloop()

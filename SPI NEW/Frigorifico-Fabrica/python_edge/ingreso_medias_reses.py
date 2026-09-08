"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - INGRESO DE MEDIAS RESES A CÁMARAS
Módulo de Faena: Palco de Pesaje al Gancho, Grilla Interactiva y Decomisos
=============================================================================
Alineado con el flujo operativo de la planilla Google Sheets de Planta:
1. Barra Superior / KPIs: CARGA, TIPO ANIMAL (MEI, CAP, etc.), CANT. MEDIAS, PESO TOTAL.
2. Referencias Oficiales: Tipos de Animal, Motivos de Decomiso Parcial y Depósitos.
3. Control de Muertes: Muertos en Traslado y Muertos en Corral interactivos.
4. Códigos Rápidos de Depósito: C1 a C6 (Cámaras Frigoríficas) y CO1 / CO2 (Oreo).
5. Pesaje al Gancho Systel Cuora (84px verde) con alternancia automática A (IZQ) / B (DER).
6. Grilla Interactiva Animal por Animal (1, 2, 3...):
   - Media Res A y Media Res B por fila
   - Estados DT (Decomiso Total), EM (Eliminar Media), DP (Decomiso Parcial)
   - Click para ver detalles completos, re-imprimir ZPL, editar DP o anular EM.
=============================================================================
"""

import sys
import os
import time
import datetime
from typing import Dict, Any, List, Optional
import customtkinter as ctk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardware"))

from config_parametros import (
    BALANZA_GANCHO_PORT,
    BALANZA_GANCHO_BAUD,
    BALANZA_GANCHO_PROTOCOL,
    ALTERNANCIA_LADO_AUTOMATICA,
    CAMARAS_PLANTA,
    LISTA_CAMARAS_NOMBRES,
    DEPOSITOS_MAP,
    DEPOSITOS_INVERSO_MAP,
    LISTA_CODIGOS_DEPOSITOS,
    TIPOS_ANIMAL,
    LISTA_TIPOS_ANIMAL_LABELS,
    LISTA_TIPOS_ANIMAL_CODIGOS,
    TIPO_ANIMAL_DEFAULT,
    MOTIVOS_DECOMISO_PARCIAL,
    LISTA_MOTIVOS_DP_LABELS,
    MOTIVOS_DP_MAP
)
from hardware.scale_driver import ScaleDriver
from hardware.zebra_printer import ZebraPrinter
from local_db import LocalDatabase
from auth_session import LoginPinModal, SupervisorAuthModal, CargaManualPesoModal, SessionManager, get_current_timestamp_iso

# Configuración Visual Dark Industrial
ctk.set_appearance_mode("dark")
COLOR_BG = "#0B0F19"
COLOR_CARD = "#0F172A"
COLOR_CARD_BORDER = "#1E293B"
COLOR_GREEN = "#10B981"
COLOR_YELLOW = "#F59E0B"
COLOR_RED = "#EF4444"
COLOR_BLUE = "#38BDF8"
COLOR_PURPLE = "#818CF8"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"
COLOR_ACCENT = "#38BDF8"


class IngresoMediasResesApp(ctk.CTk):
    """Interfaz táctil para el operador de pesaje al gancho aéreo e ingreso a cámaras."""

    def __init__(self):
        super().__init__()

        self.title("SPI - Ingreso de Medias Reses // Control de Faena y Cámaras")
        self.geometry("1400x900")
        self.minsize(1180, 800)
        self.configure(fg_color=COLOR_BG)

        # Servicios Backend & Hardware
        self.db = LocalDatabase()
        self.printer = ZebraPrinter(mock_mode=True)
        self.scale = ScaleDriver(
            port=BALANZA_GANCHO_PORT,
            baudrate=BALANZA_GANCHO_BAUD,
            protocol=BALANZA_GANCHO_PROTOCOL,
            mock_mode=True
        )
        self.scale.start()

        # Operario y Sesión Activa
        user = SessionManager.get_current_user()
        self.operario_id = user["id"]
        self.operario_nombre = user["nombre"]
        self.operario_legajo = user["legajo"]

        # Datos de la Carga y Tropa Activa
        self.numero_carga = 3
        self.tipo_animal_seleccionado = TIPO_ANIMAL_DEFAULT  # MEI por defecto
        self.tropa_actual = "TRP-2026-00412"
        self.dte_senasa = "2026-0099412-1"
        self.remito_nro = "53"
        self.granja_origen = "Granja Ulapes (11.012.0.00435/00)"
        self.peso_promedio_vivo = 113.18
        self.peso_estimado_media_res = 46.12

        # Contadores de Hacienda y Bajas
        self.cabezas_declaradas = 110
        self.muertos_traslado = 0
        self.muertos_corral = 0

        # Lado de captura actual (A = IZQ, B = DER)
        self.lado_actual = "IZQ"  # "IZQ" (A) o "DER" (B)
        self.proximo_numero_animal = 1

        # Depósito predeterminado (Código corto: C1..C6, CO1, CO2)
        self.deposito_codigo_seleccionado = "C1"
        self.camara_seleccionada = DEPOSITOS_MAP.get(self.deposito_codigo_seleccionado, "Cámara Frigorífica 1")

        # Stock simulado en Cámaras de Planta
        self.stock_camaras = {
            "Cámara de Oreo 1": 184,
            "Cámara de Oreo 2": 0,
            "Cámara Frigorífica 1": 680,
            "Cámara Frigorífica 2": 510,
            "Cámara Frigorífica 3": 120,
            "Cámara Frigorífica 4": 0,
            "Cámara Frigorífica 5": 0,
            "Cámara Frigorífica 6": 0
        }

        # Estructura de Cargas Previas: Diccionario indexado por número de animal:
        # { 1: {"A": media_dict, "B": media_dict}, 2: {...} }
        self.animales_cargas: Dict[int, Dict[str, Optional[Dict[str, Any]]]] = {}
        self.ultima_media_res_emitida: Optional[Dict[str, Any]] = None

        # Cargar datos históricos iniciales de demostración
        self._inicializar_datos_demo()

        # Construcción de la Interfaz
        self._build_top_dashboard()
        self._build_sub_control_bar()
        self._build_main_layout()
        self._build_footer()

        # Loop de refresco de balanza (100ms)
        self._poll_scale_data()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _inicializar_datos_demo(self):
        """Carga 3 animales previos de ejemplo para poblar la grilla de inmediato."""
        ejemplos = [
            (1, "IZQ", 43.10, "CO1", False, None),
            (1, "DER", 42.80, "CO1", False, None),
            (2, "IZQ", 44.50, "C1", False, {"motivo": "CO", "kilos": 3.5}),
            (2, "DER", 43.90, "C1", False, None),
            (3, "IZQ", 41.80, "C1", True, None),  # Decomiso Total
        ]
        for num, lado, peso, dep_cod, es_dt, dp_info in ejemplos:
            camara_nom = DEPOSITOS_MAP.get(dep_cod, "Cámara de Oreo 1")
            lote = f"MR-{lado}-{self.tropa_actual.replace('TRP-', '')}-{num:02d}"
            item = {
                "lote": lote,
                "numero_animal": num,
                "lado": lado,
                "lado_letra": "A" if lado == "IZQ" else "B",
                "peso_kg": peso,
                "tipo_animal": "MEI",
                "deposito_codigo": dep_cod,
                "camara_destino": camara_nom,
                "decomiso_total": es_dt,
                "decomiso_parcial": dp_info,
                "anulado": False,
                "operario_id": self.operario_id,
                "operario_nombre": self.operario_nombre,
                "operario_legajo": self.operario_legajo,
                "timestamp_iso": get_current_timestamp_iso(),
                "idempotency_key": f"DEMO-{num}-{lado}"
            }
            if num not in self.animales_cargas:
                self.animales_cargas[num] = {"A": None, "B": None}
            letra = "A" if lado == "IZQ" else "B"
            self.animales_cargas[num][letra] = item

        self.proximo_numero_animal = 3
        self.lado_actual = "DER"  # Animal 3 ya tiene IZQ (A), sigue DER (B)

    # -----------------------------------------------------------------------
    # 1. TOP DASHBOARD (Estilo Google Sheets)
    # -----------------------------------------------------------------------
    def _build_top_dashboard(self):
        self.top_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=82)
        self.top_frame.pack(fill="x", side="top")

        # Fila interna
        row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)

        # 1. CARGA
        box_carga = ctk.CTkFrame(row, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=8, width=100, height=64)
        box_carga.pack(side="left", padx=4)
        box_carga.pack_propagate(False)
        ctk.CTkLabel(box_carga, text="CARGA", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_GREEN).pack(pady=(4, 0))
        self.lbl_carga_val = ctk.CTkLabel(box_carga, text=str(self.numero_carga), font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color=COLOR_TEXT)
        self.lbl_carga_val.pack()

        # 2. TIPO DE ANIMAL (MEI, CAP, SAN, CER, CACH, LECH)
        box_tipo = ctk.CTkFrame(row, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=8, width=160, height=64)
        box_tipo.pack(side="left", padx=4)
        box_tipo.pack_propagate(False)
        ctk.CTkLabel(box_tipo, text="TIPO ANIMAL", font=ctk.CTkFont(size=10, weight="bold"), text_color="#38BDF8").pack(pady=(4, 2))
        self.combo_tipo_animal = ctk.CTkComboBox(
            box_tipo,
            values=LISTA_TIPOS_ANIMAL_CODIGOS,
            width=130,
            height=28,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            command=self._on_tipo_animal_changed
        )
        self.combo_tipo_animal.set(self.tipo_animal_seleccionado)
        self.combo_tipo_animal.pack()

        # 3. CANT. MEDIAS (Válidas)
        box_cant = ctk.CTkFrame(row, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=8, width=130, height=64)
        box_cant.pack(side="left", padx=4)
        box_cant.pack_propagate(False)
        ctk.CTkLabel(box_cant, text="CANT. MEDIAS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#FDE047").pack(pady=(4, 0))
        self.lbl_cant_medias = ctk.CTkLabel(box_cant, text="0", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color=COLOR_TEXT)
        self.lbl_cant_medias.pack()

        # 4. PESO TOTAL
        box_peso = ctk.CTkFrame(row, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=8, width=170, height=64)
        box_peso.pack(side="left", padx=4)
        box_peso.pack_propagate(False)
        ctk.CTkLabel(box_peso, text="PESO TOTAL ACUMULADO", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_GREEN).pack(pady=(4, 0))
        self.lbl_peso_total = ctk.CTkLabel(box_peso, text="0.00 kg", font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color=COLOR_GREEN)
        self.lbl_peso_total.pack()

        # Botón Referencias
        btn_ref = ctk.CTkButton(
            row, text="📋 REFERENCIAS", width=120, height=36, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E293B", hover_color="#334155", command=self._abrir_modal_referencias
        )
        btn_ref.pack(side="left", padx=(10, 4))

        # Botón Configuración de Empresa y Etiqueta
        btn_empresa = ctk.CTkButton(
            row, text="⚙️ EMPRESA / ETIQUETA", width=155, height=36, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1E293B", hover_color="#334155", command=self._abrir_modal_config_empresa
        )
        btn_empresa.pack(side="left", padx=4)

        # Lado Derecho: Estado Hardware + Operario
        right_box = ctk.CTkFrame(row, fg_color="transparent")
        right_box.pack(side="right")

        self.lbl_scale_status = ctk.CTkLabel(
            right_box, text="⚖️ BALANZA: OK", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_GREEN, fg_color="#064E3B", corner_radius=6, padx=8, pady=3
        )
        self.lbl_scale_status.pack(side="left", padx=4)

        self.lbl_zebra_status = ctk.CTkLabel(
            right_box, text="🖨️ ZEBRA: LISTA", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_BLUE, fg_color="#082F49", corner_radius=6, padx=8, pady=3
        )
        self.lbl_zebra_status.pack(side="left", padx=4)

        self.lbl_buffer_status = ctk.CTkLabel(
            right_box, text="💾 OFFLINE: 0", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_MUTED, fg_color="#1E293B", corner_radius=6, padx=8, pady=3
        )
        self.lbl_buffer_status.pack(side="left", padx=4)

        # Botón Operario PIN
        self.btn_operario = ctk.CTkButton(
            right_box, text=f"👤 {self.operario_nombre} ({self.operario_legajo})",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT,
            fg_color="#312E81", hover_color="#4338CA", corner_radius=6, height=30,
            command=self._abrir_login_modal
        )
        self.btn_operario.pack(side="left", padx=6)

    # -----------------------------------------------------------------------
    # 2. SUB-BARRA DE CONTROL OPERATIVO
    # -----------------------------------------------------------------------
    def _build_sub_control_bar(self):
        sub_bar = ctk.CTkFrame(self, fg_color="#131D31", corner_radius=0, height=48)
        sub_bar.pack(fill="x", side="top", pady=(0, 4))

        inner = ctk.CTkFrame(sub_bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=6)

        # Tropa y Remito
        ctk.CTkLabel(
            inner, text=f"TROPA: {self.tropa_actual}  |  REMITO/DT-e: {self.dte_senasa}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#38BDF8"
        ).pack(side="left", padx=(0, 15))

        # Selector Rápido de Depósito (C1..C6, CO1, CO2)
        ctk.CTkLabel(inner, text="DEPÓSITO:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(10, 4))
        self.combo_deposito_rapido = ctk.CTkComboBox(
            inner, values=LISTA_CODIGOS_DEPOSITOS, width=80, height=28,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self._on_deposito_codigo_changed
        )
        self.combo_deposito_rapido.set(self.deposito_codigo_seleccionado)
        self.combo_deposito_rapido.pack(side="left", padx=(0, 15))

        # Muertos en Traslado
        ctk.CTkLabel(inner, text="MUERTOS TRASLADO:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(5, 4))
        self.lbl_muertos_traslado_val = ctk.CTkLabel(inner, text=str(self.muertos_traslado), font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color=COLOR_TEXT)
        self.lbl_muertos_traslado_val.pack(side="left", padx=(0, 15))

        # Muertos en Corral (Interactivo con + / -)
        ctk.CTkLabel(inner, text="MUERTOS EN CORRAL:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FCA5A5").pack(side="left", padx=(5, 4))
        btn_mc_minus = ctk.CTkButton(inner, text="-", width=26, height=26, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#334155", command=lambda: self._ajustar_muertos_corral(-1))
        btn_mc_minus.pack(side="left", padx=1)
        self.lbl_muertos_corral_val = ctk.CTkLabel(inner, text=str(self.muertos_corral), font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), width=30, text_color=COLOR_RED if self.muertos_corral > 0 else COLOR_TEXT)
        self.lbl_muertos_corral_val.pack(side="left", padx=1)
        btn_mc_plus = ctk.CTkButton(inner, text="+", width=26, height=26, font=ctk.CTkFont(size=12, weight="bold"), fg_color="#334155", command=lambda: self._ajustar_muertos_corral(+1))
        btn_mc_plus.pack(side="left", padx=(1, 20))

        # KPIs Resumen Decomisos
        self.lbl_dt_resumen = ctk.CTkLabel(inner, text="DECOMISO TOTAL: 0 cant | 0.00 kg", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FCA5A5")
        self.lbl_dt_resumen.pack(side="left", padx=(10, 15))

        self.lbl_dp_resumen = ctk.CTkLabel(inner, text="DECOMISO PARCIAL: 0.00 kg", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FDE047")
        self.lbl_dp_resumen.pack(side="left", padx=(5, 10))

    # -----------------------------------------------------------------------
    # 3. CUERPO PRINCIPAL (Split Izquierda 40% Pesaje / Derecha 60% Grilla)
    # -----------------------------------------------------------------------
    def _build_main_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=4)

        # Panel Izquierdo: PESAJE AL GANCHO Y DESTINO (40%)
        self.left_frame = ctk.CTkFrame(container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(0, 6), ipadx=4)
        self.left_frame.configure(width=480)

        # Panel Derecho: GRILLA INTERACTIVA DE ANIMALES Y MEDIAS RESES (60%)
        self.right_frame = ctk.CTkFrame(container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self._build_scale_section()
        self._build_grid_section()

    # -----------------------------------------------------------------------
    # PANEL IZQUIERDO: DISPLAY DIGITAL Y ACCIONES DE PESAJE
    # -----------------------------------------------------------------------
    def _build_scale_section(self):
        ctk.CTkLabel(
            self.left_frame, text="⚖️ PALCO DE FAENA // PESAJE AL GANCHO (SYSTEL)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#A5B4FC"
        ).pack(anchor="w", padx=16, pady=(12, 4))

        # Display Digital de Balanza
        self.display_card = ctk.CTkFrame(self.left_frame, fg_color="#060911", border_color="#334155", border_width=2, corner_radius=12)
        self.display_card.pack(fill="x", padx=16, pady=6)

        self.lbl_weight = ctk.CTkLabel(
            self.display_card, text="0.00", font=ctk.CTkFont(family="Consolas", size=80, weight="bold"), text_color=COLOR_YELLOW
        )
        self.lbl_weight.pack(pady=(10, 0))

        unit_box = ctk.CTkFrame(self.display_card, fg_color="transparent")
        unit_box.pack(pady=(0, 10))

        self.lbl_stability = ctk.CTkLabel(
            unit_box, text="🟡 INESTABLE (OSCILANDO)", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_YELLOW
        )
        self.lbl_stability.pack(side="left", padx=8)

        ctk.CTkLabel(
            unit_box, text="KG GANCHO CALIENTE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=8)

        # Alternador de Lado (MEDIA A / MEDIA B)
        lado_card = ctk.CTkFrame(self.left_frame, fg_color="#1E293B", corner_radius=8)
        lado_card.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(lado_card, text="Lado Actual de la Res:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=10, pady=8)

        self.btn_izq = ctk.CTkButton(
            lado_card, text="MEDIA A (IZQ)", height=36, width=120, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4338CA" if self.lado_actual == "IZQ" else "#0F172A",
            command=lambda: self._set_lado("IZQ")
        )
        self.btn_izq.pack(side="left", padx=6)

        self.btn_der = ctk.CTkButton(
            lado_card, text="MEDIA B (DER)", height=36, width=120, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#4338CA" if self.lado_actual == "DER" else "#0F172A",
            command=lambda: self._set_lado("DER")
        )
        self.btn_der.pack(side="left", padx=6)

        # Depósito / Cámara Destino
        dest_card = ctk.CTkFrame(self.left_frame, fg_color="#1E293B", corner_radius=8)
        dest_card.pack(fill="x", padx=16, pady=6)

        top_dest = ctk.CTkFrame(dest_card, fg_color="transparent")
        top_dest.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(top_dest, text="Cámara Destino:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.combo_camaras = ctk.CTkComboBox(
            top_dest, values=LISTA_CAMARAS_NOMBRES, width=240, height=28,
            command=self._on_camara_nombre_changed
        )
        self.combo_camaras.set(self.camara_seleccionada)
        self.combo_camaras.pack(side="right")

        self.prog_bar_camara = ctk.CTkProgressBar(dest_card, height=10, corner_radius=5)
        self.prog_bar_camara.pack(fill="x", padx=10, pady=4)

        self.lbl_info_camara = ctk.CTkLabel(dest_card, text="", font=ctk.CTkFont(size=11), text_color="#CBD5E1")
        self.lbl_info_camara.pack(anchor="w", padx=10, pady=(0, 6))
        self._actualizar_info_camara()

        # BOTÓN GIGANTE: CONFIRMAR PESAJE E INGRESAR (62px)
        self.btn_confirmar = ctk.CTkButton(
            self.left_frame,
            text="⚖️ CONFIRMAR PESAJE E INGRESAR MEDIA RES",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=60,
            fg_color=COLOR_GREEN,
            hover_color="#059669",
            command=self._confirmar_ingreso_media_res
        )
        self.btn_confirmar.pack(fill="x", padx=16, pady=(10, 4))

        # BOTÓN CONTINGENCIA: CARGA MANUAL (BALANZA DAÑADA)
        self.btn_carga_manual = ctk.CTkButton(
            self.left_frame,
            text="⚠️ CARGA MANUAL (BALANZA DAÑADA / AUTORIZAR)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            fg_color="#854D0E",
            hover_color="#A16207",
            command=self._iniciar_flujo_carga_manual
        )
        self.btn_carga_manual.pack(fill="x", padx=16, pady=(2, 6))

        # Botones Secundarios de Faena
        btn_grid = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_grid.pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            btn_grid, text="🔴 DECOMISO TOTAL (DT)", height=38, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7F1D1D", hover_color=COLOR_RED, command=self._modal_decomiso_total
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_grid, text="🔪 DECOMISO PARCIAL (DP)", height=38, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#854D0E", hover_color=COLOR_YELLOW, command=self._modal_decomiso_parcial
        ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Re-imprimir última
        ctk.CTkButton(
            self.left_frame, text="🔄 Re-imprimir Última Etiqueta ZPL", height=32,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color="#1E293B", hover_color="#334155",
            command=self._reimprimir_ultima
        ).pack(fill="x", padx=16, pady=(6, 10))

    # -----------------------------------------------------------------------
    # PANEL DERECHO: GRILLA INTERACTIVA DE ANIMALES Y MEDIAS RESES
    # -----------------------------------------------------------------------
    def _build_grid_section(self):
        # Header de la Grilla
        head_grid = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        head_grid.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            head_grid, text="📊 CARGAS PREVIAS DE LA TROPA (ANIMAL POR ANIMAL)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#FDE047"
        ).pack(side="left")

        ctk.CTkLabel(
            head_grid, text="💡 Toca cualquier media res para ver datos, re-imprimir o editar",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED
        ).pack(side="right")

        # Encabezado visual de columnas
        col_bar = ctk.CTkFrame(self.right_frame, fg_color="#1E293B", height=34, corner_radius=6)
        col_bar.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(col_bar, text="N°", font=ctk.CTkFont(size=11, weight="bold"), width=44).pack(side="left", padx=4)
        ctk.CTkLabel(col_bar, text="MEDIA RES A (IZQ)          [DT | EM | DP]", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkLabel(col_bar, text="MEDIA RES B (DER)          [DT | EM | DP]", font=ctk.CTkFont(size=11, weight="bold"), text_color="#A5B4FC").pack(side="left", expand=True, fill="x", padx=4)

        # Contenedor con Scroll para las filas de animales
        self.scroll_grilla = ctk.CTkScrollableFrame(self.right_frame, fg_color="#060911", corner_radius=8)
        self.scroll_grilla.pack(fill="both", expand=True, padx=16, pady=(2, 10))

        # Renderizar datos iniciales
        self._actualizar_totales_y_grilla()

    # -----------------------------------------------------------------------
    # RENDER DE LA GRILLA DE ANIMALES
    # -----------------------------------------------------------------------
    def _actualizar_totales_y_grilla(self):
        """Recalcula cant. medias, peso total, decomisos y redibuja la tabla."""
        total_medias = 0
        total_kilos = 0.0
        decomisos_totales_cant = 0
        decomisos_totales_kg = 0.0
        decomisos_parciales_kg = 0.0

        for num_animal, lados in self.animales_cargas.items():
            for letra in ["A", "B"]:
                item = lados.get(letra)
                if item and not item.get("anulado", False):
                    peso = item["peso_kg"]
                    total_medias += 1
                    total_kilos += peso

                    if item.get("decomiso_total", False):
                        decomisos_totales_cant += 1
                        decomisos_totales_kg += peso

                    dp = item.get("decomiso_parcial")
                    if dp and dp.get("kilos", 0) > 0:
                        decomisos_parciales_kg += dp["kilos"]

        # Actualizar Tarjetas Superiores
        self.lbl_cant_medias.configure(text=str(total_medias))
        self.lbl_peso_total.configure(text=f"{total_kilos:,.2f} kg")

        self.lbl_dt_resumen.configure(text=f"DECOMISO TOTAL: {decomisos_totales_cant} cant | {decomisos_totales_kg:.2f} kg")
        self.lbl_dp_resumen.configure(text=f"DECOMISO PARCIAL: {decomisos_parciales_kg:.2f} kg")

        # Dibujar Grilla
        self._render_grilla_filas()

    def _render_grilla_filas(self):
        for w in self.scroll_grilla.winfo_children():
            w.destroy()

        animales_ordenados = sorted(self.animales_cargas.keys(), reverse=True)

        for num in animales_ordenados:
            lados = self.animales_cargas[num]
            row_frame = ctk.CTkFrame(self.scroll_grilla, fg_color="#0F172A", corner_radius=6, height=44)
            row_frame.pack(fill="x", pady=2, padx=2)

            # N° Animal
            lbl_num = ctk.CTkLabel(
                row_frame, text=f"#{num:02d}", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                width=44, text_color="#FDE047"
            )
            lbl_num.pack(side="left", padx=4, pady=4)

            # Celdas para Media A y Media B
            for letra in ["A", "B"]:
                item = lados.get(letra)
                cell_box = ctk.CTkFrame(row_frame, fg_color="#1E293B" if item else "#060911", corner_radius=6)
                cell_box.pack(side="left", expand=True, fill="both", padx=4, pady=4)

                if not item:
                    # Celda Vacía
                    ctk.CTkLabel(
                        cell_box, text=f"Media {letra}: Pendiente", font=ctk.CTkFont(size=11), text_color="#475569"
                    ).pack(side="left", padx=10, pady=4)
                elif item.get("anulado", False):
                    # Celda Anulada
                    ctk.CTkLabel(
                        cell_box, text=f"Media {letra}: [ELIMINADA / ANULADA]", font=ctk.CTkFont(size=11, weight="bold"),
                        text_color="#64748B"
                    ).pack(side="left", padx=10, pady=4)
                else:
                    # Celda con Media Res Activa
                    lado_txt = item["lado"]
                    peso_txt = f"{item['peso_kg']:.2f} kg"
                    tipo_txt = item.get("tipo_animal", "MEI")
                    dep_txt = item.get("deposito_codigo", "C1")

                    btn_main = ctk.CTkButton(
                        cell_box,
                        text=f"Media {letra} ({lado_txt}): {peso_txt} [{tipo_txt} | {dep_txt}]",
                        font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                        text_color=COLOR_TEXT,
                        fg_color="transparent",
                        hover_color="#334155",
                        anchor="w",
                        command=lambda it=item: self._abrir_modal_detalle_media_res(it)
                    )
                    btn_main.pack(side="left", expand=True, fill="x", padx=4)

                    # Badges / Botones de Acción Rápida en la Fila
                    # Badge MAN (Carga Manual de Balanza)
                    if item.get("captura_manual", False):
                        ctk.CTkLabel(cell_box, text="MAN", font=ctk.CTkFont(size=10, weight="bold"), text_color="#000000", fg_color="#F59E0B", corner_radius=4, width=32).pack(side="left", padx=2)

                    # Badge DT
                    if item.get("decomiso_total", False):
                        ctk.CTkLabel(cell_box, text="DT", font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF", fg_color=COLOR_RED, corner_radius=4, width=24).pack(side="left", padx=2)

                    # Badge DP
                    dp = item.get("decomiso_parcial")
                    if dp and dp.get("kilos", 0) > 0:
                        ctk.CTkLabel(cell_box, text=f"DP:{dp['motivo']} -{dp['kilos']:.1f}k", font=ctk.CTkFont(size=10, weight="bold"), text_color="#000000", fg_color=COLOR_YELLOW, corner_radius=4, padx=4).pack(side="left", padx=2)

                    # Botón Re-imprimir individual
                    btn_prn = ctk.CTkButton(
                        cell_box, text="🖨️", width=28, height=26, font=ctk.CTkFont(size=12),
                        fg_color="#334155", hover_color="#475569",
                        command=lambda it=item: self._reimprimir_etiqueta_media_res(it)
                    )
                    btn_prn.pack(side="left", padx=2)

                    # Botón Eliminar Media (EM)
                    btn_em = ctk.CTkButton(
                        cell_box, text="🗑️", width=28, height=26, font=ctk.CTkFont(size=12),
                        fg_color="#7F1D1D", hover_color=COLOR_RED,
                        command=lambda it=item: self._eliminar_media_res(it)
                    )
                    btn_em.pack(side="left", padx=(2, 6))

    # -----------------------------------------------------------------------
    # MODAL DE DETALLES Y ACCIONES POR MEDIA RES (Interacción)
    # -----------------------------------------------------------------------
    def _abrir_modal_detalle_media_res(self, item: Dict[str, Any]):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Gestión de Media Res: {item['lote']}")
        modal.geometry("520x510")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(
            modal, text=f"🥩 MEDIA RES: {item['lote']}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38BDF8"
        ).pack(pady=(16, 4))

        info_frame = ctk.CTkFrame(modal, fg_color="#060911", corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=10)

        peso_display = f"{item['peso_kg']:.2f} kg"
        if item.get("captura_manual"):
            peso_display += " ⚠️ [MANUAL]"

        detalles = [
            ("Animal N°:", f"Cerdo #{item['numero_animal']} (Lado {item['lado_letra']} - {item['lado']})"),
            ("Tipo de Animal:", f"{item.get('tipo_animal', 'MEI')}"),
            ("Peso Registrado:", peso_display),
            ("Depósito / Cámara:", f"{item.get('deposito_codigo', 'C1')} - {item.get('camara_destino', '')}"),
            ("Operario de Faena:", f"{item.get('operario_nombre', '')} ({item.get('operario_legajo', '')})"),
            ("Hora de Pesaje:", f"{item.get('timestamp_iso', '')[:19].replace('T', ' ')}"),
        ]

        if item.get("captura_manual"):
            detalles.append(("Autorizado Por:", item.get("autorizado_por", "SUPERVISOR")))
            detalles.append(("Motivo Falla:", item.get("motivo_contingencia", "Falla de Balanza")))

        for i, (k, v) in enumerate(detalles):
            ctk.CTkLabel(info_frame, text=k, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_MUTED).grid(row=i, column=0, sticky="w", padx=12, pady=3)
            ctk.CTkLabel(info_frame, text=v, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT).grid(row=i, column=1, sticky="w", padx=12, pady=3)

        # Estado sanitario actual
        st_txt = "CONFORME (APTA)"
        st_color = COLOR_GREEN
        if item.get("decomiso_total", False):
            st_txt = "🔴 DECOMISO TOTAL SENASA"
            st_color = COLOR_RED
        elif item.get("decomiso_parcial"):
            dp = item["decomiso_parcial"]
            st_txt = f"🟡 DECOMISO PARCIAL: {dp['motivo']} (-{dp['kilos']:.2f} kg)"
            st_color = COLOR_YELLOW

        ctk.CTkLabel(modal, text=f"ESTADO SANITARIO: {st_txt}", font=ctk.CTkFont(size=13, weight="bold"), text_color=st_color).pack(pady=4)

        # Botones de Acción
        actions_box = ctk.CTkFrame(modal, fg_color="transparent")
        actions_box.pack(fill="x", padx=20, pady=14)

        # Botón Re-imprimir ZPL
        ctk.CTkButton(
            actions_box, text="🖨️ RE-IMPRIMIR ETIQUETA ZPL", height=42, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#312E81", hover_color="#4338CA",
            command=lambda: [self._reimprimir_etiqueta_media_res(item), modal.destroy()]
        ).pack(fill="x", pady=4)

        # Botón Decomiso Parcial (DP)
        ctk.CTkButton(
            actions_box, text="🔪 APLICAR / EDITAR DECOMISO PARCIAL (DP)", height=40, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#854D0E", hover_color=COLOR_YELLOW,
            command=lambda: [modal.destroy(), self._modal_editar_dp_especifico(item)]
        ).pack(fill="x", pady=4)

        # Botón Decomiso Total (DT)
        dt_text = "🟢 QUITAR DECOMISO TOTAL" if item.get("decomiso_total", False) else "🔴 MARCAR DECOMISO TOTAL (DT)"
        ctk.CTkButton(
            actions_box, text=dt_text, height=40, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#7F1D1D", hover_color=COLOR_RED,
            command=lambda: [self._toggle_dt_media_res(item), modal.destroy()]
        ).pack(fill="x", pady=4)

        # Botón Eliminar Media (EM)
        ctk.CTkButton(
            actions_box, text="🗑️ ELIMINAR MEDIA (EM) - ANULAR PESAJE", height=40, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155", hover_color=COLOR_RED,
            command=lambda: [self._eliminar_media_res(item), modal.destroy()]
        ).pack(fill="x", pady=4)

    # -----------------------------------------------------------------------
    # MODAL DE REFERENCIAS (Tipo Animal, Motivos DP y Depósitos)
    # -----------------------------------------------------------------------
    def _abrir_modal_referencias(self):
        modal = ctk.CTkToplevel(self)
        modal.title("SPI // Referencias Oficiales de Faena")
        modal.geometry("640x520")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text="📋 CUADRO DE REFERENCIAS DE PLANTA", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38BDF8").pack(pady=(16, 12))

        cols_frame = ctk.CTkFrame(modal, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True, padx=20, pady=4)

        # Columna 1: TIPOS DE ANIMAL
        c1 = ctk.CTkFrame(cols_frame, fg_color="#060911", corner_radius=8)
        c1.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(c1, text="TIPO ANIMAL", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38BDF8").pack(pady=(8, 4))
        for t in TIPOS_ANIMAL:
            ctk.CTkLabel(c1, text=f"• {t['label']}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=10, pady=2)

        # Columna 2: MOTIVOS DECOMISO PARCIAL
        c2 = ctk.CTkFrame(cols_frame, fg_color="#060911", corner_radius=8)
        c2.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(c2, text="DECOMISO PARCIAL (DP)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FDE047").pack(pady=(8, 4))
        for m in MOTIVOS_DECOMISO_PARCIAL:
            ctk.CTkLabel(c2, text=f"• {m['label']}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=10, pady=2)

        # Columna 3: DEPÓSITOS
        c3 = ctk.CTkFrame(cols_frame, fg_color="#060911", corner_radius=8)
        c3.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(c3, text="DEPÓSITOS", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_GREEN).pack(pady=(8, 4))
        for cod, nom in DEPOSITOS_MAP.items():
            ctk.CTkLabel(c3, text=f"• {cod}: {nom}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(modal, text="ENTENDIDO", height=38, width=160, command=modal.destroy).pack(pady=14)

    def _abrir_modal_config_empresa(self):
        """Abre el editor táctil de empresa, logo y formato de etiqueta ZPL."""
        from configuracion_empresa_modal import ConfiguracionEmpresaModal

        def on_saved(cfg):
            nom = cfg.get("nombre_fantasia", "EMPRESA")
            self._set_footer_msg(f"✅ Configuración de empresa guardada: {nom}. Logo y plantilla ZPL sincronizados.")

        ConfiguracionEmpresaModal(self, on_save_callback=on_saved)

    # -----------------------------------------------------------------------
    # LOGICA DE CONFIRMACIÓN DE PESAJE E INGRESO (BALANZA / MANUAL)
    # -----------------------------------------------------------------------
    def _confirmar_ingreso_media_res(self):
        st = self.scale.get_status()
        peso = st["weight_kg"]

        if peso < 1.0:
            self._set_footer_msg("❌ Error: No hay carga sobre el gancho para pesar.", is_error=True)
            return

        self._procesar_ingreso_media_res(peso, captura_manual=False)

    def _iniciar_flujo_carga_manual(self):
        """Inicia el protocolo de contingencia por balanza rota o descalibrada."""
        num_animal = self.proximo_numero_animal
        lado = self.lado_actual
        desc = (
            f"Desbloquear carga manual de peso para Media {lado} del Cerdo #{num_animal:02d} "
            f"por contingencia técnica en balanza de gancho."
        )
        SupervisorAuthModal(
            self,
            accion_descripcion=desc,
            on_authorized_callback=self._on_supervisor_manual_autorizado
        )

    def _on_supervisor_manual_autorizado(self, supervisor: Dict[str, Any]):
        """Abre el teclado numérico de peso una vez validado el PIN de Administrador o Supervisor."""
        CargaManualPesoModal(
            self,
            supervisor_autorizante=supervisor,
            on_confirm_callback=self._on_peso_manual_confirmado
        )

    def _on_peso_manual_confirmado(self, peso: float, motivo: str, supervisor: Dict[str, Any]):
        """Ejecuta el pesaje manual autorizado y registrado."""
        nom_sup = f"{supervisor['nombre']} ({supervisor['legajo']})"
        self._procesar_ingreso_media_res(
            peso=peso,
            captura_manual=True,
            autorizado_por=nom_sup,
            motivo_contingencia=motivo
        )

    def _procesar_ingreso_media_res(
        self,
        peso: float,
        captura_manual: bool = False,
        autorizado_por: str = "",
        motivo_contingencia: str = ""
    ):
        # Verificar capacidad de la cámara seleccionada
        info_cam = CAMARAS_PLANTA[self.camara_seleccionada]
        if self.stock_camaras[self.camara_seleccionada] >= info_cam["capacidad_max_mr"]:
            self._set_footer_msg(f"❌ {self.camara_seleccionada} saturada al 100%. Elija otra cámara.", is_error=True)
            return

        num_animal = self.proximo_numero_animal
        lado = self.lado_actual
        letra = "A" if lado == "IZQ" else "B"
        lote_mr = f"MR-{lado}-{self.tropa_actual.replace('TRP-', '')}-{num_animal:02d}"
        ahora_iso = get_current_timestamp_iso()

        media_item = {
            "lote": lote_mr,
            "numero_animal": num_animal,
            "lado": lado,
            "lado_letra": letra,
            "peso_kg": peso,
            "tipo_animal": self.tipo_animal_seleccionado,
            "deposito_codigo": self.deposito_codigo_seleccionado,
            "camara_destino": self.camara_seleccionada,
            "decomiso_total": False,
            "decomiso_parcial": None,
            "captura_manual": captura_manual,
            "autorizado_por": autorizado_por,
            "motivo_contingencia": motivo_contingencia,
            "anulado": False,
            "operario_id": self.operario_id,
            "operario_nombre": self.operario_nombre,
            "operario_legajo": self.operario_legajo,
            "timestamp_iso": ahora_iso
        }

        # Guardar en SQLite WAL
        key = self.db.save_weight_record("FRIGORIFICO", "INGRESO_MEDIA_RES_CAMARA", media_item)
        media_item["idempotency_key"] = key

        # Registrar en la estructura de animales
        if num_animal not in self.animales_cargas:
            self.animales_cargas[num_animal] = {"A": None, "B": None}
        self.animales_cargas[num_animal][letra] = media_item

        # Imprimir Etiqueta Zebra ZPL
        zpl = self.printer.build_media_res_zpl(
            lote_media_res=lote_mr,
            tropa_dte=self.tropa_actual,
            lado=lado,
            kilos=peso,
            operario_id=self.operario_id,
            camara_destino=self.camara_seleccionada,
            tipo_animal=self.tipo_animal_seleccionado,
            captura_manual=captura_manual,
            autorizado_por=autorizado_por
        )
        res_prn = self.printer.send_zpl(zpl)
        if not res_prn["success"]:
            self.db.enqueue_label("CANAL_100x75", zpl)

        media_item["zpl"] = zpl
        self.ultima_media_res_emitida = media_item

        # Actualizar stock de la cámara
        self.stock_camaras[self.camara_seleccionada] += 1
        self._actualizar_info_camara()

        # Alternar lado y avanzar animal automáticamente
        if ALTERNANCIA_LADO_AUTOMATICA:
            if lado == "IZQ":
                self._set_lado("DER")  # Misma res, lado B
            else:
                self._set_lado("IZQ")  # Siguiente animal, lado A
                self.proximo_numero_animal += 1

        self._actualizar_totales_y_grilla()
        if captura_manual:
            self._set_footer_msg(f"⚠️ [PESO MANUAL] Media {letra} de #{num_animal:02d} ({peso:.2f} kg) autorizada por {autorizado_por}. Etiqueta emitida.")
        else:
            self._set_footer_msg(f"✅ Ingresada Media {letra} de #{num_animal:02d} ({peso:.2f} kg) a {self.deposito_codigo_seleccionado}. Etiqueta emitida.")

    # -----------------------------------------------------------------------
    # DECOMISOS TOTALES Y PARCIALES
    # -----------------------------------------------------------------------
    def _modal_decomiso_total(self):
        """Aplica decomiso total a la última media res o permite seleccionar."""
        st = self.scale.get_status()
        peso = st["weight_kg"]

        modal = ctk.CTkToplevel(self)
        modal.title("Dictamen Sanitario SENASA - Decomiso Total (DT)")
        modal.geometry("480x360")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text="🔴 DECOMISO TOTAL DE CANAL (DT)", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_RED).pack(pady=(16, 6))
        ctk.CTkLabel(modal, text=f"Tropa: {self.tropa_actual} | Peso: {peso:.2f} kg", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED).pack(pady=2)

        ctk.CTkLabel(modal, text="Motivo Veterinario:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(12, 2))
        combo_m = ctk.CTkComboBox(modal, values=["Sospecha Triquinosis", "Ictericia Generalizada", "Neumonía Severa", "Abscesos Múltiples"], width=320)
        combo_m.pack(anchor="w", padx=24)

        ctk.CTkLabel(modal, text="Destino Final:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(10, 2))
        combo_d = ctk.CTkComboBox(modal, values=["DIGESTOR SANITARIO", "HORNO CREMATORIO", "DESNATURALIZACIÓN"], width=320)
        combo_d.pack(anchor="w", padx=24)

        def confirmar_dt():
            motivo = combo_m.get()
            destino = combo_d.get()
            self.db.save_weight_record("FRIGORIFICO", "DECOMISO_TOTAL", {
                "tropa": self.tropa_actual,
                "motivo": motivo,
                "destino": destino,
                "peso_kg": peso,
                "operario_id": self.operario_id,
                "timestamp_iso": get_current_timestamp_iso()
            })
            zpl_dec = self.printer.build_decomiso_zpl(self.tropa_actual, motivo, destino)
            self.printer.send_zpl(zpl_dec)
            modal.destroy()
            self._set_footer_msg(f"⚠️ Decomiso Total registrado: {motivo} -> {destino}", is_error=True)

        ctk.CTkButton(modal, text="CONFIRMAR DECOMISO TOTAL", fg_color=COLOR_RED, height=44, command=confirmar_dt).pack(fill="x", padx=24, pady=20)

    def _modal_decomiso_parcial(self):
        """Permite tipificar un decomiso parcial en la media res actual."""
        modal = ctk.CTkToplevel(self)
        modal.title("Dictamen Sanitario - Decomiso Parcial (DP)")
        modal.geometry("480x380")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text="🔪 REGISTRO DE DECOMISO PARCIAL (DP)", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLOR_YELLOW).pack(pady=(16, 6))

        ctk.CTkLabel(modal, text="Motivo Oficial de Decomiso Parcial:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(12, 2))
        combo_dp = ctk.CTkComboBox(modal, values=LISTA_MOTIVOS_DP_LABELS, width=380)
        combo_dp.pack(anchor="w", padx=24)

        ctk.CTkLabel(modal, text="Kilos Afectados a Decomisar / Descontar:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(12, 2))
        txt_kilos = ctk.CTkEntry(modal, width=160, font=ctk.CTkFont(family="Consolas", size=14, weight="bold"))
        txt_kilos.insert(0, "3.50")
        txt_kilos.pack(anchor="w", padx=24)

        def confirmar_dp():
            label_sel = combo_dp.get()
            codigo = label_sel.split(" - ")[0]
            try:
                kilos_dp = float(txt_kilos.get().strip())
            except ValueError:
                kilos_dp = 0.0

            # Guardar evento en base local
            self.db.save_weight_record("FRIGORIFICO", "DECOMISO_PARCIAL", {
                "tropa": self.tropa_actual,
                "motivo_codigo": codigo,
                "motivo_descripcion": MOTIVOS_DP_MAP.get(codigo, ""),
                "kilos_decomisados": kilos_dp,
                "operario_id": self.operario_id,
                "timestamp_iso": get_current_timestamp_iso()
            })
            modal.destroy()
            self._set_footer_msg(f"🔪 Decomiso Parcial asentado: {codigo} (-{kilos_dp:.2f} kg)")

        ctk.CTkButton(modal, text="CONFIRMAR DECOMISO PARCIAL", fg_color=COLOR_YELLOW, text_color="#000000", height=44, font=ctk.CTkFont(weight="bold"), command=confirmar_dp).pack(fill="x", padx=24, pady=24)

    def _modal_editar_dp_especifico(self, item: Dict[str, Any]):
        """Abre modal para asignar o quitar DP sobre una media res específica de la grilla."""
        modal = ctk.CTkToplevel(self)
        modal.title(f"Decomiso Parcial en {item['lote']}")
        modal.geometry("460x340")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"🔪 EDITAR DECOMISO PARCIAL ({item['lote']})", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_YELLOW).pack(pady=(16, 6))

        ctk.CTkLabel(modal, text="Motivo:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(10, 2))
        combo = ctk.CTkComboBox(modal, values=LISTA_MOTIVOS_DP_LABELS, width=380)
        combo.pack(anchor="w", padx=24)

        ctk.CTkLabel(modal, text="Kilos Descontados:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(10, 2))
        txt_k = ctk.CTkEntry(modal, width=140, font=ctk.CTkFont(family="Consolas", size=13))
        prev_k = item.get("decomiso_parcial", {}).get("kilos", 3.0) if item.get("decomiso_parcial") else 3.0
        txt_k.insert(0, str(prev_k))
        txt_k.pack(anchor="w", padx=24)

        def guardar_cambio():
            cod = combo.get().split(" - ")[0]
            try:
                k = float(txt_k.get().strip())
            except ValueError:
                k = 0.0
            item["decomiso_parcial"] = {"motivo": cod, "kilos": k}
            if item.get("idempotency_key"):
                self.db.update_media_res_record(item["idempotency_key"], {"decomiso_parcial": item["decomiso_parcial"]})
            modal.destroy()
            self._actualizar_totales_y_grilla()
            self._set_footer_msg(f"✅ DP actualizado en {item['lote']}: {cod} (-{k:.2f} kg)")

        def quitar_dp():
            item["decomiso_parcial"] = None
            if item.get("idempotency_key"):
                self.db.update_media_res_record(item["idempotency_key"], {"decomiso_parcial": None})
            modal.destroy()
            self._actualizar_totales_y_grilla()
            self._set_footer_msg(f"✅ DP eliminado de {item['lote']}")

        btn_f = ctk.CTkFrame(modal, fg_color="transparent")
        btn_f.pack(fill="x", padx=24, pady=20)
        ctk.CTkButton(btn_f, text="GUARDAR DP", fg_color=COLOR_YELLOW, text_color="#000000", height=40, width=180, font=ctk.CTkFont(weight="bold"), command=guardar_cambio).pack(side="left")
        ctk.CTkButton(btn_f, text="QUITAR DP", fg_color="#334155", height=40, width=120, command=quitar_dp).pack(side="right")

    def _toggle_dt_media_res(self, item: Dict[str, Any]):
        """Alterna el estado de Decomiso Total en una res específica."""
        actual = item.get("decomiso_total", False)
        item["decomiso_total"] = not actual
        if item.get("idempotency_key"):
            self.db.update_media_res_record(item["idempotency_key"], {"decomiso_total": item["decomiso_total"]})
        self._actualizar_totales_y_grilla()
        estado_str = "MARCADA COMO DECOMISO TOTAL" if item["decomiso_total"] else "RESTABLECIDA A CONFORME"
        self._set_footer_msg(f"ℹ️ Media Res {item['lote']} {estado_str}.")

    # -----------------------------------------------------------------------
    # ELIMINAR MEDIA (EM) - ANULACIÓN DE PESAJE
    # -----------------------------------------------------------------------
    def _eliminar_media_res(self, item: Dict[str, Any]):
        """Anula un pesaje por error del operador, descuenta stock y kilos."""
        item["anulado"] = True
        cam = item.get("camara_destino", self.camara_seleccionada)
        if cam in self.stock_camaras and self.stock_camaras[cam] > 0:
            self.stock_camaras[cam] -= 1
            self._actualizar_info_camara()

        if item.get("idempotency_key"):
            self.db.update_media_res_record(item["idempotency_key"], {"anulado": True, "anulado_por": self.operario_nombre})

        self._actualizar_totales_y_grilla()
        self._set_footer_msg(f"🗑️ Media Res {item['lote']} ANULADA (EM). Se revirtió el stock de {cam}.", is_error=True)

    # -----------------------------------------------------------------------
    # RE-IMPRESIÓN DE ETIQUETA ZPL
    # -----------------------------------------------------------------------
    def _reimprimir_etiqueta_media_res(self, item: Dict[str, Any]):
        dp = item.get("decomiso_parcial")
        dp_k = dp["kilos"] if dp else 0.0
        dp_m = dp["motivo"] if dp else ""

        zpl = self.printer.build_media_res_zpl(
            lote_media_res=item["lote"],
            tropa_dte=self.tropa_actual,
            lado=item["lado"],
            kilos=item["peso_kg"],
            operario_id=item.get("operario_id", self.operario_id),
            camara_destino=item.get("camara_destino", self.camara_seleccionada),
            tipo_animal=item.get("tipo_animal", "MEI"),
            decomiso_parcial_kilos=dp_k,
            decomiso_parcial_motivo=dp_m,
            captura_manual=item.get("captura_manual", False),
            autorizado_por=item.get("autorizado_por", "")
        )
        self.printer.send_zpl(zpl)
        self._set_footer_msg(f"🔄 Etiqueta ZPL re-impresa con éxito para {item['lote']}.")

    def _reimprimir_ultima(self):
        if not self.ultima_media_res_emitida:
            self._set_footer_msg("⚠️ No hay etiqueta previa en memoria.", is_error=True)
            return
        self._reimprimir_etiqueta_media_res(self.ultima_media_res_emitida)

    # -----------------------------------------------------------------------
    # HELPERS Y CONTROLADORES DE EVENTOS
    # -----------------------------------------------------------------------
    def _set_lado(self, lado: str):
        self.lado_actual = lado
        self.btn_izq.configure(fg_color="#4338CA" if lado == "IZQ" else "#0F172A")
        self.btn_der.configure(fg_color="#4338CA" if lado == "DER" else "#0F172A")

    def _on_tipo_animal_changed(self, choice: str):
        self.tipo_animal_seleccionado = choice
        self._set_footer_msg(f"🏷️ Categoría de animal seleccionada: {choice}")

    def _on_deposito_codigo_changed(self, codigo: str):
        self.deposito_codigo_seleccionado = codigo
        nombre = DEPOSITOS_MAP.get(codigo, "Cámara Frigorífica 1")
        self.camara_seleccionada = nombre
        self.combo_camaras.set(nombre)
        self._actualizar_info_camara()

    def _on_camara_nombre_changed(self, nombre: str):
        self.camara_seleccionada = nombre
        codigo = DEPOSITOS_INVERSO_MAP.get(nombre, "C1")
        self.deposito_codigo_seleccionado = codigo
        self.combo_deposito_rapido.set(codigo)
        self._actualizar_info_camara()

    def _actualizar_info_camara(self):
        info = CAMARAS_PLANTA[self.camara_seleccionada]
        cap = info["capacidad_max_mr"]
        actual = self.stock_camaras.get(self.camara_seleccionada, 0)
        pct = actual / cap if cap > 0 else 0.0
        self.prog_bar_camara.set(pct)
        if pct > 0.95:
            self.prog_bar_camara.configure(progress_color=COLOR_RED)
        elif pct > 0.80:
            self.prog_bar_camara.configure(progress_color=COLOR_YELLOW)
        else:
            self.prog_bar_camara.configure(progress_color=COLOR_GREEN)

        self.lbl_info_camara.configure(
            text=f"Capacidad: {actual} / {cap} MR ({int(pct * 100)}%) - Libres: {max(0, cap - actual)} MR"
        )

    def _ajustar_muertos_corral(self, delta: int):
        self.muertos_corral = max(0, self.muertos_corral + delta)
        self.lbl_muertos_corral_val.configure(
            text=str(self.muertos_corral),
            text_color=COLOR_RED if self.muertos_corral > 0 else COLOR_TEXT
        )
        self._set_footer_msg(f"⚠️ Muertos en Corral actualizados: {self.muertos_corral} cabezas.")

    def _poll_scale_data(self):
        st = self.scale.get_status()
        peso = st["weight_kg"]
        estable = st["is_stable"]

        self.lbl_weight.configure(text=f"{peso:6.2f}")
        if estable and peso > 1.0:
            self.lbl_weight.configure(text_color=COLOR_GREEN)
            self.lbl_stability.configure(text="🟢 PESO ESTABLE (LISTO)", text_color=COLOR_GREEN)
            self.display_card.configure(border_color=COLOR_GREEN)
        elif peso > 1.0:
            self.lbl_weight.configure(text_color=COLOR_YELLOW)
            self.lbl_stability.configure(text="🟡 INESTABLE (OSCILANDO)", text_color=COLOR_YELLOW)
            self.display_card.configure(border_color=COLOR_YELLOW)
        else:
            self.lbl_weight.configure(text_color="#64748B")
            self.lbl_stability.configure(text="⚪ BALANZA EN CERO", text_color="#64748B")
            self.display_card.configure(border_color="#334155")

        stats = self.db.get_buffer_stats()
        self.lbl_buffer_status.configure(text=f"💾 OFFLINE: {stats['pending_sync_count']}")

        self.after(100, self._poll_scale_data)

    def _abrir_login_modal(self):
        def on_logged(user):
            self.operario_id = user["id"]
            self.operario_nombre = user["nombre"]
            self.operario_legajo = user["legajo"]
            self.btn_operario.configure(text=f"👤 {self.operario_nombre} ({self.operario_legajo})")
            self._set_footer_msg(f"✅ Sesión iniciada: {self.operario_nombre} ({user['rol']}) a las {user['login_timestamp']}")
        LoginPinModal(self, on_success_callback=on_logged)

    def _set_footer_msg(self, msg: str, is_error: bool = False):
        color = COLOR_RED if is_error else COLOR_GREEN
        self.lbl_footer.configure(text=msg, text_color=color)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="#060911", height=30, corner_radius=0)
        footer.pack(fill="x", side="bottom")

        self.lbl_footer = ctk.CTkLabel(
            footer, text="Línea de Faena y Cámaras Operativa. Conectado a Systel y Zebra ZPL.",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED
        )
        self.lbl_footer.pack(side="left", padx=16, pady=4)

        ctk.CTkLabel(
            footer, text="Capacidad Planta: 5,000 Medias Reses (800 Oreo + 4,200 Frigoríficas)",
            font=ctk.CTkFont(size=11), text_color="#475569"
        ).pack(side="right", padx=16, pady=4)

    def _on_close(self):
        self.scale.stop()
        self.destroy()


if __name__ == "__main__":
    app = IngresoMediasResesApp()
    app.mainloop()

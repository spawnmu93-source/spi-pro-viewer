"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - INGRESO DE ANIMALES Y CONTROL DT-e
Módulo de Recepción y Corrales: Validación de Hacienda vs. Documento SENASA
=============================================================================
Lógica de Negocio:
1. No hay báscula viva de camiones en frigorífico: Se controla por cabezas físicas.
2. Calcula automáticamente el PESO PROMEDIO VIVO a partir de los kilos y cabezas del DT-e.
3. Calcula el RENDIMIENTO ESTIMADO DE LA MEDIA RES (factor canal caliente ~81.5%).
4. Registra "Muertos en Traslado" y calcula los kilos perdidos en el flete.
5. Compara Cabezas Físicas (Vivos + Muertos en Traslado) vs. Cabezas del DT-e:
   -> Si coinciden: 🟢 EN_DESCANSO (Inicia cuenta regresiva de 2.5 horas antes de faena).
   -> Si hay discrepancia: 🔴 BLOQUEADA_DISCREPANCIA_DTE (Candado de faena).
=============================================================================
"""

import sys
import os
import datetime
import customtkinter as ctk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from local_db import LocalDatabase
from config_parametros import HORAS_MINIMAS_DESCANSO_CORRAL, GRANJAS_HABILITADAS
from auth_session import LoginPinModal, SessionManager, get_current_timestamp_iso

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

# Factor de rendimiento estándar de la industria para cerdo faenado (Canal Caliente / Peso Vivo)
FACTOR_RENDIMIENTO_CANAL = 0.815  # 81.5%


class IngresoAnimalesApp(ctk.CTk):
    """Pantalla táctil para operarios de corrales y descargadero de hacienda."""

    def __init__(self):
        super().__init__()

        self.title("SPI - Recepción de Hacienda // Ingreso de Animales y DT-e")
        self.geometry("1140x860")
        self.minsize(1024, 760)
        self.configure(fg_color=COLOR_BG)

        self.db = LocalDatabase()

        # Usuario de Sesión Activa
        user = SessionManager.get_current_user()
        self.operario_id = user["id"]
        self.operario_nombre = user["nombre"]
        self.operario_legajo = user["legajo"]

        # Contadores iniciales
        self.cabezas_descargadas = 110
        self.muertos_viaje = 0
        self.muertos_corral = 0

        # Métricas calculadas
        self.peso_promedio_vivo = 0.0
        self.peso_estimado_media_res = 0.0
        self.kilos_perdidos_muertos = 0.0
        self.kilos_perdidos_muertos_corral = 0.0

        self._build_ui()
        self._calcular_estado()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=64)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header,
            text="📥 SPI // RECEPCIÓN DE ANIMALES Y CONTROL DT-e SENASA",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color="#A5B4FC"
        ).pack(side="left", padx=20, pady=14)

        # Botón de Login / Cambio de Operario en Header
        self.btn_operario = ctk.CTkButton(
            header,
            text=f"👤 {self.operario_nombre} ({self.operario_legajo})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT,
            fg_color="#312E81",
            hover_color="#4338CA",
            corner_radius=6,
            height=32,
            command=self._abrir_login_modal
        )
        self.btn_operario.pack(side="right", padx=20, pady=16)

        # Contenedor Principal con Scroll si la pantalla es reducida
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=12)

        # 1. BLOQUE DOCUMENTO DT-e (Papel de Granja)
        card_dte = ctk.CTkFrame(container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_dte.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card_dte,
            text="1. DATOS DECLARADOS EN LA HOJA DT-e (SENASA)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        grid_dte = ctk.CTkFrame(card_dte, fg_color="transparent")
        grid_dte.pack(fill="x", padx=16, pady=(0, 12))

        # Fila 0: N° DT-e y N° de Tropa de Faena
        ctk.CTkLabel(grid_dte, text="N° DT-e SENASA:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", pady=4)
        self.txt_dte = ctk.CTkEntry(grid_dte, width=220, font=ctk.CTkFont(size=13))
        self.txt_dte.insert(0, "2026-0099412-1")
        self.txt_dte.grid(row=0, column=1, padx=(10, 30), pady=4)

        ctk.CTkLabel(grid_dte, text="N° de Tropa de Faena:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38BDF8").grid(row=0, column=2, sticky="w", pady=4)
        self.txt_tropa = ctk.CTkEntry(grid_dte, width=200, font=ctk.CTkFont(size=13, weight="bold"), fg_color="#060911", border_color="#38BDF8")
        self.txt_tropa.insert(0, "TRP-2026-00412")
        self.txt_tropa.grid(row=0, column=3, sticky="w", padx=(10, 0), pady=4)

        # Fila 1: Granja Origen (Exclusiva Ulapes / Chepes) y Corral Asignado
        ctk.CTkLabel(grid_dte, text="Granja Origen:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=0, sticky="w", pady=4)
        self.combo_granja = ctk.CTkComboBox(grid_dte, values=GRANJAS_HABILITADAS, width=330)
        self.combo_granja.grid(row=1, column=1, padx=(10, 30), pady=4)

        ctk.CTkLabel(grid_dte, text="Corral Asignado:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=1, column=2, sticky="w", pady=4)
        self.combo_corral = ctk.CTkComboBox(grid_dte, values=["Corral 1 (Descanso)", "Corral 2 (Descanso)", "Corral 3 (Con aspersión)", "Corral 4 (Con aspersión)"], width=200)
        self.combo_corral.grid(row=1, column=3, sticky="w", padx=(10, 0), pady=4)

        # Fila 2: Cabezas Declaradas y Kilos Declarados
        ctk.CTkLabel(grid_dte, text="Cabezas Declaradas (DT-e):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", pady=4)
        self.txt_cabezas_dte = ctk.CTkEntry(grid_dte, width=120, font=ctk.CTkFont(size=13))
        self.txt_cabezas_dte.insert(0, "110")
        self.txt_cabezas_dte.grid(row=2, column=1, sticky="w", padx=(10, 30), pady=4)
        self.txt_cabezas_dte.bind("<KeyRelease>", lambda e: self._calcular_estado())

        ctk.CTkLabel(grid_dte, text="Kilos Declarados (Granja):", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=2, sticky="w", pady=4)
        self.txt_kilos_dte = ctk.CTkEntry(grid_dte, width=140, font=ctk.CTkFont(size=13))
        self.txt_kilos_dte.insert(0, "12450.00")
        self.txt_kilos_dte.grid(row=2, column=3, sticky="w", padx=(10, 0), pady=4)
        self.txt_kilos_dte.bind("<KeyRelease>", lambda e: self._calcular_estado())

        # 2. BLOQUE DESCARGA FÍSICA EN CORRALES
        card_descarga = ctk.CTkFrame(container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_descarga.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card_descarga,
            text="2. CONTEO FÍSICO DE ANIMALES DESCARGADOS POR MANGA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FDE047"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        box_conteo = ctk.CTkFrame(card_descarga, fg_color="transparent")
        box_conteo.pack(fill="x", padx=16, pady=(0, 12))

        # Contador de Cerdos Vivos en Corral
        ctk.CTkLabel(box_conteo, text="Cerdos Vivos:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=(0, 8))
        btn_minus = ctk.CTkButton(box_conteo, text="- 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_conteo(-1))
        btn_minus.grid(row=0, column=1, padx=2)
        self.lbl_vivos = ctk.CTkLabel(box_conteo, text=str(self.cabezas_descargadas), font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), width=60)
        self.lbl_vivos.grid(row=0, column=2, padx=2)
        btn_plus = ctk.CTkButton(box_conteo, text="+ 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_conteo(+1))
        btn_plus.grid(row=0, column=3, padx=2)

        # Contador de Muertos en Traslado
        ctk.CTkLabel(box_conteo, text="Muertos Traslado:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=4, sticky="w", padx=(20, 8))
        btn_minus_m = ctk.CTkButton(box_conteo, text="- 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_muertos(-1))
        btn_minus_m.grid(row=0, column=5, padx=2)
        self.lbl_muertos = ctk.CTkLabel(
            box_conteo, text=str(self.muertos_viaje), font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), width=60, 
            text_color=COLOR_RED if self.muertos_viaje > 0 else COLOR_TEXT
        )
        self.lbl_muertos.grid(row=0, column=6, padx=2)
        btn_plus_m = ctk.CTkButton(box_conteo, text="+ 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_muertos(+1))
        btn_plus_m.grid(row=0, column=7, padx=2)

        # Contador de Muertos en Corral
        ctk.CTkLabel(box_conteo, text="Muertos Corral:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FCA5A5").grid(row=0, column=8, sticky="w", padx=(20, 8))
        btn_minus_mc = ctk.CTkButton(box_conteo, text="- 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_muertos_corral(-1))
        btn_minus_mc.grid(row=0, column=9, padx=2)
        self.lbl_muertos_corral = ctk.CTkLabel(
            box_conteo, text=str(self.muertos_corral), font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), width=60, 
            text_color=COLOR_RED if self.muertos_corral > 0 else COLOR_TEXT
        )
        self.lbl_muertos_corral.grid(row=0, column=10, padx=2)
        btn_plus_mc = ctk.CTkButton(box_conteo, text="+ 1", width=42, height=40, font=ctk.CTkFont(size=15, weight="bold"), fg_color="#334155", command=lambda: self._cambiar_muertos_corral(+1))
        btn_plus_mc.grid(row=0, column=11, padx=2)

        # 3. BLOQUE CÁLCULOS AUTOMÁTICOS: PESO PROMEDIO Y RENDIMIENTO DE MEDIA RES
        card_metricas = ctk.CTkFrame(container, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_metricas.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card_metricas,
            text="3. CÁLCULO DE PESO PROMEDIO Y RENDIMIENTO ESTIMADO (AUTOMÁTICO)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#A7F3D0"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        grid_kpis = ctk.CTkFrame(card_metricas, fg_color="transparent")
        grid_kpis.pack(fill="x", padx=16, pady=(0, 12))

        # KPI 1: Peso Promedio Vivo (DT-e)
        kpi1 = ctk.CTkFrame(grid_kpis, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=10)
        kpi1.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        ctk.CTkLabel(kpi1, text="PESO PROMEDIO VIVO", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_peso_prom = ctk.CTkLabel(kpi1, text="113.18 kg", font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color="#38BDF8")
        self.lbl_kpi_peso_prom.pack(pady=(0, 2))
        self.lbl_sub_kpi1 = ctk.CTkLabel(kpi1, text="por animal vivo (DT-e)", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED)
        self.lbl_sub_kpi1.pack(pady=(0, 8))

        # KPI 2: Rendimiento Estimado por Media Res (1 lado)
        kpi2 = ctk.CTkFrame(grid_kpis, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=10)
        kpi2.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        ctk.CTkLabel(kpi2, text="ESTIMADO MEDIA RES (1/2 CANAL)", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_media_res = ctk.CTkLabel(kpi2, text="46.12 kg", font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color=COLOR_GREEN)
        self.lbl_kpi_media_res.pack(pady=(0, 2))
        self.lbl_sub_kpi2 = ctk.CTkLabel(kpi2, text="Rendimiento 81.5% (45.5 - 46.7 kg)", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED)
        self.lbl_sub_kpi2.pack(pady=(0, 8))

        # KPI 3: Proyección Total de Canales de la Tropa
        kpi3 = ctk.CTkFrame(grid_kpis, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=10)
        kpi3.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        ctk.CTkLabel(kpi3, text="PROYECCIÓN TOTAL TROPA", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_proyeccion = ctk.CTkLabel(kpi3, text="220 Medias Reses", font=ctk.CTkFont(family="Consolas", size=20, weight="bold"), text_color="#FDE047")
        self.lbl_kpi_proyeccion.pack(pady=(0, 2))
        self.lbl_sub_kpi3 = ctk.CTkLabel(kpi3, text="~10,146 kg canal proyectados", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED)
        self.lbl_sub_kpi3.pack(pady=(0, 8))

        # KPI 4: Pérdida por Muertos en Traslado
        self.kpi4 = ctk.CTkFrame(grid_kpis, fg_color="#060911", border_color="#334155", border_width=1, corner_radius=10)
        self.kpi4.pack(side="left", expand=True, fill="both", padx=4, pady=4)
        ctk.CTkLabel(self.kpi4, text="MUERTOS EN TRASLADO", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED).pack(pady=(8, 2))
        self.lbl_kpi_muertos = ctk.CTkLabel(self.kpi4, text="0 cabezas", font=ctk.CTkFont(family="Consolas", size=20, weight="bold"), text_color=COLOR_TEXT)
        self.lbl_kpi_muertos.pack(pady=(0, 2))
        self.lbl_sub_kpi4 = ctk.CTkLabel(self.kpi4, text="0.00 kg perdidos en viaje", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED)
        self.lbl_sub_kpi4.pack(pady=(0, 8))

        # 4. BLOQUE DE ESTADO Y CANDADO DE FAENA
        self.card_status = ctk.CTkFrame(container, fg_color="#064E3B", corner_radius=12, height=80)
        self.card_status.pack(fill="x", pady=(0, 12))

        self.lbl_resultado = ctk.CTkLabel(
            self.card_status,
            text="🟢 ESTADO: HACIENDA CONFORME - EN DESCANSO EN CORRAL (2.5 HS)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLOR_GREEN
        )
        self.lbl_resultado.pack(pady=(14, 2))

        self.lbl_detalle_discrepancia = ctk.CTkLabel(
            self.card_status,
            text="Cabezas declaradas (110) == Físicas (110). Cumplido el descanso, la faena quedará habilitada.",
            font=ctk.CTkFont(size=12),
            text_color="#E2E8F0"
        )
        self.lbl_detalle_discrepancia.pack(pady=(0, 12))

        # Botón de Confirmar e Ingresar
        self.btn_guardar_ingreso = ctk.CTkButton(
            container,
            text="💾 CONFIRMAR INGRESO Y HABILITAR PARA DESCANSO",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=58,
            fg_color=COLOR_GREEN,
            hover_color="#059669",
            command=self._guardar_ingreso
        )
        self.btn_guardar_ingreso.pack(fill="x", pady=(4, 12))

    def _cambiar_conteo(self, delta: int):
        self.cabezas_descargadas = max(0, self.cabezas_descargadas + delta)
        self.lbl_vivos.configure(text=str(self.cabezas_descargadas))
        self._calcular_estado()

    def _cambiar_muertos(self, delta: int):
        self.muertos_viaje = max(0, self.muertos_viaje + delta)
        self.lbl_muertos.configure(
            text=str(self.muertos_viaje), 
            text_color=COLOR_RED if self.muertos_viaje > 0 else COLOR_TEXT
        )
        self._calcular_estado()

    def _cambiar_muertos_corral(self, delta: int):
        self.muertos_corral = max(0, self.muertos_corral + delta)
        self.lbl_muertos_corral.configure(
            text=str(self.muertos_corral), 
            text_color=COLOR_RED if self.muertos_corral > 0 else COLOR_TEXT
        )
        self._calcular_estado()

    def _calcular_estado(self):
        # 1. Obtener valores de entrada
        try:
            declaradas = int(self.txt_cabezas_dte.get().strip())
        except ValueError:
            declaradas = 0

        try:
            kilos_declarados = float(self.txt_kilos_dte.get().strip())
        except ValueError:
            kilos_declarados = 0.0

        # 2. Cálculo del Peso Promedio Vivo del DT-e
        if declaradas > 0 and kilos_declarados > 0:
            self.peso_promedio_vivo = kilos_declarados / declaradas
        else:
            self.peso_promedio_vivo = 0.0

        # 3. Cálculo de Rendimiento Estimado de Canal y Media Res (81.5%)
        peso_canal_estimado = self.peso_promedio_vivo * FACTOR_RENDIMIENTO_CANAL
        self.peso_estimado_media_res = peso_canal_estimado / 2.0

        # Rango esperado de media res (±1.5%)
        rango_min = (self.peso_promedio_vivo * 0.805) / 2.0
        rango_max = (self.peso_promedio_vivo * 0.825) / 2.0

        # 4. Impacto de Muertes (Traslado + Corral)
        self.kilos_perdidos_muertos = self.muertos_viaje * self.peso_promedio_vivo
        self.kilos_perdidos_muertos_corral = self.muertos_corral * self.peso_promedio_vivo
        total_muertes = self.muertos_viaje + self.muertos_corral
        total_kilos_perdidos = self.kilos_perdidos_muertos + self.kilos_perdidos_muertos_corral

        # 5. Proyección de Faena Efectiva (descontando muertos en corral)
        self.cabezas_faenables = max(0, self.cabezas_descargadas - self.muertos_corral)
        total_medias_reses = self.cabezas_faenables * 2
        kilos_canal_totales = self.cabezas_faenables * peso_canal_estimado

        # Actualizar Tarjetas de KPIs
        self.lbl_kpi_peso_prom.configure(text=f"{self.peso_promedio_vivo:6.2f} kg")
        self.lbl_sub_kpi1.configure(text=f"{kilos_declarados:,.1f} kg / {declaradas} cabezas")

        self.lbl_kpi_media_res.configure(text=f"{self.peso_estimado_media_res:5.2f} kg")
        self.lbl_sub_kpi2.configure(text=f"Rango esperado: {rango_min:.1f} - {rango_max:.1f} kg")

        self.lbl_kpi_proyeccion.configure(text=f"{total_medias_reses} Medias Reses")
        sub_proy = f"~{kilos_canal_totales:,.0f} kg canal ({self.cabezas_faenables} cerdos aptos)"
        if self.muertos_corral > 0:
            sub_proy += f" [-{self.muertos_corral} en corral]"
        self.lbl_sub_kpi3.configure(text=sub_proy)

        if total_muertes > 0:
            self.kpi4.configure(border_color=COLOR_RED)
            self.lbl_kpi_muertos.configure(text=f"{total_muertes} cabezas", text_color=COLOR_RED)
            self.lbl_sub_kpi4.configure(
                text=f"-{total_kilos_perdidos:,.1f} kg (Viaje: {self.muertos_viaje}, Corral: {self.muertos_corral})",
                text_color="#FCA5A5"
            )
        else:
            self.kpi4.configure(border_color="#334155")
            self.lbl_kpi_muertos.configure(text="0 cabezas", text_color=COLOR_TEXT)
            self.lbl_sub_kpi4.configure(text="0.00 kg perdidos en total", text_color=COLOR_TEXT_MUTED)

        # 6. Comparación física vs. DT-e (Candado de Faena)
        total_recibido = self.cabezas_descargadas + self.muertos_viaje
        dif = total_recibido - declaradas

        if dif == 0:
            self.card_status.configure(fg_color="#064E3B")
            self.lbl_resultado.configure(
                text="🟢 ESTADO: HACIENDA CONFORME - EN DESCANSO EN CORRAL (2.5 HS)",
                text_color=COLOR_GREEN
            )
            detalle = f"Cabezas declaradas ({declaradas}) == Físicas recibidas ({total_recibido} = {self.cabezas_descargadas} vivos + {self.muertos_viaje} muertos en viaje)."
            if self.muertos_viaje > 0:
                detalle += f" ⚠️ Bajas en viaje: {self.muertos_viaje} (-{self.kilos_perdidos_muertos:.1f} kg)."
            if self.muertos_corral > 0:
                detalle += f" ⚠️ Bajas en corral: {self.muertos_corral} (-{self.kilos_perdidos_muertos_corral:.1f} kg)."
            self.lbl_detalle_discrepancia.configure(text=detalle)
            self.btn_guardar_ingreso.configure(
                text="💾 CONFIRMAR INGRESO Y HABILITAR PARA DESCANSO",
                fg_color=COLOR_GREEN
            )
        else:
            self.card_status.configure(fg_color="#7F1D1D")
            signo = f"+{dif}" if dif > 0 else f"{dif}"
            self.lbl_resultado.configure(
                text=f"🔴 ESTADO: TROPA BLOQUEADA - DISCREPANCIA EN DT-e ({signo} CABEZAS)",
                text_color="#FCA5A5"
            )
            self.lbl_detalle_discrepancia.configure(
                text=f"Declaradas en DT-e: {declaradas} vs Físicas recibidas: {total_recibido} ({self.cabezas_descargadas} vivos + {self.muertos_viaje} muertos).\n"
                     f"⚠️ LA LÍNEA DE FAENA ESTARÁ BLOQUEADA hasta que Granja emita el DT-e rectificado de SENASA."
            )
            self.btn_guardar_ingreso.configure(
                text="⚠️ GUARDAR INGRESO COMO BLOQUEADO (ESPERANDO RECTIFICACIÓN)",
                fg_color="#B91C1C"
            )

    def _abrir_login_modal(self):
        def on_logged(user):
            self.operario_id = user["id"]
            self.operario_nombre = user["nombre"]
            self.operario_legajo = user["legajo"]
            self.btn_operario.configure(text=f"👤 {self.operario_nombre} ({self.operario_legajo})")
        LoginPinModal(self, on_success_callback=on_logged)

    def _guardar_ingreso(self):
        dte = self.txt_dte.get().strip()
        tropa = self.txt_tropa.get().strip()
        granja = self.combo_granja.get()
        corral = self.combo_corral.get()
        try:
            declaradas = int(self.txt_cabezas_dte.get().strip())
            kilos = float(self.txt_kilos_dte.get().strip())
        except ValueError:
            declaradas, kilos = 110, 12450.0

        total_recibido = self.cabezas_descargadas + self.muertos_viaje
        es_bloqueada = (total_recibido != declaradas)
        estado = "BLOQUEADA_DISCREPANCIA" if es_bloqueada else "EN_DESCANSO"
        ahora_iso = get_current_timestamp_iso()

        cabezas_faenables = max(0, self.cabezas_descargadas - self.muertos_corral)

        registro = {
            "id_tropa": tropa,
            "tropa": tropa,
            "dte_senasa": dte,
            "granja_origen": granja,
            "corral_asignado": corral,
            "cabezas_declaradas_dte": declaradas,
            "kilos_declarados_granja": kilos,
            "peso_promedio_vivo_kg": round(self.peso_promedio_vivo, 2),
            "rendimiento_estimado_canal_pct": FACTOR_RENDIMIENTO_CANAL * 100,
            "peso_estimado_media_res_kg": round(self.peso_estimado_media_res, 2),
            "cabezas_vivas_descargadas": self.cabezas_descargadas,
            "muertos_en_traslado": self.muertos_viaje,
            "kilos_perdidos_muertos_traslado_kg": round(self.kilos_perdidos_muertos, 2),
            "muertos_en_corral": self.muertos_corral,
            "kilos_perdidos_muertos_corral_kg": round(self.kilos_perdidos_muertos_corral, 2),
            "cabezas_faenables": cabezas_faenables,
            "medias_reses_proyectadas": cabezas_faenables * 2,
            "estado_tropa": estado,
            "operario_id": self.operario_id,
            "operario_nombre": self.operario_nombre,
            "operario_legajo": self.operario_legajo,
            "timestamp_captura_iso": ahora_iso,
            "hora_llegada": ahora_iso,
            "descanso_minimo_horas": HORAS_MINIMAS_DESCANSO_CORRAL
        }

        key = self.db.save_weight_record("FRIGORIFICO", "INGRESO_HACIENDA_DTE", registro)

        if es_bloqueada:
            msg = f"⚠️ Tropa {tropa} guardada con BLOQUEO por discrepancia ({key[:8]}).\nNotificando a Granja para rectificación de DT-e."
        else:
            msg = (
                f"✅ Tropa {tropa} ingresada CONFORME ({key[:8]}).\n"
                f"Granja: {granja}\n"
                f"Corral: {corral}\n"
                f"Operario: {self.operario_nombre} ({self.operario_legajo})\n"
                f"Hora: {ahora_iso}\n"
                f"Peso Promedio Vivo: {self.peso_promedio_vivo:.2f} kg\n"
                f"Media Res Estimada: {self.peso_estimado_media_res:.2f} kg\n"
                f"Medias Reses Proyectadas: {self.cabezas_descargadas * 2} canales\n"
                f"Cronómetro de descanso activado ({HORAS_MINIMAS_DESCANSO_CORRAL} hs)."
            )

        modal = ctk.CTkToplevel(self)
        modal.title("Registro de Ingreso y Proyección")
        modal.geometry("500x280")
        modal.configure(fg_color=COLOR_CARD)
        modal.transient(self)
        modal.grab_set()

        ctk.CTkLabel(modal, text=msg, font=ctk.CTkFont(size=14, weight="bold"), wraplength=440).pack(pady=(24, 16))
        ctk.CTkButton(modal, text="ACEPTAR", height=42, width=160, command=modal.destroy).pack()


if __name__ == "__main__":
    app = IngresoAnimalesApp()
    app.mainloop()

"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - EDITOR DE EMPRESA Y ETIQUETAS ZPL
Módulo: configuracion_empresa_modal.py (Configuración Flexible y Editable)
=============================================================================
Permite al administrador adecuar el sistema para cualquier frigorífico o cliente:
- Modificar Razón Social, Nombre de Fantasía, CUIT y Habilitación SENASA.
- Seleccionar y previsualizar archivo de Logo (.png, .jpg, .bmp) con conversión ZPL.
- Elegir formato de QR (AppSheet, URL o Trazabilidad).
- Emitir etiqueta ZPL de prueba para calibración inmediata.
=============================================================================
"""

import sys
import os
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from empresa_config import EmpresaConfigManager, image_to_zpl_hex
from hardware.zebra_printer import ZebraPrinter

COLOR_BG = "#0B0F19"
COLOR_CARD = "#0F172A"
COLOR_BORDER = "#334155"
COLOR_GREEN = "#10B981"
COLOR_YELLOW = "#F59E0B"
COLOR_BLUE = "#38BDF8"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"


class ConfiguracionEmpresaModal(ctk.CTkToplevel):
    """Diálogo modal interactivo para personalizar los datos de la empresa y la etiqueta ZPL."""

    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)
        self.title("SPI // Configuración de Empresa y Personalización de Etiqueta")
        self.geometry("700x720")
        self.minsize(680, 680)
        self.configure(fg_color=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self.on_save_callback = on_save_callback
        self.cfg = dict(EmpresaConfigManager.get_config())
        self.logo_path_actual = self.cfg.get("logo_path", "")
        self.printer = ZebraPrinter(mock_mode=True)

        self._build_ui()

    def _build_ui(self):
        # Header
        top_f = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=54)
        top_f.pack(fill="x", side="top")
        ctk.CTkLabel(
            top_f, text="🏷️ PERSONALIZACIÓN DE EMPRESA Y ETIQUETA ZPL",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=COLOR_BLUE
        ).pack(side="left", padx=20, pady=12)

        # Scrollable Body
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # -------------------------------------------------------------------
        # 1. DATOS FISCALES Y DE MARCA DE LA EMPRESA
        # -------------------------------------------------------------------
        sec1 = ctk.CTkFrame(body, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        sec1.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(sec1, text="🏢 IDENTIDAD DE LA EMPRESA", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A5B4FC").pack(anchor="w", padx=14, pady=(10, 4))

        # Nombre Fantasía
        ctk.CTkLabel(sec1, text="Nombre Comercial / Fantasía (Grande en Etiqueta):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(4, 2))
        self.txt_fantasia = ctk.CTkEntry(sec1, width=620, font=ctk.CTkFont(size=12))
        self.txt_fantasia.insert(0, self.cfg.get("nombre_fantasia", ""))
        self.txt_fantasia.pack(padx=14, pady=(0, 6))

        # Razón Social & CUIT
        f_row1 = ctk.CTkFrame(sec1, fg_color="transparent")
        f_row1.pack(fill="x", padx=14, pady=4)

        c1 = ctk.CTkFrame(f_row1, fg_color="transparent")
        c1.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkLabel(c1, text="Razón Social:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.txt_razon = ctk.CTkEntry(c1, font=ctk.CTkFont(size=12))
        self.txt_razon.insert(0, self.cfg.get("razon_social", ""))
        self.txt_razon.pack(fill="x")

        c2 = ctk.CTkFrame(f_row1, fg_color="transparent")
        c2.pack(side="right", expand=True, fill="x", padx=(6, 0))
        ctk.CTkLabel(c2, text="CUIT:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.txt_cuit = ctk.CTkEntry(c2, font=ctk.CTkFont(size=12))
        self.txt_cuit.insert(0, self.cfg.get("cuit", ""))
        self.txt_cuit.pack(fill="x")

        # Habilitación SENASA & Slogan
        f_row2 = ctk.CTkFrame(sec1, fg_color="transparent")
        f_row2.pack(fill="x", padx=14, pady=(4, 12))

        c3 = ctk.CTkFrame(f_row2, fg_color="transparent")
        c3.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkLabel(c3, text="N° Habilitación Oficial SENASA:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.txt_senasa = ctk.CTkEntry(c3, font=ctk.CTkFont(size=12))
        self.txt_senasa.insert(0, self.cfg.get("habilitacion_senasa", ""))
        self.txt_senasa.pack(fill="x")

        c4 = ctk.CTkFrame(f_row2, fg_color="transparent")
        c4.pack(side="right", expand=True, fill="x", padx=(6, 0))
        ctk.CTkLabel(c4, text="Slogan / Leyenda Institucional:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.txt_slogan = ctk.CTkEntry(c4, font=ctk.CTkFont(size=12))
        self.txt_slogan.insert(0, self.cfg.get("slogan", ""))
        self.txt_slogan.pack(fill="x")

        # -------------------------------------------------------------------
        # 2. LOGO DE LA EMPRESA (Carga de Imagen y Previsualización)
        # -------------------------------------------------------------------
        sec2 = ctk.CTkFrame(body, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        sec2.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(sec2, text="🖼️ LOGO DE LA EMPRESA PARA IMPRESORA ZEBRA", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_YELLOW).pack(anchor="w", padx=14, pady=(10, 4))

        logo_box = ctk.CTkFrame(sec2, fg_color="transparent")
        logo_box.pack(fill="x", padx=14, pady=6)

        # Vista previa miniatura
        self.lbl_logo_preview = ctk.CTkLabel(
            logo_box, text="[Sin Logo]", width=110, height=80, fg_color="#060911", corner_radius=6
        )
        self.lbl_logo_preview.pack(side="left", padx=(0, 14))
        self._actualizar_miniatura_logo()

        # Botones y ruta
        r_logo = ctk.CTkFrame(logo_box, fg_color="transparent")
        r_logo.pack(side="left", expand=True, fill="both")

        self.lbl_logo_path = ctk.CTkLabel(
            r_logo, text=self.logo_path_actual or "Ningún archivo seleccionado",
            font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_MUTED, anchor="w"
        )
        self.lbl_logo_path.pack(fill="x", pady=(2, 6))

        btn_row_logo = ctk.CTkFrame(r_logo, fg_color="transparent")
        btn_row_logo.pack(fill="x")

        ctk.CTkButton(
            btn_row_logo, text="📁 SELECCIONAR LOGO (.PNG / .JPG)", width=200, height=32,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color="#1E293B", hover_color="#334155",
            command=self._seleccionar_archivo_logo
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row_logo, text="❌ QUITAR", width=80, height=32,
            font=ctk.CTkFont(size=11), fg_color="#7F1D1D", hover_color="#991B1B",
            command=self._quitar_logo
        ).pack(side="left")

        # Switch para activar o desactivar logo gráfico
        self.sw_logo = ctk.CTkSwitch(
            sec2, text="Imprimir Logo Gráfico en Etiqueta (Si está apagado, imprime encabezado de texto)",
            font=ctk.CTkFont(size=11)
        )
        if self.cfg.get("habilitar_logo_grafico", True):
            self.sw_logo.select()
        else:
            self.sw_logo.deselect()
        self.sw_logo.pack(anchor="w", padx=14, pady=(6, 12))

        # -------------------------------------------------------------------
        # 3. CONFIGURACIÓN DEL CÓDIGO QR Y TEXTOS
        # -------------------------------------------------------------------
        sec3 = ctk.CTkFrame(body, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1, corner_radius=8)
        sec3.pack(fill="x", pady=6, padx=4)

        ctk.CTkLabel(sec3, text="📱 CÓDIGO QR Y DATOS DE ETIQUETA", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_GREEN).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(sec3, text="Formato de Contenido del Código QR:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(4, 2))
        self.combo_qr = ctk.CTkComboBox(
            sec3, values=["APPSHEET_ID", "URL_COMPLETA", "TEXTO_TRAZABILIDAD"], width=300, height=28
        )
        self.combo_qr.set(self.cfg.get("formato_qr", "APPSHEET_ID"))
        self.combo_qr.pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(sec3, text="Nombre del Producto Predeterminado:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(4, 2))
        self.txt_producto = ctk.CTkEntry(sec3, width=420, font=ctk.CTkFont(size=12))
        self.txt_producto.insert(0, self.cfg.get("producto_defecto", "MEDIA RES PORCINA"))
        self.txt_producto.pack(anchor="w", padx=14, pady=(0, 6))

        ctk.CTkLabel(sec3, text="Leyenda al Pie de la Etiqueta:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(4, 2))
        self.txt_pie = ctk.CTkEntry(sec3, width=620, font=ctk.CTkFont(size=12))
        self.txt_pie.insert(0, self.cfg.get("leyenda_pie", "INDUSTRIA ARGENTINA - MANTENER REFRIGERADO (0°C A 2°C)"))
        self.txt_pie.pack(anchor="w", padx=14, pady=(0, 12))

        # -------------------------------------------------------------------
        # FOOTER CON BOTONES DE ACCIÓN
        # -------------------------------------------------------------------
        foot = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0, height=64)
        foot.pack(fill="x", side="bottom")

        ctk.CTkButton(
            foot, text="💾 GUARDAR CONFIGURACIÓN", height=42, width=220,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLOR_GREEN, hover_color="#059669",
            command=self._guardar
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkButton(
            foot, text="🖨️ EMITIR ETIQUETA DE PRUEBA ZPL", height=42, width=240,
            font=ctk.CTkFont(size=12, weight="bold"), fg_color="#1E293B", hover_color="#334155",
            command=self._imprimir_prueba
        ).pack(side="left", padx=4, pady=12)

        ctk.CTkButton(
            foot, text="CANCELAR", height=42, width=100, fg_color="#334155", command=self.destroy
        ).pack(side="right", padx=20, pady=12)

        self.lbl_msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_msg.pack(side="bottom", pady=2)

    def _actualizar_miniatura_logo(self):
        if self.logo_path_actual and os.path.exists(self.logo_path_actual):
            try:
                pil_img = Image.open(self.logo_path_actual)
                pil_img.thumbnail((100, 70))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                self.lbl_logo_preview.configure(image=ctk_img, text="")
            except Exception:
                self.lbl_logo_preview.configure(image=None, text="[Error Logo]")
        else:
            self.lbl_logo_preview.configure(image=None, text="[Sin Logo]")

    def _seleccionar_archivo_logo(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Logo de la Empresa",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.logo_path_actual = file_path
            self.lbl_logo_path.configure(text=file_path)
            self._actualizar_miniatura_logo()
            self.lbl_msg.configure(text="✅ Logo cargado. Se convertirá automáticamente a ZPL al guardar.", text_color=COLOR_GREEN)

    def _quitar_logo(self):
        self.logo_path_actual = ""
        self.lbl_logo_path.configure(text="Ningún archivo seleccionado")
        self._actualizar_miniatura_logo()
        self.lbl_msg.configure(text="ℹ️ Logo eliminado. La etiqueta se imprimirá con encabezado de texto.", text_color=COLOR_TEXT_MUTED)

    def _guardar(self):
        new_cfg = {
            "nombre_fantasia": self.txt_fantasia.get().strip(),
            "razon_social": self.txt_razon.get().strip(),
            "cuit": self.txt_cuit.get().strip(),
            "habilitacion_senasa": self.txt_senasa.get().strip(),
            "slogan": self.txt_slogan.get().strip(),
            "logo_path": self.logo_path_actual,
            "habilitar_logo_grafico": bool(self.sw_logo.get()),
            "producto_defecto": self.txt_producto.get().strip(),
            "formato_qr": self.combo_qr.get(),
            "leyenda_pie": self.txt_pie.get().strip()
        }
        EmpresaConfigManager.save_config(new_cfg)
        if self.on_save_callback:
            self.on_save_callback(new_cfg)
        self.destroy()

    def _imprimir_prueba(self):
        cfg_temp = {
            "nombre_fantasia": self.txt_fantasia.get().strip(),
            "razon_social": self.txt_razon.get().strip(),
            "cuit": self.txt_cuit.get().strip(),
            "habilitacion_senasa": self.txt_senasa.get().strip(),
            "slogan": self.txt_slogan.get().strip(),
            "logo_path": self.logo_path_actual,
            "habilitar_logo_grafico": bool(self.sw_logo.get()),
            "producto_defecto": self.txt_producto.get().strip(),
            "formato_qr": self.combo_qr.get(),
            "leyenda_pie": self.txt_pie.get().strip()
        }
        if self.logo_path_actual and os.path.exists(self.logo_path_actual):
            zpl_logo, _, _ = image_to_zpl_hex(self.logo_path_actual, 130, 90)
            cfg_temp["logo_zpl_hex"] = zpl_logo

        zpl = self.printer.build_media_res_zpl(
            lote_media_res="MR-IZQ-00412-01",
            tropa_dte="TRP-2026-00412",
            lado="IZQ",
            kilos=45.80,
            tipo_animal="MEI",
            camara_destino="Cámara Frigorífica 1",
            empresa_cfg=cfg_temp
        )
        res = self.printer.send_zpl(zpl)
        self.lbl_msg.configure(text="🖨️ Etiqueta de prueba enviada a la impresora Zebra (Mock/Real).", text_color=COLOR_GREEN)


if __name__ == "__main__":
    app = ctk.CTk()
    app.geometry("400x200")
    ctk.CTkButton(app, text="Abrir Configuración", command=lambda: ConfiguracionEmpresaModal(app)).pack(pady=40)
    app.mainloop()

"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - CONFIGURACIÓN DE EMPRESA Y ETIQUETAS
Módulo: empresa_config.py (Multi-tenant, Marca Blanca y Conversor de Logo ZPL)
=============================================================================
Permite personalizar la identidad de la empresa que utiliza el sistema:
1. Razón Social, Nombre de Fantasía, CUIT y Habilitación Oficial SENASA.
2. Carga y conversión automática de Logo (.png, .jpg, .bmp) a gráficos ZPL (^GFA).
3. Configuración del Código QR (Formato para AppSheet, URL o Texto Trazable).
4. Persistencia automática en 'empresa_config.json'.
=============================================================================
"""

import os
import json
import math
from typing import Dict, Any, Optional, Tuple
from PIL import Image

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "empresa_config.json")

# Búsqueda automática de logo por defecto en el workspace
DEFAULT_LOGO_PATH = ""
curr = CONFIG_DIR
for _ in range(4):
    cand = os.path.join(curr, "Logo cerdos MINI.png")
    if os.path.exists(cand):
        DEFAULT_LOGO_PATH = cand
        break
    curr = os.path.dirname(curr)

DEFAULT_EMPRESA_CONFIG = {
    "nombre_fantasia": "FRIGORÍFICO REGIONAL",
    "razon_social": "FRIGORÍFICO Y MATADERO REGIONAL S.A.",
    "cuit": "30-71234567-9",
    "habilitacion_senasa": "OFICIAL SENASA N° 4512",
    "slogan": "INDUSTRIA ARGENTINA // CONTROL BROMATOLÓGICO",
    "logo_path": DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else "",
    "habilitar_logo_grafico": True,
    "logo_ancho_dots": 130,
    "logo_alto_dots": 90,
    "producto_defecto": "MEDIA RES PORCINA",
    "formato_qr": "APPSHEET_ID",  # Opciones: APPSHEET_ID, URL_COMPLETA, TEXTO_TRAZABILIDAD
    "url_base_qr": "https://www.appsheet.com/start/spi-stock?lote=",
    "leyenda_pie": "INDUSTRIA ARGENTINA - MANTENER REFRIGERADO (0°C A 2°C)",
    "logo_zpl_hex": ""
}


def image_to_zpl_hex(image_path: str, target_w: int = 130, target_h: int = 90) -> Tuple[str, int, int]:
    """
    Convierte cualquier archivo de imagen (PNG, JPG, BMP) en comando gráfico Zebra ZPL-II (^GFA).
    Retorna tupla: (zpl_command, width_dots, height_dots).
    """
    if not image_path or not os.path.exists(image_path):
        return "", 0, 0

    try:
        img = Image.open(image_path)

        # Si tiene transparencia (RGBA / LA / P), componer sobre fondo blanco
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            alpha = img.convert('RGBA')
            bg = Image.new('RGBA', alpha.size, (255, 255, 255, 255))
            bg.paste(alpha, mask=alpha.split()[3])
            img = bg.convert('L')
        else:
            img = img.convert('L')

        # Redimensionar conservando relación de aspecto
        img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        w, h = img.size
        bytes_per_row = math.ceil(w / 8)
        total_bytes = bytes_per_row * h

        # Binarizar: 1 = punto negro en la etiqueta, 0 = blanco
        hex_data = []
        for y in range(h):
            row_bits = 0
            for x in range(w):
                pixel = img.getpixel((x, y))
                bit = 1 if pixel < 128 else 0
                row_bits = (row_bits << 1) | bit

            # Rellenar con ceros los bits sobrantes del último byte de la fila
            padding = (bytes_per_row * 8) - w
            row_bits = row_bits << padding
            row_hex = f"{row_bits:0{bytes_per_row * 2}X}"
            hex_data.append(row_hex)

        data_str = "".join(hex_data)
        zpl_cmd = f"^GFA,{total_bytes},{total_bytes},{bytes_per_row},{data_str}"
        return zpl_cmd, w, h

    except Exception as ex:
        print(f"[ERROR] Error convirtiendo logo a ZPL: {ex}")
        return "", 0, 0


class EmpresaConfigManager:
    """Gestor singleton de configuración de empresa y personalización de etiquetas."""
    _config: Optional[Dict[str, Any]] = None

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        if cls._config is None:
            cls._load_config()
        return cls._config

    @classmethod
    def _load_config(cls):
        cfg = dict(DEFAULT_EMPRESA_CONFIG)
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg.update(saved)
            except Exception as ex:
                print(f"[WARN] No se pudo leer {CONFIG_FILE_PATH}, usando por defecto: {ex}")

        # Si hay logo configurado y no hay ZPL hex en caché o cambió el archivo, regenerar
        logo_path = cfg.get("logo_path", "")
        if logo_path and os.path.exists(logo_path) and not cfg.get("logo_zpl_hex"):
            w_dots = cfg.get("logo_ancho_dots", 130)
            h_dots = cfg.get("logo_alto_dots", 90)
            zpl_cmd, _, _ = image_to_zpl_hex(logo_path, w_dots, h_dots)
            cfg["logo_zpl_hex"] = zpl_cmd

        cls._config = cfg

    @classmethod
    def save_config(cls, new_cfg: Dict[str, Any]):
        """Guarda la configuración actualizada y regenera el ZPL del logo si es necesario."""
        current = cls.get_config()
        current.update(new_cfg)

        # Regenerar ZPL si se modificó el logo
        logo_path = current.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            w_dots = current.get("logo_ancho_dots", 130)
            h_dots = current.get("logo_alto_dots", 90)
            zpl_cmd, _, _ = image_to_zpl_hex(logo_path, w_dots, h_dots)
            current["logo_zpl_hex"] = zpl_cmd
        else:
            current["logo_zpl_hex"] = ""

        cls._config = current

        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            print(f"[OK] Configuración de empresa guardada en {CONFIG_FILE_PATH}")
        except Exception as ex:
            print(f"[ERROR] No se pudo escribir {CONFIG_FILE_PATH}: {ex}")

    @classmethod
    def build_qr_content(cls, lote: str, tropa: str, kilos: float, tipo_animal: str = "MEI") -> str:
        """Genera el contenido del código QR según el formato seleccionado."""
        cfg = cls.get_config()
        formato = cfg.get("formato_qr", "APPSHEET_ID")

        if formato == "APPSHEET_ID":
            # Directamente el ID del lote para lectura instantánea en el campo de AppSheet
            return lote
        elif formato == "URL_COMPLETA":
            base = cfg.get("url_base_qr", "https://appsheet.com/start/spi-stock?lote=")
            return f"{base}{lote}"
        else:
            # Formato estructurado delimitado para lectores industriales o escáner 2D
            return f"SPI|LOTE:{lote}|TRP:{tropa}|KG:{kilos:.2f}|TIPO:{tipo_animal}"


if __name__ == "__main__":
    cfg = EmpresaConfigManager.get_config()
    print("Configuración activa de Empresa:")
    for k, v in cfg.items():
        if k != "logo_zpl_hex":
            print(f"  {k}: {v}")
        else:
            print(f"  logo_zpl_hex: ({len(v)} caracteres)")

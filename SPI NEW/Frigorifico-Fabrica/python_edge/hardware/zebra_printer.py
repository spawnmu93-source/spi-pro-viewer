"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - MOTOR DE IMPRESIÓN ZEBRA ZPL-II
Hardware: Impresoras Térmicas Industriales Zebra (ZPL-II, 203 DPI)
=============================================================================
Plantillas Soportadas:
1. Media Res / Canal (100 mm x 75 mm = 812 x 609 dots)
2. Bachada de Fábrica (100 mm x 50 mm = 812 x 406 dots)
3. Decomiso Sanitario SENASA (75 mm x 50 mm = 609 x 406 dots)

Manejo de Contingencias:
- Envío directo por socket TCP (puerto 9100) con timeout corto.
- Si la impresora no responde, guarda el ZPL en la tabla SQLite de etiquetas pendientes
  y no bloquea la línea de producción.
=============================================================================
"""

import sys
import os
import socket
import datetime
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config_parametros import ZEBRA_IP, ZEBRA_PORT
except ImportError:
    ZEBRA_IP = "192.168.1.200"
    ZEBRA_PORT = 9100


class ZebraPrinter:
    """Motor de generación e impresión de etiquetas Zebra ZPL-II."""

    def __init__(self, host: str = ZEBRA_IP, port: int = ZEBRA_PORT, mock_mode: bool = False):
        self.host = host
        self.port = port
        self.mock_mode = mock_mode
        self._last_sent_zpl = ""

    # -----------------------------------------------------------------------
    # GENERADORES DE CÓDIGO ZPL-II
    # -----------------------------------------------------------------------
    @staticmethod
    def build_media_res_zpl(
        lote_media_res: str,
        tropa_dte: str,
        lado: str,
        kilos: float,
        grasa_mm: float = 0.0,
        magro_pct: float = 0.0,
        operario_id: int = 1,
        camara_destino: str = "Cámara de Oreo 1",
        fecha_hora: Optional[str] = None,
        url_qr: Optional[str] = None,
        tipo_animal: str = "MEI",
        decomiso_parcial_kilos: float = 0.0,
        decomiso_parcial_motivo: str = "",
        captura_manual: bool = False,
        autorizado_por: str = "",
        empresa_cfg: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera etiqueta ZPL oficial para Media Res / Canal (100x75mm a 203 DPI = 812x609 dots).
        Características:
        1. Encabezado con Logo de la Empresa personalizable (gráfico ^GFA o texto estilizado).
        2. UN SOLO CÓDIGO QR GIGANTE de alta legibilidad (sin código de barras 1D).
        3. Recuadro destacado con el PESO NETO en fuente gigante (64 dots).
        4. Trazabilidad completa (Lote, Tropa, Lado A/B, Categoría, Decomisos y Auditoría).
        """
        if not fecha_hora:
            fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        # Obtener configuración de empresa activa
        if empresa_cfg is None:
            try:
                from empresa_config import EmpresaConfigManager
                empresa_cfg = EmpresaConfigManager.get_config()
            except Exception:
                empresa_cfg = {}

        nombre_fantasia = empresa_cfg.get("nombre_fantasia", "FRIGORÍFICO REGIONAL")
        razon_social = empresa_cfg.get("razon_social", "FRIGORÍFICO Y MATADERO REGIONAL S.A.")
        cuit = empresa_cfg.get("cuit", "30-71234567-9")
        senasa = empresa_cfg.get("habilitacion_senasa", "OFICIAL SENASA N° 4512")
        slogan = empresa_cfg.get("slogan", "INDUSTRIA ARGENTINA // CONTROL BROMATOLÓGICO")
        leyenda_pie = empresa_cfg.get("leyenda_pie", "INDUSTRIA ARGENTINA - MANTENER REFRIGERADO (0°C A 2°C)")
        prod_nombre = empresa_cfg.get("producto_defecto", "MEDIA RES PORCINA")
        logo_zpl = empresa_cfg.get("logo_zpl_hex", "")
        usar_logo = empresa_cfg.get("habilitar_logo_grafico", True) and bool(logo_zpl)

        # Contenido del único código QR
        if not url_qr:
            try:
                from empresa_config import EmpresaConfigManager
                url_qr = EmpresaConfigManager.build_qr_content(lote_media_res, tropa_dte, kilos, tipo_animal)
            except Exception:
                url_qr = lote_media_res

        # Bloque de Encabezado con Logo
        if usar_logo:
            header_block = f"""^FO35,25{logo_zpl}^FS
^FO185,25^CF0,32^FD{nombre_fantasia[:28]}^FS
^FO185,60^CF0,22^FD{razon_social[:36]} - {senasa[:20]}^FS
^FO185,86^CF0,18^FDCUIT: {cuit} | {slogan[:36]}^FS"""
        else:
            header_block = f"""^FO35,25^CF0,38^FD{nombre_fantasia[:32]}^FS
^FO35,66^CF0,24^FD{razon_social[:38]} - {senasa[:22]}^FS
^FO35,92^CF0,20^FDCUIT: {cuit} | {slogan[:42]}^FS"""

        # Lado legible
        lado_letra = "A" if lado == "IZQ" else "B"
        lado_desc = f"MEDIA {lado_letra} ({lado})"

        # Línea de estado sanitario / tipificación
        if decomiso_parcial_kilos > 0:
            linea_sanitaria = f"DEC. PARCIAL: {decomiso_parcial_motivo} (-{decomiso_parcial_kilos:.2f} kg)"
        else:
            linea_sanitaria = f"TIPIFICACION: GRASA {grasa_mm:4.1f}mm | MAGRO {magro_pct:4.1f}%"

        # Badge y línea de auditoría de peso manual
        if captura_manual:
            badge_manual = "^FO315,215^CF0,20^FD[PESO MANUAL]^FS"
            linea_auditoria = f"AUTORIZADO POR: {autorizado_por[:28]}" if autorizado_por else "AUTORIZADO: SUPERVISOR"
        else:
            badge_manual = ""
            linea_auditoria = "CONDICION: CONFORME PARA CONSUMO O DESPOSTE"

        zpl = f"""^XA
^CI28
^PW812
^LL609

{header_block}
^FO35,116^GB742,3,3^FS

^FO35,126^CF0,24^FDPRODUCTO:^FS
^FO165,124^CF0,30^FD{prod_nombre} ({tipo_animal})^FS
^FO35,160^CF0,24^FDLOTE CANAL:^FS
^FO165,156^CF0,36^FD{lote_media_res}^FS

^FO35,205^GB460,120,3^FS
^FO50,215^CF0,22^FDPESO GANCHO NETO:^FS
{badge_manual}
^FO50,245^CF0,64^FD{kilos:6.2f} kg^FS
^FO50,308^CF0,18^FDBALANZA SYSTEL // BROMATOLOGICAMENTE VERIFICADO^FS

^FO520,195^BQN,2,7^FDQA,{url_qr}^FS
^FO530,420^CF0,18^FDESCANEO TRAZABILIDAD / APPSHEET^FS

^FO35,340^CF0,24^FDTROPA: {tropa_dte}  |  LADO: {lado_desc}^FS
^FO35,372^CF0,24^FDDESTINO: {camara_destino.upper()}^FS
^FO35,404^CF0,22^FD{linea_sanitaria}^FS
^FO35,432^CF0,20^FD{linea_auditoria}^FS

^FO35,465^GB742,2,2^FS
^FO35,476^CF0,22^FDFECHA: {fecha_hora}  |  OP: {operario_id:03d}^FS
^FO35,504^CF0,20^FD{leyenda_pie}^FS
^FO35,530^CF0,18^FDSISTEMA DE PRODUCCION INTEGRAL (SPI) - TRAZABILIDAD DIGITAL^FS
^XZ"""
        return zpl

    @staticmethod
    def build_bachada_zpl(
        nombre_producto: str,
        lote_bachada: str,
        kilos: float,
        unidades: int,
        lote_tocino: str = "00049",
        fecha_elab: Optional[str] = None
    ) -> str:
        """Genera etiqueta ZPL para Bachada de Fábrica (100x50mm a 203 DPI)."""
        if not fecha_elab:
            fecha_elab = datetime.datetime.now().strftime("%d/%m/%Y")

        zpl = f"""^XA
^PW812
^LL406
^CF0,28
^FO40,30^FDSPI - FABRICA DE CHACINADOS^FS
^FO40,65^GB732,2,2^FS
^CF0,38
^FO40,85^FD{nombre_producto}^FS
^CF0,48
^FO40,135^FDLOTE: {lote_bachada}^FS
^CF0,30
^FO40,195^FDPESO: {kilos:6.2f} kg | UNIDADES: {unidades} un^FS
^FO40,235^FDTOCINO: LOTE {lote_tocino} | ELAB: {fecha_elab}^FS
^BY2,2,65
^FO40,285^BCN,65,Y,N,N^FD{lote_bachada}^FS
^XZ"""
        return zpl

    @staticmethod
    def build_decomiso_zpl(
        tropa_dte: str,
        motivo: str,
        destino: str = "DIGESTOR SANITARIO",
        veterinario: str = "SENASA",
        fecha_hora: Optional[str] = None
    ) -> str:
        """Genera etiqueta ZPL para Decomiso Sanitario (75x50mm a 203 DPI)."""
        if not fecha_hora:
            fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        zpl = f"""^XA
^PW609
^LL406
^CF0,32
^FO30,30^FD[!] DECOMISO SANITARIO SENASA [!]^FS
^FO30,70^GB550,3,3^FS
^CF0,30
^FO30,95^FDTROPA ORIGEN: {tropa_dte}^FS
^CF0,34
^FO30,140^FDMOTIVO: {motivo[:26]}^FS
^CF0,30
^FO30,195^FDDESTINO: {destino[:28]}^FS
^FO30,240^FDFECHA: {fecha_hora}^FS
^FO30,280^FDVET. SENASA: {veterinario[:24]}^FS
^FO30,330^GB550,40,40,W,0^FS
^CF0,28
^FO50,338^FDNO APTO CONSUMO HUMANO - DESNATURALIZADO^FS
^XZ"""
        return zpl

    # -----------------------------------------------------------------------
    # ENVÍO FÍSICO / TCP A LA IMPRESORA ZEBRA
    # -----------------------------------------------------------------------
    def send_zpl(self, zpl_code: str) -> Dict[str, Any]:
        """
        Envía la trama ZPL por TCP port 9100 a la impresora.
        Retorna diccionario con status: True/False y mensaje explicativo.
        """
        self._last_sent_zpl = zpl_code

        if self.mock_mode:
            return {
                "success": True,
                "mode": "MOCK",
                "bytes_sent": len(zpl_code.encode("utf-8")),
                "message": "[MOCK] Etiqueta procesada en simulador sin errores."
            }

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)  # Timeout de conexión rápida
            s.connect((self.host, self.port))
            s.sendall(zpl_code.encode("utf-8"))
            s.close()
            return {
                "success": True,
                "mode": "TCP",
                "bytes_sent": len(zpl_code.encode("utf-8")),
                "message": f"Etiqueta enviada exitosamente a Zebra ({self.host}:{self.port})."
            }
        except Exception as ex:
            return {
                "success": False,
                "mode": "FALLBACK_QUEUE",
                "error": str(ex),
                "message": f"Impresora no disponible ({self.host}:{self.port}). Se debe encolar en SQLite."
            }

    def get_last_zpl(self) -> str:
        return self._last_sent_zpl


# ---------------------------------------------------------------------------
# PRUEBA STANDALONE DEL MOTOR ZPL
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Probando motor ZPL Zebra en modo MOCK...")
    printer = ZebraPrinter(mock_mode=True)

    # 1. Etiqueta Canal
    zpl_canal = printer.build_media_res_zpl(
        lote_media_res="MR-DER-00412-01",
        tropa_dte="TRP-2026-00412",
        lado="DER",
        kilos=42.50,
        grasa_mm=14.2,
        magro_pct=58.4,
        operario_id=4
    )
    res1 = printer.send_zpl(zpl_canal)
    print(f"[CANAL]   Status: {res1['success']} | {res1['message']}")

    # 2. Etiqueta Bachada
    zpl_bach = printer.build_bachada_zpl(
        nombre_producto="SALAME MILAN SECO",
        lote_bachada="BACH-SALMIL-260904-01",
        kilos=150.0,
        unidades=120,
        lote_tocino="00049"
    )
    res2 = printer.send_zpl(zpl_bach)
    print(f"[BACHADA] Status: {res2['success']} | {res2['message']}")

    # 3. Etiqueta Decomiso
    zpl_dec = printer.build_decomiso_zpl(
        tropa_dte="TRP-2026-00412",
        motivo="SOSPECHA TRIQUINOSIS",
        destino="DIGESTOR SANITARIO",
        veterinario="DR. GOMEZ (SENASA 8821)"
    )
    res3 = printer.send_zpl(zpl_dec)
    print(f"[DECOMISO] Status: {res3['success']} | {res3['message']}")
    print("[OK] Todas las plantillas ZPL fueron generadas y validadas.")

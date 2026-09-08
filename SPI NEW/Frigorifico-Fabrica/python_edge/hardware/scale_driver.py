"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - DRIVER DE BALANZAS INDUSTRIALES
Hardware: Balanzas Systel (Cuora Gancho) y Moretti (LAP Batea / Plataforma)
=============================================================================
Características:
1. Multi-protocolo: Decodifica tramas continuas Systel y Moretti.
2. Hilo daemon asíncrono no bloqueante: La interfaz gráfica nunca se congela.
3. Filtro de estabilización (Debounce): Certifica peso firme tras N lecturas estables.
4. Auto-reconexión en caliente: Si se desconecta el cable USB-Serie, reintenta en background.
5. Modo Simulación / Mock integrado: Permite pruebas de desarrollo sin hardware físico.
=============================================================================
"""

import sys
import os
import time
import threading
import re
from typing import Dict, Any, Optional

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False

# Importar configuración de parámetros
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config_parametros import (
        PESO_MINIMO_VALIDO_KG,
        DEBOUNCE_LECTURAS_CONSECUTIVAS,
        TOLERANCIA_ESTABILIDAD_KG,
        TIMEOUT_LECTURA_SERIAL_SEG
    )
except ImportError:
    PESO_MINIMO_VALIDO_KG = 1.0
    DEBOUNCE_LECTURAS_CONSECUTIVAS = 3
    TOLERANCIA_ESTABILIDAD_KG = 0.05
    TIMEOUT_LECTURA_SERIAL_SEG = 1.0


class ScaleDriver:
    """Driver industrial para captura de peso por puerto serie RS-232."""

    def __init__(self, port: str = "COM3", baudrate: int = 9600, protocol: str = "SYSTEL", mock_mode: bool = False):
        self.port = port
        self.baudrate = baudrate
        self.protocol = protocol.upper()
        self.mock_mode = mock_mode or not SERIAL_AVAILABLE

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Estado actual de la balanza
        self._current_weight: float = 0.0
        self._is_stable: bool = False
        self._is_connected: bool = False
        self._last_raw_frame: str = ""
        self._last_read_timestamp: float = 0.0
        self._error_msg: str = ""

        # Buffer para debounce / estabilización
        self._recent_readings = []

        # Instancia serie
        self._ser = None

    def start(self):
        """Inicia el hilo de lectura continua."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True, name=f"ScaleWorker-{self.protocol}")
        self._thread.start()

    def stop(self):
        """Detiene el hilo y libera el puerto serie."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._close_serial()

    def get_status(self) -> Dict[str, Any]:
        """Devuelve una instantánea thread-safe del estado actual de la balanza."""
        with self._lock:
            # Si pasaron más de 2.5s sin recibir tramas válidas, marcar como desconectado
            if not self.mock_mode and (time.time() - self._last_read_timestamp > 2.5):
                self._is_connected = False

            return {
                "weight_kg": round(self._current_weight, 2),
                "is_stable": self._is_stable,
                "is_connected": self._is_connected,
                "protocol": self.protocol,
                "port": self.port,
                "raw_frame": self._last_raw_frame,
                "mock_mode": self.mock_mode,
                "timestamp": self._last_read_timestamp,
                "error": self._error_msg
            }

    # -----------------------------------------------------------------------
    # LOOP PRINCIPAL DE LECTURA Y CONEXIÓN
    # -----------------------------------------------------------------------
    def _read_loop(self):
        """Hilo daemon que mantiene la conexión y procesa bytes del puerto."""
        while self._running:
            if self.mock_mode:
                self._mock_reading_step()
                time.sleep(0.1)
                continue

            if not self._ser or not self._ser.is_open:
                self._connect_serial()
                if not self._is_connected:
                    time.sleep(2.0)  # Espera antes de reintentar conexión
                    continue

            try:
                # Leer bytes del buffer serie
                raw_bytes = self._read_raw_frame()
                if raw_bytes:
                    parsed = self._parse_frame(raw_bytes)
                    if parsed is not None:
                        self._update_readings(parsed["weight"], parsed["stable"], parsed["raw"])
                else:
                    time.sleep(0.05)
            except Exception as ex:
                with self._lock:
                    self._error_msg = f"Error I/O serie: {str(ex)}"
                    self._is_connected = False
                self._close_serial()
                time.sleep(1.0)

    def _connect_serial(self):
        """Intenta abrir el puerto serie configurado."""
        if not SERIAL_AVAILABLE:
            self.mock_mode = True
            return

        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=TIMEOUT_LECTURA_SERIAL_SEG
            )
            with self._lock:
                self._is_connected = True
                self._error_msg = ""
                self._last_read_timestamp = time.time()
        except Exception as ex:
            with self._lock:
                self._is_connected = False
                self._error_msg = f"No se pudo abrir {self.port}: {str(ex)}"

    def _close_serial(self):
        """Cierra el puerto de forma segura."""
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
        with self._lock:
            self._is_connected = False

    # -----------------------------------------------------------------------
    # LECTURA DE TRAMAS SEGÚN DELIMITADORES
    # -----------------------------------------------------------------------
    def _read_raw_frame(self) -> bytes:
        """Lee una trama completa basada en delimitadores STX/ETX o saltos de línea."""
        if not self._ser:
            return b""

        # Protocolo Systel: delimitado por \x02 (STX) y \x03 (ETX)
        if self.protocol == "SYSTEL":
            # Buscar byte de inicio STX
            b = self._ser.read(1)
            if b != b'\x02':
                return b""
            # Leer hasta ETX (\x03) o máximo 32 bytes
            payload = self._ser.read_until(b'\x03', size=32)
            return b'\x02' + payload

        # Protocolo Moretti: líneas ASCII con \r\n o \x03
        else:
            line = self._ser.readline()
            return line

    # -----------------------------------------------------------------------
    # PARSEADORES DE PROTOCOLO (SYSTEL & MORETTI)
    # -----------------------------------------------------------------------
    def _parse_frame(self, raw: bytes) -> Optional[Dict[str, Any]]:
        """Interpreta los bytes según el protocolo de la balanza."""
        try:
            raw_str = raw.decode("latin1", errors="ignore").strip()
            if not raw_str:
                return None

            if self.protocol == "SYSTEL":
                return self._parse_systel(raw_str)
            else:
                return self._parse_moretti(raw_str)
        except Exception as ex:
            with self._lock:
                self._error_msg = f"Parse error: {str(ex)}"
            return None

    def _parse_systel(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Formato Systel Cuora Gancho Continuo:
        [STX][STATUS][SIGNO][PESO 6 DIGITOS][TARA 6 DIGITOS][ETX]
        Ej: \x02S+008450000000\x03 -> 84.50 kg (Estable)
        """
        # Limpiar caracteres de control
        clean = raw.replace('\x02', '').replace('\x03', '')
        if len(clean) < 8:
            return None

        status_char = clean[0].upper()
        sign_char = clean[1]
        weight_digits = clean[2:8]

        try:
            val = float(weight_digits) / 100.0  # Systel transmite centésimas de kg
            if sign_char == '-':
                val = -val

            is_stable = (status_char == 'S')  # 'S' = Estable, 'M' = Movimiento
            return {"weight": val, "stable": is_stable, "raw": raw}
        except ValueError:
            return None

    def _parse_moretti(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Formato Moretti LAP / Batea:
        ASCII continuo con regex flexible:
        Ej: 'P+045.250kg' o '+045.25' o 'ST,GS,+0045.25kg'
        """
        clean = raw.replace('\x02', '').replace('\x03', '')
        match = re.search(r'([+-]?\d+\.?\d*)\s*(?:kg)?', clean, re.IGNORECASE)
        if match:
            try:
                weight_val = float(match.group(1))
                # Detecta estabilidad si contiene 'ST' o 'S'
                is_stable = True
                if "US" in clean or "M" in clean:
                    is_stable = False
                return {"weight": weight_val, "stable": is_stable, "raw": raw}
            except ValueError:
                return None
        return None

    # -----------------------------------------------------------------------
    # FILTRO DE ESTABILIZACIÓN (DEBOUNCE INDUSTRIAL)
    # -----------------------------------------------------------------------
    def _update_readings(self, weight: float, raw_stable: bool, raw_str: str):
        """Aplica la ventana de lecturas consecutivas para certificar peso estable."""
        now = time.time()
        with self._lock:
            self._last_read_timestamp = now
            self._is_connected = True
            self._last_raw_frame = raw_str

            # Ignorar ruido por debajo de umbral
            if abs(weight) < PESO_MINIMO_VALIDO_KG:
                self._current_weight = 0.0
                self._is_stable = False
                self._recent_readings.clear()
                return

            self._recent_readings.append(weight)
            if len(self._recent_readings) > DEBOUNCE_LECTURAS_CONSECUTIVAS:
                self._recent_readings.pop(0)

            # Verificar si las últimas N lecturas difieren en menos de la tolerancia
            if len(self._recent_readings) == DEBOUNCE_LECTURAS_CONSECUTIVAS:
                min_w = min(self._recent_readings)
                max_w = max(self._recent_readings)
                if (max_w - min_w) <= TOLERANCIA_ESTABILIDAD_KG and raw_stable:
                    self._current_weight = round(sum(self._recent_readings) / len(self._recent_readings), 2)
                    self._is_stable = True
                else:
                    self._current_weight = round(weight, 2)
                    self._is_stable = False
            else:
                self._current_weight = round(weight, 2)
                self._is_stable = False

    # -----------------------------------------------------------------------
    # SIMULACIÓN / MOCK AUTOMÁTICO PARA DESARROLLO
    # -----------------------------------------------------------------------
    def _mock_reading_step(self):
        """Genera oscilaciones simuladas que estabilizan para pruebas de software."""
        now = time.time()
        cycle = int(now) % 15  # Ciclo de 15 segundos

        # 0 a 3s: oscilación previa al gancho (inestable)
        # 3 a 12s: peso colgado firme (estable)
        # 12 a 15s: retiro de canal (vuelve a cero)
        if cycle < 3:
            weight = 42.0 + (now * 7 % 2.5)
            stable = False
            raw = f"\x02M+{int(weight*100):06d}000000\x03"
        elif cycle < 12:
            weight = 42.50
            stable = True
            raw = f"\x02S+004250000000\x03"
        else:
            weight = 0.0
            stable = True
            raw = f"\x02S+000000000000\x03"

        self._update_readings(weight, stable, raw)


# ---------------------------------------------------------------------------
# PRUEBA STANDALONE DEL DRIVER
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Iniciando prueba de ScaleDriver en modo MOCK...")
    driver = ScaleDriver(port="COM3", baudrate=9600, protocol="SYSTEL", mock_mode=True)
    driver.start()

    try:
        for _ in range(10):
            st = driver.get_status()
            simb = "[ESTABLE]  " if st["is_stable"] else "[INESTABLE]"
            print(f"[{time.strftime('%H:%M:%S')}] Peso: {st['weight_kg']:6.2f} kg | {simb} | Conectado: {st['is_connected']}")
            time.sleep(0.5)
    finally:
        driver.stop()
        print("[OK] Driver detenido correctamente.")

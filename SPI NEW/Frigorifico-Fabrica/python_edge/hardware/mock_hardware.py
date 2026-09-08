"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - SIMULADOR Y MOCK DE HARDWARE
Servidor virtual de impresora Zebra y generador de tramas seriales Systel/Moretti
=============================================================================
Permite ejecutar y verificar las terminales táctiles de Frigorífico y Fábrica
en entornos de desarrollo sin cables ni balanzas físicas conectadas.
=============================================================================
"""

import sys
import os
import socket
import threading
import time

class MockZebraServer:
    """Servidor TCP local (puerto 9100) que simula una impresora Zebra real."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9100):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.received_labels = []
        self._thread = None

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"[MOCK-ZEBRA] Servidor TCP escuchando en {self.host}:{self.port}")

    def _listen_loop(self):
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                data = b""
                while True:
                    chunk = client.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                client.close()

                zpl_text = data.decode("utf-8", errors="ignore")
                self.received_labels.append({
                    "timestamp": time.time(),
                    "zpl": zpl_text,
                    "bytes": len(data)
                })
                print(f"[MOCK-ZEBRA] Etiqueta ZPL recibida desde {addr} ({len(data)} bytes).")
            except Exception:
                break

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        print("[MOCK-ZEBRA] Servidor TCP detenido.")

    def get_last_label(self):
        return self.received_labels[-1] if self.received_labels else None


if __name__ == "__main__":
    print("[INFO] Iniciando MockZebraServer en localhost:9100 para pruebas...")
    server = MockZebraServer(host="127.0.0.1", port=9100)
    server.start()

    # Enviar una etiqueta de prueba a través de un socket normal
    time.sleep(0.5)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9100))
    s.sendall(b"^XA^FO50,50^FDHOLA MUNDO ZPL^FS^XZ")
    s.close()

    time.sleep(0.5)
    last = server.get_last_label()
    if last:
        print(f"[OK] Etiqueta verificada: {last['zpl']}")
    server.stop()

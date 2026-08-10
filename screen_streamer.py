import io
import time
import base64
import threading
from PIL import Image, ImageGrab
import urllib.parse

# Intentar usar mss para captura ultrarrápida; fallback a PIL ImageGrab
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

# Intentar usar websocket-client
try:
    import websocket
    HAS_WEBSOCKET_CLIENT = True
except ImportError:
    HAS_WEBSOCKET_CLIENT = False

RENDER_WS_HOST = "spi-pro-viewer.onrender.com"

class ScreenStreamer:
    def __init__(self, store_name="Local 1", fps=5, quality=60):
        self.store_name = store_name
        self.fps = fps
        self.interval = 1.0 / fps
        self.quality = quality
        self.running = False
        self.thread = None
        self.ws = None

    def capture_frame_base64(self):
        try:
            if HAS_MSS:
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            else:
                img = ImageGrab.grab()
                if img.mode != 'RGB':
                    img = img.convert('RGB')

            # Redimensionar a 480p (854x480 manteniendo aspecto si es posible, o 854x480 fijo)
            img.thumbnail((854, 480), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
            b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_data}"
        except Exception as e:
            print(f"Error al capturar pantalla: {e}")
            return None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        print(f"🎥 Iniciada transmisión en vivo 480p de pantalla para: {self.store_name}")

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def _stream_loop(self):
        encoded_store = urllib.parse.quote(self.store_name)
        ws_url = f"wss://{RENDER_WS_HOST}/ws/stream/{encoded_store}"

        while self.running:
            try:
                if HAS_WEBSOCKET_CLIENT:
                    self._run_websocket_client(ws_url)
                else:
                    print("Librería websocket-client no encontrada. Reintentando...")
                    time.sleep(5)
            except Exception as e:
                print(f"Error en bucle de streaming: {e}. Reintentando en 5s...")
                time.sleep(5)

    def _run_websocket_client(self, ws_url):
        def on_open(ws):
            print(f"🟢 Conectado canal de streaming en vivo a Render ({self.store_name})")

        def on_error(ws, error):
            print(f"⚠️ Error WebSocket Streaming: {error}")

        def on_close(ws, close_status_code, close_msg):
            print(f"🔴 Conexión WebSocket de streaming cerrada ({self.store_name})")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close
        )

        # Hilo para enviar fotogramas mientras la conexión esté abierta
        def send_frames():
            while self.running and self.ws and self.ws.sock and self.ws.sock.connected:
                t0 = time.time()
                frame_b64 = self.capture_frame_base64()
                if frame_b64:
                    try:
                        self.ws.send(frame_b64)
                    except Exception as e:
                        print(f"Error al enviar frame: {e}")
                        break
                elapsed = time.time() - t0
                sleep_time = max(0.01, self.interval - elapsed)
                time.sleep(sleep_time)

        ws_thread = threading.Thread(target=send_frames, daemon=True)
        
        # Iniciar websocket app de forma bloqueante para el hilo secundario
        self.ws.run_forever(ping_interval=10, ping_timeout=5)

def start_screen_streamer_async(store_name="Local 1"):
    """Inicia la transmisión de pantalla en segundo plano para la app de escritorio."""
    streamer = ScreenStreamer(store_name=store_name, fps=5, quality=60)
    streamer.start()
    return streamer

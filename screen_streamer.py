import io
import time
import base64
import threading
import requests
import urllib.parse
from PIL import Image, ImageGrab

# Intentar mss para capturas ultrarrápidas
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

RENDER_HOST = "spi-pro-viewer.onrender.com"

class ScreenStreamer:
    def __init__(self, store_name="Local 1", fps=4, quality=55):
        self.store_name = store_name
        self.fps = fps
        self.interval = 1.0 / fps
        self.quality = quality
        self.running = False
        self.thread = None

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

            # Redimensionar a 480p (854x480)
            img.thumbnail((854, 480), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
            b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_data}"
        except Exception as e:
            return None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        print(f"🎥 Transmisión de pantalla activada para: {self.store_name}")

    def stop(self):
        self.running = False

    def _stream_loop(self):
        encoded_store = urllib.parse.quote(self.store_name)
        post_url = f"https://{RENDER_HOST}/api/stream/upload/{encoded_store}"

        while self.running:
            t0 = time.time()
            frame_b64 = self.capture_frame_base64()
            if frame_b64:
                try:
                    # Enviar fotograma mediante HTTP POST ultra-rápido
                    requests.post(
                        post_url, 
                        data=frame_b64.encode('utf-8'), 
                        headers={'Content-Type': 'text/plain'}, 
                        timeout=3
                    )
                except Exception as e:
                    # Ante cualquier fallo de red temporal, pausar brevemente y reintentar
                    time.sleep(2)
            
            elapsed = time.time() - t0
            sleep_time = max(0.05, self.interval - elapsed)
            time.sleep(sleep_time)

def start_screen_streamer_async(store_name="Local 1"):
    """Inicia la transmisión de pantalla en segundo plano para la app de escritorio."""
    streamer = ScreenStreamer(store_name=store_name, fps=4, quality=55)
    streamer.start()
    return streamer

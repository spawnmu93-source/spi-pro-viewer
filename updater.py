import os
import sys
import json
import time
import requests
import subprocess
import threading
import tempfile
import customtkinter as ctk
from tkinter import messagebox

UPDATE_SERVER_URL = "https://spi-pro-viewer.onrender.com/api/update/check"

def parse_version(v_str):
    """Convierte una cadena tipo '1.8.2' a tupla de enteros (1, 8, 2) para comparación precisa."""
    try:
        clean = v_str.lower().replace('v', '').strip()
        return tuple(int(x) for x in clean.split('.') if x.isdigit())
    except Exception:
        return (0, 0, 0)

def is_newer_version(latest_str, current_str):
    """Devuelve True si la versión latest es estrictamente mayor que la versión actual."""
    return parse_version(latest_str) > parse_version(current_str)

class AutoUpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, latest_version, current_version, changelog, download_url, filename):
        super().__init__(parent)
        
        self.title("Actualizando Sistema SPI")
        
        # MODO PANTALLA COMPLETA KIOSCO (Cubre 100% del escritorio)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Obtener dimensiones totales de la pantalla
        scr_width = self.winfo_screenwidth()
        scr_height = self.winfo_screenheight()
        self.geometry(f"{scr_width}x{scr_height}+0+0")
        
        self.configure(fg_color="#121212")
        
        self.latest_version = latest_version
        self.current_version = current_version
        self.download_url = download_url
        self.filename = filename
        
        # Bloquear cualquier intento de cierre
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Contenedor centralizado
        center_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=16, border_width=1, border_color="#2ECC71")
        center_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.75, relheight=0.6)
        
        # UI Elements
        lbl_icon = ctk.CTkLabel(center_frame, text="🚀", font=ctk.CTkFont(size=60))
        lbl_icon.pack(pady=(30, 10))
        
        lbl_title = ctk.CTkLabel(
            center_frame, 
            text=f"Instalando Actualización v{latest_version}", 
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2ECC71"
        )
        lbl_title.pack(pady=5)
        
        lbl_sub = ctk.CTkLabel(
            center_frame, 
            text=f"El sistema se actualizará e iniciará automáticamente al finalizar. No apague la PC.", 
            font=ctk.CTkFont(size=14),
            text_color="#BDC3C7"
        )
        lbl_sub.pack(pady=5)
        
        # Caja de changelog
        frame_change = ctk.CTkFrame(center_frame, fg_color="#141414", corner_radius=8)
        frame_change.pack(fill="both", expand=True, padx=30, pady=15)
        
        lbl_ch_title = ctk.CTkLabel(frame_change, text="Novedades de la versión:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3498DB", anchor="w")
        lbl_ch_title.pack(fill="x", padx=15, pady=(10, 4))
        
        lbl_ch_text = ctk.CTkLabel(frame_change, text=changelog, font=ctk.CTkFont(size=13), text_color="#ECF0F1", justify="left", wraplength=550, anchor="w")
        lbl_ch_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Barra de Progreso
        self.progress_bar = ctk.CTkProgressBar(center_frame, width=500, height=16, progress_color="#2ECC71")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 8))
        
        self.lbl_status = ctk.CTkLabel(center_frame, text="Iniciando descarga...", font=ctk.CTkFont(size=13, weight="bold"), text_color="#95A5A6")
        self.lbl_status.pack(pady=(0, 25))
        
        # Iniciar descarga inmediatamente en segundo plano
        threading.Thread(target=self.start_download, daemon=True).start()

    def start_download(self):
        try:
            full_url = self.download_url
            if not full_url.startswith("http"):
                full_url = f"https://spi-pro-viewer.onrender.com{self.download_url}"
                
            response = requests.get(full_url, stream=True, timeout=40)
            if response.status_code != 200:
                raise Exception(f"Código HTTP {response.status_code} devuelto por el servidor.")
                
            total_length = response.headers.get('content-length')
            
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, self.filename)
            
            downloaded = 0
            with open(installer_path, 'wb') as f:
                if total_length is None:
                    f.write(response.content)
                else:
                    total_size = int(total_length)
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = downloaded / total_size
                            self.after(0, lambda p=pct, d=downloaded, t=total_size: self.update_progress(p, d, t))
                            
            self.after(0, lambda: self.lbl_status.configure(text="¡Descarga completada! Aplicando actualización y reiniciando...", text_color="#2ECC71"))
            self.after(1200, lambda: self.ejecutar_instalador(installer_path))
            
        except Exception as e:
            print(f"Error durante descarga de actualización: {e}")
            self.after(0, lambda err=str(e): self.lbl_status.configure(text=f"Error al descargar: {err}", text_color="#E74C3C"))
            self.after(3000, self.destroy)

    def update_progress(self, pct, downloaded, total):
        self.progress_bar.set(pct)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.lbl_status.configure(text=f"Descargando: {mb_down:.1f} MB / {mb_total:.1f} MB ({int(pct*100)}%)")

    def ejecutar_instalador(self, installer_path):
        """Ejecuta el instalador Inno Setup en modo silencioso y reinicia la aplicación automáticamente."""
        try:
            # Flags Inno Setup: /VERYSILENT (sin UI), /NORESTART (sin reboot de Windows), /SUPPRESSMSGBOXES
            cmd = f'"{installer_path}" /VERYSILENT /NORESTART /SUPPRESSMSGBOXES'
            subprocess.Popen(cmd, shell=True)
            print(f"Instalador lanzado: {cmd}")
            
            # Cierre inmediato para permitir que Inno Setup reemplace los archivos y relance la app
            time.sleep(1)
            sys.exit(0)
        except Exception as e:
            print(f"Error al ejecutar instalador: {e}")

def check_for_updates_async(current_version, mode="vertical", root_tk=None):
    """Consulta asíncrona al servidor de Render al arrancar la app."""
    def worker():
        try:
            url = f"{UPDATE_SERVER_URL}?mode={mode}"
            res = requests.get(url, timeout=35)
            if res.status_code == 200:
                data = res.json()
                latest_v = data.get("latest_version", current_version)
                mandatory = data.get("mandatory", True)
                changelog = data.get("changelog", "")
                download_url = data.get("download_url", "")
                filename = data.get("filename", "")
                
                if is_newer_version(latest_v, current_version):
                    print(f"🚀 Nueva versión detectada: v{latest_v} (Actual: v{current_version})")
                    if root_tk:
                        root_tk.after(0, lambda: AutoUpdateDialog(root_tk, latest_v, current_version, changelog, download_url, filename))
        except Exception as e:
            print(f"Verificación de actualización silenciosa (sin conexión): {e}")

    threading.Thread(target=worker, daemon=True).start()

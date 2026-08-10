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
        
        self.title("Actualización del Sistema SPI")
        self.geometry("500x380")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        
        # Centrar en pantalla
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.latest_version = latest_version
        self.current_version = current_version
        self.download_url = download_url
        self.filename = filename
        
        # Bloquear cierre con X para actualizaciones obligatorias
        self.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
        
        # UI Elements
        lbl_icon = ctk.CTkLabel(self, text="🚀", font=ctk.CTkFont(size=40))
        lbl_icon.pack(pady=(20, 5))
        
        lbl_title = ctk.CTkLabel(
            self, 
            text=f"Nueva Versión v{latest_version} Disponible", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2ECC71"
        )
        lbl_title.pack(pady=5)
        
        lbl_sub = ctk.CTkLabel(
            self, 
            text=f"Tu versión actual (v{current_version}) requiere actualizarse para continuar.", 
            font=ctk.CTkFont(size=13),
            text_color="#BDC3C7"
        )
        lbl_sub.pack(pady=2)
        
        # Caja de changelog
        frame_change = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)
        frame_change.pack(fill="both", expand=True, padx=20, pady=15)
        
        lbl_ch_title = ctk.CTkLabel(frame_change, text="Novedades:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498DB", anchor="w")
        lbl_ch_title.pack(fill="x", padx=10, pady=(8, 2))
        
        lbl_ch_text = ctk.CTkLabel(frame_change, text=changelog, font=ctk.CTkFont(size=12), text_color="#ECF0F1", justify="left", wraplength=440, anchor="w")
        lbl_ch_text.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        # Barra de Progreso
        self.progress_bar = ctk.CTkProgressBar(self, width=440, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 5))
        
        self.lbl_status = ctk.CTkLabel(self, text="Preparando descarga...", font=ctk.CTkFont(size=12), text_color="#95A5A6")
        self.lbl_status.pack(pady=(0, 15))
        
        # Iniciar descarga inmediatamente en segundo plano
        threading.Thread(target=self.start_download, daemon=True).start()

    def on_close_attempt(self):
        messagebox.showwarning(
            "Actualización Obligatoria", 
            "La actualización es obligatoria para garantizar la integridad de los datos. Espere a que finalice la instalación.",
            parent=self
        )

    def start_download(self):
        try:
            full_url = self.download_url
            if not full_url.startswith("http"):
                full_url = f"https://spi-pro-viewer.onrender.com{self.download_url}"
                
            response = requests.get(full_url, stream=True, timeout=30)
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
                            
            self.after(0, lambda: self.lbl_status.configure(text="¡Descarga completada! Lanzando instalador...", text_color="#2ECC71"))
            self.after(1000, lambda: self.ejecutar_instalador(installer_path))
            
        except Exception as e:
            print(f"Error durante descarga de actualización: {e}")
            self.after(0, lambda err=str(e): self.lbl_status.configure(text=f"Error al descargar: {err}", text_color="#E74C3C"))
            self.after(0, lambda: messagebox.showerror("Error de Actualización", f"No se pudo descargar la actualización:\n{e}\n\nReintentando en el próximo inicio."))

    def update_progress(self, pct, downloaded, total):
        self.progress_bar.set(pct)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.lbl_status.configure(text=f"Descargando: {mb_down:.1f} MB / {mb_total:.1f} MB ({int(pct*100)}%)")

    def ejecutar_instalador(self, installer_path):
        """Ejecuta el instalador Inno Setup en modo silencioso y cierra la aplicación actual."""
        try:
            # Flags Inno Setup: /VERYSILENT (sin UI), /NORESTART (sin reinicio de Windows), /SUPPRESSMSGBOXES
            cmd = [installer_path, "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"]
            subprocess.Popen(cmd, shell=True)
            print(f"Instalador lanzado: {cmd}")
            
            # Cierre inmediato del proceso Python para permitir que Inno Setup reemplace binarios
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar instalador:\n{e}")

def check_for_updates_async(current_version, mode="vertical", root_tk=None):
    """Consulta asíncrona al servidor de Render al arrancar la app."""
    def worker():
        try:
            url = f"{UPDATE_SERVER_URL}?mode={mode}"
            res = requests.get(url, timeout=5)
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

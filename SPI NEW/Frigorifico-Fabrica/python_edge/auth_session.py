"""
=============================================================================
SISTEMA DE PRODUCCIÓN INTEGRAL (SPI) - CONTROL DE AUTENTICACIÓN Y AUDITORÍA
Módulo: auth_session.py (Login Táctil por PIN y Trazabilidad con Timestamps)
=============================================================================
Características:
1. Teclado Numérico Táctil en Pantalla (PIN Pad): Botones gigantes (60px)
   diseñados para operar con guantes en planta sin teclado físico.
2. Caché Local de Operarios: Permite loguearse y cambiar de turno 100% OFFLINE.
3. Precisión de Timestamps ISO-8601 con milisegundos y Zona Horaria (UTC-3).
4. Auditoría Inmutable: Cada pesaje y evento viaja firmado con el ID y Legajo del operario.
=============================================================================
"""

import sys
import os
import hashlib
import datetime
from typing import Dict, Any, Optional, List
import customtkinter as ctk

# Operarios maestros por defecto para contingencia offline
OPERARIOS_SEMILLA = [
    {"id": 1, "legajo": "OP-001", "nombre": "Juan Pérez", "rol": "OPERARIO_FAENA", "pin": "1234"},
    {"id": 2, "legajo": "OP-002", "nombre": "Marcos Díaz", "rol": "OPERARIO_FAENA", "pin": "2345"},
    {"id": 3, "legajo": "VET-001", "nombre": "Dr. Roberto Gómez", "rol": "VETERINARIO_SENASA", "pin": "9999"},
    {"id": 4, "legajo": "OP-004", "nombre": "Carlos Rossi", "rol": "OPERARIO_FAENA", "pin": "4321"},
    {"id": 5, "legajo": "SUP-001", "nombre": "Esteban Morales", "rol": "SUPERVISOR", "pin": "8888"},
    {"id": 6, "legajo": "FIA-001", "nombre": "Miguel Fiambrero", "rol": "MAESTRO_CHACINERO", "pin": "5555"},
    {"id": 7, "legajo": "ADM-001", "nombre": "Administrador General", "rol": "ADMINISTRADOR", "pin": "7777"},
]

COLOR_BG = "#0B0F19"
COLOR_CARD = "#0F172A"
COLOR_BORDER = "#334155"
COLOR_GREEN = "#10B981"
COLOR_RED = "#EF4444"
COLOR_YELLOW = "#F59E0B"
COLOR_BLUE = "#38BDF8"
COLOR_TEXT = "#F8FAFC"
COLOR_TEXT_MUTED = "#94A3B8"


def get_current_timestamp_iso() -> str:
    """
    Retorna timestamp ISO-8601 con microsegundos y zona horaria local.
    Ejemplo: '2026-09-04T12:05:30.123456-03:00'
    """
    tz = datetime.timezone(datetime.timedelta(hours=-3))  # Argentina UTC-3
    return datetime.datetime.now(tz).isoformat()


class SessionManager:
    """Gestor singleton de sesión activa en la terminal táctil."""
    _current_user: Optional[Dict[str, Any]] = None

    @classmethod
    def get_current_user(cls) -> Dict[str, Any]:
        if cls._current_user is None:
            # Usuario por defecto si no se ha logueado
            cls._current_user = {
                "id": 4,
                "legajo": "OP-004",
                "nombre": "Carlos Rossi",
                "rol": "OPERARIO_FAENA",
                "login_timestamp": get_current_timestamp_iso()
            }
        return cls._current_user

    @classmethod
    def set_current_user(cls, user_data: Dict[str, Any]):
        cls._current_user = {
            "id": user_data["id"],
            "legajo": user_data["legajo"],
            "nombre": user_data["nombre"],
            "rol": user_data["rol"],
            "login_timestamp": get_current_timestamp_iso()
        }

    @classmethod
    def authenticate_pin(cls, pin: str, legajo: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Valida el PIN contra los operarios registrados y establece la sesión."""
        for op in OPERARIOS_SEMILLA:
            if legajo:
                if op["legajo"] == legajo and op["pin"] == pin:
                    cls.set_current_user(op)
                    return cls.get_current_user()
            else:
                if op["pin"] == pin:
                    cls.set_current_user(op)
                    return cls.get_current_user()
        return None

    @classmethod
    def verify_supervisor_pin(cls, pin: str) -> Optional[Dict[str, Any]]:
        """Verifica si el PIN corresponde a un Administrador o Supervisor autorizado."""
        for op in OPERARIOS_SEMILLA:
            if op["pin"] == pin and op["rol"] in ("SUPERVISOR", "ADMINISTRADOR"):
                return op
        return None

    @classmethod
    def logout(cls):
        cls._current_user = None


class LoginPinModal(ctk.CTkToplevel):
    """
    Diálogo táctil modal para inicio de sesión y cambio rápido de turno.
    Incluye teclado numérico en pantalla (glove-friendly).
    """

    def __init__(self, parent, on_success_callback=None):
        super().__init__(parent)

        self.title("SPI // Control de Acceso - Iniciar Turno")
        self.geometry("440x600")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self.on_success_callback = on_success_callback
        self.pin_entered = ""

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="🔐 IDENTIFICACIÓN DE OPERARIO",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#A5B4FC"
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            self,
            text="Selecciona tu usuario e ingresa tu PIN de 4 dígitos:",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_TEXT_MUTED
        ).pack(pady=(0, 12))

        # Selector de Operario
        self.operarios_map = {f"{op['nombre']} ({op['rol']})": op for op in OPERARIOS_SEMILLA}
        self.combo_user = ctk.CTkComboBox(
            self,
            values=list(self.operarios_map.keys()),
            width=360,
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.combo_user.set(list(self.operarios_map.keys())[3])  # Carlos Rossi por defecto
        self.combo_user.pack(pady=(0, 14))

        # Visor de PIN con asteriscos
        self.lbl_pin_display = ctk.CTkLabel(
            self,
            text="• • • •",
            font=ctk.CTkFont(family="Consolas", size=32, weight="bold"),
            text_color="#38BDF8",
            fg_color="#060911",
            corner_radius=10,
            width=360,
            height=54
        )
        self.lbl_pin_display.pack(pady=(0, 16))

        # Teclado Numérico Táctil (3x4)
        numpad_frame = ctk.CTkFrame(self, fg_color="transparent")
        numpad_frame.pack()

        buttons = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("BORRAR", 3, 0), ("0", 3, 1), ("INGRESAR", 3, 2),
        ]

        for text, r, c in buttons:
            if text == "BORRAR":
                btn = ctk.CTkButton(
                    numpad_frame, text="⌫", width=100, height=56,
                    font=ctk.CTkFont(size=18, weight="bold"),
                    fg_color="#7F1D1D", hover_color=COLOR_RED,
                    command=self._on_clear
                )
            elif text == "INGRESAR":
                btn = ctk.CTkButton(
                    numpad_frame, text="✔", width=100, height=56,
                    font=ctk.CTkFont(size=18, weight="bold"),
                    fg_color=COLOR_GREEN, hover_color="#059669",
                    command=self._on_submit
                )
            else:
                digit = text
                btn = ctk.CTkButton(
                    numpad_frame, text=digit, width=100, height=56,
                    font=ctk.CTkFont(size=20, weight="bold"),
                    fg_color="#1E293B", hover_color="#334155",
                    command=lambda d=digit: self._on_digit_press(d)
                )
            btn.grid(row=r, column=c, padx=6, pady=6)

        # Mensaje de error / estado
        self.lbl_msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color=COLOR_RED)
        self.lbl_msg.pack(pady=(12, 0))

    def _on_digit_press(self, digit: str):
        if len(self.pin_entered) < 4:
            self.pin_entered += digit
            self._update_display()
            if len(self.pin_entered) == 4:
                # Auto-validar al 4to dígito
                self.after(200, self._on_submit)

    def _on_clear(self):
        self.pin_entered = ""
        self.lbl_msg.configure(text="")
        self._update_display()

    def _update_display(self):
        if not self.pin_entered:
            self.lbl_pin_display.configure(text="• • • •", text_color="#64748B")
        else:
            bullets = "● " * len(self.pin_entered) + "○ " * (4 - len(self.pin_entered))
            self.lbl_pin_display.configure(text=bullets.strip(), text_color="#38BDF8")

    def _on_submit(self):
        user_key = self.combo_user.get()
        user_data = self.operarios_map.get(user_key)

        if not user_data:
            self.lbl_msg.configure(text="Operario no válido.")
            return

        if self.pin_entered == user_data["pin"]:
            SessionManager.set_current_user(user_data)
            if self.on_success_callback:
                self.on_success_callback(SessionManager.get_current_user())
            self.destroy()
        else:
            self.lbl_msg.configure(text="❌ PIN Incorrecto. Intente nuevamente.")
            self.pin_entered = ""
            self._update_display()


# ---------------------------------------------------------------------------
# MODALES DE AUTORIZACIÓN Y CARGA MANUAL DE PESO (CONTINGENCIA BALANZA)
# ---------------------------------------------------------------------------
class SupervisorAuthModal(ctk.CTkToplevel):
    """
    Modal de seguridad táctil que solicita el PIN de un Administrador o Supervisor
    para desbloquear funciones críticas (ej. carga manual por balanza rota).
    """
    def __init__(self, parent, accion_descripcion: str, on_authorized_callback):
        super().__init__(parent)
        self.title("SPI // Autorización Administrativa")
        self.geometry("440x580")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self.accion_descripcion = accion_descripcion
        self.on_authorized_callback = on_authorized_callback
        self.pin_entered = ""

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="🛡️ AUTORIZACIÓN REQUERIDA", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_RED
        ).pack(pady=(20, 6))

        ctk.CTkLabel(
            self, text=self.accion_descripcion, font=ctk.CTkFont(size=12), text_color="#E2E8F0", wraplength=380
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            self, text="Requiere PIN de Administrador o Supervisor:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_MUTED
        ).pack(pady=(0, 6))

        self.lbl_pin_display = ctk.CTkLabel(
            self, text="• • • •", font=ctk.CTkFont(family="Consolas", size=32, weight="bold"), text_color="#64748B"
        )
        self.lbl_pin_display.pack(pady=(4, 10))

        # Teclado Numérico Táctil 60px
        keypad = ctk.CTkFrame(self, fg_color="transparent")
        keypad.pack(pady=4)

        teclas = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["C", "0", "⌫"]
        ]

        for r, fila in enumerate(teclas):
            for c, digito in enumerate(fila):
                btn = ctk.CTkButton(
                    keypad, text=digito, width=72, height=54,
                    font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
                    fg_color="#1E293B" if digito not in ("C", "⌫") else "#334155",
                    hover_color="#4338CA" if digito not in ("C", "⌫") else "#475569",
                    command=lambda d=digito: self._on_keypad_press(d)
                )
                btn.grid(row=r, column=c, padx=6, pady=4)

        self.lbl_msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_RED)
        self.lbl_msg.pack(pady=6)

        ctk.CTkButton(self, text="CANCELAR", width=140, height=36, fg_color="#334155", command=self.destroy).pack(pady=(4, 14))

    def _on_keypad_press(self, tecla: str):
        if tecla == "C":
            self.pin_entered = ""
        elif tecla == "⌫":
            self.pin_entered = self.pin_entered[:-1]
        else:
            if len(self.pin_entered) < 4:
                self.pin_entered += tecla

        self._update_display()
        if len(self.pin_entered) == 4:
            self.after(150, self._validar_pin)

    def _update_display(self):
        if not self.pin_entered:
            self.lbl_pin_display.configure(text="• • • •", text_color="#64748B")
        else:
            bullets = "● " * len(self.pin_entered) + "○ " * (4 - len(self.pin_entered))
            self.lbl_pin_display.configure(text=bullets.strip(), text_color=COLOR_RED)

    def _validar_pin(self):
        supervisor = SessionManager.verify_supervisor_pin(self.pin_entered)
        if supervisor:
            self.destroy()
            self.on_authorized_callback(supervisor)
        else:
            self.lbl_msg.configure(text="❌ PIN No Autorizado (Requiere Rango Supervisor)")
            self.pin_entered = ""
            self._update_display()


class CargaManualPesoModal(ctk.CTkToplevel):
    """
    Diálogo táctil de carga manual de peso para cuando la balanza física falla.
    Exige ingresar el peso y el motivo bromatológico/operativo de la contingencia.
    """
    MOTIVOS_CONTINGENCIA = [
        "Falla de comunicación RS-232 / Balanza desconectada",
        "Balanza fuera de servicio / En mantenimiento técnico",
        "Rotura o daño mecánico en celda de carga",
        "Oscilación eléctrica severa / Peso inestable en pantalla",
        "Balanza de contingencia externa utilizada",
    ]

    def __init__(self, parent, supervisor_autorizante: Dict[str, Any], on_confirm_callback):
        super().__init__(parent)
        self.title("SPI // Carga Manual de Peso (Contingencia)")
        self.geometry("500x530")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self.supervisor = supervisor_autorizante
        self.on_confirm_callback = on_confirm_callback
        self.peso_str = ""

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="⚠️ INGRESO MANUAL DE PESO", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLOR_YELLOW
        ).pack(pady=(16, 4))

        # Badge de autorización
        badge_sup = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=6)
        badge_sup.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(
            badge_sup,
            text=f"🛡️ AUTORIZADO POR: {self.supervisor['nombre']} ({self.supervisor['legajo']})",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_GREEN
        ).pack(padx=10, pady=6)

        # Motivo
        ctk.CTkLabel(self, text="Motivo Obligatorio de Contingencia:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(10, 2))
        self.combo_motivo = ctk.CTkComboBox(self, values=self.MOTIVOS_CONTINGENCIA, width=450, height=30)
        self.combo_motivo.pack(padx=24)

        # Display del peso ingresado
        ctk.CTkLabel(self, text="Peso en Gancho (kg):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=24, pady=(10, 2))
        self.lbl_peso_display = ctk.CTkLabel(
            self, text="0.00", font=ctk.CTkFont(family="Consolas", size=38, weight="bold"),
            text_color=COLOR_YELLOW, fg_color="#060911", corner_radius=8, width=450, height=54
        )
        self.lbl_peso_display.pack(padx=24, pady=4)

        # Teclado numérico táctil para peso
        pad = ctk.CTkFrame(self, fg_color="transparent")
        pad.pack(pady=4)

        teclas = [
            ["7", "8", "9"],
            ["4", "5", "6"],
            ["1", "2", "3"],
            ["C", "0", "."]
        ]

        for r, fila in enumerate(teclas):
            for c, digito in enumerate(fila):
                btn = ctk.CTkButton(
                    pad, text=digito, width=64, height=40,
                    font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
                    fg_color="#1E293B", hover_color="#334155",
                    command=lambda d=digito: self._on_pad_press(d)
                )
                btn.grid(row=r, column=c, padx=4, pady=2)

        self.lbl_error = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_RED)
        self.lbl_error.pack(pady=2)

        # Botón Confirmar
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=24, pady=(4, 14))

        ctk.CTkButton(
            btn_box, text="💾 CONFIRMAR PESAJE MANUAL", height=44, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_YELLOW, text_color="#000000", hover_color="#CA8A04",
            command=self._confirmar
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_box, text="CANCELAR", height=44, width=110, fg_color="#334155", command=self.destroy
        ).pack(side="right")

    def _on_pad_press(self, digito: str):
        if digito == "C":
            self.peso_str = ""
        elif digito == ".":
            if "." not in self.peso_str:
                self.peso_str += "." if self.peso_str else "0."
        else:
            if len(self.peso_str) < 6:
                self.peso_str += digito

        txt = self.peso_str if self.peso_str else "0.00"
        self.lbl_peso_display.configure(text=txt)

    def _confirmar(self):
        try:
            val = float(self.peso_str)
        except ValueError:
            val = 0.0

        if val < 5.0 or val > 200.0:
            self.lbl_error.configure(text="❌ Ingrese un peso válido entre 5.0 kg y 200.0 kg.")
            return

        motivo = self.combo_motivo.get()
        self.destroy()
        self.on_confirm_callback(val, motivo, self.supervisor)


# ---------------------------------------------------------------------------
# PRUEBA STANDALONE DEL MODAL DE LOGIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Prueba de Login")
    app.geometry("500x300")

    def callback(user):
        print(f"[OK] Usuario Autenticado: {user['nombre']} | Legajo: {user['legajo']} | Rol: {user['rol']}")
        print(f"[OK] Timestamp ISO Registrado: {user['login_timestamp']}")
        lbl.configure(text=f"Sesión activa: {user['nombre']} ({user['rol']})\nLogueado a las: {user['login_timestamp']}")

    lbl = ctk.CTkLabel(app, text="Presiona el botón para abrir el Login por PIN:", font=ctk.CTkFont(size=14))
    lbl.pack(pady=40)

    ctk.CTkButton(
        app, text="👤 CAMBIAR DE OPERARIO / LOGIN", height=50,
        command=lambda: LoginPinModal(app, on_success_callback=callback)
    ).pack()

    app.mainloop()

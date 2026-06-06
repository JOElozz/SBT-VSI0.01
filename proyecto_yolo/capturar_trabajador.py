"""
registro_trabajador_gui.py
==========================
Ventana de registro de trabajadores para A.R.G.O.S.

Flujo:
  1. Supervisor ingresa alias + PIN  →  validado contra supervisores.json (SHA-256)
  2. Supervisor ingresa alias y nombre real del trabajador
  3. Para cada foto (5 en total):
       a. Detecta parpadeo en vivo mediante Eye Aspect Ratio (EAR)
       b. Al confirmar liveness, captura y guarda la foto
  4. Registra al trabajador en el servidor Scala

Dependencias: customtkinter, Pillow, opencv-python, face_recognition, requests
"""

import os
import re
import json
import hashlib
import threading
import datetime
import tkinter as tk

import cv2
import requests
import customtkinter as ctk
from PIL import Image

# ── face_recognition se importa con manejo de error para no crashear si falta ──
try:
    import face_recognition
    FACE_REC_OK = True
except ImportError:
    FACE_REC_OK = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

RUTA_SUPERVISORES  = "supervisores.json"
CARPETA_FOTOS      = "fotos_trabajadores"
SERVER_URL         = "http://localhost:9000"
CAPTURA_URL        = f"{SERVER_URL}/trabajadores"
TOTAL_FOTOS        = 5

# Umbral EAR: por debajo = ojo cerrado
EAR_UMBRAL         = 0.21
# Frames consecutivos con ojo cerrado para confirmar parpadeo
EAR_FRAMES_MIN     = 2

# Índices de los 6 puntos del ojo en los landmarks de face_recognition
# Ojo izquierdo: left_eye  (6 puntos)
# Ojo derecho:   right_eye (6 puntos)

# ── Paleta coherente con SALVIDashboard ──
ESTILOS = {
    "fondo":          "#f8f9fa",
    "panel":          "#ffffff",
    "titulo":         "#212529",
    "normal":         "#495057",
    "secundario":     "#6c757d",
    "azul":           ("#3B8ED0", "#1F6AA5"),
    "verde":          ("#2cc985", "#2fa572"),
    "rojo":           ("#e04f5f", "#c0392b"),
    "amarillo":       ("#ffc107", "#e0a800"),
}

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════

def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def normalizar_alias(alias: str) -> str:
    alias = alias.strip().upper()
    alias = re.sub(r"[^A-Z0-9_-]", "_", alias)
    if alias and not alias.startswith("TRAB-"):
        alias = f"TRAB-{alias}"
    return alias


def cargar_supervisores() -> list:
    if not os.path.exists(RUTA_SUPERVISORES):
        return []
    with open(RUTA_SUPERVISORES, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("supervisores", [])


def validar_supervisor(alias: str, pin: str) -> tuple[bool, str]:
    """Retorna (ok, nombre_supervisor)."""
    supervisores = cargar_supervisores()
    alias_up = alias.strip().upper()
    pin_hash = sha256(pin.strip())
    for sv in supervisores:
        if sv["alias"].upper() == alias_up and sv["pin_hash"] == pin_hash:
            return True, sv.get("nombre", alias_up)
    return False, ""


def registrar_en_servidor(alias: str, nombre_real: str) -> bool:
    try:
        r = requests.post(CAPTURA_URL, json={"alias": alias, "nombre_real": nombre_real}, timeout=3)
        return r.ok
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO EAR  (Eye Aspect Ratio)
# ═══════════════════════════════════════════════════════════════════════════════

def _dist(p1, p2) -> float:
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def ear(puntos: list) -> float:
    """
    Calcula el Eye Aspect Ratio para 6 puntos del ojo:
      p0=esquina_izq, p1=arriba_izq, p2=arriba_der,
      p3=esquina_der, p4=abajo_der,  p5=abajo_izq
    EAR = (||p1-p5|| + ||p2-p4||) / (2 * ||p0-p3||)
    """
    A = _dist(puntos[1], puntos[5])
    B = _dist(puntos[2], puntos[4])
    C = _dist(puntos[0], puntos[3])
    if C < 1e-6:
        return 0.0
    return (A + B) / (2.0 * C)


def calcular_ear_frame(frame_rgb):
    """
    Detecta landmarks en el frame y retorna el EAR promedio de ambos ojos.
    Retorna None si no detecta ningún rostro.
    """
    if not FACE_REC_OK:
        return None
    landmarks_lista = face_recognition.face_landmarks(frame_rgb)
    if not landmarks_lista:
        return None
    lm = landmarks_lista[0]
    ear_izq = ear(lm["left_eye"])
    ear_der = ear(lm["right_eye"])
    return (ear_izq + ear_der) / 2.0


# ═══════════════════════════════════════════════════════════════════════════════
# VENTANA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class RegistroTrabajadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("A.R.G.O.S — Registro de Trabajador")
        self.geometry("900x620")
        self.resizable(False, False)
        self.configure(fg_color=ESTILOS["fondo"])

        # Estado interno
        self._supervisor_nombre = ""
        self._alias_trabajador  = ""
        self._nombre_real       = ""
        self._fotos_tomadas     = 0
        self._cap               = None
        self._loop_activo       = False

        # Liveness
        self._ear_bajo_count    = 0   # frames consecutivos con EAR bajo
        self._parpadeo_ok       = False
        self._liveness_status   = "Esperando parpadeo..."

        self._construir_ui()
        self._mostrar_panel("login")

    # ──────────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA UI
    # ──────────────────────────────────────────────────────────────────────────

    def _construir_ui(self):
        # Título superior
        self._frame_header = ctk.CTkFrame(self, fg_color=ESTILOS["panel"], corner_radius=0, height=60)
        self._frame_header.pack(fill="x", side="top")
        ctk.CTkLabel(
            self._frame_header,
            text="A.R.G.O.S  ·  Registro de Trabajador",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ESTILOS["titulo"],
        ).pack(side="left", padx=24, pady=14)

        self._lbl_supervisor = ctk.CTkLabel(
            self._frame_header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=ESTILOS["secundario"],
        )
        self._lbl_supervisor.pack(side="right", padx=24)

        # Contenedor central
        self._contenedor = ctk.CTkFrame(self, fg_color=ESTILOS["fondo"])
        self._contenedor.pack(fill="both", expand=True, padx=30, pady=20)

        # ── Panel: Login de supervisor ──────────────────────────────────────
        self._panel_login = ctk.CTkFrame(self._contenedor, fg_color=ESTILOS["panel"], corner_radius=12)

        ctk.CTkLabel(
            self._panel_login,
            text="Acceso de Supervisor",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ESTILOS["titulo"],
        ).pack(pady=(30, 6))
        ctk.CTkLabel(
            self._panel_login,
            text="Ingresa tu alias y PIN para continuar",
            font=ctk.CTkFont(size=13),
            text_color=ESTILOS["secundario"],
        ).pack(pady=(0, 20))

        ctk.CTkLabel(self._panel_login, text="Alias de supervisor", text_color=ESTILOS["normal"]).pack(anchor="w", padx=60)
        self._entry_sv_alias = ctk.CTkEntry(self._panel_login, width=320, placeholder_text="SUPERVISOR-01")
        self._entry_sv_alias.pack(pady=(4, 14), padx=60)

        ctk.CTkLabel(self._panel_login, text="PIN (numérico)", text_color=ESTILOS["normal"]).pack(anchor="w", padx=60)
        self._entry_sv_pin = ctk.CTkEntry(self._panel_login, width=320, placeholder_text="••••••", show="•")
        self._entry_sv_pin.pack(pady=(4, 6), padx=60)

        self._lbl_login_error = ctk.CTkLabel(
            self._panel_login, text="", text_color=ESTILOS["rojo"][0], font=ctk.CTkFont(size=12)
        )
        self._lbl_login_error.pack(pady=(0, 12))

        ctk.CTkButton(
            self._panel_login,
            text="Ingresar",
            width=320,
            fg_color=ESTILOS["azul"],
            command=self._validar_login,
        ).pack(pady=(0, 30), padx=60)

        # Enter en PIN también valida
        self._entry_sv_pin.bind("<Return>", lambda _: self._validar_login())

        # ── Panel: Datos del trabajador ─────────────────────────────────────
        self._panel_datos = ctk.CTkFrame(self._contenedor, fg_color=ESTILOS["panel"], corner_radius=12)

        ctk.CTkLabel(
            self._panel_datos,
            text="Datos del Trabajador",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ESTILOS["titulo"],
        ).pack(pady=(30, 6))
        ctk.CTkLabel(
            self._panel_datos,
            text="Completa la información antes de capturar las fotos",
            font=ctk.CTkFont(size=13),
            text_color=ESTILOS["secundario"],
        ).pack(pady=(0, 20))

        ctk.CTkLabel(self._panel_datos, text="Alias seguro del trabajador", text_color=ESTILOS["normal"]).pack(anchor="w", padx=60)
        self._entry_alias = ctk.CTkEntry(self._panel_datos, width=380, placeholder_text="TRAB-1234  (se normaliza automáticamente)")
        self._entry_alias.pack(pady=(4, 14), padx=60)

        ctk.CTkLabel(self._panel_datos, text="Nombre real (opcional)", text_color=ESTILOS["normal"]).pack(anchor="w", padx=60)
        self._entry_nombre = ctk.CTkEntry(self._panel_datos, width=380, placeholder_text="Juan Pérez")
        self._entry_nombre.pack(pady=(4, 6), padx=60)

        self._lbl_datos_error = ctk.CTkLabel(
            self._panel_datos, text="", text_color=ESTILOS["rojo"][0], font=ctk.CTkFont(size=12)
        )
        self._lbl_datos_error.pack(pady=(0, 12))

        ctk.CTkButton(
            self._panel_datos,
            text="Continuar a captura de fotos →",
            width=380,
            fg_color=ESTILOS["azul"],
            command=self._iniciar_captura,
        ).pack(pady=(0, 30), padx=60)

        # ── Panel: Captura de fotos ─────────────────────────────────────────
        self._panel_captura = ctk.CTkFrame(self._contenedor, fg_color=ESTILOS["panel"], corner_radius=12)

        # Columna izquierda — cámara
        col_cam = ctk.CTkFrame(self._panel_captura, fg_color=ESTILOS["panel"])
        col_cam.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)

        ctk.CTkLabel(col_cam, text="CÁMARA EN VIVO", font=ctk.CTkFont(weight="bold"), text_color=ESTILOS["titulo"]).pack()
        self._lbl_video = ctk.CTkLabel(col_cam, text="Iniciando cámara...")
        self._lbl_video.pack(expand=True, fill="both", pady=8)

        # Columna derecha — estado y controles
        col_info = ctk.CTkFrame(self._panel_captura, fg_color=ESTILOS["fondo"], corner_radius=10, width=240)
        col_info.pack(side="right", fill="y", padx=(10, 20), pady=20)
        col_info.pack_propagate(False)

        self._lbl_cap_titulo = ctk.CTkLabel(
            col_info, text="", font=ctk.CTkFont(size=16, weight="bold"), text_color=ESTILOS["titulo"],
            wraplength=220,
        )
        self._lbl_cap_titulo.pack(pady=(20, 6), padx=10)

        self._lbl_cap_estado = ctk.CTkLabel(
            col_info,
            text="Esperando parpadeo...",
            font=ctk.CTkFont(size=13),
            text_color=ESTILOS["secundario"],
            wraplength=220,
        )
        self._lbl_cap_estado.pack(pady=(0, 14), padx=10)

        # Barra de progreso de fotos
        ctk.CTkLabel(col_info, text="Fotos capturadas", text_color=ESTILOS["secundario"]).pack(padx=10)
        self._progress = ctk.CTkProgressBar(col_info, width=200)
        self._progress.set(0)
        self._progress.pack(pady=(4, 16), padx=10)

        self._lbl_progreso_num = ctk.CTkLabel(col_info, text=f"0 / {TOTAL_FOTOS}", text_color=ESTILOS["normal"])
        self._lbl_progreso_num.pack()

        # Indicador de liveness
        self._lbl_liveness = ctk.CTkLabel(
            col_info,
            text="👁  PARPADEA para activar la captura",
            font=ctk.CTkFont(size=12),
            text_color=ESTILOS["amarillo"][0],
            wraplength=220,
        )
        self._lbl_liveness.pack(pady=(20, 6), padx=10)

        # Botón de captura manual (solo disponible tras liveness)
        self._btn_foto = ctk.CTkButton(
            col_info,
            text="📸  Capturar foto",
            width=200,
            fg_color=ESTILOS["verde"],
            state="disabled",
            command=self._capturar_foto,
        )
        self._btn_foto.pack(pady=(10, 6), padx=10)

        # Bind tecla C también
        self.bind("<KeyPress-c>", lambda _: self._capturar_foto())
        self.bind("<KeyPress-C>", lambda _: self._capturar_foto())

        ctk.CTkLabel(col_info, text="o presiona C", text_color=ESTILOS["secundario"], font=ctk.CTkFont(size=11)).pack()

        self._btn_cancelar = ctk.CTkButton(
            col_info,
            text="Cancelar",
            width=200,
            fg_color=ESTILOS["rojo"],
            command=self._cancelar_captura,
        )
        self._btn_cancelar.pack(side="bottom", pady=20, padx=10)

        # ── Panel: Resultado final ──────────────────────────────────────────
        self._panel_resultado = ctk.CTkFrame(self._contenedor, fg_color=ESTILOS["panel"], corner_radius=12)

        self._lbl_resultado_icono = ctk.CTkLabel(
            self._panel_resultado, text="✅", font=ctk.CTkFont(size=64)
        )
        self._lbl_resultado_icono.pack(pady=(40, 10))

        self._lbl_resultado_titulo = ctk.CTkLabel(
            self._panel_resultado,
            text="",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=ESTILOS["titulo"],
        )
        self._lbl_resultado_titulo.pack()

        self._lbl_resultado_detalle = ctk.CTkLabel(
            self._panel_resultado,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=ESTILOS["secundario"],
            wraplength=500,
            justify="center",
        )
        self._lbl_resultado_detalle.pack(pady=(10, 30))

        frame_btns = ctk.CTkFrame(self._panel_resultado, fg_color="transparent")
        frame_btns.pack()
        ctk.CTkButton(
            frame_btns,
            text="Registrar otro trabajador",
            width=220,
            fg_color=ESTILOS["azul"],
            command=self._nuevo_registro,
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            frame_btns,
            text="Cerrar",
            width=160,
            fg_color=ESTILOS["rojo"],
            command=self._cerrar,
        ).pack(side="left", padx=10)

    # ──────────────────────────────────────────────────────────────────────────
    # GESTIÓN DE PANELES
    # ──────────────────────────────────────────────────────────────────────────

    def _mostrar_panel(self, nombre: str):
        for p in [self._panel_login, self._panel_datos, self._panel_captura, self._panel_resultado]:
            p.pack_forget()
        panel = {
            "login":      self._panel_login,
            "datos":      self._panel_datos,
            "captura":    self._panel_captura,
            "resultado":  self._panel_resultado,
        }[nombre]
        panel.pack(fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    # FLUJO: LOGIN
    # ──────────────────────────────────────────────────────────────────────────

    def _validar_login(self):
        alias = self._entry_sv_alias.get()
        pin   = self._entry_sv_pin.get()
        if not alias or not pin:
            self._lbl_login_error.configure(text="Alias y PIN son obligatorios.")
            return

        ok, nombre = validar_supervisor(alias, pin)
        if ok:
            self._supervisor_nombre = nombre
            self._lbl_supervisor.configure(text=f"Supervisor: {nombre}")
            self._lbl_login_error.configure(text="")
            self._mostrar_panel("datos")
        else:
            self._lbl_login_error.configure(text="Alias o PIN incorrecto. Inténtalo de nuevo.")

    # ──────────────────────────────────────────────────────────────────────────
    # FLUJO: DATOS DEL TRABAJADOR
    # ──────────────────────────────────────────────────────────────────────────

    def _iniciar_captura(self):
        alias = normalizar_alias(self._entry_alias.get())
        nombre_real = self._entry_nombre.get().strip()

        if not alias or alias == "TRAB-":
            self._lbl_datos_error.configure(text="El alias no puede estar vacío.")
            return

        self._alias_trabajador = alias
        self._nombre_real      = nombre_real
        self._lbl_datos_error.configure(text="")

        # Crear carpeta
        carpeta = os.path.join(CARPETA_FOTOS, alias)
        os.makedirs(carpeta, exist_ok=True)

        # Contar fotos previas
        self._fotos_previas = len([
            f for f in os.listdir(carpeta)
            if f.lower().endswith((".jpg", ".png"))
        ])
        self._fotos_tomadas = 0

        # Registrar en servidor (no bloquea la UI)
        if nombre_real:
            threading.Thread(
                target=registrar_en_servidor, args=(alias, nombre_real), daemon=True
            ).start()

        self._lbl_cap_titulo.configure(
            text=f"Alias: {alias}\nFotos requeridas: {TOTAL_FOTOS}"
        )
        self._actualizar_progreso()
        self._mostrar_panel("captura")
        self._iniciar_camara()

    # ──────────────────────────────────────────────────────────────────────────
    # CÁMARA Y LIVENESS
    # ──────────────────────────────────────────────────────────────────────────

    def _iniciar_camara(self):
        # Prueba los índices en orden — igual que el proyecto original usa índice 2
        self._cap = None
        for idx in [2, 0, 1]:
            cap_intento = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # CAP_DSHOW más rápido en Windows
            if cap_intento.isOpened():
                ret, _ = cap_intento.read()  # Verifica que realmente devuelve frames
                if ret:
                    self._cap = cap_intento
                    break
            cap_intento.release()

        if self._cap is None or not self._cap.isOpened():
            self._lbl_video.configure(
                text="❌ No se detectó ninguna cámara.\nVerifica que esté conectada e intenta de nuevo.",
                image=None
            )
            return

        self._loop_activo    = True
        self._parpadeo_ok    = False
        self._ear_bajo_count = 0
        self._btn_foto.configure(state="disabled")
        self._bucle_camara()

    def _bucle_camara(self):
        if not self._loop_activo:
            return

        ret, frame = self._cap.read()
        if ret:
            frame_display = frame.copy()
            alto, ancho   = frame.shape[:2]

            # ── Detección de liveness (EAR) en hilo aparte sería más limpio,
            #    pero para no complicar la lógica lo hacemos cada N frames.
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ear_val   = calcular_ear_frame(frame_rgb)

            if ear_val is not None:
                if ear_val < EAR_UMBRAL:
                    self._ear_bajo_count += 1
                else:
                    if self._ear_bajo_count >= EAR_FRAMES_MIN and not self._parpadeo_ok:
                        # ¡Parpadeo detectado!
                        self._parpadeo_ok = True
                        self._liveness_status = "✅ Liveness confirmado — presiona C o el botón"
                        self.after(0, self._on_liveness_ok)
                    self._ear_bajo_count = 0
            else:
                if not self._parpadeo_ok:
                    self._liveness_status = "Sin rostro detectado — acércate a la cámara"

            # Overlay EAR en el frame
            color_ear = (0, 200, 0) if self._parpadeo_ok else (0, 165, 255)
            estado_txt = "LIVENESS OK" if self._parpadeo_ok else f"EAR: {ear_val:.2f}" if ear_val else "Sin rostro"
            cv2.putText(frame_display, estado_txt, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ear, 2)

            # Guía de encuadre
            cx, cy = ancho // 2, alto // 2
            cv2.ellipse(frame_display, (cx, cy), (90, 120), 0, 0, 360, color_ear, 2)

            # Contador de fotos
            cv2.putText(
                frame_display,
                f"Fotos: {self._fotos_tomadas}/{TOTAL_FOTOS}",
                (10, alto - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (50, 50, 50), 2
            )

            # Renderizar en el label
            img_pil = Image.fromarray(cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB))
            img_tk  = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(480, 360))
            self._lbl_video.configure(image=img_tk, text="")
            self._lbl_video.image = img_tk

            # Actualizar texto de estado liveness
            self._lbl_liveness.configure(text=self._liveness_status)

        self.after(30, self._bucle_camara)

    def _on_liveness_ok(self):
        self._btn_foto.configure(state="normal")
        self._lbl_liveness.configure(
            text="✅ Liveness OK — presiona C o el botón",
            text_color=ESTILOS["verde"][0],
        )
        self._lbl_cap_estado.configure(
            text="Parpadeo detectado. Listo para capturar.",
            text_color=ESTILOS["verde"][0],
        )

    # ──────────────────────────────────────────────────────────────────────────
    # CAPTURA DE FOTO
    # ──────────────────────────────────────────────────────────────────────────

    def _capturar_foto(self):
        if not self._parpadeo_ok:
            return  # Seguridad extra: no captura sin liveness
        if self._fotos_tomadas >= TOTAL_FOTOS:
            return
        if self._cap is None or not self._cap.isOpened():
            return

        ret, frame = self._cap.read()
        if not ret:
            return

        carpeta = os.path.join(CARPETA_FOTOS, self._alias_trabajador)
        idx     = self._fotos_previas + self._fotos_tomadas + 1
        ruta    = os.path.join(carpeta, f"{idx}.jpg")
        cv2.imwrite(ruta, frame)

        self._fotos_tomadas += 1
        self._actualizar_progreso()

        # Resetear liveness para la siguiente foto
        self._parpadeo_ok    = False
        self._ear_bajo_count = 0
        self._btn_foto.configure(state="disabled")
        self._lbl_liveness.configure(
            text="👁  PARPADEA para la siguiente foto",
            text_color=ESTILOS["amarillo"][0],
        )
        self._lbl_cap_estado.configure(
            text=f"Foto {self._fotos_tomadas} guardada.",
            text_color=ESTILOS["normal"],
        )

        if self._fotos_tomadas >= TOTAL_FOTOS:
            self._finalizar_captura()

    def _actualizar_progreso(self):
        ratio = self._fotos_tomadas / TOTAL_FOTOS
        self._progress.set(ratio)
        self._lbl_progreso_num.configure(text=f"{self._fotos_tomadas} / {TOTAL_FOTOS}")

    def _finalizar_captura(self):
        self._loop_activo = False
        if self._cap:
            self._cap.release()
            self._cap = None

        alias       = self._alias_trabajador
        nombre_real = self._nombre_real

        self._lbl_resultado_icono.configure(text="✅")
        self._lbl_resultado_titulo.configure(
            text=f"Trabajador registrado",
            text_color=ESTILOS["verde"][0],
        )
        self._lbl_resultado_detalle.configure(
            text=(
                f"Alias: {alias}\n"
                f"{'Nombre: ' + nombre_real + chr(10) if nombre_real else ''}"
                f"{TOTAL_FOTOS} fotos capturadas con liveness verificado.\n\n"
                f"Registrado por: {self._supervisor_nombre}"
            )
        )
        self._mostrar_panel("resultado")

    # ──────────────────────────────────────────────────────────────────────────
    # CANCELAR / NUEVO REGISTRO / CERRAR
    # ──────────────────────────────────────────────────────────────────────────

    def _cancelar_captura(self):
        self._loop_activo = False
        if self._cap:
            self._cap.release()
            self._cap = None
        self._mostrar_panel("datos")

    def _nuevo_registro(self):
        self._alias_trabajador = ""
        self._nombre_real      = ""
        self._fotos_tomadas    = 0
        self._entry_alias.delete(0, tk.END)
        self._entry_nombre.delete(0, tk.END)
        self._lbl_datos_error.configure(text="")
        self._mostrar_panel("datos")

    def _cerrar(self):
        self._loop_activo = False
        if self._cap:
            self._cap.release()
        self.destroy()

    def on_closing(self):
        self._cerrar()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = RegistroTrabajadorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
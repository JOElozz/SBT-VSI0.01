import tkinter as tk
import customtkinter as ctk
from PIL import Image
import cv2
import time
import threading
import winsound
import os
import datetime
import requests
import serial

# Importar componentes de visión, evaluación e identificación 
from vision_core import AnalizadorVision
from evaluador_prolog import EvaluadorProlog
from identificador import IdentificadorTrabajador

RUTA_MODELO   = r"runs\detect\train5\weights\best.pt"
RUTA_REGLAS   = r"reglas.pl"
CARPETA_FOTOS = r"fotos_trabajadores"
TIEMPO_COOLDOWN = 6
# comunicacion con arduino para paro seguro
try:
    arduino = serial.Serial('COM3', 9600, timeout=0.1)
except Exception as e:
    print(f"No se pudo conectar con Arduino: {e}")
    arduino = None


CARPETA_EVIDENCIAS = "evidencias"
if not os.path.exists(CARPETA_EVIDENCIAS):
    os.makedirs(CARPETA_EVIDENCIAS)

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

FASES_AUDITORIA = [
    {
        "nombre": "CABEZA Y CARA",
        "clases_ok": ['Helmet', 'Glass'],
        "clases_mal": ['No-Helmet', 'No-Glass'],
        "tiempo": 4.0,
        "instruccion": "ACÉRCATE a la cámara",
        "zona_prolog": "cabeza"
    },
    {
        "nombre": "TORSO",
        "clases_ok": ['Vest'],
        "clases_mal": ['No-Vest'],
        "tiempo": 5.0,
        "instruccion": "ALÉJATE para mostrar el chaleco",
        "zona_prolog": "torso"
    },
    {
        "nombre": "MANOS",
        "clases_ok": ['Glove'],
        "clases_mal": ['No-Glove'],
        "tiempo": 4.0,
        "instruccion": "MUESTRA LOS GUANTES a la cámara",
        "zona_prolog": "manos"
    },
    {
        "nombre": "BOTAS",
        "clases_ok": ['Boots'],
        "clases_mal": ['No-Boots'],
        "tiempo": 4.0,
        "instruccion": "PANEO A LAS BOTAS",
        "zona_prolog": "botas"
    }
]

TRADUCCION = {
    'helmet': 'Casco',
    'vest':   'Chaleco',
    'glove':  'Guantes',
    'glass':  'Lentes',
    'boots':  'Botas'
}

# --- PALETA DE COLORES (TEMA CLARO) ---
ESTILOS = {
    "fondo_principal": "#f8f9fa",
    "fondo_panel": "#ffffff",
    "texto_titulos": "#212529",
    "texto_normal": "#495057",
    "texto_secundario": "#6c757d",
    
    # Colores de Estado (Formato: [Color claro, Color en hover/borde])
    "color_estado_identificando": ["#0d6efd", "#0b5ed7"], # Azul
    "color_estado_escaneando":    ["#ffc107", "#ffca2c"], # Amarillo/Naranja
    "color_estado_denegado":      ["#dc3545", "#b02a37"], # Rojo
    "color_estado_autorizado":    ["#198754", "#146c43"], # Verde
}

def emitir_sonido_async(tipo):
    def reproducir():
        if tipo == "EXITO":
            winsound.Beep(1200, 150)
            time.sleep(0.05)
            winsound.Beep(1600, 250)
        elif tipo == "ERROR":
            winsound.Beep(600, 500)
            time.sleep(0.1)
            winsound.Beep(600, 500)
        elif tipo == "FASE_OK":
            winsound.Beep(1000, 100)
    threading.Thread(target=reproducir, daemon=True).start()

def enviar_a_scala(resultado, fase, faltante="", trabajador_id="DESCONOCIDO"):
    """Envía el resultado de la auditoría al servidor Scala usando un identificador seguro."""
    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        requests.post("http://localhost:9000/auditoria", json={
            "timestamp":     ts,
            "resultado":     resultado,
            "fase":          fase,
            "faltante":      faltante,
            "trabajador_id": trabajador_id
        }, timeout=2)
    except Exception:
        pass


class SALVIDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("A.R.G.O.S ")
        self.geometry("1350x700")

        # Inicializar los tres módulos principales
        self.vision        = AnalizadorVision(RUTA_MODELO)
        self.prolog        = EvaluadorProlog(RUTA_REGLAS)
        self.identificador = IdentificadorTrabajador(CARPETA_FOTOS)

        # Variables de estado
        self.estado            = "IDENTIFICANDO"
        self.trabajador_actual = None
        self.fase_actual_idx   = 0
        self.detecciones_fase  = []
        self.inicio_etapa      = time.time()
        self.color_estado      = ("#3B8ED0", "#1F6AA5")
        self.start_scan_requested = False

        # Layout principal
        self.configure(fg_color=ESTILOS["fondo_principal"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Panel izquierdo
        self.panel_info = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=ESTILOS["fondo_panel"])
        self.panel_info.grid(row=0, column=0, sticky="nsew")
        self.panel_info.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            self.panel_info,
            text="Auditoría Secuencial",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=ESTILOS["texto_titulos"]
        ).grid(row=0, column=0, padx=20, pady=(20, 5))

        # Etiqueta del trabajador identificado
        self.label_trabajador = ctk.CTkLabel(
            self.panel_info,
            text="SIN IDENTIFICAR",
            font=ctk.CTkFont(size=13),
            text_color=ESTILOS["texto_secundario"]
        )
        self.label_trabajador.grid(row=1, column=0, padx=20, pady=(5, 0))

        self.label_estado = ctk.CTkLabel(
            self.panel_info,
            text="IDENTIFICANDO",
            corner_radius=5,
            fg_color=self.color_estado,
            text_color="white", # El texto sobre el color siempre será blanco
            font=ctk.CTkFont(size=18, weight="bold"),
            width=240,
            height=50
        )
        self.label_estado.grid(row=3, column=0, padx=20, pady=(20, 10))

        self.text_detalles = ctk.CTkTextbox(
            self.panel_info,
            width=240,
            height=240,
            font=ctk.CTkFont(size=13),
            fg_color=ESTILOS["fondo_principal"],
            text_color=ESTILOS["texto_normal"]
        )
        self.text_detalles.grid(row=4, column=0, padx=20, pady=10)
        self.text_detalles.configure(state="disabled")

        ctk.CTkLabel(
            self.panel_info,
            text="S INICIAR  |  R REINTENTAR  |  Q SALIR",
            justify="center",
            text_color=ESTILOS["texto_secundario"]
        ).grid(row=9, column=0, padx=20, pady=20)

        # Panel central — cámara en vivo
        self.panel_video = ctk.CTkFrame(self, corner_radius=10, fg_color=ESTILOS["fondo_panel"])
        self.panel_video.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")
        ctk.CTkLabel(
            self.panel_video,
            text="CÁMARA EN VIVO",
            font=ctk.CTkFont(weight="bold"),
            text_color=ESTILOS["texto_titulos"]
        ).pack(pady=10)
        self.label_video = ctk.CTkLabel(self.panel_video, text="")
        self.label_video.pack(expand=True, fill="both", padx=10, pady=10)

        # Panel derecho — evidencia
        self.panel_evidencia = ctk.CTkFrame(self, corner_radius=10, fg_color=ESTILOS["fondo_panel"]) # <--- AQUÍ LE QUITAMOS EL GRIS OSCURO
        self.panel_evidencia.grid(row=0, column=2, padx=10, pady=20, sticky="nsew")
        ctk.CTkLabel(
            self.panel_evidencia,
            text="EVIDENCIA",
            font=ctk.CTkFont(weight="bold"),
            text_color="#dc3545" # Rojo brillante
        ).pack(pady=10)
        self.label_evidencia = ctk.CTkLabel(
            self.panel_evidencia,
            text="SIN INFRACCIONES REGISTRADAS",
            font=ctk.CTkFont(size=16),
            text_color=ESTILOS["texto_secundario"]
        )
        self.label_evidencia.pack(expand=True, fill="both", padx=10, pady=10)

        # Atajos de teclado
        self.bind('<KeyPress-s>', self.solicitar_escaneo)
        self.bind('<KeyPress-q>', self.on_closing)
        self.bind('<KeyPress-r>', self.reintentar_identificacion)
        self.bind('<F5>',         self.recargar_trabajadores)

        # Placeholder de evidencia
        img_vacia = Image.new('RGB', (480, 360), color=(240, 240, 240)) # <--- GRIS CLARO PARA EL FONDO
        self.img_tk_vacia = ctk.CTkImage(
            light_image=img_vacia,
            dark_image=img_vacia,
            size=(480, 360)
        )

        emitir_sonido_async("EXITO")
        self.bucle_principal()

    def bucle_principal(self):
        ahora = time.time()

        clases_buscadas = ["Person"]
        if self.estado == "ESCANEANDO":
            fase = FASES_AUDITORIA[self.fase_actual_idx]
            clases_buscadas = fase["clases_ok"] + fase["clases_mal"]

        exito, frame, objetos_detectados_ahora = self.vision.procesar_frame(clases_buscadas)

        if exito:
            # NUEVO BLOQUE: ORQUESTADOR DE SEGURIDAD (PIR + PROLOG)
            mensaje_arduino = "DESPEJADO"

            #LEER EL DATO DEL HARDWARE (PIR)
            if arduino is not None and arduino.in_waiting > 0:
                mensaje_arduino = arduino.readline().decode('utf-8').strip()
            # RESOLUCION SLD (PROLOG) PARA EL PARO SEGURO
            permiso_operar_pir = self.prolog.evaluar_paro_seguro(mensaje_arduino)
            # LOGICA DE ACTUACION:
            #LA MAQUINA SOLO ARRANCARA SI EL PIR ESTA LIBRE (Prolog = True )
            #Y EL TRABAJADOR PASO LA AUDITORIA (self.estado = " AUTORIZADO")
            if permiso_operar_pir and self.estado == "AUTORIZADO":
                if arduino: arduino.write(b'1') #Arrancar maquina
                alerta_texto = "ZONA SEGURA: MAQUINA OPERATIVA"
                color_alerta = (0, 255, 0) #verde RGB
            else:
                if arduino: arduino.write(b'0')# paro inmediato
                alerta_texto = "¡MAQUINA BLOQUEADA / PARO ACTIVADO!"
                color_alerta = (0, 0, 255) #rojo RGB
            #SI EL ESTADO ES AUTORIZADO, PERO EL PIR DETECTA ALGO, ES UNA INTRUSION
            if self.estado == "AUTORIZADO" and not permiso_operar_pir:
                alerta_texto = "¡INTRUSION! PARO DE EMERGENCIA"
            #DIBUJAR ALERTA DIRECTAMENTE EN EL VIDEO
            cv2.rectangle(frame, (10, 10), (500, 40), (0, 0, 0), -1 )
            cv2.putText(frame, alerta_texto, (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2)
            
            # ── IDENTIFICANDO ──────────────────────────────────────────────
            if self.estado == "IDENTIFICANDO":
                self.color_estado = ("#3B8ED0", "#1F6AA5")
                nombre, frame = self.identificador.identificar(frame)

                if nombre:
                    self.trabajador_actual = nombre
                    self.label_trabajador.configure(
                        text=f" {nombre}",
                        text_color="#2cc985"
                    )
                    self.actualizar_texto(
                        f" BIENVENIDO\n{nombre}\n\n"
                        f"Colócate el EPP\ny presiona S\npara iniciar la auditoría."
                    )
                    self.estado = "ESPERA"
                    emitir_sonido_async("FASE_OK")
                else:
                    self.actualizar_texto(
                        "IDENTIFICANDO....\n\n"
                        "Mire a la cámara\nsin casco ni lentes\npara ser reconocido."
                    )

            # ── ESCANEANDO ─────────────────────────────────────────────────
            elif self.estado == "ESCANEANDO":
                fase = FASES_AUDITORIA[self.fase_actual_idx]
                transcurrido    = ahora - self.inicio_etapa
                tiempo_restante = max(0, fase["tiempo"] - transcurrido)

                self.color_estado = ("#ffcc00", "#ccaa00")
                total_fases = len(FASES_AUDITORIA)

                texto_pantalla = (
                    f"Fase {self.fase_actual_idx + 1}/{total_fases}: {fase['nombre']}\n\n"
                    f" {fase['instruccion']} \n\n"
                    f"Buscando:\n- " + "\n- ".join(fase['clases_ok']) +
                    f"\n\nTiempo: {tiempo_restante:.1f}s"
                )
                self.actualizar_texto(texto_pantalla)
                self.detecciones_fase.extend(objetos_detectados_ahora)

                progreso = int((transcurrido / fase["tiempo"]) * 640)
                cv2.rectangle(frame, (0, 0), (progreso, 10), (0, 255, 255), -1)

                if transcurrido >= fase["tiempo"]:
                    detectados_lower = [d.lower() for d in set(self.detecciones_fase)]
                    aprobada, faltantes_prolog = self.prolog.evaluar_fase(
                        fase["zona_prolog"], detectados_lower
                    )

                    if not aprobada:
                        emitir_sonido_async("ERROR")
                        self.estado = "DENEGADO"
                        self.color_estado = ("#e04f5f", "#c0392b")

                        faltan_str = "\n- ".join([TRADUCCION.get(f, f) for f in faltantes_prolog])
                        self.actualizar_texto(
                            f"FALLA EN: {fase['nombre']}\n\n"
                            f"Falta el siguiente equipo:\n- {faltan_str}\n\n"
                            f"ACCESO DENEGADO."
                        )

                        self.mostrar_evidencia(frame)
                        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        cv2.imwrite(
                            os.path.join(CARPETA_EVIDENCIAS, f"falla_{ts}.jpg"),
                            frame
                        )

                        faltante_str = ", ".join([TRADUCCION.get(f, f) for f in faltantes_prolog])
                        enviar_a_scala(
                            "DENEGADO",
                            fase['nombre'],
                            faltante_str,
                            self.trabajador_actual or "DESCONOCIDO"
                        )
                        self.inicio_etapa = ahora
                    else:
                        self.fase_actual_idx += 1
                        if self.fase_actual_idx < len(FASES_AUDITORIA):
                            emitir_sonido_async("FASE_OK")
                            self.inicio_etapa = ahora
                            self.detecciones_fase = []
                        else:
                            emitir_sonido_async("EXITO")
                            self.estado = "AUTORIZADO"
                            self.color_estado = ("#2cc985", "#2fa572")
                            self.actualizar_texto(
                                f"VEREDICTO FINAL:\n\n"
                                f"AUDITORÍA SUPERADA.\n"
                                f"EQUIPO COMPLETO.\n\n"
                                f"PUEDE INGRESAR\n{self.trabajador_actual or ''}."
                            )
                            self.inicio_etapa = ahora
                            enviar_a_scala(
                                "AUTORIZADO",
                                "COMPLETO",
                                "",
                                self.trabajador_actual or "DESCONOCIDO"
                            )

            # ── AUTORIZADO / DENEGADO ──────────────────────────────────────
            elif self.estado in ["AUTORIZADO", "DENEGADO"]:
                if ahora - self.inicio_etapa >= TIEMPO_COOLDOWN:
                    self.estado = "IDENTIFICANDO"
                    self.trabajador_actual = None
                    self.label_trabajador.configure(
                        text="SIN IDENTIFICAR",
                        text_color="#888888"
                    )

            # ── ESPERA ─────────────────────────────────────────────────────
            elif self.estado == "ESPERA":
                self.color_estado = ("#3B8ED0", "#1F6AA5")
                self.actualizar_texto(
                    f"SISTEMA LISTO\n\n"
                    f"👤 {self.trabajador_actual}\n\n"
                    f"COLÓCATE EL EPP Y\nPRESIONA [S] PARA\nINICIAR EL ESCANEADO."
                )
                if self.start_scan_requested:
                    self.estado = "ESCANEANDO"
                    self.fase_actual_idx = 0
                    self.inicio_etapa = ahora
                    self.detecciones_fase = []
                    self.start_scan_requested = False
                    self.label_evidencia.configure(image=self.img_tk_vacia, text="")

            # Renderizar fotograma
            self.label_estado.configure(text=self.estado, fg_color=self.color_estado)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil   = Image.fromarray(frame_rgb)
            img_tk    = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(480, 360))
            self.label_video.configure(image=img_tk)
            self.label_video.image = img_tk

        self.after(15, self.bucle_principal)

    def mostrar_evidencia(self, frame_cv2):
        frame_rgb = cv2.cvtColor(frame_cv2, cv2.COLOR_BGR2RGB)
        img_pil   = Image.fromarray(frame_rgb)
        img_tk    = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(480, 360))
        self.label_evidencia.configure(image=img_tk, text="")
        self.label_evidencia.image = img_tk

    def solicitar_escaneo(self, event=None):
        if self.estado == "ESPERA":
            self.start_scan_requested = True

    def reintentar_identificacion(self, event=None):
        if self.estado in ["ESPERA", "IDENTIFICANDO"]:
           self.estado = "IDENTIFICANDO"
           self.trabajador_actual = None
           self.label_trabajador.configure(
            text="SIN IDENTIFICAR",
            text_color="#888888"
        )
        self.actualizar_texto(
            "REINTENTANDO...\n\n"
            "Mire a la cámara\nsin casco ni lentes."
        )

    

    def actualizar_texto(self, texto):
        self.text_detalles.configure(state="normal")
        self.text_detalles.delete("1.0", tk.END)
        self.text_detalles.insert("1.0", texto)
        self.text_detalles.configure(state="disabled")

    def recargar_trabajadores(self, event=None):
        if self.estado == "IDENTIFICANDO":
            self.actualizar_texto("Recargando trabajadores...\nEspera un momento.")
            threading.Thread(target=self._recargar_async, daemon=True).start()

    def _recargar_async(self):
        self.identificador.recargar()
        total = len(self.identificador.conocidos_aliases)
        self.after(0, lambda: self.actualizar_texto(
            f"✅ {total} trabajador(es) cargado(s).\n\n"
            f"Mire a la cámara\nsin casco ni lentes\npara ser reconocido."
        ))

    def on_closing(self, event=None):
        self.vision.liberar_camara()
        self.destroy()


if __name__ == "__main__":  
    app = SALVIDashboard()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()



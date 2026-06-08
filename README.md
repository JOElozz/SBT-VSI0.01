# ARGOS — Sistema de Auditoría de EPP

Resumen rápido

ARGOS es una plataforma de auditoría de Equipos de Protección Personal (EPP) que combina:
- Cliente Python (detección en tiempo real con YOLO y reconocimiento facial)
- Motor de reglas Prolog para validación
- Servidor Scala/Play que guarda auditorías en SQLite y muestra un dashboard

Estructura principal

- `proyecto_yolo/`  — Cliente Python (detección, identificación, UI)
  - `main_app.py` — Aplicación principal de auditoría
  - `capturar_trabajador.py` — Registro y captura de fotos de trabajador
  - `identificador.py` — Carga de encodings faciales
  - `vision_core.py` — Wrapper de detección YOLO
  - `evaluador_prolog.py` + `reglas.pl` — Validación de reglas
  - `fotos_trabajadores/` — Fotos por trabajador
  - `evidencias/` — Imágenes guardadas en fallas
  - `runs/detect/.../weights/best.pt` — Modelo YOLO entrenado

- `argos-server/` — Backend Scala/Play
  - `conf/routes` — Endpoints HTTP
  - `app/controllers/HomeController.scala` — Handlers API
  - `app/models/` — Repositorios `HistorialRepository`, `TrabajadorRepository`
  - `public/javascripts/argos.js` — Lógica del dashboard
  - Evolutions SQL que crean tablas `historial` y `trabajadores`

Base de datos

- Tipo: **SQLite** (archivo `argos_auditoria.db`)
- Tablas principales: `historial` (auditorías), `trabajadores` (registro de empleados)

Endpoints relevantes

- `POST /auditoria` — Recibe los resultados de auditoría (timestamp, resultado, fase, faltante, trabajador_id)
- `POST /trabajadores` — Registra un trabajador (alias, nombre_real)
- `GET /historial` — Lista todo el historial
- `GET /historial/hoy` — Registros del día (usado por el dashboard)

Requisitos (vista general)

- Python 3.8+
- Entorno virtual (`venv` o similar)
- Paquetes Python sugeridos (instalar en el venv):
  - `opencv-python`
  - `face_recognition` (y `dlib`; en Windows requiere compilación/ruedas)
  - `pyswip` (cliente SWI-Prolog)
  - `requests`
  - `customtkinter` o `tkinter` (UI)
  - `ultralytics` o la librería que uses para ejecutar el modelo YOLO

- Java JDK 11+ (para Play Framework / sbt)
- `sbt` (Scala build tool)

Instalación y ejecución (rápida)

1. Preparar entorno Python (ejemplo Windows PowerShell):

```powershell
cd proyecto_yolo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install opencv-python face_recognition pyswip requests customtkinter ultralytics
```

Notas: `face_recognition` y `dlib` pueden requerir pasos adicionales en Windows (ruedas precompiladas o Visual C++ build tools).

2. Ejecutar servidor Scala/Play (desde la raíz del servidor):

```bash
cd argos-server
sbt run
```

El servidor por defecto escucha en `http://localhost:9000`.

3. Registrar un trabajador (captura de fotos):

```powershell
cd proyecto_yolo
.\.venv\Scripts\Activate.ps1
python capturar_trabajador.py
```

Sigue las instrucciones en pantalla; el script guardará fotos en `fotos_trabajadores/TRAB-XXXX/` y enviará `POST /trabajadores`.

4. Ejecutar la aplicación de auditoría (cliente):

```powershell
cd proyecto_yolo
.\.venv\Scripts\Activate.ps1
python main_app.py
```

- Ajusta la cámara si es necesario (configuración en `main_app.py`, por defecto usa `cv2.VideoCapture(2)`).
- Asegúrate de que el servidor (`sbt run`) esté corriendo para enviar resultados. Si no está disponible, la app captura localmente evidencia y continúa.

Evidencias y registros

- Imágenes de fallas guardadas en `proyecto_yolo/evidencias/`.
- Auditorías se almacenan en la base de datos SQLite (`argos_auditoria.db`) y se muestran en el dashboard en `http://localhost:9000`.

Consejos y notas útiles

- Si hay problemas con `pyswip`, instala SWI-Prolog en el sistema y verifica que `swipl` esté en el PATH.
- Para entrenar/actualizar el modelo YOLO, usa los scripts y la carpeta `runs/` (fuera del alcance de este README resumido).
- En Windows, activa el entorno con `.\.venv\Scripts\Activate.ps1` (PowerShell) o `.\.venv\Scripts\activate.bat` (cmd).

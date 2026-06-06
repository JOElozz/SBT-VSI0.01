import cv2
import os
import re
import requests

SERVER_URL = "http://localhost:9000"
CAPTURA_URL = f"{SERVER_URL}/trabajadores"


def normalizar_alias(alias: str) -> str:
    alias = alias.strip().upper()
    alias = re.sub(r"[^A-Z0-9_-]", "_", alias)
    if not alias:
        return alias
    if not alias.startswith("TRAB-"):
        alias = f"TRAB-{alias}"
    return alias


def registrar_trabajador_servidor(alias: str, nombre_real: str):
    try:
        response = requests.post(
            CAPTURA_URL,
            json={"alias": alias, "nombre_real": nombre_real},
            timeout=3
        )
        if response.ok:
            print(f"Alias {alias} registrado en el servidor.")
        else:
            print(f"Advertencia: no se pudo registrar en el servidor ({response.status_code}).")
    except Exception as exc:
        print(f"Advertencia: no se pudo conectar con el servidor para registrar al trabajador: {exc}")


alias = input("Alias seguro del trabajador (ej. TRAB-1234): ").strip()
while not alias:
    alias = input("Alias obligatorio. Ingrese alias seguro: ").strip()

alias = normalizar_alias(alias)
if not alias:
    raise SystemExit("Alias inválido.")

registrar_nombre = input("¿Desea registrar el nombre real en el servidor? (s/N): ").strip().lower() == "s"
nombre_real = ""
if registrar_nombre:
    nombre_real = input("Nombre real del trabajador: ").strip()
    if not nombre_real:
        print("Nombre real vacío, no se registrará en el servidor.")

carpeta = os.path.join("fotos_trabajadores", alias)
os.makedirs(carpeta, exist_ok=True)

# Contar fotos existentes para no sobreescribir
fotos_existentes = len([f for f in os.listdir(carpeta) if f.lower().endswith((".jpg", ".png"))])

cap = cv2.VideoCapture(2)
fotos_tomadas = 0
total_fotos = 5

print(f"\nCapturando {total_fotos} fotos para alias {alias}...")
print("PRESIONA LA TECLA C PARA TOMAR LA FOTO")
print("PRESIONA LA TECLA Q PARA CANCELAR Y SALIR\n")

if registrar_nombre and nombre_real:
    registrar_trabajador_servidor(alias, nombre_real)

while fotos_tomadas < total_fotos:
    ret, frame = cap.read()
    if not ret:
        print("Error: No se puede leer la señal de la cámara.")
        break

    frame_visualizado = frame.copy()
    alto, ancho = frame_visualizado.shape[:2]

    tamaño_box = 200
    x1 = (ancho // 2) - (tamaño_box // 2)
    y1 = (alto // 2) - (tamaño_box // 2)
    x2 = x1 + tamaño_box
    y2 = y1 + tamaño_box

    cv2.rectangle(frame_visualizado, (x1, y1), (x2, y2), (252, 252, 252), 2)

    restantes = total_fotos - fotos_tomadas
    cv2.putText(
        frame_visualizado,
        f"Alias: {alias}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        frame_visualizado,
        f"Restantes: {restantes} (Presiona 'C')",
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2,
    )

    cv2.imshow("Registro de trabajador", frame_visualizado)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord("c") or tecla == ord("C"):
        idx = fotos_existentes + fotos_tomadas + 1
        ruta = os.path.join(carpeta, f"{idx}.jpg")

        cv2.imwrite(ruta, frame)
        print(f"Foto {fotos_tomadas + 1}/{total_fotos} guardada en {ruta}")
        fotos_tomadas += 1

    elif tecla == ord("q") or tecla == ord("Q"):
        print("Captura interrumpida")
        break

cap.release()
cv2.destroyAllWindows()

if fotos_tomadas > 0:
    print(f"\nAlias {alias} registrado con {fotos_tomadas} fotos.")
else:
    print(f"\nNo se guardaron fotos de alias {alias}.")
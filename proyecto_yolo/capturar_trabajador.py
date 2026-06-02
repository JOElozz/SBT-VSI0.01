import cv2
import os

nombre = input("Nombre del trabajador: ").strip().lower()
carpeta = os.path.join("fotos_trabajadores", nombre)
os.makedirs(carpeta, exist_ok=True)

# Contar fotos existentes para no sobreescribir
fotos_existentes = len(os.listdir(carpeta))

cap = cv2.VideoCapture(2) 
fotos_tomadas = 0
total_fotos = 5

print(f"\nCapturando {total_fotos} fotos de {nombre}...")
print("PRESIONA LA TECLA C PARA TOMAR LA FOTO ")
print("PRESIONA LA TECLA Q PARA CANCELAR Y SALIR\n")

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
    cv2.putText(frame_visualizado, f"Restantes: {restantes} (Presiona 'C')",
                (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(frame_visualizado, f"Trabajador: {nombre.upper()}",
                (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    
    cv2.imshow("Registro de trabajador", frame_visualizado)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord('c') or tecla == ord('C'):
        idx = fotos_existentes + fotos_tomadas + 1
        ruta = os.path.join(carpeta, f"{idx}.jpg")
        
        cv2.imwrite(ruta, frame) 
        
        print(f"Foto {fotos_tomadas + 1}/{total_fotos} guardada en {ruta}")
        fotos_tomadas += 1
        
        
    elif tecla == ord('q') or tecla == ord('Q'):
        print("Captura interrumpida")
        break

cap.release()
cv2.destroyAllWindows()

if fotos_tomadas > 0:
    print(f"\n{nombre.upper()} registrado con {fotos_tomadas} fotos.")
else:
    print(f"\nNo se guardaron fotos de {nombre.upper()}.")
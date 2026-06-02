# vision_core.py
import cv2
from ultralytics import YOLO

class AnalizadorVision:
    def __init__(self, ruta_modelo, conf_min=0.30):
        # Inicializamos YOLO y la cámara
        self.modelo = YOLO(ruta_modelo)
        self.conf_min = conf_min
        self.cap = cv2.VideoCapture(2)

    def procesar_frame(self, clases_buscadas):
        """
        Lee la cámara, busca las clases solicitadas y dibuja los recuadros.
        Retorna: (exito_bool, frame_pintado, lista_de_objetos_detectados)
        """
        ret, frame = self.cap.read()
        if not ret:
            return False, None, []

         # Voltear el fotograma para vista de espejo
        
        # Ejecutar detección sobre el fotograma
        resultados = self.modelo(frame, stream=True, conf=self.conf_min, verbose=False)
        objetos_detectados = []

        for r in resultados:
            for box in r.boxes:
                cls = int(box.cls[0])
                nombre = self.modelo.names[cls]
                
                # Solo procesar lo que nos interesa buscar en esta fase
                if nombre in clases_buscadas:
                    objetos_detectados.append(nombre)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Dibujar cuadro delimitador y etiqueta
                    color = (0, 0, 255) if "No-" in nombre else (0, 255, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, nombre, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return True, frame, objetos_detectados

    def liberar_camara(self):
        self.cap.release()
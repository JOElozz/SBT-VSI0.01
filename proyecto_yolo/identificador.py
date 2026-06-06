import face_recognition
import cv2
import os

class IdentificadorTrabajador:
    def __init__(self, carpeta_base="fotos_trabajadores"):
        self.carpeta_base = carpeta_base
        self.conocidos_encodings = []
        self.conocidos_aliases = []
        self._cargar_rostros(carpeta_base)

    def recargar(self):
        self.conocidos_encodings = []
        self.conocidos_aliases   = []
        self._cargar_rostros(self.carpeta_base)
        print(f"[IDENTIFICADOR] Recargado: {len(self.conocidos_aliases)} trabajadores en memoria.")

    def _cargar_rostros(self, carpeta_base):
        if not os.path.exists(carpeta_base):
            os.makedirs(carpeta_base)
            print(f"Carpeta '{carpeta_base}' creada. Registra trabajadores primero.")
            return

        # Cada subcarpeta es un trabajador y debe contener un alias seguro
        for nombre in os.listdir(carpeta_base):
            ruta_trabajador = os.path.join(carpeta_base, nombre)
            if not os.path.isdir(ruta_trabajador):
                continue

            alias = nombre.strip().upper()
            fotos_cargadas = 0
            for archivo in os.listdir(ruta_trabajador):
                if not archivo.endswith((".jpg", ".png")):
                    continue
                ruta_foto = os.path.join(ruta_trabajador, archivo)
                img = face_recognition.load_image_file(ruta_foto)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    self.conocidos_encodings.append(encodings[0])
                    self.conocidos_aliases.append(alias)
                    fotos_cargadas += 1

            if fotos_cargadas > 0:
                print(f"{alias} cargado con {fotos_cargadas} fotos")
            else:
                print(f"{alias} no tiene fotos válidas")

    def identificar(self, frame):
        """
        Analiza el frame y retorna el alias seguro si reconoce a alguien.
        Retorna: (alias o None, frame con recuadro dibujado)
        """
        frame_pequeño = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(frame_pequeño, cv2.COLOR_BGR2RGB)

        ubicaciones = face_recognition.face_locations(rgb)
        encodings   = face_recognition.face_encodings(rgb, ubicaciones)

        for encoding, ubicacion in zip(encodings, ubicaciones):
            resultados = face_recognition.compare_faces(
                self.conocidos_encodings, encoding, tolerance=0.55
            )
            top, right, bottom, left = [v * 4 for v in ubicacion]

            if True in resultados:
                idx   = resultados.index(True)
                alias = self.conocidos_aliases[idx]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, alias, (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                return alias, frame
            else:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.putText(frame, "DESCONOCIDO", (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        return None, frame
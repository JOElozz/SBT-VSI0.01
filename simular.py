import sqlite3
import random
from datetime import datetime, timedelta

# Ruta a tu base de datos
ruta_db = r"argos-server\argos_auditoria.db"

# Listas de datos para simular
trabajadores = ["ANNETE", "NOE", "JHOSEP", "ITALIA", "AXEL"]
fases = ["CABEZA Y CARA", "TORSO", "MANOS", "BOTAS"]
faltantes_posibles = ["Casco", "Lentes", "Casco, Lentes", "Guantes", "Chaleco", "Botas"]

def generar_datos_simulados(cantidad=50):
    """Genera una lista de tuplas con datos aleatorios."""
    datos = []
    # Usamos la fecha y hora actual como punto de partida
    fecha_base = datetime.now()
    
    for _ in range(cantidad):
        # 1. Elegir trabajador y fase al azar
        trabajador = random.choice(trabajadores)
        fase = random.choice(fases)
        
        # 2. Decidir si fue Autorizado o Denegado (70% denegado, 30% autorizado para ver la dona)
        es_denegado = random.random() < 0.7 
        resultado = "DENEGADO" if es_denegado else "AUTORIZADO"
        
        # 3. Asignar EPP faltante solo si fue denegado
        faltante = random.choice(faltantes_posibles) if es_denegado else ""
        
        # 4. Crear un Timestamp falso (restando minutos aleatorios para simular el pasado)
        minutos_restar = random.randint(1, 600) # Restar entre 1 minuto y 10 horas
        fecha_simulada = fecha_base - timedelta(minutes=minutos_restar)
        timestamp = fecha_simulada.strftime("%Y%m%d_%H%M%S")
        
        datos.append((trabajador, timestamp, resultado, fase, faltante))
        
    return datos

try:
    # Conectarse a la base de datos
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # 1. Generar 30 registros aleatorios (puedes cambiar el número)
    nuevos_registros = generar_datos_simulados(30)
    
    # 2. Insertarlos en la tabla 'historial'
    cursor.executemany("""
        INSERT INTO historial (trabajador, timestamp, resultado, fase, faltante) 
        VALUES (?, ?, ?, ?, ?)
    """, nuevos_registros)
    
    # Guardar cambios
    conexion.commit()
    
    print(f"¡Éxito! Se han inyectado {len(nuevos_registros)} registros simulados en la base de datos.")
    print("Abre tu dashboard en el navegador (y presiona F5) para ver las gráficas.")

except Exception as e:
    print(f"Hubo un error: {e}")
finally:
    conexion.close()
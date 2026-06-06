import sqlite3

# Ruta hacia tu base de datos (ajusta si se llama diferente)
ruta_db = r"argos-server\argos_auditoria.db"

try:
    # 1. Conectarnos a la base de datos
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    
    # 2. Borrar todo el historial de escaneos
    cursor.execute("DELETE FROM historial")
    
    # 3. TRUCO: Reiniciar el contador de IDs a cero
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='historial'")
    
    # --- Opcional: Borrar también a los trabajadores ---
    # Si también quieres borrar a las personas registradas, quita el '#' de las siguientes dos líneas:
    # cursor.execute("DELETE FROM trabajadores")
    # print("Se eliminaron los trabajadores.")

    # 4. Guardar los cambios
    conexion.commit()
    
    print("¡Éxito! La tabla 'historial' quedó vacía y el contador de IDs regresó a cero.")
    
except Exception as e:
    print(f"Hubo un error al limpiar la base de datos: {e}")
finally:
    conexion.close()
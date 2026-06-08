import sqlite3

conn = sqlite3.connect("argos-server/argos_auditoria.db")

print("=== TABLAS ===")
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tablas:
    print(" -", t[0])

print("\n=== USUARIOS ===")
try:
    usuarios = conn.execute("SELECT alias, rol, activo FROM usuarios").fetchall()
    if usuarios:
        for u in usuarios:
            print(f"  alias={u[0]}  rol={u[1]}  activo={u[2]}")
    else:
        print("  (tabla vacía)")
except Exception as e:
    print(" Error:", e)

conn.close()
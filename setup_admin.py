import sqlite3
import bcrypt
import os
import re

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "argos-server", "argos_auditoria.db"
)

# ── Roles disponibles ─────────────────────────────────────────────────────────
ROLES = ["supervisor", "admin"]

def validar_alias(alias: str) -> bool:
    return bool(re.match(r'^[A-Z0-9_-]{3,30}$', alias.strip().upper()))

def crear_usuario(alias: str, nombre: str, password: str, rol: str) -> None:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT INTO usuarios (alias, nombre, password_hash, rol, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (alias.strip().upper(), nombre.strip(), password_hash, rol))
        conn.commit()
        print(f"\n✅ Usuario '{alias.upper()}' creado con rol '{rol}'.")
        print("   Guarda bien la contraseña — no se puede recuperar, solo resetear.")
    except sqlite3.IntegrityError:
        print(f"\n⚠️  El alias '{alias.upper()}' ya existe en la base de datos.")
    finally:
        conn.close()

def listar_usuarios() -> None:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT alias, nombre, rol, activo FROM usuarios ORDER BY rol, alias"
    ).fetchall()
    conn.close()

    if not rows:
        print("\n  (No hay usuarios registrados aún)")
        return

    print(f"\n{'ALIAS':<20} {'NOMBRE':<25} {'ROL':<12} {'ESTADO'}")
    print("-" * 65)
    for alias, nombre, rol, activo in rows:
        estado = "✅ Activo" if activo else "🔴 Inactivo"
        print(f"{alias:<20} {nombre:<25} {rol:<12} {estado}")

def resetear_password(alias: str, nueva_password: str) -> None:
    nuevo_hash = bcrypt.hashpw(nueva_password.encode(), bcrypt.gensalt(10)).decode()
    conn = sqlite3.connect(DB_PATH)
    filas = conn.execute(
        "UPDATE usuarios SET password_hash = ? WHERE alias = ?",
        (nuevo_hash, alias.strip().upper())
    ).rowcount
    conn.commit()
    conn.close()
    if filas:
        print(f"\n✅ Contraseña de '{alias.upper()}' actualizada.")
    else:
        print(f"\n⚠️  Alias '{alias.upper()}' no encontrado.")

# ── Menú principal ─────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró la base de datos en:\n   {DB_PATH}")
        print("   Asegúrate de haber corrido el servidor Scala al menos una vez")
        print("   para que las evolutions creen las tablas.")
        return

    while True:
        print("\n══════════════════════════════════════")
        print("   A R G O S — Gestión de Usuarios")
        print("══════════════════════════════════════")
        print("  1 Crear usuario")
        print("  2 Listar usuarios")
        print("  3 Resetear contraseña")
        print("  4 Salir")
        print("──────────────────────────────────────")

        opcion = input("Opción: ").strip()

        if opcion == "1":
            print("\n── Nuevo usuario ──────────────────────")

            alias = input("Alias (solo letras, números, guiones): ").strip().upper()
            if not validar_alias(alias):
                print("❌ Alias inválido. Usa solo A-Z, 0-9, _ o -  (3-30 caracteres)")
                continue

            nombre = input("Nombre completo: ").strip()
            if not nombre:
                print("❌ El nombre no puede estar vacío.")
                continue

            print(f"Roles disponibles: {', '.join(ROLES)}")
            rol = input("Rol [supervisor]: ").strip().lower() or "supervisor"
            if rol not in ROLES:
                print(f"❌ Rol inválido. Elige entre: {', '.join(ROLES)}")
                continue

            password = input("Contraseña (mín. 8 caracteres): ").strip()
            if len(password) < 8:
                print("❌ La contraseña debe tener al menos 8 caracteres.")
                continue

            confirmacion = input("Confirma la contraseña: ").strip()
            if password != confirmacion:
                print("❌ Las contraseñas no coinciden.")
                continue

            crear_usuario(alias, nombre, password, rol)

        elif opcion == "2":
            listar_usuarios()

        elif opcion == "3":
            print("\n── Resetear contraseña ────────────────")
            listar_usuarios()
            alias = input("\nAlias a resetear: ").strip().upper()
            nueva = input("Nueva contraseña (mín. 8 caracteres): ").strip()
            if len(nueva) < 8:
                print("❌ La contraseña debe tener al menos 8 caracteres.")
                continue
            confirmacion = input("Confirma la nueva contraseña: ").strip()
            if nueva != confirmacion:
                print("❌ Las contraseñas no coinciden.")
                continue
            resetear_password(alias, nueva)

        elif opcion == "4":
            print("\nSaliendo...\n")
            break

        else:
            print("❌ Opción no válida.")

if __name__ == "__main__":
    main()
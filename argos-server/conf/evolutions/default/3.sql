# --- !Ups

CREATE TABLE usuarios (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    alias    TEXT NOT NULL UNIQUE,
    nombre   TEXT NOT NULL,
    password_hash TEXT NOT NULL,   -- BCrypt hash, nunca texto plano
    rol      TEXT NOT NULL DEFAULT 'supervisor',  -- 'supervisor' | 'admin'
    activo   INTEGER NOT NULL DEFAULT 1           -- 1=activo, 0=desactivado
);

-- Usuarios se crean con setup_admin.py (genera hash BCrypt válido)

# --- !Downs

DROP TABLE usuarios;
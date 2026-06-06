# --- !Ups

CREATE TABLE trabajadores (
    alias TEXT PRIMARY KEY,
    nombre_real TEXT NOT NULL
);

# --- !Downs

DROP TABLE trabajadores;

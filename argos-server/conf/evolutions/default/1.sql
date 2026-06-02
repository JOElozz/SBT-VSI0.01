# --- !Ups

CREATE TABLE historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trabajador TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    resultado TEXT NOT NULL,
    fase TEXT NOT NULL,
    faltante TEXT
);

# --- !Downs

DROP TABLE historial;
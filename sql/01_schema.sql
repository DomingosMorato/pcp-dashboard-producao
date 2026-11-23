-- Modelo de dados do projeto (SQLite / compatível com SQL Server e PostgreSQL com ajustes mínimos)

CREATE TABLE setores (
    setor_id              INTEGER PRIMARY KEY,
    setor                 TEXT    NOT NULL,
    capacidade_horas_mes  INTEGER NOT NULL
);

CREATE TABLE ordens_producao (
    op_id             TEXT PRIMARY KEY,
    cliente           TEXT NOT NULL,
    tipo_servico      TEXT NOT NULL,
    setor_id          INTEGER NOT NULL REFERENCES setores (setor_id),
    prioridade        TEXT CHECK (prioridade IN ('Alta', 'Média', 'Baixa')),
    data_abertura     DATE NOT NULL,
    data_inicio       DATE,
    data_prometida    DATE NOT NULL,
    data_conclusao    DATE,          -- nulo enquanto a OP está em andamento
    horas_planejadas  REAL,
    horas_realizadas  REAL,
    status            TEXT,
    motivo_atraso     TEXT
);

CREATE INDEX ix_op_setor     ON ordens_producao (setor_id);
CREATE INDEX ix_op_abertura  ON ordens_producao (data_abertura);

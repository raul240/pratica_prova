PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidade_medida TEXT NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade >= 0 AND quantidade <= 100),
    valor_unitario REAL NOT NULL CHECK (valor_unitario > 0)
);

CREATE TABLE IF NOT EXISTS entradas (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    data_entrada TEXT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE TABLE IF NOT EXISTS saidas (
    id INTEGER PRIMARY KEY,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    data_saida TEXT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE VIEW IF NOT EXISTS vw_estoque AS
SELECT
    id,
    nome,
    categoria,
    unidade_medida,
    quantidade,
    valor_unitario,
    quantidade * valor_unitario AS valor_total
FROM produtos;

INSERT OR IGNORE INTO produtos
    (id, nome, categoria, unidade_medida, quantidade, valor_unitario)
VALUES
    (1, 'Detergente', 'Limpeza geral', 'litro', 20, 8.50),
    (2, 'Desinfetante', 'Higienizacao', 'litro', 100, 12.00),
    (3, 'Saco de lixo', 'Descartaveis', 'pacote', 0, 15.90);

INSERT OR IGNORE INTO entradas (id, produto_id, quantidade, data_entrada)
VALUES
    (1, 1, 10, '2026-09-10'),
    (2, 2, 20, '2026-09-11'),
    (3, 3, 5, '2026-09-12');

INSERT OR IGNORE INTO saidas (id, produto_id, quantidade, data_saida)
VALUES
    (1, 1, 5, '2026-09-13'),
    (2, 2, 10, '2026-09-14'),
    (3, 3, 5, '2026-09-15');
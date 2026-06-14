-- ══════════════════════════════════════════════════════════════
-- ATHIVE SISTEMA v1.3 — Schema SQLite Local
-- Fonte da verdade. Supabase é espelho/backup.
-- ══════════════════════════════════════════════════════════════

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── Usuários ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id           TEXT PRIMARY KEY,
    nome         TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    senha_hash   TEXT NOT NULL,
    perfil       TEXT NOT NULL DEFAULT 'operador'
                     CHECK(perfil IN ('admin','financeiro','operador','visualizador')),
    unidade      TEXT NOT NULL DEFAULT 'Todas',
    ativo        INTEGER NOT NULL DEFAULT 1,
    criado_em    TEXT NOT NULL DEFAULT (datetime('now')),
    ultimo_login TEXT,
    synced       INTEGER NOT NULL DEFAULT 0
);

-- ── Alunos ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alunos (
    id              TEXT PRIMARY KEY,
    nome            TEXT NOT NULL,
    cpf             TEXT UNIQUE,
    data_nascimento TEXT,
    telefone        TEXT,
    email           TEXT,
    endereco        TEXT,
    unidade         TEXT NOT NULL CHECK(unidade IN ('Unidade 1','Unidade 2')),
    plano           TEXT NOT NULL DEFAULT 'Mensal',
    valor_plano     REAL NOT NULL DEFAULT 0,
    data_inicio     TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Ativo'
                        CHECK(status IN ('Ativo','Inativo','Suspenso','Inadimplente')),
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em   TEXT NOT NULL DEFAULT (datetime('now')),
    synced          INTEGER NOT NULL DEFAULT 0,
    deleted         INTEGER NOT NULL DEFAULT 0
);

-- ── Frequência ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS frequencia (
    id          TEXT PRIMARY KEY,
    aluno_id    TEXT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    data        TEXT NOT NULL DEFAULT (date('now')),
    hora_entrada TEXT,
    hora_saida  TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now')),
    synced      INTEGER NOT NULL DEFAULT 0
);

-- ── Equipamentos ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS equipamentos (
    id                  TEXT PRIMARY KEY,
    nome                TEXT NOT NULL,
    marca               TEXT,
    modelo              TEXT,
    numero_serie        TEXT,
    unidade             TEXT NOT NULL CHECK(unidade IN ('Unidade 1','Unidade 2')),
    categoria           TEXT NOT NULL DEFAULT 'Musculação',
    data_aquisicao      TEXT,
    valor_aquisicao     REAL DEFAULT 0,
    vida_util_anos      INTEGER DEFAULT 10,
    valor_residual      REAL DEFAULT 0,
    taxa_depreciacao    REAL DEFAULT 10.0,
    metodo_depreciacao  TEXT DEFAULT 'Linha reta'
                            CHECK(metodo_depreciacao IN ('Linha reta','Saldo decrescente')),
    status              TEXT NOT NULL DEFAULT 'Ativo'
                            CHECK(status IN ('Ativo','Em manutenção','Inativo','Descartado')),
    observacoes         TEXT,
    criado_em           TEXT NOT NULL DEFAULT (datetime('now')),
    synced              INTEGER NOT NULL DEFAULT 0,
    deleted             INTEGER NOT NULL DEFAULT 0
);

-- ── Manutenção ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS manutencao (
    id               TEXT PRIMARY KEY,
    equipamento_id   TEXT NOT NULL REFERENCES equipamentos(id) ON DELETE CASCADE,
    data_manutencao  TEXT NOT NULL DEFAULT (date('now')),
    tipo             TEXT NOT NULL CHECK(tipo IN ('Corretiva','Preventiva')),
    descricao        TEXT NOT NULL,
    valor            REAL NOT NULL DEFAULT 0,
    fornecedor       TEXT,
    nota_fiscal      TEXT,
    dias_parado      INTEGER NOT NULL DEFAULT 0,
    observacoes      TEXT,
    criado_em        TEXT NOT NULL DEFAULT (datetime('now')),
    synced           INTEGER NOT NULL DEFAULT 0,
    deleted          INTEGER NOT NULL DEFAULT 0
);

-- ── Financeiro ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS financeiro (
    id              TEXT PRIMARY KEY,
    tipo            TEXT NOT NULL CHECK(tipo IN ('Receita','Despesa')),
    categoria       TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,
    data_vencimento TEXT NOT NULL,
    data_pagamento  TEXT,
    status          TEXT NOT NULL DEFAULT 'Pendente'
                        CHECK(status IN ('Pendente','Pago','Atrasado','Cancelado')),
    unidade         TEXT NOT NULL,
    aluno_id        TEXT REFERENCES alunos(id) ON DELETE SET NULL,
    forma_pagamento TEXT,
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em   TEXT NOT NULL DEFAULT (datetime('now')),
    synced          INTEGER NOT NULL DEFAULT 0,
    deleted         INTEGER NOT NULL DEFAULT 0
);

-- ── Compras ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS compras (
    id              TEXT PRIMARY KEY,
    descricao       TEXT NOT NULL,
    categoria       TEXT NOT NULL DEFAULT 'Outros',
    fornecedor      TEXT,
    quantidade      REAL NOT NULL DEFAULT 1,
    unidade_medida  TEXT DEFAULT 'un',
    valor_unitario  REAL NOT NULL DEFAULT 0,
    valor_total     REAL NOT NULL DEFAULT 0,
    data_solicitacao TEXT NOT NULL DEFAULT (date('now')),
    data_entrega    TEXT,
    status          TEXT NOT NULL DEFAULT 'Solicitado'
                        CHECK(status IN ('Solicitado','Aprovado','Recebido','Cancelado')),
    unidade         TEXT NOT NULL,
    solicitante     TEXT,
    nota_fiscal     TEXT,
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    synced          INTEGER NOT NULL DEFAULT 0,
    deleted         INTEGER NOT NULL DEFAULT 0
);

-- ── Fila de sync ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sync_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tabela      TEXT NOT NULL,
    registro_id TEXT NOT NULL,
    operacao    TEXT NOT NULL CHECK(operacao IN ('INSERT','UPDATE','DELETE')),
    payload     TEXT,
    tentativas  INTEGER NOT NULL DEFAULT 0,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now')),
    enviado_em  TEXT
);

-- ── Log de sync ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sync_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio      TEXT NOT NULL,
    fim         TEXT,
    status      TEXT,
    enviados    INTEGER DEFAULT 0,
    erros       INTEGER DEFAULT 0,
    mensagem    TEXT
);

-- ── Índices ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_alunos_unidade    ON alunos(unidade);
CREATE INDEX IF NOT EXISTS idx_alunos_status     ON alunos(status);
CREATE INDEX IF NOT EXISTS idx_alunos_venc       ON alunos(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_freq_aluno        ON frequencia(aluno_id);
CREATE INDEX IF NOT EXISTS idx_freq_data         ON frequencia(data);
CREATE INDEX IF NOT EXISTS idx_manut_equip       ON manutencao(equipamento_id);
CREATE INDEX IF NOT EXISTS idx_manut_data        ON manutencao(data_manutencao);
CREATE INDEX IF NOT EXISTS idx_fin_tipo          ON financeiro(tipo);
CREATE INDEX IF NOT EXISTS idx_fin_status        ON financeiro(status);
CREATE INDEX IF NOT EXISTS idx_fin_venc          ON financeiro(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_compras_status    ON compras(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_tab    ON sync_queue(tabela, enviado_em);

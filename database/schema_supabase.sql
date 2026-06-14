-- ══════════════════════════════════════════════════════════════
-- ATHIVE SISTEMA v1.3 — Schema Supabase (backup em nuvem)
-- Execute no SQL Editor do Supabase UMA ÚNICA VEZ
-- Desenvolvido por Tech Oliveira · tech-oliveira.com.br
-- ══════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL, perfil TEXT NOT NULL DEFAULT 'operador',
    unidade TEXT NOT NULL DEFAULT 'Todas', ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT, ultimo_login TEXT, synced INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS alunos (
    id TEXT PRIMARY KEY, nome TEXT NOT NULL, cpf TEXT UNIQUE,
    data_nascimento TEXT, telefone TEXT, email TEXT, endereco TEXT,
    unidade TEXT NOT NULL, plano TEXT NOT NULL DEFAULT 'Mensal',
    valor_plano NUMERIC NOT NULL DEFAULT 0, data_inicio TEXT NOT NULL,
    data_vencimento TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Ativo',
    observacoes TEXT, criado_em TEXT, atualizado_em TEXT,
    synced INTEGER DEFAULT 1, deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS frequencia (
    id TEXT PRIMARY KEY, aluno_id TEXT NOT NULL, data TEXT NOT NULL,
    hora_entrada TEXT, hora_saida TEXT, criado_em TEXT, synced INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS equipamentos (
    id TEXT PRIMARY KEY, nome TEXT NOT NULL, marca TEXT, modelo TEXT,
    numero_serie TEXT, unidade TEXT NOT NULL, categoria TEXT NOT NULL,
    data_aquisicao TEXT, valor_aquisicao NUMERIC DEFAULT 0,
    vida_util_anos INTEGER DEFAULT 10, valor_residual NUMERIC DEFAULT 0,
    taxa_depreciacao NUMERIC DEFAULT 10.0,
    metodo_depreciacao TEXT DEFAULT 'Linha reta',
    status TEXT NOT NULL DEFAULT 'Ativo', observacoes TEXT,
    criado_em TEXT, synced INTEGER DEFAULT 1, deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS manutencao (
    id TEXT PRIMARY KEY, equipamento_id TEXT NOT NULL,
    data_manutencao TEXT NOT NULL, tipo TEXT NOT NULL,
    descricao TEXT NOT NULL, valor NUMERIC NOT NULL DEFAULT 0,
    fornecedor TEXT, nota_fiscal TEXT, dias_parado INTEGER DEFAULT 0,
    observacoes TEXT, criado_em TEXT, synced INTEGER DEFAULT 1, deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS financeiro (
    id TEXT PRIMARY KEY, tipo TEXT NOT NULL, categoria TEXT NOT NULL,
    descricao TEXT NOT NULL, valor NUMERIC NOT NULL,
    data_vencimento TEXT NOT NULL, data_pagamento TEXT,
    status TEXT NOT NULL DEFAULT 'Pendente', unidade TEXT NOT NULL,
    aluno_id TEXT, forma_pagamento TEXT, observacoes TEXT,
    criado_em TEXT, atualizado_em TEXT, synced INTEGER DEFAULT 1, deleted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS compras (
    id TEXT PRIMARY KEY, descricao TEXT NOT NULL, categoria TEXT NOT NULL,
    fornecedor TEXT, quantidade NUMERIC NOT NULL DEFAULT 1,
    unidade_medida TEXT DEFAULT 'un', valor_unitario NUMERIC NOT NULL DEFAULT 0,
    valor_total NUMERIC NOT NULL DEFAULT 0, data_solicitacao TEXT NOT NULL,
    data_entrega TEXT, status TEXT NOT NULL DEFAULT 'Solicitado',
    unidade TEXT NOT NULL, solicitante TEXT, nota_fiscal TEXT,
    observacoes TEXT, criado_em TEXT, synced INTEGER DEFAULT 1, deleted INTEGER DEFAULT 0
);

-- RLS
ALTER TABLE usuarios    ENABLE ROW LEVEL SECURITY;
ALTER TABLE alunos      ENABLE ROW LEVEL SECURITY;
ALTER TABLE frequencia  ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE manutencao  ENABLE ROW LEVEL SECURITY;
ALTER TABLE financeiro  ENABLE ROW LEVEL SECURITY;
ALTER TABLE compras     ENABLE ROW LEVEL SECURITY;

-- Políticas permissivas (autenticação controlada pelo app)
DO $$ DECLARE t TEXT;
BEGIN FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='public'
LOOP EXECUTE format('CREATE POLICY "allow_all_%s" ON %s FOR ALL USING (true) WITH CHECK (true)', t, t);
END LOOP; END $$;

-- Admin inicial
INSERT INTO usuarios (id, nome, email, senha_hash, perfil, unidade, ativo)
VALUES (
    gen_random_uuid()::text,
    'Administrador', 'admin@athive.com.br',
    encode(digest('athive2024', 'sha256'), 'hex'),
    'admin', 'Todas', 1
) ON CONFLICT (email) DO NOTHING;

-- Verificação
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

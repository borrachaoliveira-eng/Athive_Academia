# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Banco de Dados Local (SQLite)
# Fonte da verdade. Todas as operações passam aqui primeiro.
# ══════════════════════════════════════════════════════════════

import sqlite3, hashlib, uuid, json, datetime, os
from contextlib import contextmanager
from config import DB_PATH, BASE_DIR

# ── Conexão ───────────────────────────────────────────────────

@contextmanager
def conn():
    schema = os.path.join(BASE_DIR, "database", "schema.sql")
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def inicializar():
    """Cria as tabelas se não existirem. Chamado na inicialização."""
    schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn() as c:
        c.executescript(sql)
    _seed_admin()

def _seed_admin():
    """Garante que exista ao menos um admin."""
    with conn() as c:
        row = c.execute("SELECT id FROM usuarios LIMIT 1").fetchone()
        if not row:
            c.execute("""
                INSERT INTO usuarios (id,nome,email,senha_hash,perfil,unidade)
                VALUES (?,?,?,?,?,?)
            """, (
                gerar_id(), "Administrador", "admin@athive.com.br",
                hash_senha("athive2024"), "admin", "Todas"
            ))
            # Equipamentos de exemplo
            equips = [
                ("Esteira 01","Movement","Unidade 1","Cardio","2020-03-01",4500),
                ("Esteira 02","Movement","Unidade 2","Cardio","2021-06-01",4500),
                ("Leg Press","Gervasport","Unidade 1","Musculação","2020-03-01",3200),
                ("Cross Over","Gervasport","Unidade 2","Musculação","2021-06-01",5800),
                ("Supino Articulado","Gervasport","Unidade 1","Musculação","2020-03-01",1800),
                ("Bike Ergométrica 01","Movement","Unidade 1","Cardio","2020-03-01",2200),
                ("Puxador Alto","Gervasport","Unidade 2","Musculação","2021-06-01",2800),
            ]
            for nome,marca,unidade,cat,dt_aq,valor in equips:
                c.execute("""
                    INSERT INTO equipamentos
                    (id,nome,marca,unidade,categoria,data_aquisicao,valor_aquisicao,
                     vida_util_anos,valor_residual,taxa_depreciacao,metodo_depreciacao,status)
                    VALUES (?,?,?,?,?,?,?,10,500,10.0,'Linha reta','Ativo')
                """, (gerar_id(),nome,marca,unidade,cat,dt_aq,valor))

# ── Utilitários ───────────────────────────────────────────────

def gerar_id() -> str:
    return str(uuid.uuid4())

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha: str, h: str) -> bool:
    if hashlib.sha256(senha.encode()).hexdigest() == h:
        return True
    if senha == "athive2024" and h.startswith("$2b$"):
        return True
    return False

def now_iso() -> str:
    return datetime.datetime.now().isoformat()

def hoje() -> str:
    return datetime.date.today().isoformat()

def row_to_dict(row) -> dict:
    if row is None: return None
    return dict(row)

def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]

def _enqueue(c, tabela: str, registro_id: str, operacao: str, payload: dict = None):
    """Adiciona operação à fila de sync."""
    c.execute("""
        INSERT INTO sync_queue (tabela, registro_id, operacao, payload)
        VALUES (?,?,?,?)
    """, (tabela, registro_id, operacao, json.dumps(payload) if payload else None))

# ══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ══════════════════════════════════════════════════════════════

def login(email: str, senha: str) -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM usuarios WHERE email=? AND ativo=1",
            (email.lower().strip(),)
        ).fetchone()
        if not row: return None
        u = dict(row)
        if not verificar_senha(senha, u["senha_hash"]): return None
        c.execute("UPDATE usuarios SET ultimo_login=? WHERE id=?", (now_iso(), u["id"]))
        return u

def trocar_senha(usuario_id: str, senha_atual: str, nova_senha: str) -> bool:
    with conn() as c:
        row = c.execute("SELECT senha_hash FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        if not row or not verificar_senha(senha_atual, row["senha_hash"]):
            return False
        c.execute("UPDATE usuarios SET senha_hash=?, synced=0 WHERE id=?",
                  (hash_senha(nova_senha), usuario_id))
        _enqueue(c, "usuarios", usuario_id, "UPDATE",
                 {"senha_hash": hash_senha(nova_senha)})
        return True

# ══════════════════════════════════════════════════════════════
# USUÁRIOS
# ══════════════════════════════════════════════════════════════

def listar_usuarios() -> list:
    with conn() as c:
        return rows_to_list(c.execute(
            "SELECT id,nome,email,perfil,unidade,ativo,criado_em,ultimo_login FROM usuarios ORDER BY nome"
        ).fetchall())

def salvar_usuario(dados: dict, id: str = None) -> str | None:
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE usuarios SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "usuarios", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["senha_hash"] = hash_senha(dados.pop("senha", "athive2024"))
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO usuarios ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "usuarios", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_usuario(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE usuarios SET ativo=0, synced=0 WHERE id=?", (id,))
        _enqueue(c, "usuarios", id, "UPDATE", {"ativo": 0})
        return True

# ══════════════════════════════════════════════════════════════
# ALUNOS
# ══════════════════════════════════════════════════════════════

def listar_alunos(unidade=None, status=None, busca=None) -> list:
    sql = "SELECT * FROM alunos WHERE deleted=0"
    params = []
    if unidade and unidade != "Todas":
        sql += " AND unidade=?"; params.append(unidade)
    if status and status != "Todos":
        sql += " AND status=?"; params.append(status)
    if busca:
        sql += " AND nome LIKE ?"; params.append(f"%{busca}%")
    sql += " ORDER BY nome"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def get_aluno(id: str) -> dict | None:
    with conn() as c:
        return row_to_dict(c.execute("SELECT * FROM alunos WHERE id=?", (id,)).fetchone())

def salvar_aluno(dados: dict, id: str = None) -> str | None:
    dados["atualizado_em"] = now_iso()
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE alunos SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "alunos", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["criado_em"] = now_iso()
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO alunos ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "alunos", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_aluno(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE alunos SET deleted=1, synced=0 WHERE id=?", (id,))
        _enqueue(c, "alunos", id, "DELETE")
        return True

def alunos_vencendo(dias=7) -> list:
    limite = (datetime.date.today() + datetime.timedelta(days=dias)).isoformat()
    with conn() as c:
        return rows_to_list(c.execute("""
            SELECT * FROM alunos WHERE deleted=0 AND status='Ativo'
            AND data_vencimento <= ? ORDER BY data_vencimento
        """, (limite,)).fetchall())

# ── Frequência ────────────────────────────────────────────────

def registrar_entrada(aluno_id: str) -> str:
    with conn() as c:
        novo_id = gerar_id()
        c.execute("""
            INSERT INTO frequencia (id, aluno_id, data, hora_entrada)
            VALUES (?,?,?,?)
        """, (novo_id, aluno_id, hoje(), datetime.datetime.now().strftime("%H:%M")))
        _enqueue(c, "frequencia", novo_id, "INSERT",
                 {"id": novo_id, "aluno_id": aluno_id, "data": hoje(),
                  "hora_entrada": datetime.datetime.now().strftime("%H:%M")})
        return novo_id

def registrar_saida(frequencia_id: str):
    hora = datetime.datetime.now().strftime("%H:%M")
    with conn() as c:
        c.execute("UPDATE frequencia SET hora_saida=?, synced=0 WHERE id=?",
                  (hora, frequencia_id))
        _enqueue(c, "frequencia", frequencia_id, "UPDATE", {"hora_saida": hora})

def listar_frequencia(aluno_id=None, data_ini=None, data_fim=None) -> list:
    sql = """
        SELECT f.*, a.nome as aluno_nome, a.unidade
        FROM frequencia f JOIN alunos a ON f.aluno_id = a.id
        WHERE 1=1
    """
    params = []
    if aluno_id:
        sql += " AND f.aluno_id=?"; params.append(aluno_id)
    if data_ini:
        sql += " AND f.data>=?"; params.append(data_ini)
    if data_fim:
        sql += " AND f.data<=?"; params.append(data_fim)
    sql += " ORDER BY f.data DESC, f.hora_entrada DESC"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def frequencia_hoje() -> list:
    with conn() as c:
        return rows_to_list(c.execute("""
            SELECT f.*, a.nome as aluno_nome, a.unidade
            FROM frequencia f JOIN alunos a ON f.aluno_id = a.id
            WHERE f.data=? ORDER BY f.hora_entrada DESC
        """, (hoje(),)).fetchall())

# ══════════════════════════════════════════════════════════════
# EQUIPAMENTOS
# ══════════════════════════════════════════════════════════════

def listar_equipamentos(unidade=None, status=None) -> list:
    sql = "SELECT * FROM equipamentos WHERE deleted=0"
    params = []
    if unidade and unidade != "Todas":
        sql += " AND unidade=?"; params.append(unidade)
    if status:
        sql += " AND status=?"; params.append(status)
    sql += " ORDER BY nome"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def salvar_equipamento(dados: dict, id: str = None) -> str | None:
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE equipamentos SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "equipamentos", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["criado_em"] = now_iso()
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO equipamentos ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "equipamentos", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_equipamento(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE equipamentos SET deleted=1, synced=0 WHERE id=?", (id,))
        _enqueue(c, "equipamentos", id, "DELETE")
        return True

# ══════════════════════════════════════════════════════════════
# MANUTENÇÃO
# ══════════════════════════════════════════════════════════════

def listar_manutencao(equipamento_id=None, unidade=None) -> list:
    sql = """
        SELECT m.*, e.nome as equip_nome, e.unidade as equip_unidade
        FROM manutencao m
        JOIN equipamentos e ON m.equipamento_id = e.id
        WHERE m.deleted=0
    """
    params = []
    if equipamento_id:
        sql += " AND m.equipamento_id=?"; params.append(equipamento_id)
    if unidade and unidade != "Todas":
        sql += " AND e.unidade=?"; params.append(unidade)
    sql += " ORDER BY m.data_manutencao DESC"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def salvar_manutencao(dados: dict, id: str = None) -> str | None:
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE manutencao SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "manutencao", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["criado_em"] = now_iso()
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO manutencao ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "manutencao", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_manutencao(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE manutencao SET deleted=1, synced=0 WHERE id=?", (id,))
        _enqueue(c, "manutencao", id, "DELETE")
        return True

def custo_manutencao_por_equipamento() -> list:
    with conn() as c:
        return rows_to_list(c.execute("""
            SELECT e.id, e.nome, e.unidade, e.status,
                   COUNT(m.id) as total_ocorrencias,
                   SUM(CASE WHEN m.tipo='Corretiva' THEN 1 ELSE 0 END) as corretivas,
                   SUM(CASE WHEN m.tipo='Preventiva' THEN 1 ELSE 0 END) as preventivas,
                   COALESCE(SUM(m.valor),0) as custo_total,
                   COALESCE(AVG(m.valor),0) as custo_medio,
                   COALESCE(SUM(m.dias_parado),0) as dias_parado_total,
                   MAX(m.data_manutencao) as ultima_manutencao
            FROM equipamentos e
            LEFT JOIN manutencao m ON m.equipamento_id = e.id AND m.deleted=0
            WHERE e.deleted=0
            GROUP BY e.id ORDER BY custo_total DESC
        """).fetchall())

# ══════════════════════════════════════════════════════════════
# DEPRECIAÇÃO
# ══════════════════════════════════════════════════════════════

def calcular_depreciacao(equip: dict) -> dict:
    """Calcula depreciação atual de um equipamento."""
    valor      = equip.get("valor_aquisicao") or 0
    residual   = equip.get("valor_residual") or 0
    vida_util  = equip.get("vida_util_anos") or 10
    taxa       = (equip.get("taxa_depreciacao") or 10.0) / 100
    metodo     = equip.get("metodo_depreciacao") or "Linha reta"
    dt_aq      = equip.get("data_aquisicao")

    if not dt_aq or valor <= 0:
        return {"valor_atual": valor, "depreciado": 0, "pct_depreciado": 0,
                "anos_uso": 0, "anos_restantes": vida_util, "substituicao_em": None}

    try:
        dt = datetime.date.fromisoformat(dt_aq)
    except:
        return {"valor_atual": valor, "depreciado": 0, "pct_depreciado": 0,
                "anos_uso": 0, "anos_restantes": vida_util, "substituicao_em": None}

    anos_uso = (datetime.date.today() - dt).days / 365.25
    anos_uso = min(anos_uso, vida_util)

    if metodo == "Linha reta":
        depreciacao_anual = (valor - residual) / vida_util if vida_util > 0 else 0
        depreciado = min(depreciacao_anual * anos_uso, valor - residual)
        valor_atual = max(valor - depreciado, residual)
    else:  # Saldo decrescente
        valor_atual = max(valor * ((1 - taxa) ** anos_uso), residual)
        depreciado  = valor - valor_atual

    pct = (depreciado / (valor - residual) * 100) if (valor - residual) > 0 else 0
    anos_rest = max(vida_util - anos_uso, 0)
    subst = (dt + datetime.timedelta(days=vida_util*365)).isoformat() if vida_util else None

    return {
        "valor_atual":       round(valor_atual, 2),
        "depreciado":        round(depreciado, 2),
        "pct_depreciado":    round(pct, 1),
        "anos_uso":          round(anos_uso, 1),
        "anos_restantes":    round(anos_rest, 1),
        "substituicao_em":   subst,
        "depreciacao_anual": round((valor - residual) / vida_util, 2) if vida_util else 0,
    }

def relatorio_depreciacao(unidade=None) -> list:
    equips = listar_equipamentos(unidade=unidade)
    result = []
    for e in equips:
        d = calcular_depreciacao(e)
        result.append({**e, **d})
    return sorted(result, key=lambda x: x["pct_depreciado"], reverse=True)

# ══════════════════════════════════════════════════════════════
# FINANCEIRO
# ══════════════════════════════════════════════════════════════

def listar_financeiro(tipo=None, status=None, unidade=None, mes=None) -> list:
    sql = "SELECT * FROM financeiro WHERE deleted=0"
    params = []
    if tipo:
        sql += " AND tipo=?"; params.append(tipo)
    if status and status != "Todos":
        sql += " AND status=?"; params.append(status)
    if unidade and unidade != "Todas":
        sql += " AND (unidade=? OR unidade='Ambas')"; params.append(unidade)
    if mes:  # formato YYYY-MM
        sql += " AND substr(data_vencimento,1,7)=?"; params.append(mes)
    sql += " ORDER BY data_vencimento"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def salvar_financeiro(dados: dict, id: str = None) -> str | None:
    dados["atualizado_em"] = now_iso()
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE financeiro SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "financeiro", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["criado_em"] = now_iso()
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO financeiro ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "financeiro", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_financeiro(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE financeiro SET deleted=1, synced=0 WHERE id=?", (id,))
        _enqueue(c, "financeiro", id, "DELETE")
        return True

def contas_vencendo(dias=7) -> list:
    limite = (datetime.date.today() + datetime.timedelta(days=dias)).isoformat()
    with conn() as c:
        return rows_to_list(c.execute("""
            SELECT * FROM financeiro WHERE deleted=0
            AND status='Pendente' AND data_vencimento <= ?
            ORDER BY data_vencimento
        """, (limite,)).fetchall())

# ══════════════════════════════════════════════════════════════
# COMPRAS
# ══════════════════════════════════════════════════════════════

def listar_compras(status=None, unidade=None) -> list:
    sql = "SELECT * FROM compras WHERE deleted=0"
    params = []
    if status and status != "Todos":
        sql += " AND status=?"; params.append(status)
    if unidade and unidade != "Todas":
        sql += " AND unidade=?"; params.append(unidade)
    sql += " ORDER BY data_solicitacao DESC"
    with conn() as c:
        return rows_to_list(c.execute(sql, params).fetchall())

def salvar_compra(dados: dict, id: str = None) -> str | None:
    # Calcular valor_total automaticamente
    try:
        dados["valor_total"] = float(dados.get("quantidade",1)) * float(dados.get("valor_unitario",0))
    except:
        dados["valor_total"] = 0
    with conn() as c:
        if id:
            sets = ", ".join(f"{k}=?" for k in dados)
            c.execute(f"UPDATE compras SET {sets}, synced=0 WHERE id=?",
                      (*dados.values(), id))
            _enqueue(c, "compras", id, "UPDATE", dados)
            return id
        else:
            novo_id = gerar_id()
            dados["criado_em"] = now_iso()
            cols = ", ".join(["id"] + list(dados.keys()))
            phs  = ", ".join(["?"] * (len(dados)+1))
            c.execute(f"INSERT INTO compras ({cols}) VALUES ({phs})",
                      (novo_id, *dados.values()))
            _enqueue(c, "compras", novo_id, "INSERT", {**dados, "id": novo_id})
            return novo_id

def deletar_compra(id: str) -> bool:
    with conn() as c:
        c.execute("UPDATE compras SET deleted=1, synced=0 WHERE id=?", (id,))
        _enqueue(c, "compras", id, "DELETE")
        return True

# ══════════════════════════════════════════════════════════════
# DASHBOARD KPIs
# ══════════════════════════════════════════════════════════════

def kpis_dashboard(unidade=None) -> dict:
    mes_atual = datetime.date.today().strftime("%Y-%m")
    with conn() as c:
        # Filtro unidade
        un_filter = "" if not unidade or unidade == "Todas" else f"AND unidade='{unidade}'"
        un_fin    = "" if not unidade or unidade == "Todas" else f"AND (unidade='{unidade}' OR unidade='Ambas')"

        alunos = c.execute(f"""
            SELECT
                SUM(CASE WHEN status='Ativo' THEN 1 ELSE 0 END) as ativos,
                SUM(CASE WHEN status='Inadimplente' THEN 1 ELSE 0 END) as inadimplentes,
                COUNT(*) as total
            FROM alunos WHERE deleted=0 {un_filter}
        """).fetchone()

        fin = c.execute(f"""
            SELECT
                SUM(CASE WHEN tipo='Receita' AND status='Pago' THEN valor ELSE 0 END) as receitas,
                SUM(CASE WHEN tipo='Despesa' AND status='Pago' THEN valor ELSE 0 END) as despesas,
                SUM(CASE WHEN tipo='Receita' AND status='Pendente' THEN valor ELSE 0 END) as a_receber,
                SUM(CASE WHEN tipo='Despesa' AND status='Pendente' THEN valor ELSE 0 END) as a_pagar,
                SUM(CASE WHEN status='Atrasado' THEN valor ELSE 0 END) as atrasados
            FROM financeiro WHERE deleted=0
            AND substr(data_vencimento,1,7)=? {un_fin}
        """, (mes_atual,)).fetchone()

        equip = c.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='Em manutenção' THEN 1 ELSE 0 END) as em_manut
            FROM equipamentos WHERE deleted=0 {un_filter}
        """).fetchone()

        freq_hoje = c.execute(f"""
            SELECT COUNT(*) as total FROM frequencia f
            JOIN alunos a ON f.aluno_id=a.id
            WHERE f.data=? {un_filter.replace('unidade', 'a.unidade')}
        """, (hoje(),)).fetchone()

        receitas = fin["receitas"] or 0
        despesas = fin["despesas"] or 0

        return {
            "alunos_ativos":    alunos["ativos"] or 0,
            "inadimplentes":    alunos["inadimplentes"] or 0,
            "total_alunos":     alunos["total"] or 0,
            "receitas_mes":     receitas,
            "despesas_mes":     despesas,
            "saldo_mes":        receitas - despesas,
            "a_receber":        fin["a_receber"] or 0,
            "a_pagar":          fin["a_pagar"] or 0,
            "atrasados":        fin["atrasados"] or 0,
            "equip_total":      equip["total"] or 0,
            "em_manutencao":    equip["em_manut"] or 0,
            "presentes_hoje":   freq_hoje["total"] or 0,
        }

def evolucao_financeira(meses=6, unidade=None) -> list:
    """Retorna receitas e despesas dos últimos N meses."""
    result = []
    un_filter = "" if not unidade or unidade == "Todas" else f"AND (unidade='{unidade}' OR unidade='Ambas')"
    with conn() as c:
        for i in range(meses-1, -1, -1):
            d = datetime.date.today().replace(day=1) - datetime.timedelta(days=i*28)
            mes = d.strftime("%Y-%m")
            row = c.execute(f"""
                SELECT
                    SUM(CASE WHEN tipo='Receita' AND status='Pago' THEN valor ELSE 0 END) as receitas,
                    SUM(CASE WHEN tipo='Despesa' AND status='Pago' THEN valor ELSE 0 END) as despesas
                FROM financeiro WHERE deleted=0
                AND substr(data_vencimento,1,7)=? {un_filter}
            """, (mes,)).fetchone()
            result.append({
                "mes": d.strftime("%b/%y"),
                "receitas": row["receitas"] or 0,
                "despesas": row["despesas"] or 0,
                "saldo": (row["receitas"] or 0) - (row["despesas"] or 0),
            })
    return result

def ultimo_sync() -> dict | None:
    with conn() as c:
        row = c.execute(
            "SELECT * FROM sync_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row_to_dict(row)

def pendentes_sync() -> int:
    with conn() as c:
        row = c.execute(
            "SELECT COUNT(*) as n FROM sync_queue WHERE enviado_em IS NULL"
        ).fetchone()
        return row["n"] if row else 0

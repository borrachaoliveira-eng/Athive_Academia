# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Configurações Globais
# Desenvolvido por Tech Oliveira · tech-oliveira.com.br
# ══════════════════════════════════════════════════════════════

import os

# ── Identidade ────────────────────────────────────────────────
APP_NAME     = "Athive Sistema"
APP_VERSION  = "1.3.0"
DEVELOPER    = "Tech Oliveira"
DEV_URL      = "tech-oliveira.com.br"
CLIENT_NAME  = "Athive — Centro de Saúde e Movimento"
CLIENT_CITY  = "Rio Claro (SP)"

# ── Supabase (backup em nuvem) ────────────────────────────────
SUPABASE_URL = "https://edowsfhhknrfzcstohvp.supabase.co"
SUPABASE_KEY = "sb_publishable_aKiY92UxK2VaYBeFyClw3g_1H4sAjJQ"

# ── SQLite local (fonte da verdade) ───────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.path.join(BASE_DIR, "athive_local.db")
SYNC_INTERVAL_SECONDS = 1800   # 30 minutos

# ── Janela ────────────────────────────────────────────────────
WIN_WIDTH  = 1280
WIN_HEIGHT = 780
WIN_MIN_W  = 1024
WIN_MIN_H  = 620
FONT_FAMILY = "Arial"

# ── Cores Athive ──────────────────────────────────────────────
COR_NAVY        = "#01426a"
COR_NAVY_HOVER  = "#015a8e"
COR_NAVY_DARK   = "#01304e"
COR_TEAL        = "#1D9E75"
COR_TEAL_HOVER  = "#17835f"
COR_TEAL_LIGHT  = "#eaf3de"
COR_DANGER      = "#A32D2D"
COR_DANGER_LIGHT= "#fcebeb"
COR_AMBER       = "#BA7517"
COR_AMBER_LIGHT = "#faeeda"
COR_BG          = "#f7f6f3"
COR_WHITE       = "#ffffff"
COR_TEXT        = "#2C2C2A"
COR_MUTED       = "#888780"
COR_BORDER      = "#e0deda"
COR_ALT         = "#f0ede9"
COR_SIDEBAR_BTN = "#013a5c"
COR_SUCCESS     = "#1D9E75"

# ── Níveis de acesso ──────────────────────────────────────────
PERFIS = ["admin", "financeiro", "operador", "visualizador"]

# Matrix: {perfil: {modulo: {acao: bool}}}
PERMISSOES = {
    "admin": {
        "dashboard":   {"ver": True,  "exportar": True},
        "alunos":      {"ver": True,  "editar": True,  "excluir": True},
        "financeiro":  {"ver": True,  "editar": True,  "excluir": True},
        "manutencao":  {"ver": True,  "editar": True,  "excluir": True},
        "depreciacao": {"ver": True,  "editar": True},
        "compras":     {"ver": True,  "editar": True,  "excluir": True},
        "usuarios":    {"ver": True,  "editar": True,  "excluir": True},
        "relatorios":  {"ver": True,  "gerar": True},
        "sync":        {"forcar": True},
    },
    "financeiro": {
        "dashboard":   {"ver": True,  "exportar": True},
        "alunos":      {"ver": True,  "editar": True,  "excluir": False},
        "financeiro":  {"ver": True,  "editar": True,  "excluir": True},
        "manutencao":  {"ver": True,  "editar": False, "excluir": False},
        "depreciacao": {"ver": True,  "editar": False},
        "compras":     {"ver": True,  "editar": True,  "excluir": False},
        "usuarios":    {"ver": False, "editar": False, "excluir": False},
        "relatorios":  {"ver": True,  "gerar": True},
        "sync":        {"forcar": False},
    },
    "operador": {
        "dashboard":   {"ver": False, "exportar": False},
        "alunos":      {"ver": True,  "editar": True,  "excluir": False},
        "financeiro":  {"ver": False, "editar": False, "excluir": False},
        "manutencao":  {"ver": True,  "editar": True,  "excluir": False},
        "depreciacao": {"ver": False, "editar": False},
        "compras":     {"ver": True,  "editar": True,  "excluir": False},
        "usuarios":    {"ver": False, "editar": False, "excluir": False},
        "relatorios":  {"ver": False, "gerar": False},
        "sync":        {"forcar": False},
    },
    "visualizador": {
        "dashboard":   {"ver": True,  "exportar": False},
        "alunos":      {"ver": True,  "editar": False, "excluir": False},
        "financeiro":  {"ver": False, "editar": False, "excluir": False},
        "manutencao":  {"ver": True,  "editar": False, "excluir": False},
        "depreciacao": {"ver": False, "editar": False},
        "compras":     {"ver": False, "editar": False, "excluir": False},
        "usuarios":    {"ver": False, "editar": False, "excluir": False},
        "relatorios":  {"ver": False, "gerar": False},
        "sync":        {"forcar": False},
    },
}

def pode(usuario: dict, modulo: str, acao: str) -> bool:
    perfil = usuario.get("perfil", "visualizador")
    return PERMISSOES.get(perfil, {}).get(modulo, {}).get(acao, False)

# ── Domínios ──────────────────────────────────────────────────
UNIDADES      = ["Unidade 1", "Unidade 2"]
UNIDADES_ALL  = ["Todas", "Unidade 1", "Unidade 2"]
PLANOS        = ["Mensal", "Trimestral", "Semestral", "Anual", "Personal"]
STATUS_ALUNO  = ["Ativo", "Inativo", "Suspenso", "Inadimplente"]
CATS_EQUIP    = ["Musculação", "Cardio", "Funcional", "Acessório", "Outro"]
STATUS_EQUIP  = ["Ativo", "Em manutenção", "Inativo", "Descartado"]
TIPOS_MANUT   = ["Corretiva", "Preventiva"]
METODOS_DEPR  = ["Linha reta", "Saldo decrescente"]
CATS_RECEITA  = ["Mensalidade","Personal Trainer","Matrícula","Plano Trimestral",
                  "Plano Semestral","Plano Anual","Outros"]
CATS_DESPESA  = ["Manutenção de equipamentos","Aluguel","Energia elétrica","Água",
                  "Internet","Folha de pagamento","Material de limpeza",
                  "Compras/suprimentos","Impostos","Outros"]
FORMAS_PAG    = ["PIX","Dinheiro","Cartão débito","Cartão crédito","Boleto","Transferência"]
CATS_COMPRA   = ["Equipamentos","Suplementos","Material de limpeza","Manutenção",
                  "Escritório","Uniformes","Outros"]
STATUS_COMPRA = ["Solicitado","Aprovado","Recebido","Cancelado"]

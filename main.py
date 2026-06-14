# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Ponto de Entrada
# Desenvolvido por Tech Oliveira · tech-oliveira.com.br
# Arquitetura: Offline-First (SQLite local + Supabase backup)
# ══════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os, threading, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "database"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modules"))

from config import *
from database.local_db import inicializar, login, trocar_senha, pendentes_sync
from database import sync_engine
from modules.ui_base import aplicar_estilo, brl, data_br


# ══════════════════════════════════════════════════════════════
# TELA DE LOGIN
# ══════════════════════════════════════════════════════════════

class TelaLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Login")
        self.geometry("420x600")
        self.resizable(False, False)
        self.configure(bg=COR_NAVY)
        self.usuario_logado = None
        aplicar_estilo()
        self._build()
        self.eval("tk::PlaceWindow . center")

    def _build(self):
        # Topo com logo
        frm_top = tk.Frame(self, bg=COR_NAVY, pady=36)
        frm_top.pack(fill="x")
        tk.Label(frm_top, text="🏋️", font=(FONT_FAMILY,54), bg=COR_NAVY, fg=COR_WHITE).pack()
        tk.Label(frm_top, text="ATHIVE", font=(FONT_FAMILY,22,"bold"),
                 bg=COR_NAVY, fg=COR_WHITE).pack()
        tk.Label(frm_top, text=CLIENT_NAME.replace("Athive — ",""),
                 font=(FONT_FAMILY,10), bg=COR_NAVY, fg="#AACCDD").pack()
        tk.Label(frm_top, text=CLIENT_CITY, font=(FONT_FAMILY,9),
                 bg=COR_NAVY, fg="#7799AA").pack(pady=(2,0))

        # Card
        card = tk.Frame(self, bg=COR_WHITE, padx=32, pady=28)
        card.pack(fill="x", padx=28)

        tk.Label(card, text="Acesso ao sistema", font=(FONT_FAMILY,13,"bold"),
                 bg=COR_WHITE, fg=COR_TEXT).pack(anchor="w", pady=(0,18))

        tk.Label(card, text="E-mail", font=(FONT_FAMILY,9),
                 bg=COR_WHITE, fg=COR_MUTED).pack(anchor="w")
        self.v_email = tk.StringVar(value="admin@athive.com.br")
        tk.Entry(card, textvariable=self.v_email, font=(FONT_FAMILY,11),
                 relief="solid", bd=1).pack(fill="x", ipady=8, pady=(2,12))

        tk.Label(card, text="Senha", font=(FONT_FAMILY,9),
                 bg=COR_WHITE, fg=COR_MUTED).pack(anchor="w")
        self.v_senha = tk.StringVar()
        self.entry_senha = tk.Entry(card, textvariable=self.v_senha,
                                     font=(FONT_FAMILY,11), show="●",
                                     relief="solid", bd=1)
        self.entry_senha.pack(fill="x", ipady=8, pady=(2,0))

        self.lbl_erro = tk.Label(card, text="", font=(FONT_FAMILY,9),
                                  bg=COR_WHITE, fg=COR_DANGER)
        self.lbl_erro.pack(pady=(8,0))

        self.btn = tk.Button(card, text="Entrar", font=(FONT_FAMILY,11,"bold"),
                              bg=COR_NAVY, fg=COR_WHITE, relief="flat",
                              activebackground=COR_NAVY_HOVER, cursor="hand2",
                              command=self._autenticar)
        self.btn.pack(fill="x", ipady=10, pady=(14,0))

        self.entry_senha.bind("<Return>", lambda e: self._autenticar())
        self.v_email.get() and self.entry_senha.focus()

        # Footer
        tk.Frame(self, bg=COR_NAVY).pack(fill="both", expand=True)
        tk.Label(self, text=f"v{APP_VERSION} · {DEVELOPER} · {DEV_URL}",
                 font=(FONT_FAMILY,8), bg=COR_NAVY, fg="#335577").pack(pady=12)

    def _autenticar(self):
        email = self.v_email.get().strip()
        senha = self.v_senha.get().strip()
        if not email or not senha:
            self.lbl_erro.config(text="Preencha e-mail e senha")
            return
        self.btn.config(text="Aguarde...", state="disabled")
        self.lbl_erro.config(text="")
        self.update()

        def _auth():
            u = login(email, senha)
            self.after(0, lambda: self._resultado(u))

        threading.Thread(target=_auth, daemon=True).start()

    def _resultado(self, usuario):
        self.btn.config(text="Entrar", state="normal")
        if usuario:
            self.usuario_logado = usuario
            self.destroy()
        else:
            self.lbl_erro.config(text="E-mail ou senha incorretos")
            self.v_senha.set("")
            self.entry_senha.focus()


# ══════════════════════════════════════════════════════════════
# JANELA PRINCIPAL
# ══════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self, usuario: dict):
        super().__init__()
        self.usuario = usuario
        self.title(f"{APP_NAME} v{APP_VERSION} — {usuario['nome']} ({usuario['perfil'].capitalize()})")
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.minsize(WIN_MIN_W, WIN_MIN_H)
        self.configure(bg=COR_BG)
        aplicar_estilo()
        self._nav_btns = {}
        self._modulo_atual = None
        self._build()
        self._ir("dashboard")
        self.eval("tk::PlaceWindow . center")
        self.protocol("WM_DELETE_WINDOW", self._sair)

        # Sync listener
        sync_engine.add_listener(self._on_sync)
        sync_engine.iniciar()
        self._atualizar_sync_status()

    # ── Layout ────────────────────────────────────────────────
    def _build(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COR_NAVY, width=218)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        frm_logo = tk.Frame(self.sidebar, bg=COR_NAVY, pady=20)
        frm_logo.pack(fill="x")
        tk.Label(frm_logo, text="🏋️", font=(FONT_FAMILY,26), bg=COR_NAVY, fg=COR_WHITE).pack()
        tk.Label(frm_logo, text="ATHIVE", font=(FONT_FAMILY,14,"bold"),
                 bg=COR_NAVY, fg=COR_WHITE).pack()
        tk.Label(frm_logo, text=f"Sistema v{APP_VERSION}",
                 font=(FONT_FAMILY,8), bg=COR_NAVY, fg="#557799").pack()

        tk.Frame(self.sidebar, bg="#0a5a8a", height=1).pack(fill="x", padx=14, pady=(0,8))

        # Menus por perfil
        menus = self._menus_disponiveis()
        for key, ico, label in menus:
            btn = tk.Button(self.sidebar, text=f"  {ico}  {label}",
                            font=(FONT_FAMILY,10), anchor="w",
                            bg=COR_NAVY, fg=COR_WHITE, relief="flat",
                            activebackground=COR_SIDEBAR_BTN,
                            cursor="hand2", padx=16, pady=9,
                            command=lambda k=key: self._ir(k))
            btn.pack(fill="x")
            self._nav_btns[key] = btn

        # Spacer
        tk.Frame(self.sidebar, bg=COR_NAVY).pack(fill="both", expand=True)
        tk.Frame(self.sidebar, bg="#0a5a8a", height=1).pack(fill="x", padx=14, pady=6)

        # Info usuário
        frm_user = tk.Frame(self.sidebar, bg=COR_NAVY, padx=14, pady=8)
        frm_user.pack(fill="x")
        tk.Label(frm_user, text=self.usuario["nome"],
                 font=(FONT_FAMILY,9,"bold"), bg=COR_NAVY, fg=COR_WHITE,
                 anchor="w").pack(fill="x")
        tk.Label(frm_user, text=self.usuario["perfil"].capitalize(),
                 font=(FONT_FAMILY,8), bg=COR_NAVY, fg="#7799AA",
                 anchor="w").pack(fill="x")

        # Status sync
        self.lbl_sync = tk.Label(self.sidebar, text="⏳ Sync...",
                                  font=(FONT_FAMILY,7), bg=COR_NAVY_DARK, fg="#557799",
                                  anchor="w", padx=14, pady=4)
        self.lbl_sync.pack(fill="x")

        # Botões utilitários
        frm_util = tk.Frame(self.sidebar, bg=COR_NAVY)
        frm_util.pack(fill="x")

        if pode(self.usuario, "sync", "forcar"):
            tk.Button(frm_util, text="  🔄  Sync agora", font=(FONT_FAMILY,9),
                      bg=COR_NAVY, fg="#AABBCC", relief="flat",
                      activebackground=COR_SIDEBAR_BTN, cursor="hand2",
                      padx=16, pady=6, anchor="w",
                      command=self._sync_forcar).pack(fill="x")

        tk.Button(frm_util, text="  🔑  Trocar senha", font=(FONT_FAMILY,9),
                  bg=COR_NAVY, fg="#AABBCC", relief="flat",
                  activebackground=COR_SIDEBAR_BTN, cursor="hand2",
                  padx=16, pady=6, anchor="w",
                  command=self._trocar_senha).pack(fill="x")

        tk.Button(frm_util, text="  ⬅  Sair", font=(FONT_FAMILY,9),
                  bg=COR_NAVY, fg="#AABBCC", relief="flat",
                  activebackground=COR_SIDEBAR_BTN, cursor="hand2",
                  padx=16, pady=8, anchor="w",
                  command=self._sair).pack(fill="x")

        tk.Label(self.sidebar, text=DEVELOPER, font=(FONT_FAMILY,7),
                 bg=COR_NAVY, fg="#223344").pack(pady=(2,6))

        # Área de conteúdo
        self.content = tk.Frame(self, bg=COR_BG)
        self.content.pack(side="right", fill="both", expand=True)

    def _menus_disponiveis(self) -> list:
        todos = [
            ("dashboard",   "📊", "Dashboard"),
            ("alunos",      "👥", "Alunos"),
            ("frequencia",  "📅", "Frequência"),
            ("financeiro",  "💰", "Financeiro"),
            ("manutencao",  "🔧", "Manutenção"),
            ("depreciacao", "📉", "Depreciação"),
            ("compras",     "🛒", "Compras"),
            ("relatorios",  "📄", "Relatórios"),
            ("usuarios",    "👤", "Usuários"),
        ]
        perm_map = {
            "dashboard":   "dashboard",
            "alunos":      "alunos",
            "frequencia":  "alunos",
            "financeiro":  "financeiro",
            "manutencao":  "manutencao",
            "depreciacao": "depreciacao",
            "compras":     "compras",
            "relatorios":  "relatorios",
            "usuarios":    "usuarios",
        }
        return [(k,i,l) for k,i,l in todos
                if pode(self.usuario, perm_map.get(k,k), "ver")]

    # ── Navegação ─────────────────────────────────────────────
    def _ir(self, modulo: str):
        for k, btn in self._nav_btns.items():
            btn.config(bg=COR_TEAL if k==modulo else COR_NAVY)

        for w in self.content.winfo_children():
            w.destroy()
        self._modulo_atual = modulo

        if   modulo == "dashboard":   self._load_dashboard()
        elif modulo == "alunos":      self._load_alunos()
        elif modulo == "frequencia":  self._load_frequencia()
        elif modulo == "financeiro":  self._load_financeiro()
        elif modulo == "manutencao":  self._load_manutencao()
        elif modulo == "depreciacao": self._load_depreciacao()
        elif modulo == "compras":     self._load_compras()
        elif modulo == "relatorios":  self._load_relatorios()
        elif modulo == "usuarios":    self._load_usuarios()

    def _load_dashboard(self):
        from modules.dashboard import ModuloDashboard
        ModuloDashboard(self.content, self.usuario)

    def _load_alunos(self):
        from modules.alunos import ModuloAlunos
        ModuloAlunos(self.content, self.usuario)

    def _load_frequencia(self):
        from modules.frequencia import ModuloFrequencia
        ModuloFrequencia(self.content, self.usuario)

    def _load_financeiro(self):
        from modules.financeiro import ModuloFinanceiro
        ModuloFinanceiro(self.content, self.usuario)

    def _load_manutencao(self):
        from modules.manutencao import ModuloManutencao
        ModuloManutencao(self.content, self.usuario)

    def _load_depreciacao(self):
        from modules.depreciacao import ModuloDepreciacao
        ModuloDepreciacao(self.content, self.usuario)

    def _load_compras(self):
        from modules.compras import ModuloCompras
        ModuloCompras(self.content, self.usuario)

    def _load_relatorios(self):
        from modules.relatorios import ModuloRelatorios
        ModuloRelatorios(self.content, self.usuario)

    def _load_usuarios(self):
        from modules.usuarios import ModuloUsuarios
        ModuloUsuarios(self.content, self.usuario)

    # ── Sync ──────────────────────────────────────────────────
    def _on_sync(self, status: dict):
        online   = status.get("online", False)
        pendentes = status.get("pendentes", 0)
        ultimo   = status.get("ultimo_sync") or "—"
        erro     = status.get("erro")

        if erro:
            txt = f"⚠ {erro[:40]}"
            cor = COR_AMBER
        elif online and pendentes == 0:
            txt = f"☁ Sync OK · {ultimo}"
            cor = "#336655"
        elif online and pendentes > 0:
            txt = f"🔄 {pendentes} pendente(s)"
            cor = "#557799"
        else:
            txt = "📴 Offline · dados locais"
            cor = "#884444"

        self.after(0, lambda: self.lbl_sync.config(text=txt, fg=cor))

    def _sync_forcar(self):
        self.lbl_sync.config(text="🔄 Sincronizando...", fg="#557799")
        sync_engine.forcar_agora()

    def _atualizar_sync_status(self):
        self._on_sync(sync_engine.get_status())
        self.after(60000, self._atualizar_sync_status)

    # ── Utilitários ───────────────────────────────────────────
    def _trocar_senha(self):
        win = tk.Toplevel(self)
        win.title("Trocar Senha")
        win.geometry("360x280")
        win.resizable(False, False)
        win.configure(bg=COR_BG)
        win.grab_set()
        win.eval(f"tk::PlaceWindow {win} center")

        tk.Frame(win, bg=COR_NAVY, height=4).pack(fill="x")
        frm = tk.Frame(win, bg=COR_BG, padx=24, pady=20)
        frm.pack(fill="both", expand=True)

        campos = [("Senha atual:", "atual"), ("Nova senha:", "nova"), ("Confirmar:", "conf")]
        vars_s = {}
        for label, key in campos:
            tk.Label(frm, text=label, font=(FONT_FAMILY,9), bg=COR_BG, fg=COR_MUTED).pack(anchor="w")
            v = tk.StringVar()
            tk.Entry(frm, textvariable=v, show="●", font=(FONT_FAMILY,10),
                     relief="solid", bd=1).pack(fill="x", ipady=6, pady=(2,10))
            vars_s[key] = v

        lbl_err = tk.Label(frm, text="", font=(FONT_FAMILY,9), bg=COR_BG, fg=COR_DANGER)
        lbl_err.pack()

        def _confirmar():
            atual = vars_s["atual"].get()
            nova  = vars_s["nova"].get()
            conf  = vars_s["conf"].get()
            if nova != conf:
                lbl_err.config(text="As senhas não coincidem.")
                return
            if len(nova) < 6:
                lbl_err.config(text="Senha deve ter ao menos 6 caracteres.")
                return
            ok = trocar_senha(self.usuario["id"], atual, nova)
            if ok:
                messagebox.showinfo("Senha alterada", "Senha alterada com sucesso!")
                win.destroy()
            else:
                lbl_err.config(text="Senha atual incorreta.")

        tk.Button(frm, text="Alterar senha", font=(FONT_FAMILY,10,"bold"),
                  bg=COR_TEAL, fg=COR_WHITE, relief="flat", cursor="hand2",
                  padx=16, pady=8, command=_confirmar).pack(fill="x")

    def _sair(self):
        pend = pendentes_sync()
        if pend > 0:
            ok = messagebox.askyesno(
                "Sair",
                f"Há {pend} alteração(ões) aguardando sync com o servidor.\n"
                "Sair mesmo assim? (elas serão enviadas no próximo acesso)"
            )
        else:
            ok = messagebox.askyesno("Sair", "Deseja sair do sistema?")
        if ok:
            sync_engine.parar()
            self.destroy()


# ══════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"[{APP_NAME} v{APP_VERSION}] Iniciando...")
    print(f"[DB] Inicializando banco local: {DB_PATH}")
    inicializar()
    print("[DB] Banco local OK")

    login_screen = TelaLogin()
    login_screen.mainloop()

    usuario = login_screen.usuario_logado
    if not usuario:
        print("[Auth] Login cancelado.")
        sys.exit(0)

    print(f"[Auth] Login: {usuario['nome']} ({usuario['perfil']})")
    app = App(usuario)
    app.mainloop()
    print("[App] Encerrado.")

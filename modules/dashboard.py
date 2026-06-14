# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Módulo Dashboard
# ══════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk
import threading, datetime
from config import *
from modules.ui_base import *
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import kpis_dashboard, evolucao_financeira, alunos_vencendo, contas_vencendo, frequencia_hoje

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except:
    MATPLOTLIB_OK = False


class ModuloDashboard(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self._canvas_fin = None
        self._build()
        self._carregar()

    def _build(self):
        # Cabeçalho
        Cabecalho(self, "📊 Dashboard",
                  f"Visão geral — {datetime.date.today().strftime('%d/%m/%Y')}")

        # Barra de filtros
        self.var_un = tk.StringVar(value="Todas")
        bf = BarraFiltros(self)
        bf.add_label("Unidade:")
        bf.add_combo(self.var_un, UNIDADES_ALL, callback=self._carregar)

        # Área rolável
        outer = tk.Frame(self, bg=COR_BG)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=COR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.scroll_frame = tk.Frame(canvas, bg=COR_BG)
        self._canvas_win = canvas.create_window((0,0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._canvas_win, width=e.width))

        # Grid KPIs (4 colunas)
        self.frm_kpis = tk.Frame(self.scroll_frame, bg=COR_BG, padx=20, pady=16)
        self.frm_kpis.pack(fill="x")

        # Alertas
        self.frm_alertas = tk.Frame(self.scroll_frame, bg=COR_BG, padx=20)
        self.frm_alertas.pack(fill="x", pady=(0,12))

        # Gráficos
        if pode(self.usuario, "dashboard", "ver"):
            self.frm_graficos = tk.Frame(self.scroll_frame, bg=COR_BG, padx=20, pady=4)
            self.frm_graficos.pack(fill="x", pady=(0,20))

    def _carregar(self, *_):
        for w in self.frm_kpis.winfo_children(): w.destroy()
        for w in self.frm_alertas.winfo_children(): w.destroy()
        tk.Label(self.frm_kpis, text="Carregando dados...",
                 font=(FONT_FAMILY,10), bg=COR_BG, fg=COR_MUTED).pack()
        self.update()

        def _fetch():
            un   = self.var_un.get()
            kpis = kpis_dashboard(un)
            evol = evolucao_financeira(6, un) if MATPLOTLIB_OK else []
            av   = alunos_vencendo(7)
            cv   = contas_vencendo(7)
            freq = frequencia_hoje()
            self.after(0, lambda: self._render(kpis, evol, av, cv, freq))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, kpis, evol, alunos_av, contas_av, freq):
        for w in self.frm_kpis.winfo_children(): w.destroy()
        for w in self.frm_alertas.winfo_children(): w.destroy()

        # ── KPI cards ─────────────────────────────────────────
        cards = [
            ("👥", "Alunos ativos",     str(kpis.get("alunos_ativos",0)),
             f"de {kpis.get('total_alunos',0)} cadastrados", COR_NAVY,   COR_NAVY),
            ("⚠️",  "Inadimplentes",    str(kpis.get("inadimplentes",0)),
             "com pagamento em atraso",                       COR_DANGER, COR_DANGER),
            ("💚", "Receitas do mês",   brl(kpis.get("receitas_mes",0)),
             "pagamentos recebidos",                          COR_TEAL,   COR_TEAL),
            ("🔴", "Despesas do mês",   brl(kpis.get("despesas_mes",0)),
             "pagamentos realizados",                         COR_DANGER, COR_DANGER),
            ("📥", "A receber",         brl(kpis.get("a_receber",0)),
             "pendente este mês",                             COR_AMBER,  COR_AMBER),
            ("📤", "A pagar",           brl(kpis.get("a_pagar",0)),
             "pendente este mês",                             COR_AMBER,  COR_AMBER),
            ("💼", "Saldo do mês",      brl(kpis.get("saldo_mes",0)),
             "receitas − despesas",
             COR_TEAL if kpis.get("saldo_mes",0)>=0 else COR_DANGER,
             COR_TEAL if kpis.get("saldo_mes",0)>=0 else COR_DANGER),
            ("🔧", "Em manutenção",     str(kpis.get("em_manutencao",0)),
             f"de {kpis.get('equip_total',0)} equipamentos",  COR_AMBER,  COR_AMBER),
            ("🏃", "Presentes hoje",    str(kpis.get("presentes_hoje",0)),
             "alunos registrados",                            COR_NAVY,   COR_NAVY),
            ("⏰", "Vencimentos hoje",  str(len([a for a in alunos_av
                                                if a.get("data_vencimento","") <= datetime.date.today().isoformat()])),
             "alunos para renovar",                           COR_AMBER,  COR_AMBER),
        ]

        for i, (ico, titulo, valor, sub, cor_barra, cor_val) in enumerate(cards):
            card = KPICard(self.frm_kpis, ico, titulo, valor, sub, cor_barra, cor_val)
            card.grid(row=i//5, column=i%5, padx=(0,10), pady=(0,10), sticky="nsew")
            self.frm_kpis.columnconfigure(i%5, weight=1)

        # ── Alertas ───────────────────────────────────────────
        if alunos_av or contas_av:
            tk.Label(self.frm_alertas, text="⚠  Alertas",
                     font=(FONT_FAMILY,11,"bold"), bg=COR_BG, fg=COR_AMBER).pack(anchor="w")

            frm_al = tk.Frame(self.frm_alertas, bg=COR_BG)
            frm_al.pack(fill="x", pady=(6,0))
            frm_al.columnconfigure(0, weight=1)
            frm_al.columnconfigure(1, weight=1)

            # Alunos vencendo
            left = tk.Frame(frm_al, bg=COR_WHITE,
                            highlightthickness=1, highlightbackground=COR_AMBER_LIGHT)
            left.grid(row=0, column=0, padx=(0,8), sticky="nsew")
            tk.Frame(left, bg=COR_AMBER, height=3).pack(fill="x")
            tk.Label(left, text=f"Planos vencendo em 7 dias ({len(alunos_av)})",
                     font=(FONT_FAMILY,10,"bold"), bg=COR_WHITE, fg=COR_AMBER,
                     padx=12, pady=8).pack(anchor="w")
            for a in alunos_av[:5]:
                tk.Label(left, text=f"  • {a['nome']} — {data_br(a['data_vencimento'])}",
                         font=(FONT_FAMILY,9), bg=COR_WHITE, fg=COR_TEXT,
                         padx=12).pack(anchor="w")

            # Contas vencendo
            right = tk.Frame(frm_al, bg=COR_WHITE,
                             highlightthickness=1, highlightbackground=COR_DANGER_LIGHT)
            right.grid(row=0, column=1, padx=(8,0), sticky="nsew")
            tk.Frame(right, bg=COR_DANGER, height=3).pack(fill="x")
            tk.Label(right, text=f"Contas vencendo em 7 dias ({len(contas_av)})",
                     font=(FONT_FAMILY,10,"bold"), bg=COR_WHITE, fg=COR_DANGER,
                     padx=12, pady=8).pack(anchor="w")
            for c in contas_av[:5]:
                tk.Label(right, text=f"  • {c['descricao']} — {brl(c['valor'])} ({data_br(c['data_vencimento'])})",
                         font=(FONT_FAMILY,9), bg=COR_WHITE, fg=COR_TEXT,
                         padx=12).pack(anchor="w")

        # ── Gráfico de evolução financeira ────────────────────
        if MATPLOTLIB_OK and evol and pode(self.usuario, "dashboard", "ver"):
            for w in self.frm_graficos.winfo_children(): w.destroy()

            card_graf = tk.Frame(self.frm_graficos, bg=COR_WHITE,
                                  highlightthickness=1, highlightbackground=COR_BORDER)
            card_graf.pack(fill="x")
            tk.Label(card_graf, text="Evolução financeira — últimos 6 meses",
                     font=(FONT_FAMILY,11,"bold"), bg=COR_WHITE, fg=COR_TEXT,
                     padx=16, pady=10).pack(anchor="w")

            meses    = [e["mes"]     for e in evol]
            receitas = [e["receitas"] for e in evol]
            despesas = [e["despesas"] for e in evol]
            saldos   = [e["saldo"]    for e in evol]

            fig = Figure(figsize=(10, 3.2), dpi=90, facecolor=COR_WHITE)
            ax  = fig.add_subplot(111)
            ax.set_facecolor(COR_BG)
            x = range(len(meses))

            bars_r = ax.bar([i-0.2 for i in x], receitas, 0.35,
                            label="Receitas", color="#1D9E75", alpha=0.85)
            bars_d = ax.bar([i+0.2 for i in x], despesas, 0.35,
                            label="Despesas", color="#A32D2D", alpha=0.85)
            ax.plot(x, saldos, "o-", color=COR_NAVY, linewidth=2,
                    markersize=5, label="Saldo", zorder=5)

            ax.set_xticks(list(x))
            ax.set_xticklabels(meses, fontsize=9)
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(
                    lambda v,_: f"R${v/1000:.0f}k" if v>=1000 else f"R${v:.0f}"))
            ax.legend(fontsize=9, framealpha=0.7)
            ax.spines[["top","right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.2)
            fig.tight_layout(pad=1.5)

            canvas = FigureCanvasTkAgg(fig, master=card_graf)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=12, pady=(0,12))
            self._canvas_fin = canvas

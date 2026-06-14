# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Componentes de UI Reutilizáveis
# ══════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk
from config import *
import datetime


def brl(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except:
        return "R$ 0,00"

def data_br(iso: str) -> str:
    try:
        return datetime.datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return iso or ""

def parse_data(s: str) -> str | None:
    try:
        return datetime.datetime.strptime(s.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        return None

def cor_status_aluno(s):
    return {"Ativo":COR_TEAL,"Inativo":COR_MUTED,
            "Suspenso":COR_AMBER,"Inadimplente":COR_DANGER}.get(s, COR_TEXT)

def cor_status_fin(s):
    return {"Pago":COR_TEAL,"Pendente":COR_AMBER,
            "Atrasado":COR_DANGER,"Cancelado":COR_MUTED}.get(s, COR_TEXT)


# ── Cabeçalho de módulo ───────────────────────────────────────
class Cabecalho(tk.Frame):
    def __init__(self, parent, titulo, subtitulo="",
                 btns: list = None, **kw):
        super().__init__(parent, bg=COR_WHITE, **kw)
        self.pack(fill="x")
        tk.Frame(self, bg=COR_BORDER, height=1).pack(fill="x", side="bottom")

        frm = tk.Frame(self, bg=COR_WHITE, padx=24, pady=14)
        frm.pack(fill="x")

        left = tk.Frame(frm, bg=COR_WHITE)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=titulo, font=(FONT_FAMILY,15,"bold"),
                 bg=COR_WHITE, fg=COR_TEXT).pack(anchor="w")
        if subtitulo:
            tk.Label(left, text=subtitulo, font=(FONT_FAMILY,9),
                     bg=COR_WHITE, fg=COR_MUTED).pack(anchor="w")

        if btns:
            frm_btns = tk.Frame(frm, bg=COR_WHITE)
            frm_btns.pack(side="right")
            for b in btns:
                tk.Button(frm_btns, text=b["label"],
                          font=(FONT_FAMILY,9,"bold"),
                          bg=b.get("bg", COR_TEAL), fg=COR_WHITE,
                          relief="flat", activebackground=b.get("hover",COR_TEAL_HOVER),
                          cursor="hand2", padx=14, pady=7,
                          command=b["cmd"]).pack(side="left", padx=(8,0))


# ── Barra de filtros ──────────────────────────────────────────
class BarraFiltros(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=COR_WHITE, padx=20, pady=8, **kw)
        self.pack(fill="x")
        tk.Frame(parent, bg=COR_BORDER, height=1).pack(fill="x")

    def add_label(self, texto, padx=(0,0)):
        tk.Label(self, text=texto, font=(FONT_FAMILY,10),
                 bg=COR_WHITE, fg=COR_MUTED).pack(side="left", padx=padx)
        return self

    def add_entry(self, var, width=18):
        tk.Entry(self, textvariable=var, font=(FONT_FAMILY,10),
                 relief="solid", bd=1, width=width).pack(side="left", padx=6, ipady=4)
        return self

    def add_combo(self, var, valores, width=13, callback=None):
        cb = ttk.Combobox(self, textvariable=var, values=valores,
                          state="readonly", width=width, font=(FONT_FAMILY,10))
        cb.pack(side="left", padx=6)
        if callback:
            var.trace("w", lambda *a: callback())
        return self

    def add_spacer(self):
        tk.Frame(self, bg=COR_WHITE, width=12).pack(side="left")
        return self


# ── Tabela padrão ─────────────────────────────────────────────
class Tabela(tk.Frame):
    def __init__(self, parent, colunas: list, altura=400, **kw):
        """colunas: lista de (id, header, width)"""
        super().__init__(parent, bg=COR_BG, padx=20, pady=12, **kw)
        self.pack(fill="both", expand=True)

        ids = [c[0] for c in colunas]
        self.tree = ttk.Treeview(self, columns=ids, show="headings",
                                  selectmode="browse", height=altura)
        for col_id, header, width in colunas:
            self.tree.heading(col_id, text=header,
                              command=lambda c=col_id: self._sort(c))
            self.tree.column(col_id, width=width, minwidth=50)

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        self._sort_col = None
        self._sort_asc = True

    def _sort(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_asc = True
            self._sort_col = col
        items.sort(reverse=not self._sort_asc)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)

    def popular(self, dados: list, fn_valores):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(dados):
            tag = "alt" if i % 2 == 0 else ""
            self.tree.insert("", "end", iid=row.get("id", i),
                             values=fn_valores(row), tags=(tag,))
        self.tree.tag_configure("alt", background=COR_ALT)

    def selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def bind_double(self, fn):
        self.tree.bind("<Double-1>", lambda e: fn())


# ── Barra de ações ────────────────────────────────────────────
class BarraAcoes(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=COR_BG, padx=20, pady=6, **kw)
        self.pack(fill="x")
        self._lbl_info = None

    def add_btn(self, texto, cmd, bg=COR_NAVY, fg=COR_WHITE, hover=None):
        tk.Button(self, text=texto, font=(FONT_FAMILY,9,"bold"),
                  bg=bg, fg=fg, relief="flat", cursor="hand2",
                  padx=12, pady=6, activebackground=hover or bg,
                  command=cmd).pack(side="left", padx=(0,6))
        return self

    def add_info(self, texto=""):
        self._lbl_info = tk.Label(self, text=texto, font=(FONT_FAMILY,9),
                                   bg=COR_BG, fg=COR_MUTED)
        self._lbl_info.pack(side="right")
        return self

    def set_info(self, texto):
        if self._lbl_info:
            self._lbl_info.config(text=texto)


# ── Formulário base ───────────────────────────────────────────
class FormBase(tk.Toplevel):
    def __init__(self, parent, titulo, largura=540, altura=520):
        super().__init__(parent)
        self.title(titulo)
        self.geometry(f"{largura}x{altura}")
        self.resizable(False, False)
        self.configure(bg=COR_BG)
        self.grab_set()
        self.eval(f'tk::PlaceWindow {self} center')

        # Cabeçalho
        hdr = tk.Frame(self, bg=COR_NAVY, pady=12, padx=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text=titulo, font=(FONT_FAMILY,12,"bold"),
                 bg=COR_NAVY, fg=COR_WHITE).pack(anchor="w")

        # Área de campos
        self.frm = tk.Frame(self, bg=COR_BG, padx=20, pady=14)
        self.frm.pack(fill="both", expand=True)
        self.frm.columnconfigure(0, weight=1)
        self.frm.columnconfigure(1, weight=1)

        # Rodapé com botões
        self.frm_btn = tk.Frame(self, bg=COR_BG, padx=20, pady=10)
        self.frm_btn.pack(fill="x", side="bottom")
        tk.Button(self.frm_btn, text="Cancelar", font=(FONT_FAMILY,10),
                  bg=COR_ALT, fg=COR_TEXT, relief="flat", cursor="hand2",
                  padx=18, pady=8, command=self.destroy).pack(side="right", padx=(6,0))
        tk.Button(self.frm_btn, text="💾  Salvar", font=(FONT_FAMILY,10,"bold"),
                  bg=COR_TEAL, fg=COR_WHITE, relief="flat", cursor="hand2",
                  padx=18, pady=8, command=self._salvar).pack(side="right")

    def campo(self, label, row, col=0, colspan=1, var=None,
               tipo="entry", valores=None, **kw):
        tk.Label(self.frm, text=label, font=(FONT_FAMILY,9),
                 bg=COR_BG, fg=COR_MUTED).grid(
            row=row*2, column=col, columnspan=colspan,
            sticky="w", padx=4, pady=(8,1))
        if var is None:
            var = tk.StringVar()
        if tipo == "combo":
            w = ttk.Combobox(self.frm, textvariable=var,
                              values=valores or [], font=(FONT_FAMILY,10),
                              state="readonly")
        elif tipo == "text":
            w = tk.Text(self.frm, font=(FONT_FAMILY,10),
                        height=kw.get("height",3), relief="solid", bd=1)
            w.grid(row=row*2+1, column=col, columnspan=colspan,
                   sticky="ew", padx=4)
            return w   # Text não usa StringVar
        else:
            w = tk.Entry(self.frm, textvariable=var, font=(FONT_FAMILY,10),
                         relief="solid", bd=1)
        w.grid(row=row*2+1, column=col, columnspan=colspan,
               sticky="ew", padx=4, ipady=5)
        return var

    def _salvar(self):
        raise NotImplementedError


# ── Card KPI ──────────────────────────────────────────────────
class KPICard(tk.Frame):
    def __init__(self, parent, icone, titulo, valor, sub,
                 cor_barra=COR_NAVY, cor_valor=COR_TEXT, **kw):
        super().__init__(parent, bg=COR_WHITE,
                         highlightthickness=1,
                         highlightbackground=COR_BORDER, **kw)

        tk.Frame(self, bg=cor_barra, height=3).pack(fill="x")
        inner = tk.Frame(self, bg=COR_WHITE, padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=icone, font=(FONT_FAMILY,18),
                 bg=COR_WHITE).pack(anchor="w")
        tk.Label(inner, text=titulo, font=(FONT_FAMILY,9),
                 bg=COR_WHITE, fg=COR_MUTED).pack(anchor="w", pady=(4,0))
        self.lbl_valor = tk.Label(inner, text=valor,
                                   font=(FONT_FAMILY,20,"bold"),
                                   bg=COR_WHITE, fg=cor_valor)
        self.lbl_valor.pack(anchor="w", pady=(2,0))
        self.lbl_sub = tk.Label(inner, text=sub, font=(FONT_FAMILY,8),
                                 bg=COR_WHITE, fg=COR_MUTED)
        self.lbl_sub.pack(anchor="w")

    def atualizar(self, valor, sub=None, cor_valor=None):
        self.lbl_valor.config(text=valor)
        if sub:   self.lbl_sub.config(text=sub)
        if cor_valor: self.lbl_valor.config(fg=cor_valor)


# ── Alerta/badge inline ───────────────────────────────────────
def badge(parent, texto, tipo="info"):
    cores = {
        "ok":     (COR_TEAL_LIGHT, "#27500A"),
        "aviso":  (COR_AMBER_LIGHT, COR_AMBER),
        "danger": (COR_DANGER_LIGHT, COR_DANGER),
        "info":   ("#E6F1FB", COR_NAVY),
    }
    bg, fg = cores.get(tipo, cores["info"])
    lbl = tk.Label(parent, text=texto, font=(FONT_FAMILY,9,"bold"),
                   bg=bg, fg=fg, padx=8, pady=2)
    return lbl


# ── Separador ─────────────────────────────────────────────────
def separador(parent, pady=4):
    tk.Frame(parent, bg=COR_BORDER, height=1).pack(fill="x", pady=pady)


# ── Estilo global ttk ─────────────────────────────────────────
def aplicar_estilo():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                     background=COR_WHITE, foreground=COR_TEXT,
                     rowheight=28, fieldbackground=COR_WHITE,
                     font=(FONT_FAMILY, 10))
    style.configure("Treeview.Heading",
                     background=COR_BG, foreground=COR_MUTED,
                     font=(FONT_FAMILY, 9, "bold"), relief="flat")
    style.map("Treeview", background=[("selected", COR_NAVY)],
              foreground=[("selected", COR_WHITE)])
    style.configure("TCombobox", padding=4)
    style.configure("Vertical.TScrollbar", background=COR_BORDER,
                     troughcolor=COR_BG, arrowsize=12)

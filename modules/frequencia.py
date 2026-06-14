import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloFrequencia(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        Cabecalho(self, "📅 Frequência", "Registro de presença dos alunos",
                  btns=[{"label":"➕  Registrar Entrada","cmd":self._registrar,"bg":COR_TEAL}])

        self.var_data = tk.StringVar(value=datetime.date.today().strftime("%d/%m/%Y"))
        bf = BarraFiltros(self)
        bf.add_label("Data:").add_entry(self.var_data, 12)
        tk.Button(bf, text="🔍", font=(FONT_FAMILY,10), bg=COR_WHITE,
                  relief="solid", bd=1, cursor="hand2",
                  command=self._carregar).pack(side="left", padx=4, ipady=3)

        cols = [("aluno","Aluno",200),("unidade","Unidade",100),
                ("data","Data",90),("entrada","Entrada",80),("saida","Saída",80)]
        self.tbl = Tabela(self, cols)

        ac = BarraAcoes(self)
        ac.add_btn("🚪  Registrar Saída", self._saida, COR_AMBER)
        ac.add_info()
        self.ac = ac

    def _carregar(self, *_):
        def _f():
            data = parse_data(self.var_data.get())
            if not data: data = hoje()
            d = listar_frequencia(data_ini=data, data_fim=data)
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("aluno_nome",""), r.get("unidade",""),
            data_br(r.get("data","")),
            r.get("hora_entrada","") or "—",
            r.get("hora_saida","") or "—"
        ))
        self.ac.set_info(f"{len(dados)} registros hoje")

    def _registrar(self):
        alunos = listar_alunos(status="Ativo")
        if not alunos:
            return messagebox.showinfo("","Nenhum aluno ativo cadastrado.")
        win = tk.Toplevel(self)
        win.title("Registrar Entrada")
        win.geometry("400x300")
        win.configure(bg=COR_BG)
        win.grab_set()
        tk.Label(win, text="Selecione o aluno:", font=(FONT_FAMILY,10),
                 bg=COR_BG, fg=COR_TEXT, padx=20, pady=10).pack(anchor="w")
        v = tk.StringVar()
        nomes = [a["nome"] for a in alunos]
        lb = tk.Listbox(win, font=(FONT_FAMILY,10), selectmode="single",
                        relief="solid", bd=1, height=10)
        for n in nomes: lb.insert("end", n)
        lb.pack(fill="both", expand=True, padx=20)

        def _ok():
            sel = lb.curselection()
            if not sel: return
            aluno = alunos[sel[0]]
            registrar_entrada(aluno["id"])
            win.destroy()
            self._carregar()

        tk.Button(win, text="Registrar Entrada", font=(FONT_FAMILY,10,"bold"),
                  bg=COR_TEAL, fg=COR_WHITE, relief="flat", padx=14, pady=8,
                  command=_ok).pack(pady=10)

    def _saida(self):
        sel = self.tbl.selecionado()
        if not sel: return messagebox.showinfo("","Selecione um registro.")
        registrar_saida(sel)
        self._carregar()


# ══════════════════════════════════════════════════════════════
# MÓDULO FINANCEIRO
# ══════════════════════════════════════════════════════════════

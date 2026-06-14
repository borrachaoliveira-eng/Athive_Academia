import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloAlunos(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        btns = []
        if pode(self.usuario,"alunos","editar"):
            btns.append({"label":"➕  Novo Aluno","cmd":self._novo,"bg":COR_TEAL})
        Cabecalho(self, "👥 Alunos", "Cadastro e gestão de alunos", btns=btns or None)

        self.var_busca = tk.StringVar()
        self.var_busca.trace("w", lambda *a: self._carregar())
        self.var_un    = tk.StringVar(value="Todas")
        self.var_st    = tk.StringVar(value="Todos")

        bf = BarraFiltros(self)
        bf.add_label("Buscar:").add_entry(self.var_busca, 22)
        bf.add_spacer().add_label("Unidade:")
        bf.add_combo(self.var_un, UNIDADES_ALL, callback=self._carregar)
        bf.add_spacer().add_label("Status:")
        bf.add_combo(self.var_st, ["Todos"]+STATUS_ALUNO, callback=self._carregar)

        cols = [("nome","Nome",200),("unidade","Unidade",90),("plano","Plano",90),
                ("valor","Valor",90),("vencimento","Vencimento",100),("status","Status",90),
                ("telefone","Telefone",110)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        if pode(self.usuario,"alunos","editar"):
            ac.add_btn("✏  Editar", self._editar, COR_NAVY)
        if pode(self.usuario,"alunos","excluir"):
            ac.add_btn("🗑  Excluir", self._excluir, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self, *_):
        def _f():
            un = self.var_un.get()
            st = self.var_st.get()
            d  = listar_alunos(
                unidade=un if un!="Todas" else None,
                status=st if st!="Todos" else None,
                busca=self.var_busca.get().strip() or None
            )
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("nome",""), r.get("unidade",""), r.get("plano",""),
            brl(r.get("valor_plano",0)), data_br(r.get("data_vencimento","")),
            r.get("status",""), r.get("telefone","") or "—"
        ))
        self.ac.set_info(f"{len(dados)} aluno(s) · Total mensalidades: {brl(sum(a.get('valor_plano',0) for a in dados if a.get('status')=='Ativo'))}")

    def _novo(self):      FormAluno(self, None, self._carregar)
    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return messagebox.showinfo("","Selecione um aluno.")
        a = next((x for x in self.dados if x["id"]==sel), None)
        if a: FormAluno(self, a, self._carregar)
    def _excluir(self):
        sel = self.tbl.selecionado()
        if not sel: return
        a = next((x for x in self.dados if x["id"]==sel), None)
        if a and messagebox.askyesno("Confirmar", f"Excluir {a['nome']}?"):
            deletar_aluno(sel); self._carregar()


class FormAluno(FormBase):
    def __init__(self, parent, aluno, callback):
        super().__init__(parent, "Novo Aluno" if not aluno else "Editar Aluno", 560, 580)
        self.aluno    = aluno
        self.callback = callback

        self.v_nome  = self.campo("Nome completo *", 0, colspan=2)
        self.v_cpf   = self.campo("CPF", 1, col=0)
        self.v_tel   = self.campo("Telefone / WhatsApp", 1, col=1)
        self.v_email = self.campo("E-mail", 2, colspan=2)
        self.v_un    = self.campo("Unidade *", 3, col=0, tipo="combo", valores=UNIDADES)
        self.v_plano = self.campo("Plano *",   3, col=1, tipo="combo", valores=PLANOS)
        self.v_valor = self.campo("Valor plano (R$) *", 4, col=0)
        self.v_ini   = self.campo("Início (DD/MM/AAAA) *", 4, col=1)
        self.v_venc  = self.campo("Vencimento (DD/MM/AAAA) *", 5, col=0)
        self.v_st    = self.campo("Status *", 5, col=1, tipo="combo", valores=STATUS_ALUNO)
        self.txt_obs = self.campo("Observações", 6, colspan=2, tipo="text")

        if aluno:
            self.v_nome.set(aluno.get("nome",""))
            self.v_cpf.set(aluno.get("cpf","") or "")
            self.v_tel.set(aluno.get("telefone","") or "")
            self.v_email.set(aluno.get("email","") or "")
            self.v_un.set(aluno.get("unidade",""))
            self.v_plano.set(aluno.get("plano",""))
            self.v_valor.set(str(aluno.get("valor_plano","0")))
            self.v_ini.set(data_br(aluno.get("data_inicio","")))
            self.v_venc.set(data_br(aluno.get("data_vencimento","")))
            self.v_st.set(aluno.get("status","Ativo"))
            if aluno.get("observacoes"): self.txt_obs.insert("1.0", aluno["observacoes"])
        else:
            self.v_st.set("Ativo")
            self.v_ini.set(datetime.date.today().strftime("%d/%m/%Y"))

    def _salvar(self):
        nome  = self.v_nome.get().strip()
        un    = self.v_un.get()
        plano = self.v_plano.get()
        ini   = parse_data(self.v_ini.get())
        venc  = parse_data(self.v_venc.get())
        st    = self.v_st.get()
        try:    valor = float(self.v_valor.get().replace(",","."))
        except: return messagebox.showwarning("","Valor inválido.")
        if not all([nome, un, plano, ini, venc, st]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        dados = {"nome":nome,"cpf":self.v_cpf.get().strip() or None,
                 "telefone":self.v_tel.get().strip() or None,
                 "email":self.v_email.get().strip() or None,
                 "unidade":un,"plano":plano,"valor_plano":valor,
                 "data_inicio":ini,"data_vencimento":venc,"status":st,
                 "observacoes":self.txt_obs.get("1.0","end").strip() or None}
        salvar_aluno(dados, self.aluno["id"] if self.aluno else None)
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════════════
# MÓDULO FREQUÊNCIA
# ══════════════════════════════════════════════════════════════

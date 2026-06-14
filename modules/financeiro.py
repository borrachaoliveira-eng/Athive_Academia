import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloFinanceiro(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        btns = []
        if pode(self.usuario,"financeiro","editar"):
            btns.append({"label":"➕  Novo Lançamento","cmd":self._novo,"bg":COR_TEAL})
        Cabecalho(self,"💰 Financeiro","Contas a pagar e a receber",btns=btns or None)

        self.var_tipo = tk.StringVar(value="Todos")
        self.var_st   = tk.StringVar(value="Todos")
        self.var_un   = tk.StringVar(value="Todas")
        bf = BarraFiltros(self)
        bf.add_label("Tipo:")
        bf.add_combo(self.var_tipo,["Todos","Receita","Despesa"],callback=self._carregar)
        bf.add_spacer().add_label("Status:")
        bf.add_combo(self.var_st,["Todos","Pendente","Pago","Atrasado","Cancelado"],callback=self._carregar)
        bf.add_spacer().add_label("Unidade:")
        bf.add_combo(self.var_un,UNIDADES_ALL,callback=self._carregar)

        cols = [("tipo","Tipo",70),("categoria","Categoria",120),("descricao","Descrição",200),
                ("valor","Valor",90),("vencimento","Vencimento",100),
                ("status","Status",90),("unidade","Unidade",90),("forma","Forma Pag.",100)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        if pode(self.usuario,"financeiro","editar"):
            ac.add_btn("✏  Editar", self._editar, COR_NAVY)
            ac.add_btn("✅  Marcar Pago", self._pagar, COR_TEAL)
        if pode(self.usuario,"financeiro","excluir"):
            ac.add_btn("🗑  Excluir", self._excluir, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self, *_):
        def _f():
            tipo = self.var_tipo.get()
            st   = self.var_st.get()
            un   = self.var_un.get()
            d = listar_financeiro(
                tipo=tipo if tipo!="Todos" else None,
                status=st if st!="Todos" else None,
                unidade=un if un!="Todas" else None
            )
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("tipo",""), r.get("categoria",""), r.get("descricao",""),
            brl(r.get("valor",0)), data_br(r.get("data_vencimento","")),
            r.get("status",""), r.get("unidade",""),
            r.get("forma_pagamento","") or "—"
        ))
        rec  = sum(r["valor"] for r in dados if r.get("tipo")=="Receita")
        desp = sum(r["valor"] for r in dados if r.get("tipo")=="Despesa")
        self.ac.set_info(f"{len(dados)} registros · Receitas: {brl(rec)} · Despesas: {brl(desp)} · Saldo: {brl(rec-desp)}")

    def _novo(self):    FormFinanceiro(self, None, self._carregar)
    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        r = next((x for x in self.dados if x["id"]==sel), None)
        if r: FormFinanceiro(self, r, self._carregar)
    def _pagar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        if messagebox.askyesno("Confirmar","Marcar como Pago?"):
            salvar_financeiro({"status":"Pago","data_pagamento":hoje()}, sel)
            self._carregar()
    def _excluir(self):
        sel = self.tbl.selecionado()
        if not sel: return
        if messagebox.askyesno("Confirmar","Excluir este lançamento?"):
            deletar_financeiro(sel); self._carregar()


class FormFinanceiro(FormBase):
    def __init__(self, parent, reg, callback):
        super().__init__(parent,"Novo Lançamento" if not reg else "Editar Lançamento", 520, 500)
        self.reg = reg; self.callback = callback

        self.v_tipo  = self.campo("Tipo *",0,col=0,tipo="combo",valores=["Receita","Despesa"])
        self.v_un    = self.campo("Unidade *",0,col=1,tipo="combo",valores=["Unidade 1","Unidade 2","Ambas"])
        self.v_cat   = self.campo("Categoria *",1,colspan=2)
        self.v_desc  = self.campo("Descrição *",2,colspan=2)
        self.v_valor = self.campo("Valor (R$) *",3,col=0)
        self.v_venc  = self.campo("Vencimento (DD/MM/AAAA) *",3,col=1)
        self.v_st    = self.campo("Status *",4,col=0,tipo="combo",
                                   valores=["Pendente","Pago","Atrasado","Cancelado"])
        self.v_forma = self.campo("Forma de pagamento",4,col=1,tipo="combo",valores=FORMAS_PAG)
        self.txt_obs = self.campo("Observações",5,colspan=2,tipo="text")

        self.v_st.set("Pendente")
        if reg:
            self.v_tipo.set(reg.get("tipo",""))
            self.v_un.set(reg.get("unidade",""))
            self.v_cat.set(reg.get("categoria",""))
            self.v_desc.set(reg.get("descricao",""))
            self.v_valor.set(str(reg.get("valor","0")))
            self.v_venc.set(data_br(reg.get("data_vencimento","")))
            self.v_st.set(reg.get("status","Pendente"))
            self.v_forma.set(reg.get("forma_pagamento","") or "")
            if reg.get("observacoes"): self.txt_obs.insert("1.0",reg["observacoes"])

    def _salvar(self):
        try: valor = float(self.v_valor.get().replace(",","."))
        except: return messagebox.showwarning("","Valor inválido.")
        venc = parse_data(self.v_venc.get())
        if not all([self.v_tipo.get(),self.v_un.get(),self.v_cat.get().strip(),
                    self.v_desc.get().strip(),venc,self.v_st.get()]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        dados = {"tipo":self.v_tipo.get(),"unidade":self.v_un.get(),
                 "categoria":self.v_cat.get().strip(),"descricao":self.v_desc.get().strip(),
                 "valor":valor,"data_vencimento":venc,"status":self.v_st.get(),
                 "forma_pagamento":self.v_forma.get() or None,
                 "observacoes":self.txt_obs.get("1.0","end").strip() or None}
        salvar_financeiro(dados, self.reg["id"] if self.reg else None)
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════════════
# MÓDULO MANUTENÇÃO
# ══════════════════════════════════════════════════════════════

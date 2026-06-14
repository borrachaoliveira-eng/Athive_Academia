import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloCompras(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        btns = []
        if pode(self.usuario,"compras","editar"):
            btns.append({"label":"➕  Nova Compra","cmd":self._novo,"bg":COR_TEAL})
        Cabecalho(self,"🛒 Compras","Pedidos de compra e suprimentos",btns=btns or None)

        self.var_st = tk.StringVar(value="Todos")
        self.var_un = tk.StringVar(value="Todas")
        bf = BarraFiltros(self)
        bf.add_label("Status:")
        bf.add_combo(self.var_st,["Todos"]+STATUS_COMPRA,callback=self._carregar)
        bf.add_spacer().add_label("Unidade:")
        bf.add_combo(self.var_un,UNIDADES_ALL,callback=self._carregar)

        cols = [("desc","Descrição",180),("cat","Categoria",110),("forn","Fornecedor",130),
                ("qtd","Qtd",60),("vlr_un","Vlr Unit.",90),("total","Total",90),
                ("solicit","Solicitação",100),("status","Status",100),("unidade","Unidade",90)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        if pode(self.usuario,"compras","editar"):
            ac.add_btn("✏  Editar", self._editar, COR_NAVY)
            ac.add_btn("✅  Recebido", self._recebido, COR_TEAL)
        if pode(self.usuario,"compras","excluir"):
            ac.add_btn("🗑  Excluir", self._excluir, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self, *_):
        def _f():
            st = self.var_st.get()
            un = self.var_un.get()
            d  = listar_compras(status=st if st!="Todos" else None,
                                unidade=un if un!="Todas" else None)
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("descricao",""), r.get("categoria",""),
            r.get("fornecedor","") or "—",
            str(r.get("quantidade",1)), brl(r.get("valor_unitario",0)),
            brl(r.get("valor_total",0)), data_br(r.get("data_solicitacao","")),
            r.get("status",""), r.get("unidade","")
        ))
        total = sum(d.get("valor_total",0) for d in dados)
        self.ac.set_info(f"{len(dados)} pedidos · Total: {brl(total)}")

    def _novo(self):    FormCompra(self, None, self._carregar)
    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        r = next((x for x in self.dados if x["id"]==sel), None)
        if r: FormCompra(self, r, self._carregar)
    def _recebido(self):
        sel = self.tbl.selecionado()
        if not sel: return
        if messagebox.askyesno("Confirmar","Marcar como Recebido?"):
            salvar_compra({"status":"Recebido","data_entrega":hoje()}, sel)
            self._carregar()
    def _excluir(self):
        sel = self.tbl.selecionado()
        if not sel: return
        if messagebox.askyesno("Confirmar","Excluir este pedido?"):
            deletar_compra(sel); self._carregar()


class FormCompra(FormBase):
    def __init__(self, parent, reg, callback):
        super().__init__(parent,"Nova Compra" if not reg else "Editar Compra", 520, 480)
        self.reg = reg; self.callback = callback

        self.v_desc  = self.campo("Descrição *",0,colspan=2)
        self.v_cat   = self.campo("Categoria *",1,col=0,tipo="combo",valores=CATS_COMPRA)
        self.v_un    = self.campo("Unidade *",1,col=1,tipo="combo",valores=UNIDADES)
        self.v_forn  = self.campo("Fornecedor",2,col=0)
        self.v_sol   = self.campo("Solicitante",2,col=1)
        self.v_qtd   = self.campo("Quantidade *",3,col=0)
        self.v_vlrun = self.campo("Valor unitário (R$) *",3,col=1)
        self.v_st    = self.campo("Status *",4,col=0,tipo="combo",valores=STATUS_COMPRA)
        self.v_nf    = self.campo("NF / Recibo",4,col=1)
        self.txt_obs = self.campo("Observações",5,colspan=2,tipo="text")

        self.v_st.set("Solicitado")
        self.v_qtd.set("1")

        if reg:
            self.v_desc.set(reg.get("descricao",""))
            self.v_cat.set(reg.get("categoria",""))
            self.v_un.set(reg.get("unidade",""))
            self.v_forn.set(reg.get("fornecedor","") or "")
            self.v_sol.set(reg.get("solicitante","") or "")
            self.v_qtd.set(str(reg.get("quantidade",1)))
            self.v_vlrun.set(str(reg.get("valor_unitario",0)))
            self.v_st.set(reg.get("status","Solicitado"))
            self.v_nf.set(reg.get("nota_fiscal","") or "")
            if reg.get("observacoes"): self.txt_obs.insert("1.0",reg["observacoes"])

    def _salvar(self):
        desc = self.v_desc.get().strip()
        cat  = self.v_cat.get()
        un   = self.v_un.get()
        st   = self.v_st.get()
        try:
            qtd   = float(self.v_qtd.get().replace(",","."))
            vlrun = float(self.v_vlrun.get().replace(",","."))
        except: return messagebox.showwarning("","Verifique os campos numéricos.")
        if not all([desc, cat, un, st]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        dados = {"descricao":desc,"categoria":cat,"unidade":un,"status":st,
                 "quantidade":qtd,"valor_unitario":vlrun,
                 "fornecedor":self.v_forn.get().strip() or None,
                 "solicitante":self.v_sol.get().strip() or None,
                 "nota_fiscal":self.v_nf.get().strip() or None,
                 "observacoes":self.txt_obs.get("1.0","end").strip() or None}
        salvar_compra(dados, self.reg["id"] if self.reg else None)
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════════════
# MÓDULO USUÁRIOS (somente Admin)
# ══════════════════════════════════════════════════════════════

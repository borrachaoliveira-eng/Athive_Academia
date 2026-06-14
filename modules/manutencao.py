import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloManutencao(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self.equips  = []
        self._build()
        self._carregar()

    def _build(self):
        btns = []
        if pode(self.usuario,"manutencao","editar"):
            btns = [{"label":"➕  Nova Manutenção","cmd":self._novo,"bg":COR_TEAL},
                    {"label":"🔩  Equipamentos","cmd":self._gerenciar_equip,"bg":COR_NAVY}]
        Cabecalho(self,"🔧 Manutenção","Equipamentos e histórico de manutenções",btns=btns or None)

        self.var_un = tk.StringVar(value="Todas")
        bf = BarraFiltros(self)
        bf.add_label("Unidade:")
        bf.add_combo(self.var_un, UNIDADES_ALL, callback=self._carregar)

        cols = [("equip","Equipamento",150),("unidade","Unidade",90),
                ("data","Data",90),("tipo","Tipo",90),("descricao","Descrição",220),
                ("valor","Valor",90),("dias","Dias",70),("forn","Fornecedor",130)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        if pode(self.usuario,"manutencao","editar"):
            ac.add_btn("✏  Editar", self._editar, COR_NAVY)
        if pode(self.usuario,"manutencao","excluir"):
            ac.add_btn("🗑  Excluir", self._excluir, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self, *_):
        def _f():
            un = self.var_un.get()
            d  = listar_manutencao(unidade=un if un!="Todas" else None)
            eq = listar_equipamentos(unidade=un if un!="Todas" else None)
            self.after(0, lambda: self._render(d, eq))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados, equips):
        self.dados  = dados
        self.equips = equips
        self.tbl.popular(dados, lambda r: (
            r.get("equip_nome",""), r.get("equip_unidade",""),
            data_br(r.get("data_manutencao","")), r.get("tipo",""),
            r.get("descricao",""), brl(r.get("valor",0)),
            r.get("dias_parado",0), r.get("fornecedor","") or "—"
        ))
        total = sum(d.get("valor",0) for d in dados)
        self.ac.set_info(f"{len(dados)} registros · Total: {brl(total)}")

    def _novo(self):
        if not self.equips:
            return messagebox.showinfo("","Cadastre equipamentos primeiro.")
        FormManutencao(self, None, self.equips, self._carregar)

    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        r = next((x for x in self.dados if x["id"]==sel), None)
        if r: FormManutencao(self, r, self.equips, self._carregar)

    def _excluir(self):
        sel = self.tbl.selecionado()
        if not sel: return
        if messagebox.askyesno("Confirmar","Excluir este registro?"):
            deletar_manutencao(sel); self._carregar()

    def _gerenciar_equip(self):
        GerenciarEquipamentos(self, self._carregar)


class FormManutencao(FormBase):
    def __init__(self, parent, reg, equips, callback):
        super().__init__(parent,"Nova Manutenção" if not reg else "Editar Manutenção", 520, 460)
        self.reg      = reg
        self.equips   = equips
        self.callback = callback

        nomes = [f"{e['nome']} — {e['unidade']}" for e in equips]
        self.v_equip = self.campo("Equipamento *",0,colspan=2,tipo="combo",valores=nomes)
        self.v_data  = self.campo("Data (DD/MM/AAAA) *",1,col=0)
        self.v_tipo  = self.campo("Tipo *",1,col=1,tipo="combo",valores=TIPOS_MANUT)
        self.v_desc  = self.campo("Descrição *",2,colspan=2)
        self.v_valor = self.campo("Valor (R$) *",3,col=0)
        self.v_dias  = self.campo("Dias parado",3,col=1)
        self.v_forn  = self.campo("Fornecedor / Técnico",4,col=0)
        self.v_nf    = self.campo("NF / Recibo nº",4,col=1)
        self.txt_obs = self.campo("Observações",5,colspan=2,tipo="text")

        self.v_data.set(datetime.date.today().strftime("%d/%m/%Y"))
        self.v_dias.set("0")

        if reg:
            nome_eq = f"{reg.get('equip_nome','')} — {reg.get('equip_unidade','')}"
            self.v_equip.set(nome_eq)
            self.v_data.set(data_br(reg.get("data_manutencao","")))
            self.v_tipo.set(reg.get("tipo",""))
            self.v_desc.set(reg.get("descricao",""))
            self.v_valor.set(str(reg.get("valor","0")))
            self.v_dias.set(str(reg.get("dias_parado","0")))
            self.v_forn.set(reg.get("fornecedor","") or "")
            self.v_nf.set(reg.get("nota_fiscal","") or "")
            if reg.get("observacoes"): self.txt_obs.insert("1.0",reg["observacoes"])

    def _salvar(self):
        eq_str = self.v_equip.get()
        data   = parse_data(self.v_data.get())
        tipo   = self.v_tipo.get()
        desc   = self.v_desc.get().strip()
        try:
            valor = float(self.v_valor.get().replace(",","."))
            dias  = int(self.v_dias.get() or 0)
        except: return messagebox.showwarning("","Verifique os campos numéricos.")
        if not all([eq_str, data, tipo, desc]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        equip = next((e for e in self.equips
                      if f"{e['nome']} — {e['unidade']}" == eq_str), None)
        if not equip: return messagebox.showwarning("","Selecione um equipamento válido.")
        dados = {"equipamento_id":equip["id"],"data_manutencao":data,"tipo":tipo,
                 "descricao":desc,"valor":valor,"dias_parado":dias,
                 "fornecedor":self.v_forn.get().strip() or None,
                 "nota_fiscal":self.v_nf.get().strip() or None,
                 "observacoes":self.txt_obs.get("1.0","end").strip() or None}
        salvar_manutencao(dados, self.reg["id"] if self.reg else None)
        self.callback(); self.destroy()


class GerenciarEquipamentos(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Gerenciar Equipamentos")
        self.geometry("800x520")
        self.configure(bg=COR_BG)
        self.grab_set()
        self.callback = callback
        self.dados    = []
        self._build()
        self._carregar()

    def _build(self):
        frm_top = tk.Frame(self, bg=COR_NAVY, padx=20, pady=12)
        frm_top.pack(fill="x")
        tk.Label(frm_top, text="🔩  Gerenciar Equipamentos",
                 font=(FONT_FAMILY,12,"bold"), bg=COR_NAVY, fg=COR_WHITE).pack(side="left")
        tk.Button(frm_top, text="➕ Novo", font=(FONT_FAMILY,9,"bold"),
                  bg=COR_TEAL, fg=COR_WHITE, relief="flat", cursor="hand2",
                  padx=12, pady=6, command=self._novo).pack(side="right")

        cols = [("nome","Nome",160),("unidade","Unidade",100),("categoria","Categoria",110),
                ("marca","Marca",110),("serie","Série",100),("aquisicao","Aquisição",90),
                ("valor","Valor Aq.",100),("status","Status",100)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        ac.add_btn("✏  Editar", self._editar, COR_NAVY)
        ac.add_btn("🗑  Excluir", self._excluir, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self):
        def _f():
            d = listar_equipamentos()
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("nome",""), r.get("unidade",""), r.get("categoria",""),
            r.get("marca","") or "—", r.get("numero_serie","") or "—",
            data_br(r.get("data_aquisicao","")) if r.get("data_aquisicao") else "—",
            brl(r.get("valor_aquisicao",0)), r.get("status","")
        ))
        self.ac.set_info(f"{len(dados)} equipamentos")

    def _novo(self):    FormEquipamento(self, None, self._carregar)
    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        eq = next((x for x in self.dados if x["id"]==sel), None)
        if eq: FormEquipamento(self, eq, self._carregar)
    def _excluir(self):
        sel = self.tbl.selecionado()
        if not sel: return
        eq = next((x for x in self.dados if x["id"]==sel), None)
        if eq and messagebox.askyesno("Confirmar",f"Excluir {eq['nome']}? O histórico de manutenções também será removido."):
            deletar_equipamento(sel); self._carregar(); self.callback()


class FormEquipamento(FormBase):
    def __init__(self, parent, eq, callback):
        super().__init__(parent,"Novo Equipamento" if not eq else "Editar Equipamento", 520, 480)
        self.eq = eq; self.callback = callback

        self.v_nome  = self.campo("Nome *",0,colspan=2)
        self.v_un    = self.campo("Unidade *",1,col=0,tipo="combo",valores=UNIDADES)
        self.v_cat   = self.campo("Categoria *",1,col=1,tipo="combo",valores=CATS_EQUIP)
        self.v_marca = self.campo("Marca",2,col=0)
        self.v_mod   = self.campo("Modelo",2,col=1)
        self.v_serie = self.campo("Número de série",3,col=0)
        self.v_st    = self.campo("Status *",3,col=1,tipo="combo",valores=STATUS_EQUIP)
        self.v_aq    = self.campo("Data aquisição (DD/MM/AAAA)",4,col=0)
        self.v_val   = self.campo("Valor de aquisição (R$)",4,col=1)
        self.txt_obs = self.campo("Observações",5,colspan=2,tipo="text")

        self.v_st.set("Ativo")
        if eq:
            self.v_nome.set(eq.get("nome",""))
            self.v_un.set(eq.get("unidade",""))
            self.v_cat.set(eq.get("categoria",""))
            self.v_marca.set(eq.get("marca","") or "")
            self.v_mod.set(eq.get("modelo","") or "")
            self.v_serie.set(eq.get("numero_serie","") or "")
            self.v_st.set(eq.get("status","Ativo"))
            if eq.get("data_aquisicao"): self.v_aq.set(data_br(eq["data_aquisicao"]))
            if eq.get("valor_aquisicao"): self.v_val.set(str(eq["valor_aquisicao"]))
            if eq.get("observacoes"): self.txt_obs.insert("1.0",eq["observacoes"])

    def _salvar(self):
        nome = self.v_nome.get().strip()
        un   = self.v_un.get()
        cat  = self.v_cat.get()
        st   = self.v_st.get()
        if not all([nome, un, cat, st]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        dados = {"nome":nome,"unidade":un,"categoria":cat,"status":st,
                 "marca":self.v_marca.get().strip() or None,
                 "modelo":self.v_mod.get().strip() or None,
                 "numero_serie":self.v_serie.get().strip() or None,
                 "data_aquisicao":parse_data(self.v_aq.get()) or None,
                 "observacoes":self.txt_obs.get("1.0","end").strip() or None}
        if self.v_val.get().strip():
            try: dados["valor_aquisicao"] = float(self.v_val.get().replace(",","."))
            except: pass
        salvar_equipamento(dados, self.eq["id"] if self.eq else None)
        self.callback(); self.destroy()


# ══════════════════════════════════════════════════════════════
# MÓDULO COMPRAS
# ══════════════════════════════════════════════════════════════

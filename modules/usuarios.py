import tkinter as tk
from tkinter import ttk, messagebox
import threading, datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import *
from config import *
from modules.ui_base import *


class ModuloUsuarios(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        Cabecalho(self,"👤 Usuários","Gerenciamento de acessos ao sistema",
                  btns=[{"label":"➕  Novo Usuário","cmd":self._novo,"bg":COR_TEAL}])

        cols = [("nome","Nome",160),("email","E-mail",200),("perfil","Perfil",110),
                ("unidade","Unidade",110),("ativo","Ativo",70),("ultimo","Último Login",140)]
        self.tbl = Tabela(self, cols)
        self.tbl.bind_double(self._editar)

        ac = BarraAcoes(self)
        ac.add_btn("✏  Editar", self._editar, COR_NAVY)
        ac.add_btn("🔒  Desativar", self._desativar, COR_DANGER)
        ac.add_info()
        self.ac = ac

    def _carregar(self):
        def _f():
            d = listar_usuarios()
            self.after(0, lambda: self._render(d))
        threading.Thread(target=_f, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("nome",""), r.get("email",""),
            r.get("perfil","").capitalize(), r.get("unidade",""),
            "Sim" if r.get("ativo") else "Não",
            data_br(r.get("ultimo_login","")) if r.get("ultimo_login") else "—"
        ))
        self.ac.set_info(f"{len(dados)} usuário(s)")

    def _novo(self):    FormUsuario(self, None, self._carregar)
    def _editar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        u = next((x for x in self.dados if x["id"]==sel), None)
        if u: FormUsuario(self, u, self._carregar)
    def _desativar(self):
        sel = self.tbl.selecionado()
        if not sel: return
        u = next((x for x in self.dados if x["id"]==sel), None)
        if u and u["id"] == self.usuario["id"]:
            return messagebox.showwarning("","Não é possível desativar seu próprio usuário.")
        if u and messagebox.askyesno("Confirmar",f"Desativar {u['nome']}?"):
            deletar_usuario(sel); self._carregar()


class FormUsuario(FormBase):
    def __init__(self, parent, usuario, callback):
        super().__init__(parent,"Novo Usuário" if not usuario else "Editar Usuário", 480, 400)
        self.usuario_edit = usuario; self.callback = callback

        self.v_nome  = self.campo("Nome completo *",0,colspan=2)
        self.v_email = self.campo("E-mail *",1,colspan=2)
        self.v_perf  = self.campo("Perfil *",2,col=0,tipo="combo",valores=PERFIS)
        self.v_un    = self.campo("Unidade",2,col=1,tipo="combo",valores=UNIDADES_ALL)

        if not usuario:
            self.v_senha = self.campo("Senha inicial *",3,colspan=2)

        if usuario:
            self.v_nome.set(usuario.get("nome",""))
            self.v_email.set(usuario.get("email",""))
            self.v_perf.set(usuario.get("perfil","operador"))
            self.v_un.set(usuario.get("unidade","Todas"))
        else:
            self.v_perf.set("operador")
            self.v_un.set("Todas")

    def _salvar(self):
        nome  = self.v_nome.get().strip()
        email = self.v_email.get().strip().lower()
        perf  = self.v_perf.get()
        un    = self.v_un.get()
        if not all([nome, email, perf]):
            return messagebox.showwarning("","Preencha os campos obrigatórios (*).")
        dados = {"nome":nome,"email":email,"perfil":perf,"unidade":un}
        if not self.usuario_edit:
            senha = self.v_senha.get().strip()
            if len(senha) < 6:
                return messagebox.showwarning("","A senha deve ter ao menos 6 caracteres.")
            dados["senha"] = senha
        salvar_usuario(dados, self.usuario_edit["id"] if self.usuario_edit else None)
        self.callback(); self.destroy()

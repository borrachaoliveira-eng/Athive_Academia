# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Módulo Depreciação de Equipamentos
# ══════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, datetime, os
from config import *
from modules.ui_base import *
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import relatorio_depreciacao, listar_equipamentos, salvar_equipamento

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except:
    MATPLOTLIB_OK = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_OK = True
except:
    REPORTLAB_OK = False


class ModuloDepreciacao(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self.dados   = []
        self._build()
        self._carregar()

    def _build(self):
        btns = []
        if pode(self.usuario, "depreciacao", "editar"):
            btns.append({"label":"⚙  Config. Depreciação","cmd":self._config_selecionado,
                          "bg":COR_NAVY})
        if pode(self.usuario, "relatorios", "gerar"):
            btns.append({"label":"📄  Exportar PDF","cmd":self._exportar_pdf,
                          "bg":COR_DANGER})
        Cabecalho(self, "📉 Depreciação de Equipamentos",
                  "Linha reta e saldo decrescente · configurável por equipamento",
                  btns=btns if btns else None)

        # Filtros
        self.var_un = tk.StringVar(value="Todas")
        self.var_metodo = tk.StringVar(value="Todos")
        bf = BarraFiltros(self)
        bf.add_label("Unidade:")
        bf.add_combo(self.var_un, UNIDADES_ALL, callback=self._carregar)
        bf.add_spacer()
        bf.add_label("Método:")
        bf.add_combo(self.var_metodo, ["Todos"]+METODOS_DEPR, callback=self._carregar)

        # Tabela
        cols = [
            ("nome",         "Equipamento",        160),
            ("unidade",      "Unidade",             90),
            ("metodo",       "Método",             120),
            ("valor_aq",     "Valor Aquisição",    110),
            ("vida_util",    "Vida Útil",           80),
            ("anos_uso",     "Anos em uso",         90),
            ("valor_atual",  "Valor Atual",        110),
            ("depreciado",   "Depreciado",         110),
            ("pct",          "% Depreciado",        90),
            ("anos_rest",    "Anos restantes",      90),
            ("substituicao", "Substituição est.",  120),
        ]
        self.tbl = Tabela(self, cols)

        ac = BarraAcoes(self)
        ac.add_btn("⚙  Configurar", self._config_selecionado, bg=COR_NAVY)
        ac.add_info()
        self.barra_ac = ac

        # Gráfico de pizza abaixo
        if MATPLOTLIB_OK:
            self.frm_graf = tk.Frame(self, bg=COR_BG, padx=20, pady=8)
            self.frm_graf.pack(fill="x")

    def _carregar(self, *_):
        def _fetch():
            un     = self.var_un.get()
            dados  = relatorio_depreciacao(un if un != "Todas" else None)
            metodo = self.var_metodo.get()
            if metodo != "Todos":
                dados = [d for d in dados if d.get("metodo_depreciacao") == metodo]
            self.after(0, lambda: self._render(dados))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render(self, dados):
        self.dados = dados
        self.tbl.popular(dados, lambda r: (
            r.get("nome",""),
            r.get("unidade",""),
            r.get("metodo_depreciacao",""),
            brl(r.get("valor_aquisicao",0)),
            f"{r.get('vida_util_anos',0)} anos",
            f"{r.get('anos_uso',0):.1f} anos",
            brl(r.get("valor_atual",0)),
            brl(r.get("depreciado",0)),
            f"{r.get('pct_depreciado',0):.1f}%",
            f"{r.get('anos_restantes',0):.1f} anos",
            data_br(r.get("substituicao_em","")) if r.get("substituicao_em") else "—",
        ))
        self.barra_ac.set_info(
            f"{len(dados)} equipamentos · "
            f"Valor total atual: {brl(sum(d.get('valor_atual',0) for d in dados))} · "
            f"Total depreciado: {brl(sum(d.get('depreciado',0) for d in dados))}"
        )
        self._render_grafico(dados)

    def _render_grafico(self, dados):
        if not MATPLOTLIB_OK or not dados: return
        for w in self.frm_graf.winfo_children(): w.destroy()

        card = tk.Frame(self.frm_graf, bg=COR_WHITE,
                        highlightthickness=1, highlightbackground=COR_BORDER)
        card.pack(fill="x")
        tk.Label(card, text="Valor atual vs. depreciado por equipamento",
                 font=(FONT_FAMILY,10,"bold"), bg=COR_WHITE, fg=COR_TEXT,
                 padx=14, pady=8).pack(anchor="w")

        nomes   = [d["nome"][:16] for d in dados[:8]]
        atuais  = [d.get("valor_atual",0)  for d in dados[:8]]
        deprec  = [d.get("depreciado",0)   for d in dados[:8]]

        fig = Figure(figsize=(10,2.8), dpi=90, facecolor=COR_WHITE)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(COR_BG)
        x = range(len(nomes))
        ax.barh([i+0.2 for i in x], atuais,  0.35, label="Valor atual",  color="#1D9E75", alpha=0.85)
        ax.barh([i-0.2 for i in x], deprec,  0.35, label="Depreciado",   color="#A32D2D", alpha=0.85)
        ax.set_yticks(list(x))
        ax.set_yticklabels(nomes, fontsize=9)
        ax.xaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v,_: f"R${v/1000:.0f}k" if v>=1000 else f"R${v:.0f}"))
        ax.legend(fontsize=9)
        ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout(pad=1.2)

        cv = FigureCanvasTkAgg(fig, master=card)
        cv.draw()
        cv.get_tk_widget().pack(fill="x", padx=12, pady=(0,12))

    def _config_selecionado(self):
        sel = self.tbl.selecionado()
        if not sel:
            messagebox.showinfo("Selecione", "Selecione um equipamento.")
            return
        equip = next((d for d in self.dados if d["id"]==sel), None)
        if equip:
            FormConfigDepreciacao(self, equip, self._carregar)

    def _exportar_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showwarning("ReportLab", "Biblioteca reportlab não instalada.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"depreciacao_{datetime.date.today()}.pdf"
        )
        if not path: return
        threading.Thread(target=lambda: self._gerar_pdf(path), daemon=True).start()

    def _gerar_pdf(self, path):
        try:
            doc   = SimpleDocTemplate(path, pagesize=A4,
                                       topMargin=2*cm, bottomMargin=2*cm,
                                       leftMargin=2*cm, rightMargin=2*cm)
            styles = getSampleStyleSheet()
            story  = []

            titulo = ParagraphStyle("titulo", parent=styles["Title"],
                                     textColor=colors.HexColor(COR_NAVY),
                                     spaceAfter=4)
            story.append(Paragraph("Athive — Relatório de Depreciação de Equipamentos", titulo))
            story.append(Paragraph(
                f"Emitido em {datetime.date.today().strftime('%d/%m/%Y')} · "
                f"Desenvolvido por Tech Oliveira",
                styles["Normal"]))
            story.append(Spacer(1, 0.4*cm))

            headers = ["Equipamento","Unidade","Método","Valor Aq.","Vida Útil",
                       "Anos Uso","Valor Atual","Depreciado","% Depr.","Substituição"]
            rows = [headers]
            for d in self.dados:
                rows.append([
                    d.get("nome",""),
                    d.get("unidade",""),
                    d.get("metodo_depreciacao",""),
                    brl(d.get("valor_aquisicao",0)),
                    f"{d.get('vida_util_anos',0)} anos",
                    f"{d.get('anos_uso',0):.1f}",
                    brl(d.get("valor_atual",0)),
                    brl(d.get("depreciado",0)),
                    f"{d.get('pct_depreciado',0):.1f}%",
                    data_br(d.get("substituicao_em","")) if d.get("substituicao_em") else "—",
                ])

            tbl = Table(rows, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND",   (0,0), (-1,0), colors.HexColor(COR_NAVY)),
                ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
                ("FONTSIZE",     (0,0), (-1,0), 8),
                ("FONTSIZE",     (0,1), (-1,-1), 7.5),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),
                 [colors.HexColor("#f7f6f3"), colors.white]),
                ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor(COR_BORDER)),
                ("ALIGN",        (0,0), (-1,-1), "CENTER"),
                ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING",   (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 0.4*cm))

            total_aq  = sum(d.get("valor_aquisicao",0) for d in self.dados)
            total_at  = sum(d.get("valor_atual",0)     for d in self.dados)
            total_dep = sum(d.get("depreciado",0)       for d in self.dados)
            story.append(Paragraph(
                f"<b>Total Aquisição:</b> {brl(total_aq)} · "
                f"<b>Valor Atual:</b> {brl(total_at)} · "
                f"<b>Total Depreciado:</b> {brl(total_dep)}",
                styles["Normal"]))

            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado",
                f"Relatório salvo em:\n{path}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))


class FormConfigDepreciacao(FormBase):
    def __init__(self, parent, equip, callback):
        super().__init__(parent, f"Configurar Depreciação — {equip['nome']}", 480, 420)
        self.equip    = equip
        self.callback = callback

        self.v_vida   = self.campo("Vida útil (anos)", 0, col=0)
        self.v_resid  = self.campo("Valor residual (R$)", 0, col=1)
        self.v_taxa   = self.campo("Taxa depreciação anual (%)", 1, col=0)
        self.v_metodo = self.campo("Método", 1, col=1,
                                    tipo="combo", valores=METODOS_DEPR)

        # Preencher
        self.v_vida.set(str(equip.get("vida_util_anos",10)))
        self.v_resid.set(str(equip.get("valor_residual",0)))
        self.v_taxa.set(str(equip.get("taxa_depreciacao",10.0)))
        self.v_metodo.set(equip.get("metodo_depreciacao","Linha reta"))

        # Preview
        tk.Label(self.frm, text="Prévia do cálculo:", font=(FONT_FAMILY,9,"bold"),
                 bg=COR_BG, fg=COR_TEXT).grid(row=6, column=0, columnspan=2,
                                                sticky="w", padx=4, pady=(16,4))
        self.lbl_prev = tk.Label(self.frm, text="", font=(FONT_FAMILY,9),
                                  bg=COR_WHITE, fg=COR_TEXT, padx=10, pady=8,
                                  relief="solid", bd=1, justify="left", anchor="w")
        self.lbl_prev.grid(row=7, column=0, columnspan=2, sticky="ew", padx=4)

        for v in [self.v_vida, self.v_resid, self.v_taxa, self.v_metodo]:
            v.trace("w", lambda *a: self._preview())
        self._preview()

    def _preview(self):
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
            from local_db import calcular_depreciacao
            eq_temp = {**self.equip,
                       "vida_util_anos":     int(self.v_vida.get() or 10),
                       "valor_residual":     float(self.v_resid.get().replace(",",".") or 0),
                       "taxa_depreciacao":   float(self.v_taxa.get().replace(",",".") or 10),
                       "metodo_depreciacao": self.v_metodo.get()}
            d = calcular_depreciacao(eq_temp)
            self.lbl_prev.config(
                text=(f"Valor atual:  {brl(d['valor_atual'])}   |   "
                      f"Depreciado:  {brl(d['depreciado'])} ({d['pct_depreciado']:.1f}%)\n"
                      f"Anos em uso: {d['anos_uso']:.1f}   |   "
                      f"Depr. anual: {brl(d['depreciacao_anual'])}   |   "
                      f"Substituição: {data_br(d['substituicao_em']) if d['substituicao_em'] else '—'}")
            )
        except:
            self.lbl_prev.config(text="Preencha os campos para ver a prévia.")

    def _salvar(self):
        try:
            dados = {
                "vida_util_anos":    int(self.v_vida.get()),
                "valor_residual":    float(self.v_resid.get().replace(",",".")),
                "taxa_depreciacao":  float(self.v_taxa.get().replace(",",".")),
                "metodo_depreciacao": self.v_metodo.get(),
            }
            salvar_equipamento(dados, self.equip["id"])
            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showwarning("Dados inválidos", str(e))

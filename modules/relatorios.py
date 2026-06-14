# ══════════════════════════════════════════════════════════════
# ATHIVE SISTEMA v1.3 — Módulo de Relatórios PDF
# ══════════════════════════════════════════════════════════════

import tkinter as tk
from tkinter import messagebox, filedialog
import threading, datetime, os
from config import *
from modules.ui_base import *
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'database'))
from local_db import (listar_alunos, listar_financeiro, listar_manutencao,
                       custo_manutencao_por_equipamento, relatorio_depreciacao,
                       listar_compras, kpis_dashboard)

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True
except:
    REPORTLAB_OK = False

NAVY_COLOR   = colors.HexColor(COR_NAVY)
TEAL_COLOR   = colors.HexColor(COR_TEAL)
BORDER_COLOR = colors.HexColor(COR_BORDER)
ALT_COLOR    = colors.HexColor(COR_ALT)
WHITE        = colors.white


def _header_style(styles):
    return ParagraphStyle("athive_title", parent=styles["Title"],
                           textColor=NAVY_COLOR, spaceAfter=2, fontSize=16)

def _sub_style(styles):
    return ParagraphStyle("athive_sub", parent=styles["Normal"],
                           textColor=colors.HexColor(COR_MUTED), spaceAfter=8, fontSize=9)

def _tbl_style(headers=True):
    s = [
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("GRID",         (0,0), (-1,-1), 0.3, BORDER_COLOR),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[ALT_COLOR, WHITE]),
    ]
    if headers:
        s += [
            ("BACKGROUND",  (0,0), (-1,0), NAVY_COLOR),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTSIZE",    (0,0), (-1,0), 8),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ]
    return TableStyle(s)

def _rodape(styles):
    return Paragraph(
        f"Desenvolvido por <b>Tech Oliveira</b> · tech-oliveira.com.br · "
        f"Gerado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("rodape", parent=styles["Normal"],
                        textColor=colors.HexColor(COR_MUTED), fontSize=7,
                        alignment=TA_CENTER))


class ModuloRelatorios(tk.Frame):
    def __init__(self, parent, usuario):
        super().__init__(parent, bg=COR_BG)
        self.pack(fill="both", expand=True)
        self.usuario = usuario
        self._build()

    def _build(self):
        Cabecalho(self, "📄 Relatórios", "Geração de relatórios em PDF")

        frm = tk.Frame(self, bg=COR_BG, padx=28, pady=20)
        frm.pack(fill="both", expand=True)

        relatorios = [
            ("📋 Relatório de Alunos",
             "Lista completa de alunos com status, plano e vencimento.",
             self._rel_alunos, COR_NAVY),
            ("💰 Relatório Financeiro",
             "Receitas e despesas com totais por categoria e status.",
             self._rel_financeiro, COR_TEAL),
            ("🔧 Relatório de Manutenção",
             "Histórico completo de manutenções com custo e MTBF.",
             self._rel_manutencao, COR_AMBER),
            ("📉 Relatório de Depreciação",
             "Valor atual e depreciação de todos os equipamentos.",
             self._rel_depreciacao, COR_DANGER),
            ("🛒 Relatório de Compras",
             "Pedidos de compra por status, categoria e fornecedor.",
             self._rel_compras, COR_NAVY),
            ("📊 Relatório Gerencial",
             "Visão executiva consolidada com KPIs de todas as unidades.",
             self._rel_gerencial, COR_TEAL),
        ]

        for i, (titulo, desc, cmd, cor) in enumerate(relatorios):
            card = tk.Frame(frm, bg=COR_WHITE,
                            highlightthickness=1, highlightbackground=COR_BORDER)
            card.grid(row=i//2, column=i%2, padx=(0 if i%2==0 else 8, 8 if i%2==0 else 0),
                      pady=(0,12), sticky="nsew")
            frm.columnconfigure(i%2, weight=1)
            frm.rowconfigure(i//2, weight=1)

            tk.Frame(card, bg=cor, height=3).pack(fill="x")
            inner = tk.Frame(card, bg=COR_WHITE, padx=16, pady=14)
            inner.pack(fill="both", expand=True)
            tk.Label(inner, text=titulo, font=(FONT_FAMILY,11,"bold"),
                     bg=COR_WHITE, fg=COR_TEXT).pack(anchor="w")
            tk.Label(inner, text=desc, font=(FONT_FAMILY,9),
                     bg=COR_WHITE, fg=COR_MUTED, wraplength=280,
                     justify="left").pack(anchor="w", pady=(4,12))
            tk.Button(inner, text="Gerar PDF →",
                      font=(FONT_FAMILY,9,"bold"), bg=cor, fg=COR_WHITE,
                      relief="flat", cursor="hand2", padx=14, pady=6,
                      activebackground=cor, command=cmd).pack(anchor="e")

        if not REPORTLAB_OK:
            tk.Label(frm, text="⚠  ReportLab não instalado. Execute: pip install reportlab",
                     font=(FONT_FAMILY,10), bg=COR_AMBER_LIGHT, fg=COR_AMBER,
                     padx=12, pady=8).grid(row=3, column=0, columnspan=2, sticky="ew", pady=8)

    def _pedir_path(self, nome) -> str | None:
        return filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=f"{nome}_{datetime.date.today()}.pdf"
        )

    def _rel_alunos(self):
        if not REPORTLAB_OK: return
        path = self._pedir_path("alunos")
        if not path: return
        def _gerar():
            alunos = listar_alunos()
            styles = getSampleStyleSheet()
            doc    = SimpleDocTemplate(path, pagesize=landscape(A4),
                                        topMargin=1.5*cm, bottomMargin=1.5*cm,
                                        leftMargin=1.5*cm, rightMargin=1.5*cm)
            story = [
                Paragraph("Athive — Relatório de Alunos", _header_style(styles)),
                Paragraph(f"Total: {len(alunos)} alunos · {datetime.date.today().strftime('%d/%m/%Y')}",
                           _sub_style(styles)),
                Spacer(1, 0.3*cm),
            ]
            headers = ["Nome","CPF","Telefone","Unidade","Plano","Valor","Início","Vencimento","Status"]
            rows = [headers] + [[
                a.get("nome",""), a.get("cpf","") or "—", a.get("telefone","") or "—",
                a.get("unidade",""), a.get("plano",""), brl(a.get("valor_plano",0)),
                data_br(a.get("data_inicio","")), data_br(a.get("data_vencimento","")),
                a.get("status",""),
            ] for a in alunos]
            story.append(Table(rows, repeatRows=1, style=_tbl_style()))
            story += [Spacer(1,0.4*cm), HRFlowable(width="100%",color=BORDER_COLOR), _rodape(styles)]
            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado", f"Salvo em:\n{path}"))
        threading.Thread(target=_gerar, daemon=True).start()

    def _rel_financeiro(self):
        if not REPORTLAB_OK: return
        path = self._pedir_path("financeiro")
        if not path: return
        def _gerar():
            registros = listar_financeiro()
            receitas  = [r for r in registros if r["tipo"]=="Receita"]
            despesas  = [r for r in registros if r["tipo"]=="Despesa"]
            styles    = getSampleStyleSheet()
            doc       = SimpleDocTemplate(path, pagesize=landscape(A4),
                                           topMargin=1.5*cm, bottomMargin=1.5*cm,
                                           leftMargin=1.5*cm, rightMargin=1.5*cm)
            story = [
                Paragraph("Athive — Relatório Financeiro", _header_style(styles)),
                Paragraph(f"Total de lançamentos: {len(registros)}", _sub_style(styles)),
                Spacer(1,0.3*cm),
                Paragraph("Receitas", ParagraphStyle("sec", parent=styles["Heading2"],
                                                      textColor=TEAL_COLOR)),
            ]
            headers = ["Categoria","Descrição","Valor","Vencimento","Pagamento","Status","Unidade","Forma Pag."]
            rows_r = [headers] + [[
                r.get("categoria",""), r.get("descricao",""),
                brl(r.get("valor",0)), data_br(r.get("data_vencimento","")),
                data_br(r.get("data_pagamento","")) if r.get("data_pagamento") else "—",
                r.get("status",""), r.get("unidade",""), r.get("forma_pagamento","") or "—",
            ] for r in receitas]
            story.append(Table(rows_r, repeatRows=1, style=_tbl_style()))
            story += [Spacer(1,0.4*cm),
                      Paragraph(f"Total receitas: {brl(sum(r['valor'] for r in receitas))}",
                                 styles["Normal"]),
                      Spacer(1,0.4*cm),
                      Paragraph("Despesas", ParagraphStyle("sec2", parent=styles["Heading2"],
                                                            textColor=colors.HexColor(COR_DANGER)))]
            rows_d = [headers] + [[
                r.get("categoria",""), r.get("descricao",""),
                brl(r.get("valor",0)), data_br(r.get("data_vencimento","")),
                data_br(r.get("data_pagamento","")) if r.get("data_pagamento") else "—",
                r.get("status",""), r.get("unidade",""), r.get("forma_pagamento","") or "—",
            ] for r in despesas]
            story.append(Table(rows_d, repeatRows=1, style=_tbl_style()))
            story += [Spacer(1,0.3*cm),
                      Paragraph(f"Total despesas: {brl(sum(r['valor'] for r in despesas))}",
                                 styles["Normal"]),
                      Spacer(1,0.4*cm), HRFlowable(width="100%",color=BORDER_COLOR), _rodape(styles)]
            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado", f"Salvo em:\n{path}"))
        threading.Thread(target=_gerar, daemon=True).start()

    def _rel_manutencao(self):
        if not REPORTLAB_OK: return
        path = self._pedir_path("manutencao")
        if not path: return
        def _gerar():
            registros = listar_manutencao()
            resumo    = custo_manutencao_por_equipamento()
            styles    = getSampleStyleSheet()
            doc       = SimpleDocTemplate(path, pagesize=landscape(A4),
                                           topMargin=1.5*cm, bottomMargin=1.5*cm,
                                           leftMargin=1.5*cm, rightMargin=1.5*cm)
            story = [
                Paragraph("Athive — Relatório de Manutenção", _header_style(styles)),
                Paragraph(f"{len(registros)} eventos registrados", _sub_style(styles)),
                Spacer(1,0.3*cm),
                Paragraph("Resumo por Equipamento", styles["Heading2"]),
            ]
            hdr_res = ["Equipamento","Unidade","Ocorrências","Corretivas","Preventivas",
                       "Custo Total","Custo Médio","Dias Parado","Última Manutenção"]
            rows_res = [hdr_res] + [[
                r.get("nome",""), r.get("unidade",""),
                str(r.get("total_ocorrencias",0)), str(r.get("corretivas",0)),
                str(r.get("preventivas",0)), brl(r.get("custo_total",0)),
                brl(r.get("custo_medio",0)), str(r.get("dias_parado_total",0)),
                data_br(r.get("ultima_manutencao","")) if r.get("ultima_manutencao") else "—",
            ] for r in resumo]
            story += [Table(rows_res, repeatRows=1, style=_tbl_style()),
                      Spacer(1,0.4*cm),
                      Paragraph("Histórico Completo", styles["Heading2"])]
            hdr_hist = ["Data","Equipamento","Unidade","Tipo","Descrição","Valor","Dias","Fornecedor"]
            rows_hist = [hdr_hist] + [[
                data_br(r.get("data_manutencao","")),
                r.get("equip_nome",""), r.get("equip_unidade",""),
                r.get("tipo",""), r.get("descricao",""),
                brl(r.get("valor",0)), str(r.get("dias_parado",0)),
                r.get("fornecedor","") or "—",
            ] for r in registros]
            story += [Table(rows_hist, repeatRows=1, style=_tbl_style()),
                      Spacer(1,0.4*cm), HRFlowable(width="100%",color=BORDER_COLOR), _rodape(styles)]
            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado", f"Salvo em:\n{path}"))
        threading.Thread(target=_gerar, daemon=True).start()

    def _rel_depreciacao(self):
        # Delegar ao módulo de depreciação
        from modules.depreciacao import ModuloDepreciacao
        m = ModuloDepreciacao.__new__(ModuloDepreciacao)
        m.dados   = relatorio_depreciacao()
        m.usuario = self.usuario
        m.after   = self.after
        m._exportar_pdf()

    def _rel_compras(self):
        if not REPORTLAB_OK: return
        path = self._pedir_path("compras")
        if not path: return
        def _gerar():
            compras = listar_compras()
            styles  = getSampleStyleSheet()
            doc     = SimpleDocTemplate(path, pagesize=landscape(A4),
                                         topMargin=1.5*cm, bottomMargin=1.5*cm,
                                         leftMargin=1.5*cm, rightMargin=1.5*cm)
            story = [
                Paragraph("Athive — Relatório de Compras", _header_style(styles)),
                Paragraph(f"{len(compras)} pedidos", _sub_style(styles)),
                Spacer(1,0.3*cm),
            ]
            headers = ["Descrição","Categoria","Fornecedor","Qtd","Vlr Unit.","Total","Solicitação","Status","Unidade"]
            rows = [headers] + [[
                c.get("descricao",""), c.get("categoria",""),
                c.get("fornecedor","") or "—",
                str(c.get("quantidade",1)), brl(c.get("valor_unitario",0)),
                brl(c.get("valor_total",0)),
                data_br(c.get("data_solicitacao","")),
                c.get("status",""), c.get("unidade",""),
            ] for c in compras]
            story += [Table(rows, repeatRows=1, style=_tbl_style()),
                      Spacer(1,0.3*cm),
                      Paragraph(f"Total: {brl(sum(c.get('valor_total',0) for c in compras))}",
                                 styles["Normal"]),
                      Spacer(1,0.4*cm), HRFlowable(width="100%",color=BORDER_COLOR), _rodape(styles)]
            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado", f"Salvo em:\n{path}"))
        threading.Thread(target=_gerar, daemon=True).start()

    def _rel_gerencial(self):
        if not REPORTLAB_OK: return
        path = self._pedir_path("relatorio_gerencial")
        if not path: return
        def _gerar():
            styles = getSampleStyleSheet()
            doc    = SimpleDocTemplate(path, pagesize=A4,
                                        topMargin=1.5*cm, bottomMargin=1.5*cm,
                                        leftMargin=2*cm, rightMargin=2*cm)
            story = [
                Paragraph("Athive — Relatório Gerencial", _header_style(styles)),
                Paragraph(f"Consolidado todas as unidades · {datetime.date.today().strftime('%d/%m/%Y')}",
                           _sub_style(styles)),
                Spacer(1,0.5*cm),
            ]
            for un in ["Todas","Unidade 1","Unidade 2"]:
                kpis = kpis_dashboard(un if un != "Todas" else None)
                story.append(Paragraph(
                    f"{'Consolidado' if un == 'Todas' else un}",
                    ParagraphStyle("sec", parent=styles["Heading2"],
                                    textColor=NAVY_COLOR)))
                kpi_data = [
                    ["Alunos ativos", str(kpis.get("alunos_ativos",0)),
                     "Inadimplentes", str(kpis.get("inadimplentes",0))],
                    ["Receitas do mês", brl(kpis.get("receitas_mes",0)),
                     "Despesas do mês", brl(kpis.get("despesas_mes",0))],
                    ["A receber",        brl(kpis.get("a_receber",0)),
                     "A pagar",          brl(kpis.get("a_pagar",0))],
                    ["Saldo do mês",     brl(kpis.get("saldo_mes",0)),
                     "Em manutenção",    str(kpis.get("em_manutencao",0))],
                ]
                tbl = Table(kpi_data, colWidths=[4*cm,4*cm,4*cm,4*cm])
                tbl.setStyle(TableStyle([
                    ("FONTSIZE",  (0,0),(-1,-1), 9),
                    ("TEXTCOLOR", (0,0),(0,-1),  colors.HexColor(COR_MUTED)),
                    ("TEXTCOLOR", (2,0),(2,-1),  colors.HexColor(COR_MUTED)),
                    ("FONTNAME",  (1,0),(1,-1),  "Helvetica-Bold"),
                    ("FONTNAME",  (3,0),(3,-1),  "Helvetica-Bold"),
                    ("GRID",      (0,0),(-1,-1), 0.3, BORDER_COLOR),
                    ("ROWBACKGROUNDS",(0,0),(-1,-1),[ALT_COLOR,WHITE]),
                    ("TOPPADDING",(0,0),(-1,-1), 5),
                    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
                ]))
                story += [tbl, Spacer(1,0.4*cm)]

            story += [HRFlowable(width="100%",color=BORDER_COLOR), _rodape(styles)]
            doc.build(story)
            self.after(0, lambda: messagebox.showinfo("PDF gerado", f"Salvo em:\n{path}"))
        threading.Thread(target=_gerar, daemon=True).start()

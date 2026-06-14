# ATHIVE SISTEMA v1.3
### Desenvolvido por Tech Oliveira · tech-oliveira.com.br

---

## ARQUITETURA

```
SQLite local (fonte da verdade — offline-first)
        ↕  sync automático a cada 30 minutos
Supabase PostgreSQL (backup em nuvem — gratuito)
```

O sistema funciona **100% offline**. A internet só é usada para sincronizar os dados com o backup na nuvem. Se a internet cair, ninguém percebe.

---

## PRIMEIRO USO — SIGA ESTA ORDEM

### PASSO 1 — Criar as tabelas no Supabase (uma única vez)

1. Acesse https://supabase.com e entre no seu projeto
2. Vá em **SQL Editor → New Query**
3. Abra o arquivo `database/schema_supabase.sql`
4. Cole e clique em **Run**

### PASSO 2 — Instalar Python (nas máquinas de desenvolvimento)

Baixe Python 3.11+ em https://www.python.org/downloads/
Durante a instalação, marque **"Add Python to PATH"**

### PASSO 3 — Instalar dependências

```bash
pip install -r requirements.txt
```

### PASSO 4 — Executar o sistema

```bash
python main.py
```

### PASSO 5 — Primeiro login

| Campo  | Valor                  |
|--------|------------------------|
| E-mail | admin@athive.com.br    |
| Senha  | athive2024             |

⚠️ **Troque a senha imediatamente após o primeiro acesso!**
(Menu lateral → Trocar senha)

---

## GERAR O .EXE (Windows)

### Opção A — Script automático (recomendado)
```
Duplo clique em: build_exe.bat
```

### Opção B — Manual
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Athive Sistema" --add-data "database/schema.sql;database" main.py
```

O `.exe` gerado estará em `dist/Athive Sistema.exe`

**Distribuição:** copie apenas o `.exe` para cada máquina. Não precisa instalar Python.

---

## MÓDULOS DO SISTEMA

| Módulo         | Descrição                                           |
|----------------|-----------------------------------------------------|
| 📊 Dashboard   | KPIs em tempo real + gráfico evolução financeira    |
| 👥 Alunos      | Cadastro completo + alertas de vencimento           |
| 📅 Frequência  | Registro de entrada/saída dos alunos                |
| 💰 Financeiro  | Contas a pagar e receber + marcar pago              |
| 🔧 Manutenção  | Equipamentos + histórico + MTBF                     |
| 📉 Depreciação | Linha reta + saldo decrescente + gráfico + PDF      |
| 🛒 Compras     | Pedidos de suprimentos + controle de status         |
| 📄 Relatórios  | 6 relatórios em PDF (alunos, financeiro, gerencial…)|
| 👤 Usuários    | Gerenciamento de acessos (somente Admin)            |

---

## NÍVEIS DE ACESSO

| Perfil        | Acesso                                                      |
|---------------|-------------------------------------------------------------|
| Admin         | Tudo, incluindo usuários e sync manual                      |
| Financeiro    | Dashboard + Alunos (ver/editar) + Financeiro + Relatórios   |
| Operador      | Alunos + Frequência + Manutenção + Compras                  |
| Visualizador  | Dashboard (KPIs) + Alunos (ver) + Manutenção (ver)          |

---

## DEPRECIAÇÃO DE EQUIPAMENTOS

Dois métodos disponíveis por equipamento:

**Linha reta**
```
Depreciação anual = (Valor aquisição − Valor residual) / Vida útil
```

**Saldo decrescente**
```
Valor atual = Valor aquisição × (1 − taxa)^anos_uso
```

Configure em: Manutenção → Equipamentos → ⚙ Configurar Depreciação

---

## SINCRONIZAÇÃO COM SUPABASE

- Sync automático a cada **30 minutos** (quando houver internet)
- Status visível no rodapé da sidebar (☁ online / 📴 offline)
- Sync manual disponível para o perfil Admin
- Itens pendentes são enfileirados e enviados quando a internet voltar
- Máximo de 5 tentativas por item antes de reportar erro

---

## ESTRUTURA DO PROJETO

```
athive_sistema/
├── main.py                        ← Entrada da aplicação
├── config.py                      ← Configurações e permissões
├── requirements.txt               ← Dependências Python
├── build_exe.bat                  ← Script de build Windows
├── athive_local.db                ← Banco SQLite (criado automaticamente)
├── database/
│   ├── local_db.py                ← Todas as operações SQLite
│   ├── sync_engine.py             ← Motor de sync com Supabase
│   ├── schema.sql                 ← Schema SQLite local
│   └── schema_supabase.sql        ← Schema para o Supabase
└── modules/
    ├── ui_base.py                 ← Componentes de UI reutilizáveis
    ├── dashboard.py               ← Dashboard + gráficos
    ├── alunos.py                  ← Módulo alunos
    ├── frequencia.py              ← Módulo frequência
    ├── financeiro.py              ← Módulo financeiro
    ├── manutencao.py              ← Módulo manutenção
    ├── depreciacao.py             ← Módulo depreciação
    ├── compras.py                 ← Módulo compras
    ├── relatorios.py              ← Gerador de PDFs
    └── usuarios.py                ← Módulo usuários
```

---

## ROADMAP

| Versão | Funcionalidade                              |
|--------|---------------------------------------------|
| V1.4   | App mobile (PWA) para sócios                |
| V1.5   | Notificações WhatsApp (vencimentos)         |
| V2.0   | Migração para React + FastAPI (multi-filial)|

---

## SUPORTE

**Tech Oliveira**
Site: tech-oliveira.com.br
Sistema: Athive Centro de Saúde e Movimento · Rio Claro (SP)

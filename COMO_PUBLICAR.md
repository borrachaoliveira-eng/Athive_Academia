# Como publicar no GitHub e baixar o .exe
### Athive Sistema v1.3 · Desenvolvido por Tech Oliveira

---

## PASSO 1 — Criar conta no GitHub (se não tiver)

1. Acesse https://github.com
2. Clique em **Sign up**
3. Crie sua conta gratuita

---

## PASSO 2 — Criar o repositório

1. Clique no **+** no canto superior direito
2. Clique em **New repository**
3. Preencha:
   - **Repository name:** `athive-sistema`
   - **Visibility:** ✅ Private (para manter o código privado)
4. Clique em **Create repository**

---

## PASSO 3 — Subir os arquivos

### Opção A — Pela interface do GitHub (mais fácil, sem instalar nada)

1. Na página do repositório recém criado, clique em **uploading an existing file**
2. Arraste **todos os arquivos e pastas** do zip que você baixou
3. Clique em **Commit changes**

> ⚠️ Atenção: o GitHub não aceita arrastar pastas pela interface web.
> Use a **Opção B** abaixo (GitHub Desktop) para subir a estrutura de pastas correta.

### Opção B — GitHub Desktop (recomendado, mais fácil com pastas)

1. Baixe e instale o **GitHub Desktop**:
   👉 https://desktop.github.com

2. Faça login com sua conta GitHub

3. Clique em **File → Clone Repository**
   - Selecione `athive-sistema`
   - Escolha uma pasta no seu computador (ex: `C:\Projetos\athive-sistema`)

4. Descompacte o zip do sistema nessa pasta

5. No GitHub Desktop vai aparecer todos os arquivos como "Changed"

6. Escreva uma mensagem no campo **Summary** (ex: "versão inicial")

7. Clique em **Commit to main**

8. Clique em **Push origin**

---

## PASSO 4 — Acompanhar a compilação

1. Acesse seu repositório no GitHub
2. Clique na aba **Actions** (menu superior)
3. Você verá o build rodando com o nome **"Build Athive Sistema .exe"**
4. Aguarde de **3 a 8 minutos** até aparecer ✅ verde

---

## PASSO 5 — Baixar o .exe

1. Clique no build concluído (✅)
2. Role a página até a seção **Artifacts**
3. Clique em **Athive-Sistema-Windows**
4. Um arquivo `.zip` será baixado contendo o `Athive Sistema.exe`
5. Extraia o `.exe` e coloque onde quiser no computador

---

## PASSO 6 — Usar o sistema

1. Dê **duplo clique** em `Athive Sistema.exe`
2. No primeiro acesso:
   - **E-mail:** admin@athive.com.br
   - **Senha:** athive2024
3. Vá em **Trocar senha** no menu lateral imediatamente

---

## Sempre que atualizar o sistema

Basta subir os novos arquivos no GitHub (via GitHub Desktop)
e o Actions vai compilar um novo `.exe` automaticamente.

---

## Instalar nas outras máquinas da academia

Copie apenas o arquivo `Athive Sistema.exe` para cada computador.
Não precisa instalar nada. O banco de dados fica em:

```
C:\Users\[seu usuário]\athive_local.db
```

Cada máquina tem seu próprio banco local e sincroniza com o
Supabase a cada 30 minutos automaticamente.

---

## Suporte

**Tech Oliveira · tech-oliveira.com.br**

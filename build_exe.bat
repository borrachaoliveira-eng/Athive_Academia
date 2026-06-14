@echo off
:: ══════════════════════════════════════════════════════════════
:: ATHIVE SISTEMA v1.3 — Script de Build para Windows
:: Desenvolvido por Tech Oliveira · tech-oliveira.com.br
:: Execute este arquivo na pasta do projeto
:: ══════════════════════════════════════════════════════════════

echo.
echo  ██████████████████████████████████████████
echo     ATHIVE SISTEMA v1.3 — Build .EXE
echo     Tech Oliveira · tech-oliveira.com.br
echo  ██████████████████████████████████████████
echo.

echo [1/3] Instalando dependencias...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo     OK.

echo [2/3] Gerando executavel...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "Athive Sistema" ^
    --add-data "database/schema.sql;database" ^
    --hidden-import "supabase" ^
    --hidden-import "matplotlib" ^
    --hidden-import "reportlab" ^
    --clean ^
    main.py

if errorlevel 1 (
    echo ERRO: Falha ao gerar o executavel.
    pause
    exit /b 1
)

echo [3/3] Concluido!
echo.
echo  O arquivo esta em:  dist\Athive Sistema.exe
echo  Copie APENAS este arquivo para outras maquinas.
echo  Ele nao precisa de Python instalado para rodar.
echo.
echo  LOGIN INICIAL:
echo    E-mail: admin@athive.com.br
echo    Senha:  athive2024
echo.
echo  IMPORTANTE: Troque a senha no primeiro acesso!
echo.
pause

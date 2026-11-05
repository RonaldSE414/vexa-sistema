@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    py -m venv .venv
)
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Criado .env no modo demonstracao. Edite para ativar os bancos reais.
)
echo Instalando dependencias... 
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar dependencias. Verifique o Python e a internet.
    pause
    exit /b 1
)
echo.
echo Abra http://127.0.0.1:5000 no navegador.
".venv\Scripts\python.exe" app.py
pause

@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set CEREBRO_USE_GPU=0
set CEREBRO_LANGUAGE_TUTOR=1
echo Modo CPU + tutor de lenguaje activo
python app.py
pause

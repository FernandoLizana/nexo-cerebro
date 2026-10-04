@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set CEREBRO_USE_GPU=1
set CEREBRO_GPU_MAX_STEPS=120
set CEREBRO_GPU_MIN_STEPS=6
set CEREBRO_MIN_NEURONS_GPU=400
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0
echo CUDA activado — NVIDIA dedicada (RTX)
echo   max pasos GPU/episodio: %CEREBRO_GPU_MAX_STEPS%
echo   min pasos para activar GPU: %CEREBRO_GPU_MIN_STEPS%
python app.py
pause

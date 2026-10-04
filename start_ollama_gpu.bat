@echo off
REM Reinicia Ollama forzando NVIDIA CUDA (no Intel iGPU / Vulkan).
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0
set OLLAMA_VULKAN=0
echo Ollama con CUDA NVIDIA (cierra el icono de bandeja antes si ya corre)
ollama serve

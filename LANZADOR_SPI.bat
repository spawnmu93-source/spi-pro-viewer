@echo off
title SPI - Panel Maestro de Control
color 0B
cd /d "%~dp0"
echo Iniciando Panel de Control SPI...
python panel_control.py
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo iniciar el panel de control.
    pause
)

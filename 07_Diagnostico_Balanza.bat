@echo off
title SPI - Herramienta de Diagnostico Serial (Balanza)
color 09
cd /d "%~dp0"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - DIAGNOSTICO
echo               TEST Y CONFIGURACION DE BALANZA SERIAL
echo ======================================================================
echo.
echo Iniciando interfaz de diagnostico...
python test_serial_gui.py
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo ejecutar el modulo de diagnostico.
    pause
)

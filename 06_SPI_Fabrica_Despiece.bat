@echo off
title SPI - Terminal Fabrica (Chacinados y Batea)
color 0D
cd /d "%~dp0SPI NEW\Frigorifico-Fabrica\python_edge"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - FABRICA
echo           TERMINAL CHACINADOS (PESAJE BATEA + SEMAFORO TERMICO)
echo ======================================================================
echo.
echo Iniciando terminal industrial...
python terminal_fabrica.py
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores o no se pudo iniciar.
    pause
)

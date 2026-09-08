@echo off
title SPI - Terminal Frigorifico (Pesaje Faena Gancho)
color 0C
cd /d "%~dp0SPI NEW\Frigorifico-Fabrica\python_edge"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - FRIGORIFICO
echo           TERMINAL DE FAENA (PESAJE GANCHO AEREO + ZPL)
echo ======================================================================
echo.
echo Iniciando terminal industrial...
python terminal_frigorifico.py
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores o no se pudo iniciar.
    pause
)

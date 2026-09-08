@echo off
title SPI - Despiece Vertical
color 0B
cd /d "%~dp0"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - DESPIECE
echo                          MODO VERTICAL
echo ======================================================================
echo.
echo Iniciando aplicacion...
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores o no se pudo iniciar.
    pause
)

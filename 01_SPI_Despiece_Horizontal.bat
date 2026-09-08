@echo off
title SPI - Despiece Horizontal (Balanza)
color 0B
cd /d "%~dp0"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - DESPIECE
echo                  MODO HORIZONTAL / PESAJE DE COMBOS
echo ======================================================================
echo.
echo Iniciando aplicacion...
python main_horizontal.py
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores o no se pudo iniciar.
    pause
)

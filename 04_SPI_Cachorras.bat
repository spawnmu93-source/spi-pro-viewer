@echo off
title SPI - Gestion de Cachorras (Granja)
color 0E
cd /d "%~dp0SPI - Cachorras"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - CACHORRAS
echo                MODULO DE GRANJA Y CRIA DE CERDOS
echo ======================================================================
echo.
echo Iniciando aplicacion...
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion se cerro con errores o no se pudo iniciar.
    pause
)

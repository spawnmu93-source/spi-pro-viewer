@echo off
title SPI - Suite de Pruebas Unitarias y Regresion
color 0F
cd /d "%~dp0"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - SUITE DE TESTS
echo        VALIDACION DE COMBOS, INTEGRIDAD Y PROTOCOLOS DE COMUNICACION
echo ======================================================================
echo.
python -m unittest discover tests -v
echo.
echo ======================================================================
echo Pruebas finalizadas.
echo ======================================================================
pause

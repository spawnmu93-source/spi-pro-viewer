@echo off
title Reenvío de CSVs a Google Sheets - SPI
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================================
echo   SISTEMA DE PRODUCCION INTEGRAL (SPI)
echo   Reenvio y Recuperacion de CSVs a Google Sheets
echo =========================================================
echo.

python recuperar_y_enviar_csv.py
if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo iniciar el script. Verifique que Python este instalado.
    pause
)

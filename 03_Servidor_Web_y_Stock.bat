@echo off
title SPI - Servidor Central y Control de Stock
color 0A
cd /d "%~dp0"
echo ======================================================================
echo           SISTEMA DE PRODUCCION INTEGRAL (SPI) - CENTRAL
echo                SERVIDOR API REST + PANEL WEB DE STOCK
echo ======================================================================
echo.
echo Abriendo aplicacion Web en el navegador (http://localhost:8000)...
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"
echo Iniciando servidor FastAPI...
echo Presione Ctrl+C para detener el servidor.
python server.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ocurrio un error al ejecutar el servidor.
    pause
)

@echo off
REM Script de inicio rápido para MiChaska POS
REM Windows

echo ========================================
echo MiChaska POS - Inicio Rapido
echo ========================================
echo.

REM Verificar si existe venv
if not exist "venv\" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
) else (
    echo [1/4] Entorno virtual ya existe
)

echo [2/4] Activando entorno virtual...
call venv\Scripts\activate

echo [3/4] Instalando dependencias...
pip install -r requirements.txt --quiet

echo [4/4] Iniciando servidor Flask...
echo.
echo ========================================
echo Servidor corriendo en http://localhost:5000
echo Presiona Ctrl+C para detener
echo ========================================
echo.

python server.py

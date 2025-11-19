#!/bin/bash
# Script de inicio rápido para MiChaska POS
# Linux/Mac

echo "========================================"
echo "MiChaska POS - Inicio Rápido"
echo "========================================"
echo ""

# Verificar si existe venv
if [ ! -d "venv" ]; then
    echo "[1/4] Creando entorno virtual..."
    python3 -m venv venv
else
    echo "[1/4] Entorno virtual ya existe"
fi

echo "[2/4] Activando entorno virtual..."
source venv/bin/activate

echo "[3/4] Instalando dependencias..."
pip install -r requirements.txt --quiet

echo "[4/4] Iniciando servidor Flask..."
echo ""
echo "========================================"
echo "Servidor corriendo en http://localhost:5000"
echo "Presiona Ctrl+C para detener"
echo "========================================"
echo ""

python server.py

#!/bin/bash
# Script de inicio para MiChaska - Sistema de Facturación
# Compatible con Linux y funciona también en Windows con Git Bash o WSL

echo "🛒 Iniciando MiChaska - Sistema de Facturación"
echo "============================================="

# Verificar si existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "⚠️ Entorno virtual no encontrado. Creando..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
else
    echo "✅ Entorno virtual encontrado"
    source .venv/bin/activate
fi

# Verificar que las dependencias estén instaladas
echo "🔍 Verificando dependencias..."
python test_system.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 ¡Iniciando MiChaska!"
    echo "📱 El sistema se abrirá en tu navegador web"
    echo "🌐 URL: http://localhost:8501"
    echo ""
    echo "⭐ Presiona Ctrl+C para detener el sistema"
    echo "============================================="
    
    # Iniciar Streamlit
    streamlit run app.py --server.port 8501 --server.address localhost
else
    echo "❌ Error en las pruebas del sistema. No se puede iniciar."
    exit 1
fi

#!/bin/bash

# Script de inicio para Mi Chas-K
# Versión 4.0.0 - Sistema Híbrido Robusto

echo "🛒 Iniciando Mi Chas-K - Sistema de Punto de Venta Híbrido"
echo "============================================================"
echo ""
echo "📋 Verificando sistema..."

# Verificar que estamos en el directorio correcto
if [ ! -f "app_hybrid_v4.py" ]; then
    echo "❌ Error: No se encontró app_hybrid_v4.py"
    echo "   Asegúrate de estar en el directorio correcto"
    exit 1
fi

echo "✅ Archivo principal encontrado"

# Verificar dependencias
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: No se encontró requirements.txt"
    exit 1
fi

echo "✅ Dependencias verificadas"

# Crear directorio de datos si no existe
if [ ! -d "data" ]; then
    echo "📁 Creando directorio de datos..."
    mkdir -p data
fi

echo "✅ Directorio de datos listo"

# Crear directorio de tickets si no existe
if [ ! -d "tickets" ]; then
    echo "🎫 Creando directorio de tickets..."
    mkdir -p tickets
fi

echo "✅ Directorio de tickets listo"

echo ""
echo "🚀 Iniciando aplicación Streamlit..."
echo "📝 Usa Ctrl+C para detener la aplicación"
echo "🌐 La aplicación se abrirá en: http://localhost:8501"
echo ""

# Iniciar Streamlit
streamlit run app_hybrid_v4.py

#!/bin/bash
# Script para verificar el estado del sistema

echo "=== Verificación del Sistema Mi Chas-K ==="

# Verificar archivos principales
echo "1. Verificando archivos principales..."
files=("app_hybrid.py" "database/connection_adapter.py" "pages/punto_venta_simple.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (faltante)"
    fi
done

# Verificar base de datos
echo "2. Verificando base de datos..."
if [ -f "data/local_database.db" ]; then
    echo "   ✅ Base de datos local existe"
    # Obtener tamaño del archivo
    size=$(wc -c < "data/local_database.db")
    echo "   📊 Tamaño: $size bytes"
else
    echo "   ❌ Base de datos local no existe"
fi

# Verificar dependencias de Python
echo "3. Verificando dependencias de Python..."
python3 -c "
import sys
modules = ['streamlit', 'sqlite3', 'psycopg2', 'dotenv']
for module in modules:
    try:
        __import__(module)
        print(f'   ✅ {module}')
    except ImportError:
        print(f'   ❌ {module}')
" 2>/dev/null

echo "4. Verificación completada"

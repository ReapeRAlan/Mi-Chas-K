#!/bin/bash

# Script para desarrollo local de Mi Chas-K
# Facilita el testing y desarrollo antes de subir a producción

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🛠️  Mi Chas-K - Herramientas de Desarrollo" $BLUE
print_message "=========================================" $BLUE

# Función para mostrar menú
show_menu() {
    echo
    print_message "Selecciona una opción:" $YELLOW
    echo "1. 🚀 Ejecutar aplicación en modo desarrollo"
    echo "2. 🧪 Ejecutar tests del sistema"
    echo "3. 📦 Instalar/actualizar dependencias"
    echo "4. 🔄 Reiniciar base de datos"
    echo "5. 📊 Verificar estado del sistema"
    echo "6. 🌐 Sincronizar con GitHub"
    echo "7. 📝 Ver logs de la aplicación"
    echo "8. ❌ Salir"
    echo
    echo -n "Opción: "
}

# Función para ejecutar la aplicación
run_app() {
    print_message "\n🚀 Iniciando Mi Chas-K en modo desarrollo..." $GREEN
    
    # Verificar si existe archivo .env
    if [ ! -f ".env" ]; then
        print_message "⚠️  Archivo .env no encontrado. Creando uno básico..." $YELLOW
        cat > .env << EOF
# Configuración para desarrollo local
DATABASE_URL=
DB_HOST=localhost
DB_NAME=chaskabd
DB_USER=admin
DB_PASSWORD=
DB_PORT=5432

# Para desarrollo, puedes usar SQLite comentando DATABASE_URL
# y descomentando la siguiente línea:
# USE_SQLITE=true
EOF
        print_message "✅ Archivo .env creado. Edítalo según tu configuración." $GREEN
    fi
    
    # Verificar dependencias
    if [ ! -d "venv" ] && [ ! -f "requirements.txt" ]; then
        print_message "❌ No se encontraron dependencias instaladas" $RED
        return 1
    fi
    
    # Activar entorno virtual si existe
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_message "✅ Entorno virtual activado" $GREEN
    fi
    
    # Ejecutar aplicación
    print_message "🌐 Abriendo http://localhost:8501" $BLUE
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0
}

# Función para ejecutar tests
run_tests() {
    print_message "\n🧪 Ejecutando tests del sistema..." $GREEN
    
    test_files=("test_db_connection.py" "test_system.py" "test_categorias.py" "test_tickets.py" "test_ventas.py")
    
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_message "📋 Ejecutando $test_file..." $BLUE
            python "$test_file" || print_message "❌ Error en $test_file" $RED
        fi
    done
    
    print_message "✅ Tests completados" $GREEN
}

# Función para instalar dependencias
install_deps() {
    print_message "\n📦 Instalando/actualizando dependencias..." $GREEN
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        print_message "🔨 Creando entorno virtual..." $BLUE
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_message "✅ Dependencias instaladas" $GREEN
    else
        print_message "❌ Archivo requirements.txt no encontrado" $RED
    fi
}

# Función para reiniciar base de datos
reset_database() {
    print_message "\n🔄 Reiniciando base de datos..." $YELLOW
    print_message "⚠️  ADVERTENCIA: Esto eliminará todos los datos existentes" $RED
    echo -n "¿Continuar? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ -f "reset_database.py" ]; then
            python reset_database.py
            print_message "✅ Base de datos reiniciada" $GREEN
        else
            print_message "❌ Script reset_database.py no encontrado" $RED
        fi
    else
        print_message "❌ Operación cancelada" $YELLOW
    fi
}

# Función para verificar estado del sistema
check_system() {
    print_message "\n📊 Verificando estado del sistema..." $BLUE
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version)
        print_message "✅ Python: $python_version" $GREEN
    else
        print_message "❌ Python no encontrado" $RED
    fi
    
    # Verificar entorno virtual
    if [ -d "venv" ]; then
        print_message "✅ Entorno virtual: Disponible" $GREEN
    else
        print_message "⚠️  Entorno virtual: No encontrado" $YELLOW
    fi
    
    # Verificar archivos principales
    main_files=("app.py" "requirements.txt" "database/" "pages/" "utils/")
    for file in "${main_files[@]}"; do
        if [ -e "$file" ]; then
            print_message "✅ $file: Presente" $GREEN
        else
            print_message "❌ $file: Faltante" $RED
        fi
    done
    
    # Verificar conectividad (si hay internet)
    if ping -c 1 google.com &> /dev/null; then
        print_message "✅ Conectividad: OK" $GREEN
    else
        print_message "⚠️  Conectividad: Sin internet" $YELLOW
    fi
}

# Función para ver logs
view_logs() {
    print_message "\n📝 Logs de la aplicación..." $BLUE
    
    if [ -f "app.log" ]; then
        tail -50 app.log
    else
        print_message "⚠️  No se encontraron logs" $YELLOW
    fi
}

# Bucle principal
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            run_app
            ;;
        2)
            run_tests
            ;;
        3)
            install_deps
            ;;
        4)
            reset_database
            ;;
        5)
            check_system
            ;;
        6)
            if [ -f "sync_github.sh" ]; then
                ./sync_github.sh
            else
                print_message "❌ Script sync_github.sh no encontrado" $RED
            fi
            ;;
        7)
            view_logs
            ;;
        8)
            print_message "\n👋 ¡Hasta luego!" $GREEN
            exit 0
            ;;
        *)
            print_message "\n❌ Opción inválida" $RED
            ;;
    esac
    
    print_message "\nPresiona Enter para continuar..." $BLUE
    read -r
done

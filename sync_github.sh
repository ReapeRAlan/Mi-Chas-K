#!/bin/bash

# Script de sincronización con GitHub para Mi Chas-K
# Este script permite hacer cambios locales y subirlos a GitHub de forma segura

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_message() {
    echo -e "${2}${1}${NC}"
}

# Verificar que estamos en un repositorio git
if [ ! -d ".git" ]; then
    print_message "❌ Error: Este directorio no es un repositorio Git" $RED
    exit 1
fi

print_message "🚀 Script de Sincronización Mi Chas-K" $BLUE
print_message "=====================================" $BLUE

# Mostrar estado actual
print_message "📊 Estado actual del repositorio:" $YELLOW
git status --short

# Verificar si hay cambios
if [ -z "$(git status --porcelain)" ]; then
    print_message "✅ No hay cambios para sincronizar" $GREEN
    exit 0
fi

# Mostrar archivos modificados
print_message "\n📝 Archivos modificados:" $YELLOW
git diff --name-only

# Pedir confirmación al usuario
print_message "\n¿Deseas continuar con la sincronización? (y/N): " $BLUE
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    print_message "❌ Sincronización cancelada por el usuario" $RED
    exit 0
fi

# Pedir mensaje de commit
print_message "\n📝 Ingresa un mensaje para el commit:" $BLUE
echo -n "> "
read -r commit_message

if [ -z "$commit_message" ]; then
    commit_message="Actualizaciones automáticas $(date '+%Y-%m-%d %H:%M:%S')"
    print_message "⚠️  Usando mensaje automático: $commit_message" $YELLOW
fi

# Verificar conexión a internet
print_message "\n🌐 Verificando conexión a internet..." $BLUE
if ! ping -c 1 github.com &> /dev/null; then
    print_message "❌ Error: No hay conexión a internet" $RED
    exit 1
fi

# Verificar configuración de Git
if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
    print_message "⚠️  Configurando usuario de Git..." $YELLOW
    
    echo -n "Ingresa tu nombre: "
    read -r git_name
    echo -n "Ingresa tu email: "
    read -r git_email
    
    git config user.name "$git_name"
    git config user.email "$git_email"
    
    print_message "✅ Usuario de Git configurado" $GREEN
fi

# Realizar backup de archivos importantes antes de sincronizar
print_message "\n💾 Creando backup de seguridad..." $BLUE
backup_dir="backup_$(date '+%Y%m%d_%H%M%S')"
mkdir -p "$backup_dir"

# Backup de archivos críticos
critical_files=("database/" "pages/" "utils/" "app.py" "requirements.txt")
for file in "${critical_files[@]}"; do
    if [ -e "$file" ]; then
        cp -r "$file" "$backup_dir/"
    fi
done

print_message "✅ Backup creado en: $backup_dir" $GREEN

# Agregar archivos al staging
print_message "\n📦 Agregando archivos al staging..." $BLUE
git add .

# Verificar que no hay archivos sensibles
sensitive_patterns=("*.env" "*.key" "*.pem" "config.json" "secrets.*")
for pattern in "${sensitive_patterns[@]}"; do
    if git diff --cached --name-only | grep -q "$pattern"; then
        print_message "⚠️  ADVERTENCIA: Archivo sensible detectado: $pattern" $YELLOW
        print_message "¿Continuar de todas formas? (y/N): " $BLUE
        read -r continue_response
        if [[ ! "$continue_response" =~ ^[Yy]$ ]]; then
            git reset
            print_message "❌ Sincronización cancelada por seguridad" $RED
            exit 1
        fi
    fi
done

# Crear commit
print_message "\n📝 Creando commit..." $BLUE
git commit -m "$commit_message"

# Verificar rama actual
current_branch=$(git branch --show-current)
print_message "📍 Rama actual: $current_branch" $BLUE

# Intentar hacer pull para evitar conflictos
print_message "\n⬇️  Sincronizando con repositorio remoto..." $BLUE
if git pull origin "$current_branch" --rebase; then
    print_message "✅ Sincronización exitosa" $GREEN
else
    print_message "⚠️  Conflictos detectados. Resolviendo automáticamente..." $YELLOW
    
    # Intentar resolución automática
    if git rebase --continue 2>/dev/null; then
        print_message "✅ Conflictos resueltos automáticamente" $GREEN
    else
        print_message "❌ No se pudieron resolver los conflictos automáticamente" $RED
        print_message "Por favor resuelve los conflictos manualmente y ejecuta:" $YELLOW
        print_message "  git rebase --continue" $YELLOW
        print_message "  ./sync_github.sh" $YELLOW
        exit 1
    fi
fi

# Subir cambios al repositorio remoto
print_message "\n⬆️  Subiendo cambios a GitHub..." $BLUE
if git push origin "$current_branch"; then
    print_message "✅ Cambios subidos exitosamente a GitHub" $GREEN
else
    print_message "❌ Error al subir cambios a GitHub" $RED
    print_message "Verifica tu conexión y permisos del repositorio" $YELLOW
    exit 1
fi

# Mostrar resumen final
print_message "\n🎉 SINCRONIZACIÓN COMPLETADA" $GREEN
print_message "==============================" $GREEN
print_message "📝 Commit: $commit_message" $BLUE
print_message "📍 Rama: $current_branch" $BLUE
print_message "🌐 Repositorio actualizado en GitHub" $BLUE
print_message "💾 Backup guardado en: $backup_dir" $BLUE

# Limpiar backups antiguos (mantener solo los últimos 5)
print_message "\n🧹 Limpiando backups antiguos..." $BLUE
ls -dt backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
print_message "✅ Limpieza completada" $GREEN

print_message "\n✨ ¡Sincronización finalizada con éxito!" $GREEN

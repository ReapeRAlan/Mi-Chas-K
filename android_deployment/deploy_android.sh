#!/bin/bash

# Script completo para deployment Android de MiChaska
# Ejecutar desde el directorio del proyecto

echo "🚀 === MICHASKA ANDROID DEPLOYMENT ==="
echo ""

# Verificar prerequisites
echo "🔍 Verificando prerequisites..."

# Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado"
    echo "   Instalar desde: https://nodejs.org/"
    exit 1
else
    echo "✅ Node.js: $(node --version)"
fi

# NPM
if ! command -v npm &> /dev/null; then
    echo "❌ NPM no está instalado"
    exit 1
else
    echo "✅ NPM: $(npm --version)"
fi

# Java (para Android)
if ! command -v java &> /dev/null; then
    echo "⚠️  Java no encontrado - necesario para Android Studio"
    echo "   Instalar OpenJDK 11+"
fi

echo ""
echo "📋 Opciones de deployment:"
echo "1) Configuración inicial (primera vez)"
echo "2) Ejecutar en desarrollo (browser)"
echo "3) Construir para Android"
echo "4) Generar APK"
echo "5) Ver guías de ayuda"
echo "0) Salir"
echo ""

read -p "Selecciona una opción (1-5): " option

case $option in
    1)
        echo "🔧 === CONFIGURACIÓN INICIAL ==="
        
        # Ejecutar script de configuración
        if [ ! -f "./android_deployment/setup_android.sh" ]; then
            echo "❌ Script de configuración no encontrado"
            exit 1
        fi
        
        cd android_deployment
        ./setup_android.sh
        
        echo ""
        echo "✅ Configuración completada!"
        echo "📝 Próximos pasos:"
        echo "   1. Personalizar iconos en michaska-android/public/"
        echo "   2. Ajustar URL del servidor en public/index.html"
        echo "   3. Ejecutar opción 2 para pruebas"
        ;;
        
    2)
        echo "🌐 === MODO DESARROLLO ==="
        
        if [ ! -d "./android_deployment/michaska-android" ]; then
            echo "❌ Proyecto no configurado. Ejecuta opción 1 primero."
            exit 1
        fi
        
        cd android_deployment/michaska-android
        
        # Verificar si Streamlit está corriendo
        echo "🔍 Verificando servidor Streamlit..."
        if ! curl -s http://localhost:8501 &> /dev/null; then
            echo "⚠️  Servidor Streamlit no detectado en puerto 8501"
            echo "   Ejecutar en otra terminal:"
            echo "   cd $(pwd)/../.."
            echo "   streamlit run app_tablet.py --server.port 8501"
            echo ""
            read -p "¿Continuar con servidor web local? (y/n): " continue_local
            if [ "$continue_local" != "y" ]; then
                exit 1
            fi
        else
            echo "✅ Servidor Streamlit activo"
        fi
        
        # Servidor de desarrollo
        echo "🌍 Iniciando servidor de desarrollo..."
        echo "   Abrirá en: http://localhost:8080"
        echo "   Presiona Ctrl+C para detener"
        python3 -m http.server 8080 --directory public
        ;;
        
    3)
        echo "📱 === CONSTRUIR PARA ANDROID ==="
        
        if [ ! -d "./android_deployment/michaska-android" ]; then
            echo "❌ Proyecto no configurado. Ejecuta opción 1 primero."
            exit 1
        fi
        
        cd android_deployment/michaska-android
        
        # Sincronizar con Capacitor
        echo "🔄 Sincronizando proyecto..."
        npx cap sync
        
        # Abrir Android Studio
        echo "📂 Abriendo Android Studio..."
        npx cap open android
        
        echo ""
        echo "📝 En Android Studio:"
        echo "   1. Esperar que termine la sincronización"
        echo "   2. Conectar dispositivo Android o iniciar emulador"
        echo "   3. Presionar 'Run' (triángulo verde)"
        ;;
        
    4)
        echo "📦 === GENERAR APK ==="
        
        if [ ! -d "./android_deployment/michaska-android" ]; then
            echo "❌ Proyecto no configurado. Ejecuta opción 1 primero."
            exit 1
        fi
        
        echo "📝 Para generar APK:"
        echo ""
        echo "1️⃣  Opción automática (desarrollo):"
        echo "   cd android_deployment/michaska-android"
        echo "   npx cap sync"
        echo "   cd android/app"
        echo "   ./gradlew assembleDebug"
        echo ""
        echo "2️⃣  Opción manual (recomendada):"
        echo "   - Abrir Android Studio (opción 3)"
        echo "   - Build > Build Bundle(s)/APK(s) > Build APK(s)"
        echo "   - Para APK firmado: Build > Generate Signed Bundle/APK"
        echo ""
        echo "📁 APK generado en:"
        echo "   android/app/build/outputs/apk/debug/app-debug.apk"
        ;;
        
    5)
        echo "📚 === GUÍAS DE AYUDA ==="
        echo ""
        echo "📖 Guías disponibles:"
        echo "   • android_deployment/ANDROID_GUIDE.md - Guía completa"
        echo "   • android_deployment/IMPRESORAS_COMPATIBLES.md - Lista de impresoras"
        echo "   • android_deployment/MOBILE_OPTIONS.md - Opciones de desarrollo"
        echo "   • android_deployment/PWA_GUIDE.md - Detalles técnicos PWA"
        echo ""
        
        # Mostrar resumen de ANDROID_GUIDE.md
        if [ -f "./android_deployment/ANDROID_GUIDE.md" ]; then
            echo "📋 Resumen rápido:"
            head -20 ./android_deployment/ANDROID_GUIDE.md
            echo "..."
            echo ""
            echo "💡 Ver archivo completo para más detalles"
        fi
        ;;
        
    0)
        echo "👋 ¡Hasta luego!"
        exit 0
        ;;
        
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "✨ === PROCESO COMPLETADO ==="
echo ""
echo "🔗 Enlaces útiles:"
echo "   • Capacitor Docs: https://capacitorjs.com/docs"
echo "   • Android Studio: https://developer.android.com/studio"
echo "   • ESC/POS Commands: https://reference.epson-biz.com/modules/ref_escpos/index.php"
echo ""
echo "❓ ¿Necesitas ayuda? Revisa las guías en android_deployment/"

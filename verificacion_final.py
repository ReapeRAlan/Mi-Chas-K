#!/usr/bin/env python3
"""
Verificación Final del Sistema Mi Chas-K
Ejecuta una serie de tests para confirmar que todo funciona correctamente
"""

import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Verifica que un archivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NO ENCONTRADO")
        return False

def check_import(module_path, module_name):
    """Verifica que un módulo se puede importar"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ Módulo {module_name} importado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando {module_name}: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA MI CHAS-K")
    print("=" * 50)
    
    base_path = "/home/ghost/Escritorio/Mi-Chas-K"
    os.chdir(base_path)
    
    # Verificar archivos principales
    print("\n📁 Verificando archivos principales...")
    files_ok = True
    
    files_to_check = [
        ("app_hybrid_v4.py", "Aplicación principal híbrida"),
        ("requirements.txt", "Dependencias del proyecto"),
        ("database/connection_adapter.py", "Adaptador de base de datos"),
        ("pages/punto_venta_simple.py", "Página punto de venta"),
        ("pages/inventario_simple.py", "Página inventario"),
        ("pages/dashboard_simple.py", "Página dashboard"),
        ("pages/configuracion_simple.py", "Página configuración"),
        ("utils/pdf_generator.py", "Generador de PDF"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            files_ok = False
    
    # Verificar directorios
    print("\n📂 Verificando directorios...")
    directories = ["database", "pages", "utils", "data"]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ Directorio {directory} existe")
        else:
            print(f"❌ Directorio {directory} NO EXISTE")
            files_ok = False
    
    # Crear directorio data si no existe
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 Directorio 'data' creado")
    
    # Verificar imports principales
    print("\n🔧 Verificando importaciones...")
    
    # Agregar el directorio actual al path
    sys.path.insert(0, base_path)
    
    imports_ok = True
    try:
        from database.connection_adapter import DatabaseAdapter
        print("✅ DatabaseAdapter importado correctamente")
    except Exception as e:
        print(f"❌ Error importando DatabaseAdapter: {e}")
        imports_ok = False
    
    try:
        from pages.punto_venta_simple import show_punto_venta
        print("✅ Página punto de venta importada")
    except Exception as e:
        print(f"❌ Error importando punto de venta: {e}")
        imports_ok = False
    
    try:
        from pages.inventario_simple import show_inventario
        print("✅ Página inventario importada")
    except Exception as e:
        print(f"❌ Error importando inventario: {e}")
        imports_ok = False
    
    try:
        from pages.dashboard_simple import show_dashboard
        print("✅ Página dashboard importada")
    except Exception as e:
        print(f"❌ Error importando dashboard: {e}")
        imports_ok = False
    
    try:
        from pages.configuracion_simple import show_configuracion
        print("✅ Página configuración importada")
    except Exception as e:
        print(f"❌ Error importando configuración: {e}")
        imports_ok = False
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE LA VERIFICACIÓN")
    print("=" * 50)
    
    if files_ok and imports_ok:
        print("🎉 ¡VERIFICACIÓN EXITOSA!")
        print("✅ Todos los archivos y módulos están correctos")
        print("🚀 El sistema está listo para ejecutarse")
        print("\n💡 Para iniciar la aplicación, ejecuta:")
        print("   streamlit run app_hybrid_v4.py")
        return True
    else:
        print("❌ VERIFICACIÓN FALLIDA")
        if not files_ok:
            print("⚠️  Algunos archivos están faltando")
        if not imports_ok:
            print("⚠️  Hay errores de importación")
        print("🔧 Revisa los errores mostrados arriba")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

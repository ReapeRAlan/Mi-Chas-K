#!/usr/bin/env python3
"""
Script de prueba específico para producción
"""
import os
import sys
from dotenv import load_dotenv

# Simular entorno de producción
os.environ['DATABASE_URL'] = 'postgresql://admin:wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu@dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com/chaskabd'
os.environ['RENDER'] = 'true'

# Cargar variables de entorno
load_dotenv()

print("🔍 Simulación de Entorno de Producción")
print("=" * 50)

print("📋 Variables de entorno configuradas:")
print(f"DATABASE_URL: {'✅ Configurada' if os.getenv('DATABASE_URL') else '❌ No encontrada'}")
print(f"RENDER: {os.getenv('RENDER', 'No definida')}")

print("\n🔌 Probando importación de módulos...")
try:
    from database.connection import get_db_connection, init_database, is_database_initialized, test_connection, is_production_environment
    print("✅ Módulos importados correctamente")
except Exception as e:
    print(f"❌ Error importando módulos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n🏗️ Estado de inicialización inicial: {'✅ Inicializada' if is_database_initialized() else '❌ No inicializada'}")
print(f"🌍 Entorno de producción: {'✅ Sí' if is_production_environment() else '❌ No'}")

print("\n🔌 Probando conexión a base de datos de producción...")
try:
    if test_connection():
        print("✅ Conexión exitosa")
    else:
        print("❌ Conexión fallida")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error en conexión: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🚀 Probando inicialización...")
try:
    init_database()
    print("✅ Inicialización exitosa")
except Exception as e:
    print(f"❌ Error en inicialización: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n🏗️ Estado final: {'✅ Inicializada' if is_database_initialized() else '❌ No inicializada'}")

print("\n✅ Todas las pruebas de producción pasaron correctamente")

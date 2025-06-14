#!/usr/bin/env python3
"""
Script de prueba de conexión para diagnosticar problemas con la base de datos
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("🔍 Diagnóstico de Conexión Mi Chas-K")
print("=" * 50)

# Verificar variables de entorno
print("📋 Variables de entorno:")
print(f"DATABASE_URL: {'✅ Configurada' if os.getenv('DATABASE_URL') else '❌ No encontrada'}")
print(f"DB_HOST: {os.getenv('DB_HOST', 'No definida')}")
print(f"DB_NAME: {os.getenv('DB_NAME', 'No definida')}")
print(f"DB_USER: {os.getenv('DB_USER', 'No definida')}")
print(f"DB_PASSWORD: {'✅ Configurada' if os.getenv('DB_PASSWORD') else '❌ No encontrada'}")
print(f"DB_PORT: {os.getenv('DB_PORT', 'No definida')}")

print("\n🔌 Probando importación de módulos...")
try:
    from database.connection import get_db_connection, init_database, is_database_initialized, test_connection
    print("✅ Módulos importados correctamente")
except Exception as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

print(f"\n🏗️ Estado de inicialización: {'✅ Inicializada' if is_database_initialized() else '❌ No inicializada'}")

print("\n🔌 Probando conexión...")
try:
    if test_connection():
        print("✅ Conexión exitosa")
    else:
        print("❌ Conexión fallida")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error en conexión: {e}")
    sys.exit(1)

print("\n🚀 Probando inicialización...")
try:
    init_database()
    print("✅ Inicialización exitosa")
except Exception as e:
    print(f"❌ Error en inicialización: {e}")
    sys.exit(1)

print(f"\n🏗️ Estado final: {'✅ Inicializada' if is_database_initialized() else '❌ No inicializada'}")

print("\n✅ Todas las pruebas pasaron correctamente")

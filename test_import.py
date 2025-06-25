#!/usr/bin/env python3
"""
Test básico de importación del adaptador
"""
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.getcwd())

print("Intentando importar módulos...")

try:
    print("1. Importando sqlite3...")
    import sqlite3
    print("✅ sqlite3 OK")
    
    print("2. Importando psycopg2...")
    import psycopg2
    print("✅ psycopg2 OK")
    
    print("3. Importando dotenv...")
    from dotenv import load_dotenv
    print("✅ dotenv OK")
    
    print("4. Importando el adaptador...")
    from database.connection_adapter import DatabaseAdapter
    print("✅ DatabaseAdapter importado")
    
    print("5. Creando instancia del adaptador...")
    adapter = DatabaseAdapter()
    print("✅ Adaptador creado")
    
    print("6. Probando consulta simple...")
    result = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
    print(f"✅ Consulta exitosa: {result}")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(f"Detalle del error:")
    print(traceback.format_exc())

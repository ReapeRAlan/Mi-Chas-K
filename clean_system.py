#!/usr/bin/env python3
"""
Script para limpiar completamente el sistema y la cola de sincronización
"""
import os
import sqlite3
import json

def clean_system():
    """Limpiar sistema completamente"""
    print("=== LIMPIEZA COMPLETA DEL SISTEMA ===")
    
    # 1. Limpiar cola de sincronización
    db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    if os.path.exists(db_path):
        print("1. Limpiando cola de sincronización...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Eliminar toda la cola de sincronización
        cursor.execute("DELETE FROM sync_queue")
        conn.commit()
        
        count = cursor.execute("SELECT COUNT(*) FROM sync_queue").fetchone()[0]
        print(f"   Cola de sincronización limpiada: {count} elementos restantes")
        
        conn.close()
    
    # 2. Limpiar archivo de cola JSON si existe
    sync_queue_path = os.path.join(os.getcwd(), 'data', 'sync_queue.json')
    if os.path.exists(sync_queue_path):
        print("2. Limpiando archivo de cola JSON...")
        with open(sync_queue_path, 'w') as f:
            json.dump([], f)
        print("   Archivo de cola JSON limpiado")
    
    # 3. Verificar integridad de la base de datos
    print("3. Verificando integridad de la base de datos...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar que las tablas existen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    required_tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
    
    for table in required_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   Tabla {table}: {count} registros")
        else:
            print(f"   ❌ Tabla {table} NO EXISTE")
    
    conn.close()
    
    print("\n✅ Limpieza completada")

if __name__ == "__main__":
    clean_system()

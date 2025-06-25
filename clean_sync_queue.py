#!/usr/bin/env python3
"""
Limpiar cola de sincronización con datos corruptos
"""
import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')

try:
    print("=== LIMPIANDO COLA DE SINCRONIZACIÓN ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ver cuántos elementos hay en la cola
    cursor.execute("SELECT COUNT(*) FROM sync_queue")
    count_before = cursor.fetchone()[0]
    print(f"Elementos en cola antes: {count_before}")
    
    # Eliminar elementos de la cola que puedan estar corruptos
    cursor.execute("DELETE FROM sync_queue")
    
    cursor.execute("SELECT COUNT(*) FROM sync_queue")
    count_after = cursor.fetchone()[0]
    print(f"Elementos en cola después: {count_after}")
    
    conn.commit()
    conn.close()
    
    print("✅ Cola de sincronización limpiada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    print(traceback.format_exc())

#!/usr/bin/env python3
"""
Script para limpiar cola de sincronización y corregir datos JSON malformados
"""
import os
import sys
import sqlite3
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_sync_queue():
    """Limpiar y corregir cola de sincronización"""
    db_path = os.path.join('data', 'local_database.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Obtener todos los elementos de la cola
            cursor.execute("SELECT id, table_name, operation, data, status FROM sync_queue")
            items = cursor.fetchall()
            
            print(f"🔍 Encontrados {len(items)} elementos en la cola de sincronización")
            
            # 2. Analizar y corregir elementos
            fixed_count = 0
            removed_count = 0
            
            for item_id, table_name, operation, data_str, status in items:
                print(f"\n📋 Procesando item {item_id}: {operation} en {table_name}")
                print(f"   Estado: {status}")
                print(f"   Datos: {data_str[:100]}...")
                
                # Intentar deserializar datos JSON
                try:
                    if data_str:
                        # Intentar parsear JSON
                        parsed_data = json.loads(data_str)
                        print(f"   ✅ JSON válido")
                        
                        # Verificar estructura
                        if isinstance(parsed_data, dict):
                            print(f"   ✅ Estructura correcta: {list(parsed_data.keys())}")
                        else:
                            print(f"   ⚠️ Estructura inesperada: {type(parsed_data)}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON inválido: {e}")
                    
                    # Intentar corregir datos comunes
                    corrected_data = None
                    
                    # Caso 1: Datos que parecen Python dict en lugar de JSON
                    if data_str.startswith("{'") or data_str.startswith('{"'):
                        try:
                            # Intentar evaluar como Python dict (PELIGROSO, solo para limpieza)
                            import ast
                            python_dict = ast.literal_eval(data_str)
                            corrected_data = json.dumps(python_dict)
                            print(f"   🔧 Corregido formato Python dict a JSON")
                        except:
                            print(f"   ❌ No se pudo corregir como Python dict")
                    
                    # Caso 2: String simple que no es JSON
                    elif not data_str.startswith('{') and not data_str.startswith('['):
                        corrected_data = json.dumps({"data": data_str})
                        print(f"   🔧 Envuelto string simple en JSON")
                    
                    if corrected_data:
                        # Actualizar con datos corregidos
                        cursor.execute("""
                            UPDATE sync_queue 
                            SET data = ?, status = 'pending'
                            WHERE id = ?
                        """, (corrected_data, item_id))
                        fixed_count += 1
                        print(f"   ✅ Datos corregidos y guardados")
                    else:
                        # Eliminar elemento que no se puede corregir
                        cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                        removed_count += 1
                        print(f"   🗑️ Elemento eliminado (no corregible)")
                
                except Exception as e:
                    print(f"   ❌ Error procesando: {e}")
                    # Eliminar elementos problemáticos
                    cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                    removed_count += 1
                    print(f"   🗑️ Elemento eliminado (error general)")
            
            conn.commit()
            
            print(f"\n📊 RESUMEN DE LIMPIEZA:")
            print(f"   🔧 Elementos corregidos: {fixed_count}")
            print(f"   🗑️ Elementos eliminados: {removed_count}")
            print(f"   📋 Elementos procesados: {len(items)}")
            
            # 3. Mostrar estado final
            cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
            final_stats = cursor.fetchall()
            
            print(f"\n📈 ESTADO FINAL DE LA COLA:")
            for status, count in final_stats:
                print(f"   {status}: {count} elementos")
            
            return True
            
    except Exception as e:
        logger.error(f"Error limpiando cola: {e}")
        return False

def main():
    """Función principal"""
    print("🧹 LIMPIADOR DE COLA DE SINCRONIZACIÓN")
    print("=" * 50)
    
    if clean_sync_queue():
        print("\n✅ Limpieza completada exitosamente")
    else:
        print("\n❌ Error durante la limpieza")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script para corregir y limpiar completamente la cola de sincronización
Elimina elementos problemáticos y reinicia con orden correcto
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_sync_queue_completely():
    """Corrección completa de la cola de sincronización"""
    logger.info("🔧 CORRECCIÓN COMPLETA DE COLA DE SINCRONIZACIÓN")
    
    local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    if not os.path.exists(local_db_path):
        logger.error("❌ Base de datos local no encontrada")
        return False
    
    try:
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Obtener estadísticas antes
            cursor.execute("SELECT COUNT(*) FROM sync_queue")
            total_before = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
            pending_before = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE attempts >= 3")
            failed_before = cursor.fetchone()[0]
            
            logger.info(f"📊 Estado inicial: {total_before} total, {pending_before} pendientes, {failed_before} fallidos")
            
            # 2. Analizar elementos problemáticos
            cursor.execute("""
                SELECT id, table_name, operation, data 
                FROM sync_queue 
                WHERE status IN ('pending', 'failed') OR attempts >= 3
            """)
            
            problematic_items = cursor.fetchall()
            
            items_to_delete = []
            items_to_fix = []
            
            for item in problematic_items:
                item_id, table_name, operation, data_json = item
                
                try:
                    # Intentar deserializar JSON
                    data = json.loads(data_json)
                    
                    # Verificar si es el formato con metadata
                    if isinstance(data, dict) and 'data' in data:
                        actual_data = data['data']
                    else:
                        actual_data = data
                    
                    # Verificar si los datos son válidos
                    if not actual_data or not isinstance(actual_data, dict):
                        logger.warning(f"⚠️ Item {item_id}: datos vacíos o inválidos")
                        items_to_delete.append(item_id)
                        continue
                    
                    # Verificar si tiene campos problemáticos
                    has_problems = False
                    clean_data = {}
                    
                    for key, value in actual_data.items():
                        # Saltar campos de metadata
                        if key in ['original_query', 'original_params', 'timestamp', 'metadata', 'tags']:
                            continue
                        
                        # Verificar expresiones SQL en valores
                        if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                            logger.warning(f"⚠️ Item {item_id}: campo {key} con expresión SQL: {value}")
                            has_problems = True
                            continue
                        
                        # Convertir boolean problemáticos en campos enteros
                        if table_name == 'detalle_ventas' and key in ['cantidad', 'venta_id', 'producto_id']:
                            if isinstance(value, bool):
                                clean_data[key] = 1 if value else 0
                                has_problems = True
                            else:
                                clean_data[key] = value
                        else:
                            clean_data[key] = value
                    
                    if has_problems:
                        if clean_data:
                            # Datos reparables
                            items_to_fix.append((item_id, table_name, operation, clean_data))
                        else:
                            # Sin datos válidos
                            items_to_delete.append(item_id)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Item {item_id}: JSON inválido - {e}")
                    items_to_delete.append(item_id)
                except Exception as e:
                    logger.error(f"❌ Item {item_id}: error procesando - {e}")
                    items_to_delete.append(item_id)
            
            # 3. Eliminar elementos problemáticos
            if items_to_delete:
                placeholders = ','.join(['?'] * len(items_to_delete))
                cursor.execute(f"DELETE FROM sync_queue WHERE id IN ({placeholders})", items_to_delete)
                logger.info(f"🗑️ Eliminados {len(items_to_delete)} elementos problemáticos")
            
            # 4. Reparar elementos con problemas menores
            for item_id, table_name, operation, clean_data in items_to_fix:
                try:
                    # Crear nuevo JSON limpio
                    clean_json = json.dumps({
                        'table': table_name,
                        'operation': operation,
                        'data': clean_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    cursor.execute("""
                        UPDATE sync_queue 
                        SET data = ?, attempts = 0, status = 'pending'
                        WHERE id = ?
                    """, (clean_json, item_id))
                    
                except Exception as e:
                    logger.error(f"❌ Error reparando item {item_id}: {e}")
                    items_to_delete.append(item_id)
            
            if items_to_fix:
                logger.info(f"🔧 Reparados {len(items_to_fix)} elementos")
            
            # 5. Eliminar duplicados por tabla/operación/datos
            cursor.execute("""
                DELETE FROM sync_queue 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM sync_queue 
                    GROUP BY table_name, operation, data
                )
            """)
            duplicates_removed = cursor.rowcount
            
            if duplicates_removed > 0:
                logger.info(f"🧹 Eliminados {duplicates_removed} duplicados")
            
            # 6. Marcar elementos muy antiguos como fallidos
            cursor.execute("""
                UPDATE sync_queue 
                SET status = 'failed_old'
                WHERE attempts >= 5 OR timestamp < datetime('now', '-1 day')
            """)
            old_marked = cursor.rowcount
            
            if old_marked > 0:
                logger.info(f"⏰ Marcados {old_marked} elementos antiguos como fallidos")
            
            conn.commit()
            
            # 7. Estadísticas finales
            cursor.execute("SELECT COUNT(*) FROM sync_queue")
            total_after = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
            pending_after = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status LIKE 'failed%'")
            failed_after = cursor.fetchone()[0]
            
            logger.info("✅ CORRECCIÓN COMPLETADA:")
            logger.info(f"   📊 Total: {total_before} → {total_after}")
            logger.info(f"   ⏳ Pendientes: {pending_before} → {pending_after}")
            logger.info(f"   ❌ Fallidos: {failed_before} → {failed_after}")
            logger.info(f"   🗑️ Eliminados: {items_to_delete}")
            logger.info(f"   🔧 Reparados: {len(items_to_fix)}")
            logger.info(f"   🧹 Duplicados: {duplicates_removed}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error en corrección: {e}")
        return False

def validate_sync_queue():
    """Validar que la cola esté en buen estado"""
    logger.info("🔍 VALIDANDO COLA DE SINCRONIZACIÓN")
    
    local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    try:
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar elementos pendientes
            cursor.execute("""
                SELECT id, table_name, operation, data 
                FROM sync_queue 
                WHERE status = 'pending'
                ORDER BY timestamp ASC
                LIMIT 10
            """)
            
            pending_items = cursor.fetchall()
            
            if not pending_items:
                logger.info("✅ No hay elementos pendientes")
                return True
            
            logger.info(f"📋 {len(pending_items)} elementos pendientes:")
            
            all_valid = True
            
            for item in pending_items:
                item_id, table_name, operation, data_json = item
                
                try:
                    data = json.loads(data_json)
                    
                    # Verificar estructura
                    if isinstance(data, dict) and 'data' in data:
                        actual_data = data['data']
                    else:
                        actual_data = data
                    
                    if not actual_data or not isinstance(actual_data, dict):
                        logger.error(f"❌ Item {item_id}: datos inválidos")
                        all_valid = False
                        continue
                    
                    # Verificar que no tenga expresiones SQL
                    has_sql_expressions = False
                    for key, value in actual_data.items():
                        if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                            has_sql_expressions = True
                            break
                    
                    if has_sql_expressions:
                        logger.warning(f"⚠️ Item {item_id}: contiene expresiones SQL")
                        all_valid = False
                    else:
                        logger.info(f"✅ Item {item_id}: {operation} en {table_name} - OK")
                
                except json.JSONDecodeError:
                    logger.error(f"❌ Item {item_id}: JSON inválido")
                    all_valid = False
                except Exception as e:
                    logger.error(f"❌ Item {item_id}: error - {e}")
                    all_valid = False
            
            return all_valid
            
    except Exception as e:
        logger.error(f"❌ Error validando: {e}")
        return False

def main():
    """Ejecutar corrección completa"""
    logger.info("🚀 INICIANDO CORRECCIÓN COMPLETA DE SINCRONIZACIÓN")
    
    # 1. Corregir cola
    if fix_sync_queue_completely():
        logger.info("✅ Corrección de cola exitosa")
    else:
        logger.error("❌ Error en corrección de cola")
        return False
    
    # 2. Validar resultado
    if validate_sync_queue():
        logger.info("✅ Validación exitosa - cola lista para sincronización")
    else:
        logger.warning("⚠️ Aún hay problemas en la cola")
    
    logger.info("🎯 CORRECCIÓN COMPLETA FINALIZADA")
    return True

if __name__ == "__main__":
    main()

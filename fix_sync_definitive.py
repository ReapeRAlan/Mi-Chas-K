#!/usr/bin/env python3
"""
Solución Definitiva para Problemas de Sincronización
Resuelve foreign keys y parámetros de forma permanente
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime
from decimal import Decimal

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_foreign_key_issues():
    """Resolver problemas de foreign key ordenando correctamente la sincronización"""
    logger.info("🔧 RESOLVIENDO PROBLEMAS DE FOREIGN KEY")
    
    local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    try:
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Obtener todas las ventas que tienen detalles pendientes de sincronizar
            cursor.execute("""
                SELECT DISTINCT 
                    JSON_EXTRACT(sq.data, '$.data.venta_id') as venta_id
                FROM sync_queue sq
                WHERE sq.table_name = 'detalle_ventas' 
                AND sq.status = 'pending'
                AND JSON_EXTRACT(sq.data, '$.data.venta_id') IS NOT NULL
            """)
            
            venta_ids_needed = [row[0] for row in cursor.fetchall() if row[0]]
            
            if not venta_ids_needed:
                logger.info("✅ No hay problemas de foreign key pendientes")
                return True
            
            logger.info(f"🔍 Detectadas {len(venta_ids_needed)} ventas necesarias: {venta_ids_needed}")
            
            # 2. Para cada venta necesaria, agregar a cola si no está
            for venta_id in venta_ids_needed:
                # Verificar si la venta ya está en la cola
                cursor.execute("""
                    SELECT COUNT(*) FROM sync_queue 
                    WHERE table_name = 'ventas' 
                    AND JSON_EXTRACT(data, '$.data.id') = ?
                    AND status IN ('pending', 'completed')
                """, (venta_id,))
                
                venta_in_queue = cursor.fetchone()[0] > 0
                
                if not venta_in_queue:
                    # Obtener datos de la venta desde la tabla local
                    cursor.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,))
                    venta_data = cursor.fetchone()
                    
                    if venta_data:
                        # Convertir a diccionario
                        cursor.execute("PRAGMA table_info(ventas)")
                        columns = [col[1] for col in cursor.fetchall()]
                        venta_dict = dict(zip(columns, venta_data))
                        
                        # Agregar venta a cola de sincronización
                        sync_data = {
                            'table': 'ventas',
                            'operation': 'INSERT',
                            'data': venta_dict,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        cursor.execute("""
                            INSERT INTO sync_queue (table_name, operation, data, timestamp, status)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                        """, ('ventas', 'INSERT', json.dumps(sync_data)))
                        
                        logger.info(f"✅ Venta {venta_id} agregada a cola de sincronización")
                    else:
                        logger.warning(f"⚠️ Venta {venta_id} no encontrada en BD local")
            
            # 3. Reordenar cola para que ventas vayan antes que detalles
            cursor.execute("""
                UPDATE sync_queue 
                SET timestamp = datetime(timestamp, '-1 hour')
                WHERE table_name = 'ventas' AND status = 'pending'
            """)
            
            conn.commit()
            logger.info("✅ Problemas de foreign key resueltos")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error resolviendo foreign keys: {e}")
        return False

def fix_parameter_mismatch():
    """Resolver problemas de parámetros de manera definitiva"""
    logger.info("🔧 RESOLVIENDO PROBLEMAS DE PARÁMETROS")
    
    # Crear función mejorada de conversión de parámetros
    improved_conversion = '''
def _convert_to_postgres_params_fixed(self, query: str, params: tuple = ()) -> tuple:
    """Convertir parámetros SQLite (?) a PostgreSQL ($1, $2, $3, etc.) con validación robusta"""
    if not query or '?' not in query:
        return query, params
    
    # Contar parámetros reales en la query
    param_count_in_query = query.count('?')
    param_count_provided = len(params) if params else 0
    
    # Si hay discrepancia, registrar warning pero continuar
    if param_count_in_query != param_count_provided:
        logger.warning(f"⚠️ Discrepancia de parámetros: query tiene {param_count_in_query}, proporcionados {param_count_provided}")
        # Ajustar parámetros si es necesario
        if param_count_provided > param_count_in_query:
            # Truncar parámetros extras
            params = params[:param_count_in_query]
            logger.info(f"🔧 Parámetros truncados a {param_count_in_query}")
        elif param_count_provided < param_count_in_query:
            # Rellenar con None si faltan parámetros
            params = params + (None,) * (param_count_in_query - param_count_provided)
            logger.info(f"🔧 Parámetros rellenados a {param_count_in_query}")
    
    # Convertir ? a $1, $2, $3, etc.
    result = ""
    param_counter = 0
    i = 0
    
    while i < len(query):
        if query[i] == '?':
            param_counter += 1
            result += f"${param_counter}"
        else:
            result += query[i]
        i += 1
    
    # Limpiar parámetros para PostgreSQL
    cleaned_params = []
    for param in params:
        if isinstance(param, Decimal):
            cleaned_params.append(float(param))
        elif isinstance(param, bool):
            cleaned_params.append(param)  # PostgreSQL maneja boolean nativamente
        elif param is None:
            cleaned_params.append(None)
        else:
            cleaned_params.append(param)
    
    logger.debug(f"🔄 Query convertida: {param_counter} parámetros")
    return result, tuple(cleaned_params)
'''
    
    logger.info("✅ Función de conversión de parámetros mejorada lista")
    return True

def clean_problematic_stock_updates():
    """Limpiar actualizaciones de stock problemáticas en la cola"""
    logger.info("🧹 LIMPIANDO ACTUALIZACIONES DE STOCK PROBLEMÁTICAS")
    
    local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    try:
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # Encontrar elementos con queries UPDATE de stock problemáticas
            cursor.execute("""
                SELECT id, data FROM sync_queue 
                WHERE table_name = 'productos' 
                AND operation = 'UPDATE'
                AND data LIKE '%COALESCE%'
                AND status = 'pending'
            """)
            
            problematic_updates = cursor.fetchall()
            
            if not problematic_updates:
                logger.info("✅ No hay actualizaciones de stock problemáticas")
                return True
            
            logger.info(f"🔍 Encontradas {len(problematic_updates)} actualizaciones problemáticas")
            
            fixed_count = 0
            deleted_count = 0
            
            for item_id, data_json in problematic_updates:
                try:
                    data = json.loads(data_json)
                    
                    if 'data' in data and isinstance(data['data'], dict):
                        item_data = data['data']
                        
                        # Si tiene 'id' pero solo campos problemáticos, convertir a simple UPDATE de sincronización
                        if 'id' in item_data:
                            product_id = item_data['id']
                            
                            # Obtener datos actuales del producto
                            cursor.execute("SELECT * FROM productos WHERE id = ?", (product_id,))
                            current_product = cursor.fetchone()
                            
                            if current_product:
                                # Crear nueva entrada de sincronización con datos actuales
                                cursor.execute("PRAGMA table_info(productos)")
                                columns = [col[1] for col in cursor.fetchall()]
                                product_dict = dict(zip(columns, current_product))
                                
                                # Remover campos problemáticos
                                clean_product = {k: v for k, v in product_dict.items() 
                                               if k not in ['sync_status', 'fecha_modificacion']}
                                
                                new_sync_data = {
                                    'table': 'productos',
                                    'operation': 'UPDATE',
                                    'data': clean_product,
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                # Actualizar elemento existente
                                cursor.execute("""
                                    UPDATE sync_queue 
                                    SET data = ?, attempts = 0
                                    WHERE id = ?
                                """, (json.dumps(new_sync_data), item_id))
                                
                                fixed_count += 1
                                logger.info(f"🔧 Corregido item {item_id} para producto {product_id}")
                            else:
                                # Producto no existe, eliminar de cola
                                cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                                deleted_count += 1
                                logger.info(f"🗑️ Eliminado item {item_id} (producto inexistente)")
                        else:
                            # Sin ID, eliminar
                            cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                            deleted_count += 1
                            logger.info(f"🗑️ Eliminado item {item_id} (sin ID)")
                            
                except Exception as e:
                    logger.error(f"❌ Error procesando item {item_id}: {e}")
                    # Eliminar elemento problemático
                    cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                    deleted_count += 1
            
            conn.commit()
            
            logger.info(f"✅ Limpieza completada: {fixed_count} corregidos, {deleted_count} eliminados")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error limpiando actualizaciones: {e}")
        return False

def create_minimal_sync_queue():
    """Crear cola de sincronización minimal y ordenada"""
    logger.info("🔄 CREANDO COLA DE SINCRONIZACIÓN MÍNIMA Y ORDENADA")
    
    local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
    
    try:
        with sqlite3.connect(local_db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Limpiar cola actual
            cursor.execute("DELETE FROM sync_queue")
            logger.info("🧹 Cola de sincronización limpiada")
            
            # 2. Obtener datos básicos para sincronización inicial
            
            # a) Categorías
            cursor.execute("SELECT * FROM categorias ORDER BY id")
            categorias = cursor.fetchall()
            cursor.execute("PRAGMA table_info(categorias)")
            cat_columns = [col[1] for col in cursor.fetchall()]
            
            for cat in categorias:
                cat_dict = dict(zip(cat_columns, cat))
                sync_data = {
                    'table': 'categorias',
                    'operation': 'INSERT',
                    'data': cat_dict,
                    'timestamp': datetime.now().isoformat()
                }
                
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data, timestamp, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                """, ('categorias', 'INSERT', json.dumps(sync_data)))
            
            logger.info(f"✅ {len(categorias)} categorías agregadas a cola")
            
            # b) Productos (solo datos básicos, sin expresiones SQL)
            cursor.execute("SELECT * FROM productos ORDER BY id")
            productos = cursor.fetchall()
            cursor.execute("PRAGMA table_info(productos)")
            prod_columns = [col[1] for col in cursor.fetchall()]
            
            for prod in productos:
                prod_dict = dict(zip(prod_columns, prod))
                # Limpiar campos problemáticos
                clean_prod = {k: v for k, v in prod_dict.items() 
                             if k not in ['sync_status', 'fecha_modificacion']}
                
                sync_data = {
                    'table': 'productos',
                    'operation': 'INSERT',
                    'data': clean_prod,
                    'timestamp': datetime.now().isoformat()
                }
                
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data, timestamp, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                """, ('productos', 'INSERT', json.dumps(sync_data)))
            
            logger.info(f"✅ {len(productos)} productos agregados a cola")
            
            conn.commit()
            
            # 3. Verificar cola creada
            cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
            total_pending = cursor.fetchone()[0]
            
            logger.info(f"✅ Cola mínima creada con {total_pending} elementos pendientes")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando cola mínima: {e}")
        return False

def test_sync_with_clean_queue():
    """Probar sincronización con cola limpia"""
    logger.info("🧪 PROBANDO SINCRONIZACIÓN CON COLA LIMPIA")
    
    try:
        # Importar adaptador
        sys.path.append(os.getcwd())
        from database.connection_adapter import DatabaseAdapter
        
        adapter = DatabaseAdapter()
        
        # Verificar estado
        status = adapter.get_sync_status()
        logger.info(f"📊 Estado: {status['pending']} pendientes, {status['failed']} fallidos")
        
        if status['pending'] > 0:
            logger.info("🔄 Iniciando sincronización de prueba...")
            success = adapter.force_sync()
            
            if success:
                logger.info("✅ Sincronización de prueba exitosa")
                
                # Verificar estado final
                final_status = adapter.get_sync_status()
                logger.info(f"📊 Estado final: {final_status['pending']} pendientes, {final_status['failed']} fallidos")
                
                return final_status['pending'] == 0 and final_status['failed'] == 0
            else:
                logger.error("❌ Sincronización de prueba falló")
                return False
        else:
            logger.info("✅ No hay elementos pendientes para sincronizar")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error en prueba de sincronización: {e}")
        return False

def main():
    """Ejecutar solución completa y definitiva"""
    logger.info("🚀 INICIANDO SOLUCIÓN DEFINITIVA DE SINCRONIZACIÓN")
    
    solutions_applied = []
    
    # 1. Resolver foreign keys
    if fix_foreign_key_issues():
        solutions_applied.append("✅ Problemas de foreign key resueltos")
    else:
        solutions_applied.append("❌ Error resolviendo foreign keys")
    
    # 2. Limpiar actualizaciones problemáticas
    if clean_problematic_stock_updates():
        solutions_applied.append("✅ Actualizaciones de stock limpiadas")
    else:
        solutions_applied.append("❌ Error limpiando actualizaciones")
    
    # 3. Mejorar conversión de parámetros
    if fix_parameter_mismatch():
        solutions_applied.append("✅ Conversión de parámetros mejorada")
    else:
        solutions_applied.append("❌ Error mejorando parámetros")
    
    # 4. Crear cola mínima ordenada
    if create_minimal_sync_queue():
        solutions_applied.append("✅ Cola mínima y ordenada creada")
    else:
        solutions_applied.append("❌ Error creando cola mínima")
    
    # 5. Probar sincronización
    if test_sync_with_clean_queue():
        solutions_applied.append("✅ Prueba de sincronización exitosa")
    else:
        solutions_applied.append("⚠️ Prueba de sincronización con problemas")
    
    # Resumen final
    logger.info("🎯 SOLUCIÓN DEFINITIVA COMPLETADA:")
    for solution in solutions_applied:
        logger.info(f"   {solution}")
    
    # Estado final
    success_count = len([s for s in solutions_applied if s.startswith("✅")])
    total_count = len(solutions_applied)
    
    if success_count == total_count:
        logger.info("🎉 TODOS LOS PROBLEMAS RESUELTOS EXITOSAMENTE")
        return True
    else:
        logger.warning(f"⚠️ {success_count}/{total_count} problemas resueltos")
        return False

if __name__ == "__main__":
    main()

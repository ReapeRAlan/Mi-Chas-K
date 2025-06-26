#!/usr/bin/env python3
"""
Script definitivo para solucionar todos los problemas críticos de sincronización
- Violaciones de foreign key
- Errores de parámetros PostgreSQL
- Expresiones SQL en campos
- Orden de sincronización
- Conversión de tipos boolean/integer
"""

import sqlite3
import psycopg2
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
from psycopg2.extras import RealDictCursor

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyncFixer:
    def __init__(self):
        self.local_db_path = 'mi_chaska.db'
        self.load_env_vars()
        
    def load_env_vars(self):
        """Cargar variables de entorno"""
        from dotenv import load_dotenv
        load_dotenv()
        
        self.db_host = os.getenv('DB_HOST')
        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_port = os.getenv('DB_PORT', 5432)
        
    def analyze_sync_queue(self):
        """Analizar estado actual de la cola de sincronización"""
        logger.info("🔍 Analizando cola de sincronización...")
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM sync_queue")
                total = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
                pending = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE attempts >= 3")
                failed = cursor.fetchone()[0]
                
                logger.info(f"📊 Cola de sincronización: {total} total, {pending} pendientes, {failed} fallidos")
                
                # Analizar por tabla y operación
                cursor.execute("""
                    SELECT table_name, operation, COUNT(*) as count
                    FROM sync_queue 
                    WHERE status = 'pending'
                    GROUP BY table_name, operation
                    ORDER BY count DESC
                """)
                
                operations = cursor.fetchall()
                logger.info("📋 Operaciones pendientes por tabla:")
                for table, op, count in operations:
                    logger.info(f"  - {table}: {op} ({count})")
                
                # Analizar elementos problemáticos
                cursor.execute("""
                    SELECT id, table_name, operation, data, attempts, error_msg
                    FROM sync_queue 
                    WHERE status = 'pending' AND attempts > 0
                    ORDER BY attempts DESC, timestamp ASC
                    LIMIT 20
                """)
                
                problematic = cursor.fetchall()
                if problematic:
                    logger.info("⚠️ Elementos problemáticos:")
                    for item in problematic:
                        item_id, table, op, data_json, attempts, error = item
                        logger.info(f"  - ID {item_id}: {table}.{op} (intentos: {attempts})")
                        if error:
                            logger.info(f"    Error: {error[:100]}...")
                
                return {
                    'total': total,
                    'pending': pending,
                    'failed': failed,
                    'operations': operations,
                    'problematic': problematic
                }
                
        except Exception as e:
            logger.error(f"❌ Error analizando cola: {e}")
            return None
    
    def fix_foreign_key_order(self):
        """Reordenar cola respetando dependencias de foreign keys"""
        logger.info("🔧 Reordenando cola por dependencias de foreign keys...")
        
        # Orden correcto por dependencias
        dependency_order = {
            'categorias': 1,      # Sin dependencias
            'vendedores': 2,      # Sin dependencias
            'productos': 3,       # Depende de categorias
            'ventas': 4,          # Depende de vendedores
            'detalle_ventas': 5   # Depende de ventas y productos
        }
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener todos los elementos pendientes
                cursor.execute("""
                    SELECT id, table_name, operation, data, timestamp
                    FROM sync_queue 
                    WHERE status = 'pending'
                    ORDER BY timestamp ASC
                """)
                
                items = cursor.fetchall()
                logger.info(f"📦 Reordenando {len(items)} elementos...")
                
                # Reordenar por prioridad
                sorted_items = sorted(items, key=lambda x: (
                    dependency_order.get(x[1], 999),  # Prioridad por tabla
                    0 if x[2] == 'INSERT' else 1 if x[2] == 'UPDATE' else 2,  # Prioridad por operación
                    x[4]  # Timestamp original
                ))
                
                # Actualizar orden en la base de datos
                for new_order, item in enumerate(sorted_items, 1):
                    item_id = item[0]
                    new_timestamp = datetime.now().isoformat() + f"_{new_order:06d}"
                    
                    cursor.execute("""
                        UPDATE sync_queue 
                        SET timestamp = ?, priority = ?
                        WHERE id = ?
                    """, (new_timestamp, new_order, item_id))
                
                conn.commit()
                logger.info("✅ Cola reordenada correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error reordenando cola: {e}")
    
    def clean_problematic_updates(self):
        """Limpiar UPDATEs problemáticos (vacíos o con expresiones SQL)"""
        logger.info("🧹 Limpiando UPDATEs problemáticos...")
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener UPDATEs pendientes
                cursor.execute("""
                    SELECT id, table_name, data
                    FROM sync_queue 
                    WHERE status = 'pending' AND operation = 'UPDATE'
                """)
                
                updates = cursor.fetchall()
                removed_count = 0
                fixed_count = 0
                
                for item_id, table_name, data_json in updates:
                    try:
                        data = json.loads(data_json)
                        
                        # Verificar si es un UPDATE vacío o problemático
                        if not self._has_valid_update_data(data, table_name):
                            # Eliminar UPDATE vacío
                            cursor.execute("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                            removed_count += 1
                            logger.info(f"🗑️ Eliminado UPDATE vacío: {table_name} ID {item_id}")
                        else:
                            # Limpiar datos problemáticos
                            cleaned_data = self._clean_update_data(data, table_name)
                            if cleaned_data != data:
                                # Actualizar con datos limpios
                                cursor.execute("""
                                    UPDATE sync_queue 
                                    SET data = ?
                                    WHERE id = ?
                                """, (json.dumps(cleaned_data), item_id))
                                fixed_count += 1
                                logger.info(f"🔧 Limpiado UPDATE: {table_name} ID {item_id}")
                    
                    except Exception as e:
                        logger.error(f"❌ Error procesando UPDATE {item_id}: {e}")
                
                conn.commit()
                logger.info(f"✅ UPDATEs procesados: {removed_count} eliminados, {fixed_count} corregidos")
                
        except Exception as e:
            logger.error(f"❌ Error limpiando UPDATEs: {e}")
    
    def _has_valid_update_data(self, data: dict, table_name: str) -> bool:
        """Verificar si un UPDATE tiene datos válidos"""
        if not isinstance(data, dict):
            return False
        
        # Campos que no son válidos para UPDATE
        invalid_fields = {
            'original_query', 'original_params', 'timestamp', 'metadata', 
            'tags', 'sync_status', 'id'
        }
        
        # Contar campos válidos
        valid_fields = 0
        for key, value in data.items():
            if key in invalid_fields:
                continue
            
            # Verificar si es expresión SQL
            if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/', 'SELECT']):
                continue
            
            # Verificar si es None
            if value is None:
                continue
            
            valid_fields += 1
        
        return valid_fields > 0
    
    def _clean_update_data(self, data: dict, table_name: str) -> dict:
        """Limpiar datos de UPDATE eliminando campos problemáticos"""
        cleaned_data = {}
        
        # Campos que no son válidos para UPDATE
        invalid_fields = {
            'original_query', 'original_params', 'timestamp', 'metadata', 
            'tags', 'sync_status'
        }
        
        for key, value in data.items():
            # Saltar campos inválidos
            if key in invalid_fields:
                continue
            
            # Saltar expresiones SQL
            if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/', 'SELECT']):
                logger.debug(f"🚫 Omitiendo expresión SQL en {key}: {value}")
                continue
            
            # Saltar valores None
            if value is None:
                continue
            
            # Convertir tipos apropiadamente
            if isinstance(value, Decimal):
                cleaned_data[key] = float(value)
            elif isinstance(value, bool) and table_name in ['productos', 'categorias', 'vendedores'] and key == 'activo':
                # Para PostgreSQL necesitamos boolean real
                cleaned_data[key] = value  # Mantener como boolean
            else:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def fix_parameter_mismatches(self):
        """Corregir discrepancias de parámetros en queries"""
        logger.info("🔧 Corrigiendo discrepancias de parámetros...")
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener elementos con queries originales
                cursor.execute("""
                    SELECT id, table_name, operation, data
                    FROM sync_queue 
                    WHERE status = 'pending' AND data LIKE '%original_query%'
                """)
                
                items = cursor.fetchall()
                fixed_count = 0
                
                for item_id, table_name, operation, data_json in items:
                    try:
                        full_data = json.loads(data_json)
                        
                        if 'original_query' in full_data and 'original_params' in full_data:
                            query = full_data['original_query']
                            params = full_data['original_params']
                            
                            # Contar parámetros en query
                            query_param_count = query.count('?') if query else 0
                            actual_param_count = len(params) if params else 0
                            
                            if query_param_count != actual_param_count:
                                logger.info(f"🔧 Corrigiendo parámetros en {table_name} ID {item_id}: query={query_param_count}, params={actual_param_count}")
                                
                                # Reconstruir datos sin query problemática
                                clean_data = {
                                    'table': table_name,
                                    'operation': operation,
                                    'data': full_data.get('data', {}),
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                cursor.execute("""
                                    UPDATE sync_queue 
                                    SET data = ?, attempts = 0, error_msg = NULL
                                    WHERE id = ?
                                """, (json.dumps(clean_data), item_id))
                                
                                fixed_count += 1
                    
                    except Exception as e:
                        logger.error(f"❌ Error corrigiendo parámetros en {item_id}: {e}")
                
                conn.commit()
                logger.info(f"✅ Parámetros corregidos en {fixed_count} elementos")
                
        except Exception as e:
            logger.error(f"❌ Error corrigiendo parámetros: {e}")
    
    def validate_remote_connection(self):
        """Validar conexión a base de datos remota"""
        logger.info("🔗 Validando conexión remota...")
        
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"✅ Conexión remota exitosa: {version[:50]}...")
                
                # Verificar tablas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"📋 Tablas remotas disponibles: {', '.join(tables)}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error conexión remota: {e}")
            return False
    
    def test_sync_single_item(self):
        """Probar sincronización de un solo elemento"""
        logger.info("🧪 Probando sincronización de elemento único...")
        
        if not self.validate_remote_connection():
            logger.error("❌ No hay conexión remota, cancelando prueba")
            return False
        
        try:
            with sqlite3.connect(self.local_db_path) as local_conn:
                local_cursor = local_conn.cursor()
                
                # Obtener el primer elemento pendiente más simple
                local_cursor.execute("""
                    SELECT id, table_name, operation, data
                    FROM sync_queue 
                    WHERE status = 'pending' AND table_name IN ('categorias', 'vendedores')
                    ORDER BY timestamp ASC
                    LIMIT 1
                """)
                
                item = local_cursor.fetchone()
                if not item:
                    logger.info("ℹ️ No hay elementos simples para probar")
                    return True
                
                item_id, table_name, operation, data_json = item
                logger.info(f"🧪 Probando: {table_name}.{operation} (ID: {item_id})")
                
                # Conectar a remoto
                remote_conn = psycopg2.connect(
                    host=self.db_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    port=self.db_port
                )
                
                try:
                    data = json.loads(data_json)
                    if 'data' in data:
                        record_data = data['data']
                    else:
                        record_data = data
                    
                    success = self._sync_single_record(remote_conn, table_name, operation, record_data)
                    
                    if success:
                        # Marcar como completado
                        local_cursor.execute("""
                            UPDATE sync_queue 
                            SET status = 'completed', synced_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (item_id,))
                        local_conn.commit()
                        logger.info("✅ Prueba de sincronización exitosa")
                        return True
                    else:
                        logger.error("❌ Falló la prueba de sincronización")
                        return False
                        
                finally:
                    remote_conn.close()
                    
        except Exception as e:
            logger.error(f"❌ Error en prueba de sincronización: {e}")
            return False
    
    def _sync_single_record(self, remote_conn, table_name: str, operation: str, data: dict) -> bool:
        """Sincronizar un solo registro"""
        try:
            with remote_conn.cursor() as cursor:
                if operation == 'INSERT':
                    return self._remote_insert(cursor, table_name, data)
                elif operation == 'UPDATE':
                    return self._remote_update(cursor, table_name, data)
                elif operation == 'DELETE':
                    return self._remote_delete(cursor, table_name, data)
                else:
                    logger.error(f"❌ Operación no soportada: {operation}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error sincronizando registro: {e}")
            return False
    
    def _remote_insert(self, cursor, table_name: str, data: dict) -> bool:
        """Insertar en remoto con validación"""
        try:
            # Adaptar datos para PostgreSQL
            adapted_data = self._adapt_data_for_postgres(data, table_name)
            
            if not adapted_data:
                logger.error("❌ No hay datos válidos para insertar")
                return False
            
            # Verificar duplicados
            if 'id' in adapted_data:
                cursor.execute(f"SELECT id FROM {table_name} WHERE id = %s", (adapted_data['id'],))
                if cursor.fetchone():
                    logger.info(f"🔄 Registro ya existe, actualizando...")
                    return self._remote_update(cursor, table_name, adapted_data)
            
            # Construir INSERT
            columns = list(adapted_data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(adapted_data.values())
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            cursor.execute(query, values)
            cursor.connection.commit()
            
            logger.info(f"✅ INSERT exitoso en {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en INSERT remoto: {e}")
            cursor.connection.rollback()
            return False
    
    def _remote_update(self, cursor, table_name: str, data: dict) -> bool:
        """Actualizar en remoto con validación"""
        try:
            if 'id' not in data:
                logger.error("❌ No se puede actualizar sin ID")
                return False
            
            # Adaptar datos
            adapted_data = self._adapt_data_for_postgres(data, table_name)
            
            # Construir UPDATE
            set_clauses = []
            values = []
            
            for key, value in adapted_data.items():
                if key != 'id':
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                logger.warning("⚠️ No hay campos para actualizar")
                return True
            
            values.append(adapted_data['id'])
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = %s"
            
            cursor.execute(query, values)
            cursor.connection.commit()
            
            logger.info(f"✅ UPDATE exitoso en {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en UPDATE remoto: {e}")
            cursor.connection.rollback()
            return False
    
    def _remote_delete(self, cursor, table_name: str, data: dict) -> bool:
        """Eliminar en remoto"""
        try:
            if 'id' not in data:
                logger.error("❌ No se puede eliminar sin ID")
                return False
            
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (data['id'],))
            cursor.connection.commit()
            
            logger.info(f"✅ DELETE exitoso en {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en DELETE remoto: {e}")
            cursor.connection.rollback()
            return False
    
    def _adapt_data_for_postgres(self, data: dict, table_name: str) -> dict:
        """Adaptar datos para PostgreSQL con conversión de tipos correcta"""
        adapted = {}
        
        for key, value in data.items():
            # Saltar campos de metadata
            if key in ['original_query', 'original_params', 'timestamp', 'metadata', 'tags', 'sync_status']:
                continue
            
            # Saltar expresiones SQL
            if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/', 'SELECT']):
                continue
            
            # Saltar valores None
            if value is None:
                continue
            
            # Conversiones de tipo
            if isinstance(value, Decimal):
                adapted[key] = float(value)
            elif key == 'activo' and table_name in ['productos', 'categorias', 'vendedores']:
                # Para PostgreSQL, mantener como boolean real
                if isinstance(value, bool):
                    adapted[key] = value
                elif isinstance(value, (int, str)):
                    adapted[key] = bool(int(value)) if str(value).isdigit() else value == 'true'
                else:
                    adapted[key] = bool(value)
            elif key in ['cantidad', 'stock', 'venta_id', 'producto_id', 'vendedor_id'] and isinstance(value, bool):
                # Campos numéricos no pueden ser boolean
                adapted[key] = 1 if value else 0
            else:
                adapted[key] = value
        
        return adapted
    
    def process_sync_queue_batch(self, batch_size: int = 10):
        """Procesar cola de sincronización en lotes"""
        logger.info(f"🔄 Procesando cola en lotes de {batch_size}...")
        
        if not self.validate_remote_connection():
            logger.error("❌ No hay conexión remota")
            return False
        
        try:
            with sqlite3.connect(self.local_db_path) as local_conn:
                local_cursor = local_conn.cursor()
                
                # Conectar a remoto
                remote_conn = psycopg2.connect(
                    host=self.db_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    port=self.db_port
                )
                
                try:
                    # Procesar en lotes
                    processed = 0
                    errors = 0
                    
                    while True:
                        # Obtener siguiente lote
                        local_cursor.execute("""
                            SELECT id, table_name, operation, data
                            FROM sync_queue 
                            WHERE status = 'pending'
                            ORDER BY timestamp ASC
                            LIMIT ?
                        """, (batch_size,))
                        
                        batch = local_cursor.fetchall()
                        if not batch:
                            break
                        
                        logger.info(f"📦 Procesando lote de {len(batch)} elementos...")
                        
                        for item in batch:
                            item_id, table_name, operation, data_json = item
                            
                            try:
                                data = json.loads(data_json)
                                record_data = data.get('data', data)
                                
                                success = self._sync_single_record(remote_conn, table_name, operation, record_data)
                                
                                if success:
                                    local_cursor.execute("""
                                        UPDATE sync_queue 
                                        SET status = 'completed', synced_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (item_id,))
                                    processed += 1
                                else:
                                    local_cursor.execute("""
                                        UPDATE sync_queue 
                                        SET attempts = attempts + 1, 
                                            error_msg = 'Sync failed',
                                            last_attempt = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (item_id,))
                                    errors += 1
                                    
                            except Exception as e:
                                logger.error(f"❌ Error procesando item {item_id}: {e}")
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET attempts = attempts + 1, 
                                        error_msg = ?,
                                        last_attempt = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (str(e)[:500], item_id))
                                errors += 1
                        
                        local_conn.commit()
                        
                        if errors > processed:
                            logger.warning(f"⚠️ Muchos errores ({errors}), pausando...")
                            break
                    
                    logger.info(f"✅ Sincronización completada: {processed} exitosos, {errors} errores")
                    return processed > 0
                    
                finally:
                    remote_conn.close()
                    
        except Exception as e:
            logger.error(f"❌ Error procesando cola: {e}")
            return False
    
    def run_full_fix(self):
        """Ejecutar corrección completa"""
        logger.info("🚀 Iniciando corrección completa de sincronización...")
        
        # 1. Analizar estado actual
        self.analyze_sync_queue()
        
        # 2. Reordenar por dependencias
        self.fix_foreign_key_order()
        
        # 3. Limpiar UPDATEs problemáticos
        self.clean_problematic_updates()
        
        # 4. Corregir parámetros
        self.fix_parameter_mismatches()
        
        # 5. Probar con un elemento
        if self.test_sync_single_item():
            # 6. Procesar cola en lotes
            self.process_sync_queue_batch(5)
        
        # 7. Analizar resultado final
        logger.info("📊 Estado final:")
        self.analyze_sync_queue()
        
        logger.info("✅ Corrección completa finalizada")

def main():
    """Función principal"""
    print("🔧 Script de Corrección Crítica de Sincronización")
    print("=" * 50)
    
    fixer = SyncFixer()
    fixer.run_full_fix()

if __name__ == "__main__":
    main()

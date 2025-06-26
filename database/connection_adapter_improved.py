"""
Adaptador de Base de Datos Mejorado - Versión Final
Sistema híbrido SQLite/PostgreSQL con sincronización robusta
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import json
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Generator, Dict, Any, List, Optional, Union
from dotenv import load_dotenv
import re

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class ImprovedDatabaseAdapter:
    """Adaptador mejorado que maneja la compatibilidad entre esquemas local y remoto"""
    
    def __init__(self):
        self.local_db_path = 'sistema_facturacion.db'
        self.remote_available = False
        self.sync_enabled = True
        self.remote_schema_cache = {}
        self.sync_thread = None
        self.sync_running = False
        self._check_remote_connection()
        self._ensure_local_structure()
        self._start_sync_thread()
        
    def _check_remote_connection(self):
        """Verificar conexión remota"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
            else:
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
            
            # Verificar estructura mínima
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['categorias', 'vendedores', 'productos', 'ventas', 'detalle_ventas']
                if all(table in tables for table in required_tables):
                    self.remote_available = True
                    logger.info("✅ Conexión remota verificada y estructura válida")
                else:
                    logger.warning("⚠️ Estructura remota incompleta")
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"⚠️ Sin conexión remota: {e}")
            self.remote_available = False
    
    def _ensure_local_structure(self):
        """Asegurar estructura local correcta"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Crear tabla de sincronización si no existe
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        attempts INTEGER DEFAULT 0,
                        error_message TEXT
                    )
                """)
                
                # Verificar tablas principales
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"📊 Tablas locales encontradas: {existing_tables}")
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Error verificando estructura local: {e}")
    
    def _start_sync_thread(self):
        """Iniciar hilo de sincronización"""
        if self.remote_available and self.sync_enabled:
            self.sync_running = True
            self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
            self.sync_thread.start()
            logger.info("🔄 Hilo de sincronización iniciado")
    
    def _sync_worker(self):
        """Worker de sincronización mejorado"""
        while self.sync_running:
            try:
                if self.remote_available:
                    self._process_sync_queue()
                time.sleep(10)  # Sincronizar cada 10 segundos
            except Exception as e:
                logger.error(f"❌ Error en worker de sincronización: {e}")
                time.sleep(30)  # Esperar más tiempo si hay error
    
    def _process_sync_queue(self):
        """Procesar cola de sincronización con manejo mejorado de errores"""
        try:
            with sqlite3.connect(self.local_db_path) as local_conn:
                local_cursor = local_conn.cursor()
                
                # Obtener elementos pendientes ordenados por dependencias
                local_cursor.execute("""
                    SELECT id, table_name, operation, data, attempts
                    FROM sync_queue 
                    WHERE status = 'pending' AND attempts < 3
                    ORDER BY 
                        CASE table_name 
                            WHEN 'categorias' THEN 1
                            WHEN 'vendedores' THEN 2
                            WHEN 'productos' THEN 3
                            WHEN 'ventas' THEN 4
                            WHEN 'detalle_ventas' THEN 5
                            ELSE 6
                        END,
                        CASE operation
                            WHEN 'INSERT' THEN 1
                            WHEN 'UPDATE' THEN 2
                            WHEN 'DELETE' THEN 3
                            ELSE 4
                        END,
                        timestamp
                    LIMIT 10
                """)
                
                items = local_cursor.fetchall()
                
                if not items:
                    return
                
                # Conectar a remoto
                database_url = os.getenv('DATABASE_URL')
                if database_url:
                    remote_conn = psycopg2.connect(database_url)
                else:
                    remote_conn = psycopg2.connect(
                        host=os.getenv('DB_HOST'),
                        database=os.getenv('DB_NAME'),
                        user=os.getenv('DB_USER'),
                        password=os.getenv('DB_PASSWORD'),
                        port=os.getenv('DB_PORT', 5432)
                    )
                
                with remote_conn.cursor() as remote_cursor:
                    for item in items:
                        item_id, table_name, operation, data_json, attempts = item
                        
                        try:
                            data = json.loads(data_json)
                            success = self._sync_single_item(remote_cursor, table_name, operation, data)
                            
                            if success:
                                # Marcar como completado
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET status = 'completed' 
                                    WHERE id = ?
                                """, (item_id,))
                                remote_conn.commit()
                            else:
                                # Incrementar intentos
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET attempts = attempts + 1,
                                        error_message = 'Sync failed'
                                    WHERE id = ?
                                """, (item_id,))
                                remote_conn.rollback()
                            
                        except Exception as e:
                            logger.error(f"❌ Error sincronizando item {item_id}: {e}")
                            
                            # Marcar como fallido después de 3 intentos
                            if attempts >= 2:
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET status = 'failed',
                                        error_message = ?
                                    WHERE id = ?
                                """, (str(e), item_id))
                            else:
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET attempts = attempts + 1,
                                        error_message = ?
                                    WHERE id = ?
                                """, (str(e), item_id))
                            
                            remote_conn.rollback()
                
                local_conn.commit()
                remote_conn.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando cola de sincronización: {e}")
    
    def _sync_single_item(self, cursor, table_name, operation, data):
        """Sincronizar un elemento individual con manejo robusto"""
        try:
            data_dict = data.get('data', {}) if isinstance(data, dict) else {}
            
            # Filtrar y limpiar datos
            clean_data = self._clean_data_for_sync(data_dict, table_name)
            
            if operation == 'INSERT':
                return self._execute_remote_insert(cursor, table_name, clean_data)
            elif operation == 'UPDATE':
                return self._execute_remote_update(cursor, table_name, clean_data)
            elif operation == 'DELETE':
                return self._execute_remote_delete(cursor, table_name, clean_data)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error en sync_single_item: {e}")
            return False
    
    def _clean_data_for_sync(self, data, table_name):
        """Limpiar datos para sincronización"""
        clean_data = {}
        
        # Campos a excluir
        exclude_fields = [
            'original_query', 'original_params', 'timestamp', 
            'metadata', 'tags', 'sync_status'
        ]
        
        for key, value in data.items():
            # Excluir campos de metadatos
            if key in exclude_fields:
                continue
            
            # Excluir valores None
            if value is None:
                continue
            
            # Limpiar expresiones SQL
            if isinstance(value, str) and self._is_sql_expression(value):
                logger.warning(f"🧹 Omitiendo expresión SQL: {key} = {value}")
                continue
            
            # Convertir tipos apropiadamente
            clean_data[key] = self._convert_value_for_postgres(key, value, table_name)
        
        return clean_data
    
    def _is_sql_expression(self, value):
        """Detectar si un valor es una expresión SQL"""
        if not isinstance(value, str):
            return False
        
        sql_indicators = [
            'COALESCE', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            '(', ')', '+', '-', '*', '/', 'WHERE', 'FROM'
        ]
        
        return any(indicator in value.upper() for indicator in sql_indicators)
    
    def _convert_value_for_postgres(self, key, value, table_name):
        """Convertir valor para PostgreSQL"""
        # Convertir Decimal a float
        if isinstance(value, Decimal):
            return float(value)
        
        # Manejo especial de campos boolean
        if key == 'activo':
            if isinstance(value, bool):
                return value  # PostgreSQL acepta boolean directamente
            elif isinstance(value, (int, str)):
                return bool(int(value))
        
        # Convertir otros campos boolean a entero si es necesario
        if isinstance(value, bool) and key not in ['activo']:
            return 1 if value else 0
        
        return value
    
    def _execute_remote_insert(self, cursor, table_name, data):
        """Ejecutar INSERT remoto con manejo de errores"""
        try:
            if not data:
                logger.warning(f"⚠️ Datos vacíos para INSERT en {table_name}")
                return False
            
            columns = list(data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(data.values())
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            cursor.execute(query, values)
            logger.debug(f"✅ INSERT exitoso en {table_name}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"❌ Error INSERT en {table_name}: {e}")
            return False
    
    def _execute_remote_update(self, cursor, table_name, data):
        """Ejecutar UPDATE remoto con manejo de errores"""
        try:
            if 'id' not in data:
                logger.warning(f"⚠️ Sin ID para UPDATE en {table_name}")
                return False
            
            # Separar ID del resto de datos
            update_data = {k: v for k, v in data.items() if k != 'id'}
            
            if not update_data:
                logger.warning(f"⚠️ Sin datos para UPDATE en {table_name}")
                return True  # Considerar como exitoso
            
            set_clauses = [f"{key} = %s" for key in update_data.keys()]
            values = list(update_data.values()) + [data['id']]
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = %s"
            
            cursor.execute(query, values)
            logger.debug(f"✅ UPDATE exitoso en {table_name}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"❌ Error UPDATE en {table_name}: {e}")
            return False
    
    def _execute_remote_delete(self, cursor, table_name, data):
        """Ejecutar DELETE remoto con manejo de errores"""
        try:
            if 'id' not in data:
                logger.warning(f"⚠️ Sin ID para DELETE en {table_name}")
                return False
            
            query = f"DELETE FROM {table_name} WHERE id = %s"
            cursor.execute(query, [data['id']])
            logger.debug(f"✅ DELETE exitoso en {table_name}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"❌ Error DELETE en {table_name}: {e}")
            return False
    
    def add_to_sync_queue(self, table_name, operation, data):
        """Agregar elemento a cola de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    table_name,
                    operation,
                    json.dumps(data),
                    datetime.now().isoformat()
                ))
                conn.commit()
                logger.debug(f"📝 Agregado a cola de sync: {operation} en {table_name}")
        except Exception as e:
            logger.error(f"❌ Error agregando a cola de sync: {e}")
    
    @contextmanager
    def get_connection(self):
        """Obtener conexión local"""
        conn = sqlite3.connect(self.local_db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """Ejecutar query en base local y agregar a cola de sync si es necesario"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Detectar tipo de operación
                operation = query.strip().upper().split()[0]
                
                if operation in ['INSERT', 'UPDATE', 'DELETE']:
                    # Extraer tabla de la query
                    table_name = self._extract_table_name(query)
                    
                    if table_name and self.sync_enabled:
                        # Construir datos para sync
                        sync_data = {
                            'original_query': query,
                            'original_params': params or [],
                            'data': self._build_sync_data(query, params, operation)
                        }
                        
                        self.add_to_sync_queue(table_name, operation, sync_data)
                    
                    conn.commit()
                    return cursor.lastrowid
                
                elif operation == 'SELECT':
                    if fetch_one:
                        return dict(cursor.fetchone()) if cursor.fetchone() else None
                    elif fetch_all:
                        return [dict(row) for row in cursor.fetchall()]
                    else:
                        return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando query: {e}")
            raise
    
    def _extract_table_name(self, query):
        """Extraer nombre de tabla de la query"""
        try:
            query_upper = query.strip().upper()
            
            if query_upper.startswith('INSERT'):
                match = re.search(r'INSERT\s+INTO\s+(\w+)', query_upper)
            elif query_upper.startswith('UPDATE'):
                match = re.search(r'UPDATE\s+(\w+)', query_upper)
            elif query_upper.startswith('DELETE'):
                match = re.search(r'DELETE\s+FROM\s+(\w+)', query_upper)
            else:
                return None
            
            return match.group(1).lower() if match else None
            
        except Exception:
            return None
    
    def _build_sync_data(self, query, params, operation):
        """Construir datos para sincronización"""
        data = {}
        
        try:
            if operation == 'INSERT' and params:
                # Para INSERT, intentar mapear parámetros a campos
                query_upper = query.upper()
                
                # Buscar columnas en la query
                if '(' in query_upper and ')' in query_upper:
                    columns_match = re.search(r'\(([^)]+)\)', query)
                    if columns_match:
                        columns = [col.strip() for col in columns_match.group(1).split(',')]
                        
                        # Mapear parámetros a columnas
                        for i, col in enumerate(columns):
                            if i < len(params):
                                data[col] = params[i]
            
            elif operation == 'UPDATE' and params:
                # Para UPDATE, es más complejo extraer los campos
                # Por ahora, usar parámetros tal como están
                data['params'] = params
            
            elif operation == 'DELETE' and params:
                # Para DELETE, normalmente solo necesitamos el ID
                data['id'] = params[0] if params else None
        
        except Exception as e:
            logger.warning(f"⚠️ Error construyendo sync data: {e}")
        
        return data
    
    def get_sync_status(self):
        """Obtener estado de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM sync_queue
                    GROUP BY status
                """)
                
                status_counts = dict(cursor.fetchall())
                
                return {
                    'remote_available': self.remote_available,
                    'sync_enabled': self.sync_enabled,
                    'queue_status': status_counts,
                    'total_pending': status_counts.get('pending', 0)
                }
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de sync: {e}")
            return {'error': str(e)}
    
    def force_sync(self):
        """Forzar sincronización inmediata"""
        if self.remote_available:
            logger.info("🔄 Forzando sincronización...")
            self._process_sync_queue()
            return True
        else:
            logger.warning("⚠️ No se puede forzar sync - sin conexión remota")
            return False
    
    def clear_failed_sync_items(self):
        """Limpiar elementos fallidos de la cola"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_queue WHERE status = 'failed'")
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"🗑️ Eliminados {deleted} elementos fallidos de la cola")
                return deleted
        except Exception as e:
            logger.error(f"❌ Error limpiando elementos fallidos: {e}")
            return 0
    
    def stop_sync(self):
        """Detener sincronización"""
        self.sync_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        logger.info("🛑 Sincronización detenida")

# Instancia global del adaptador mejorado
db_adapter = ImprovedDatabaseAdapter()

# Funciones de compatibilidad
def get_db_connection():
    """Función de compatibilidad para obtener conexión"""
    return db_adapter.get_connection()

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """Función de compatibilidad para ejecutar queries"""
    return db_adapter.execute_query(query, params, fetch_one, fetch_all)

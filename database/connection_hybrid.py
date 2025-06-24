"""
Sistema de Base de Datos Híbrido (Local/Remoto) con Sincronización Automática
Versión: 3.0.0 - Modo Híbrido
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
from typing import Generator, Dict, Any, List, Optional, Union
from dotenv import load_dotenv
import requests

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseHybrid:
    """Manejador de base de datos híbrido que funciona offline/online"""
    
    def __init__(self):
        self.local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
        self.sync_queue_path = os.path.join(os.getcwd(), 'data', 'sync_queue.json')
        self.is_online = False
        self.sync_enabled = True
        self._create_local_structure()
        self._start_sync_thread()
        
    def _create_local_structure(self):
        """Crear estructura de directorios y base de datos local"""
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.sync_queue_path), exist_ok=True)
        
        with sqlite3.connect(self.local_db_path) as conn:
            cursor = conn.cursor()
            
            # Crear tablas locales
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    precio DECIMAL(10,2) NOT NULL,
                    categoria_id INTEGER,
                    stock INTEGER DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
                );
                
                CREATE TABLE IF NOT EXISTS vendedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total DECIMAL(10,2) NOT NULL,
                    metodo_pago TEXT DEFAULT 'Efectivo',
                    vendedor TEXT,
                    observaciones TEXT,
                    descuento DECIMAL(10,2) DEFAULT 0.00,
                    sync_status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS items_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                );
                
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending'
                );
            """)
            
            # Insertar datos por defecto si no existen
            cursor.execute("SELECT COUNT(*) FROM vendedores")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO vendedores (nombre, activo) 
                    VALUES ('Sistema', 1), ('Vendedor 1', 1)
                """)
            
            cursor.execute("SELECT COUNT(*) FROM categorias")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO categorias (nombre, descripcion) 
                    VALUES 
                    ('Bebidas', 'Bebidas y refrescos'),
                    ('Comida', 'Productos alimenticios'),
                    ('Otros', 'Productos varios')
                """)
            
            conn.commit()
    
    def check_internet_connection(self) -> bool:
        """Verificar conexión a internet"""
        try:
            response = requests.get('https://www.google.com', timeout=5)
            self.is_online = response.status_code == 200
        except:
            self.is_online = False
        return self.is_online
    
    def check_database_connection(self) -> bool:
        """Verificar conexión a la base de datos remota"""
        if not self.check_internet_connection():
            return False
            
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                conn.close()
                return True
        except Exception as e:
            logger.warning(f"No se pudo conectar a la base de datos remota: {e}")
        return False
    
    @contextmanager
    def get_connection(self, prefer_remote: bool = True) -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
        """Obtener conexión a base de datos (remota si es posible, local como fallback)"""
        
        if prefer_remote and self.check_database_connection():
            # Intentar conexión remota
            try:
                database_url = os.getenv('DATABASE_URL')
                conn = psycopg2.connect(database_url)
                conn.autocommit = False
                logger.info("🌐 Usando base de datos remota")
                yield conn
                return
            except Exception as e:
                logger.warning(f"Error en conexión remota, usando local: {e}")
        
        # Usar base de datos local
        logger.info("💾 Usando base de datos local")
        with sqlite3.connect(self.local_db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn
    
    def execute_query(self, query: str, params: tuple = (), prefer_remote: bool = True) -> List[Dict[str, Any]]:
        """Ejecutar consulta de lectura"""
        try:
            with self.get_connection(prefer_remote) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(query, params)
                        result = cursor.fetchall()
                        return [dict(row) for row in result]
                else:
                    # SQLite
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
        """Ejecutar consulta de escritura con cola de sincronización"""
        try:
            with self.get_connection(prefer_remote=True) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL - ejecutar directamente
                    with conn.cursor() as cursor:
                        cursor.execute(query, params)
                        conn.commit()
                        if cursor.rowcount > 0:
                            return cursor.lastrowid if hasattr(cursor, 'lastrowid') else cursor.rowcount
                else:
                    # SQLite - ejecutar y agregar a cola de sincronización
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    row_id = cursor.lastrowid
                    
                    # Agregar a cola de sincronización si hay datos
                    if sync_data and self.sync_enabled:
                        self._add_to_sync_queue(sync_data)
                    
                    return row_id
        except Exception as e:
            logger.error(f"Error ejecutando actualización: {e}")
            return None
    
    def _add_to_sync_queue(self, sync_data: Dict):
        """Agregar operación a la cola de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data)
                    VALUES (?, ?, ?)
                """, (sync_data['table'], sync_data['operation'], json.dumps(sync_data['data'])))
                conn.commit()
        except Exception as e:
            logger.error(f"Error agregando a cola de sincronización: {e}")
    
    def _start_sync_thread(self):
        """Iniciar hilo de sincronización en segundo plano"""
        if not self.sync_enabled:
            return
            
        def sync_worker():
            while self.sync_enabled:
                try:
                    if self.check_database_connection():
                        self._process_sync_queue()
                    time.sleep(30)  # Verificar cada 30 segundos
                except Exception as e:
                    logger.error(f"Error en sincronización: {e}")
                    time.sleep(60)  # Esperar más tiempo si hay error
        
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        logger.info("🔄 Hilo de sincronización iniciado")
    
    def _process_sync_queue(self):
        """Procesar cola de sincronización pendiente"""
        try:
            with sqlite3.connect(self.local_db_path) as local_conn:
                cursor = local_conn.cursor()
                cursor.execute("""
                    SELECT id, table_name, operation, data
                    FROM sync_queue 
                    WHERE status = 'pending' AND attempts < 3
                    ORDER BY timestamp ASC
                    LIMIT 10
                """)
                
                pending_items = cursor.fetchall()
                
                if not pending_items:
                    return
                
                logger.info(f"🔄 Sincronizando {len(pending_items)} elementos pendientes")
                
                # Conectar a base de datos remota
                database_url = os.getenv('DATABASE_URL')
                with psycopg2.connect(database_url) as remote_conn:
                    with remote_conn.cursor() as remote_cursor:
                        
                        for item in pending_items:
                            try:
                                item_id, table_name, operation, data_json = item
                                data = json.loads(data_json)
                                
                                if operation == 'INSERT':
                                    self._sync_insert(remote_cursor, table_name, data)
                                elif operation == 'UPDATE':
                                    self._sync_update(remote_cursor, table_name, data)
                                elif operation == 'DELETE':
                                    self._sync_delete(remote_cursor, table_name, data)
                                
                                # Marcar como sincronizado
                                cursor.execute("""
                                    UPDATE sync_queue 
                                    SET status = 'completed' 
                                    WHERE id = ?
                                """, (item_id,))
                                
                            except Exception as e:
                                logger.error(f"Error sincronizando item {item_id}: {e}")
                                cursor.execute("""
                                    UPDATE sync_queue 
                                    SET attempts = attempts + 1 
                                    WHERE id = ?
                                """, (item_id,))
                        
                        remote_conn.commit()
                        local_conn.commit()
                        
        except Exception as e:
            logger.error(f"Error procesando cola de sincronización: {e}")
    
    def _sync_insert(self, cursor, table_name: str, data: Dict):
        """Sincronizar inserción"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(data.values()))
    
    def _sync_update(self, cursor, table_name: str, data: Dict):
        """Sincronizar actualización"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys() if k != 'id'])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        values = [v for k, v in data.items() if k != 'id'] + [data['id']]
        cursor.execute(query, values)
    
    def _sync_delete(self, cursor, table_name: str, data: Dict):
        """Sincronizar eliminación"""
        query = f"DELETE FROM {table_name} WHERE id = %s"
        cursor.execute(query, (data['id'],))
    
    def force_sync(self) -> bool:
        """Forzar sincronización manual"""
        if not self.check_database_connection():
            logger.warning("No hay conexión a internet para sincronizar")
            return False
        
        try:
            self._process_sync_queue()
            logger.info("✅ Sincronización forzada completada")
            return True
        except Exception as e:
            logger.error(f"Error en sincronización forzada: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """Obtener estado de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
                pending = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'completed'")
                completed = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE attempts >= 3")
                failed = cursor.fetchone()[0]
                
                return {
                    'online': self.is_online,
                    'pending': pending,
                    'completed': completed,
                    'failed': failed,
                    'database_available': self.check_database_connection()
                }
        except Exception as e:
            logger.error(f"Error obteniendo estado de sync: {e}")
            return {'online': False, 'pending': 0, 'completed': 0, 'failed': 0, 'database_available': False}

# Instancia global
db_hybrid = DatabaseHybrid()

# Funciones de compatibilidad
def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Función de compatibilidad para consultas"""
    return db_hybrid.execute_query(query, params)

def execute_update(query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
    """Función de compatibilidad para actualizaciones"""
    return db_hybrid.execute_update(query, params, sync_data)

@contextmanager
def get_db_connection() -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
    """Función de compatibilidad para conexiones"""
    with db_hybrid.get_connection() as conn:
        yield conn

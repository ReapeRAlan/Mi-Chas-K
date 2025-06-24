"""
Adaptador de Base de Datos para compatibilidad con esquema existente
Versión 3.1.0 - Compatible con BD existente de Render
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

class DatabaseAdapter:
    """Adaptador que maneja la compatibilidad entre esquemas local y remoto"""
    
    def __init__(self):
        self.local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
        self.sync_queue_path = os.path.join(os.getcwd(), 'data', 'sync_queue.json')
        self.is_online = False
        self.sync_enabled = True
        self.remote_schema_cache = {}
        self._create_local_structure()
        self._start_sync_thread()
        
    def _create_local_structure(self):
        """Crear estructura de directorios y base de datos local"""
        os.makedirs(os.path.dirname(self.local_db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.sync_queue_path), exist_ok=True)
        
        with sqlite3.connect(self.local_db_path) as conn:
            cursor = conn.cursor()
            
            # Crear tablas locales con esquema compatible
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
                    categoria TEXT DEFAULT 'General',
                    stock INTEGER DEFAULT 0,
                    descripcion TEXT,
                    codigo_barras TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
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
                    impuestos DECIMAL(10,2) DEFAULT 0.00,
                    sync_status TEXT DEFAULT 'pending'
                );
                
                CREATE TABLE IF NOT EXISTS detalle_ventas (
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
                    ('Chascas', 'Productos principales'),
                    ('Bebidas', 'Bebidas y refrescos'),
                    ('Comida', 'Productos alimenticios'),
                    ('General', 'Productos varios')
                """)
            
            # Verificar y migrar esquema si es necesario
            try:
                cursor.execute("PRAGMA table_info(productos)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Agregar columnas faltantes si es necesario
                if 'categoria' not in column_names and 'categoria_id' in column_names:
                    cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
                    cursor.execute("""
                        UPDATE productos 
                        SET categoria = CASE 
                            WHEN categoria_id = 1 THEN 'Chascas'
                            WHEN categoria_id = 2 THEN 'Bebidas' 
                            WHEN categoria_id = 3 THEN 'Comida'
                            ELSE 'General'
                        END
                        WHERE categoria IS NULL OR categoria = 'General'
                    """)
                
                if 'descripcion' not in column_names:
                    cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT")
                
                if 'codigo_barras' not in column_names:
                    cursor.execute("ALTER TABLE productos ADD COLUMN codigo_barras TEXT")
                    
                if 'fecha_modificacion' not in column_names:
                    cursor.execute("ALTER TABLE productos ADD COLUMN fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
            except Exception as e:
                logger.warning(f"Error migrando esquema: {e}")
            
            # Insertar productos de ejemplo si no existen
            cursor.execute("SELECT COUNT(*) FROM productos")
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute("""
                        INSERT INTO productos (nombre, precio, categoria, stock, descripcion, activo) 
                        VALUES 
                        ('Chasca Original', 15.50, 'Chascas', 100, 'Chasca tradicional', 1),
                        ('Chasca Especial', 18.00, 'Chascas', 80, 'Chasca con ingredientes especiales', 1),
                        ('Coca Cola 600ml', 12.00, 'Bebidas', 50, 'Refresco de cola', 1),
                        ('Agua Natural 500ml', 8.00, 'Bebidas', 75, 'Agua purificada', 1),
                        ('Papas Fritas', 10.00, 'Comida', 60, 'Papas fritas caseras', 1),
                        ('Sandwich Mixto', 22.00, 'Comida', 30, 'Sandwich de jamón y queso', 1),
                        ('Dulces Variados', 5.00, 'General', 200, 'Dulces surtidos', 1),
                        ('Cigarros', 25.00, 'General', 40, 'Cigarrillos', 1)
                    """)
                    print("✅ Productos de ejemplo insertados en base de datos local")
                except Exception as e:
                    logger.warning(f"Error insertando productos de ejemplo: {e}")
            
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
    
    def _get_remote_schema(self, table_name: str) -> Dict:
        """Obtener esquema de tabla remota y cachear"""
        if table_name in self.remote_schema_cache:
            return self.remote_schema_cache[table_name]
        
        try:
            database_url = os.getenv('DATABASE_URL')
            with psycopg2.connect(database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    columns = cursor.fetchall()
                    schema = {col['column_name']: col['data_type'] for col in columns}
                    self.remote_schema_cache[table_name] = schema
                    return schema
        except Exception as e:
            logger.error(f"Error obteniendo esquema de {table_name}: {e}")
            return {}
    
    def _adapt_query_for_remote(self, query: str, table_context: str = None) -> str:
        """Adaptar consulta para esquema remoto"""
        # Adaptaciones específicas conocidas
        adaptations = {
            # Problemas de tipo boolean
            "WHERE activo = 1": "WHERE activo = TRUE",
            "WHERE activo = 0": "WHERE activo = FALSE", 
            "SET activo = 1": "SET activo = TRUE",
            "SET activo = 0": "SET activo = FALSE",
            
            # Relaciones de categoría
            "categoria_id": "categoria",
            "LEFT JOIN categorias c ON p.categoria_id = c.id": "LEFT JOIN categorias c ON p.categoria = c.nombre",
            
            # Nombres de tablas
            "items_venta": "detalle_ventas",
        }
        
        adapted_query = query
        for old, new in adaptations.items():
            adapted_query = adapted_query.replace(old, new)
        
        return adapted_query
    
    def _adapt_params_for_remote(self, params: tuple, table_name: str) -> tuple:
        """Adaptar parámetros para esquema remoto"""
        if not params:
            return params
        
        # Convertir valores booleanos para PostgreSQL
        adapted_params = []
        for param in params:
            if isinstance(param, (int, bool)) and param in (0, 1, True, False):
                # Para campos activo, convertir a boolean
                adapted_params.append(bool(param))
            else:
                adapted_params.append(param)
        
        return tuple(adapted_params)
    
    @contextmanager
    def get_connection(self, prefer_remote: bool = True) -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
        """Obtener conexión a base de datos (remota si es posible, local como fallback)"""
        
        if prefer_remote and self.check_database_connection():
            # Intentar conexión remota
            try:
                database_url = os.getenv('DATABASE_URL')
                conn = psycopg2.connect(database_url)
                conn.autocommit = False
                logger.info("🌐 Usando base de datos remota (PostgreSQL)")
                yield conn
                return
            except Exception as e:
                logger.warning(f"Error en conexión remota, usando local: {e}")
        
        # Usar base de datos local
        logger.info("💾 Usando base de datos local (SQLite)")
        with sqlite3.connect(self.local_db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn
    
    def execute_query(self, query: str, params: tuple = (), prefer_remote: bool = True) -> List[Dict[str, Any]]:
        """Ejecutar consulta de lectura con adaptación automática"""
        try:
            with self.get_connection(prefer_remote) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL - adaptar consulta
                    adapted_query = self._adapt_query_for_remote(query)
                    adapted_params = self._adapt_params_for_remote(params, "")
                    
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        cursor.execute(adapted_query, adapted_params)
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
            # En caso de error, intentar con base local
            if prefer_remote:
                logger.info("Reintentando con base de datos local...")
                return self.execute_query(query, params, prefer_remote=False)
            return []
    
    def execute_update(self, query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
        """Ejecutar consulta de escritura con cola de sincronización"""
        try:
            with self.get_connection(prefer_remote=True) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL - adaptar consulta
                    adapted_query = self._adapt_query_for_remote(query)
                    adapted_params = self._adapt_params_for_remote(params, sync_data.get('table', '') if sync_data else '')
                    
                    with conn.cursor() as cursor:
                        cursor.execute(adapted_query, adapted_params)
                        conn.commit()
                        # PostgreSQL no siempre tiene lastrowid
                        if cursor.rowcount > 0:
                            try:
                                cursor.execute("SELECT lastval()")
                                return cursor.fetchone()[0]
                            except:
                                return cursor.rowcount
                        return None
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
        """Sincronizar inserción con adaptaciones"""
        # Adaptar nombres de tabla
        if table_name == 'items_venta':
            table_name = 'detalle_ventas'
        
        # Adaptar datos
        adapted_data = {}
        for key, value in data.items():
            if key == 'categoria_id' and table_name == 'productos':
                # Obtener nombre de categoría en lugar de ID
                adapted_data['categoria'] = value  # Asumir que ya es nombre
            elif key in ['activo'] and isinstance(value, int):
                adapted_data[key] = bool(value)
            else:
                adapted_data[key] = value
        
        columns = ', '.join(adapted_data.keys())
        placeholders = ', '.join(['%s'] * len(adapted_data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(adapted_data.values()))
    
    def _sync_update(self, cursor, table_name: str, data: Dict):
        """Sincronizar actualización con adaptaciones"""
        if table_name == 'items_venta':
            table_name = 'detalle_ventas'
        
        adapted_data = {}
        for key, value in data.items():
            if key == 'categoria_id' and table_name == 'productos':
                adapted_data['categoria'] = value
            elif key in ['activo'] and isinstance(value, int):
                adapted_data[key] = bool(value)
            else:
                adapted_data[key] = value
        
        set_clause = ', '.join([f"{k} = %s" for k in adapted_data.keys() if k != 'id'])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        values = [v for k, v in adapted_data.items() if k != 'id'] + [adapted_data['id']]
        cursor.execute(query, values)
    
    def _sync_delete(self, cursor, table_name: str, data: Dict):
        """Sincronizar eliminación"""
        if table_name == 'items_venta':
            table_name = 'detalle_ventas'
        
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

# Instancia global (se crea solo cuando es necesaria)
_db_adapter = None

def get_adapter():
    """Obtener instancia del adaptador (lazy loading)"""
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = DatabaseAdapter()
    return _db_adapter

# Funciones de compatibilidad
def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Función de compatibilidad para consultas"""
    return get_adapter().execute_query(query, params)

def execute_update(query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
    """Función de compatibilidad para actualizaciones"""
    return get_adapter().execute_update(query, params, sync_data)

@contextmanager
def get_db_connection() -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
    """Función de compatibilidad para conexiones"""
    with get_adapter().get_connection() as conn:
        yield conn

def ensure_products_exist():
    """Asegurar que existen productos en la base de datos"""
    try:
        productos = execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = 1")
        if productos and productos[0]['count'] == 0:
            # Si no hay productos activos, insertar algunos de ejemplo
            execute_update("""
                INSERT INTO productos (nombre, precio, categoria, stock, descripcion, activo) 
                VALUES 
                ('Chasca Original', 15.50, 'Chascas', 100, 'Chasca tradicional', 1),
                ('Chasca Especial', 18.00, 'Chascas', 80, 'Chasca con ingredientes especiales', 1),
                ('Coca Cola 600ml', 12.00, 'Bebidas', 50, 'Refresco de cola', 1),
                ('Agua Natural 500ml', 8.00, 'Bebidas', 75, 'Agua purificada', 1)
            """)
            print("✅ Productos de ejemplo insertados")
        return True
    except Exception as e:
        print(f"Error en ensure_products_exist: {e}")
        return False

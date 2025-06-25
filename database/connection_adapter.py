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
from decimal import Decimal
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
        self.sync_enabled = True  # HABILITADO para operaciones híbridas
        self.remote_schema_cache = {}
        self.remote_available = False
        self.last_sync_attempt = None
        self._create_local_structure()
        self._validate_remote_structure()
        self._start_sync_thread()
        
    def _validate_remote_structure(self):
        """Validar y analizar estructura completa de PostgreSQL"""
        try:
            logger.info("🔍 Validando estructura de base de datos remota...")
            
            render_conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                cursor_factory=RealDictCursor
            )
            
            cursor = render_conn.cursor()
            
            # 1. Obtener todas las tablas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            logger.info(f"📊 Tablas encontradas en PostgreSQL: {tables}")
            
            # 2. Analizar estructura de cada tabla
            self.remote_schema_cache = {}
            for table in tables:
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cursor.fetchall()
                self.remote_schema_cache[table] = {
                    'columns': {col['column_name']: {
                        'type': col['data_type'],
                        'nullable': col['is_nullable'] == 'YES',
                        'default': col['column_default'],
                        'max_length': col['character_maximum_length']
                    } for col in columns},
                    'column_names': [col['column_name'] for col in columns]
                }
                
                logger.info(f"📋 Tabla {table}: {len(columns)} columnas")
                for col in columns:
                    logger.info(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
            # 3. Verificar datos existentes
            cursor.execute("SELECT COUNT(*) as count FROM productos")
            productos_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM categorias")
            categorias_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM ventas")
            ventas_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM detalle_ventas")
            detalles_count = cursor.fetchone()['count']
            
            logger.info(f"📈 Datos en PostgreSQL:")
            logger.info(f"   - Productos: {productos_count}")
            logger.info(f"   - Categorías: {categorias_count}")
            logger.info(f"   - Ventas: {ventas_count}")
            logger.info(f"   - Detalles de venta: {detalles_count}")
            
            # 4. Sincronizar datos si es necesario
            if productos_count > 0:
                self._sync_from_render_complete()
            
            cursor.close()
            render_conn.close()
            
            self.remote_available = True
            logger.info("✅ Validación de estructura remota completada exitosamente")
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo validar estructura remota: {e}")
            self.remote_available = False
            
            # Continuar con datos locales si no hay conexión remota
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM productos")
                if cursor.fetchone()[0] == 0:
                    self._insert_sample_products(cursor)
                    conn.commit()
                    logger.info("💾 Usando datos de ejemplo en base local")
    
    def _sync_from_render_complete(self):
        """Sincronización completa y robusta desde Render"""
        try:
            logger.info("🔄 Iniciando sincronización completa desde PostgreSQL...")
            
            render_conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                cursor_factory=RealDictCursor
            )
            
            with sqlite3.connect(self.local_db_path) as local_conn:
                render_cursor = render_conn.cursor()
                local_cursor = local_conn.cursor()
                
                # 1. Sincronizar productos
                logger.info("📦 Sincronizando productos...")
                render_cursor.execute("SELECT * FROM productos ORDER BY id")
                productos = render_cursor.fetchall()
                
                local_cursor.execute("DELETE FROM productos")
                for prod in productos:
                    local_cursor.execute("""
                        INSERT INTO productos 
                        (id, nombre, precio, categoria, stock, descripcion, codigo_barras, activo, fecha_creacion, fecha_modificacion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prod['id'], prod['nombre'], float(prod['precio']),
                        prod['categoria'] or 'General', prod['stock'] or 0,
                        prod['descripcion'] or '', prod['codigo_barras'] or '',
                        1 if prod['activo'] else 0, prod['fecha_creacion'], prod['fecha_modificacion']
                    ))
                logger.info(f"✅ {len(productos)} productos sincronizados")
                
                # 2. Sincronizar categorías
                logger.info("🏷️ Sincronizando categorías...")
                try:
                    render_cursor.execute("SELECT * FROM categorias ORDER BY id")
                    categorias = render_cursor.fetchall()
                    
                    local_cursor.execute("DELETE FROM categorias")
                    for cat in categorias:
                        local_cursor.execute("""
                            INSERT INTO categorias (id, nombre, descripcion, activo)
                            VALUES (?, ?, ?, ?)
                        """, (cat['id'], cat['nombre'], cat.get('descripcion', ''), 1 if cat.get('activo', True) else 0))
                    logger.info(f"✅ {len(categorias)} categorías sincronizadas")
                except Exception as e:
                    logger.warning(f"⚠️ Error sincronizando categorías: {e}")
                    # Crear categorías desde productos si no existe tabla categorias
                    render_cursor.execute("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL")
                    categorias_productos = render_cursor.fetchall()
                    
                    local_cursor.execute("DELETE FROM categorias")
                    for i, cat in enumerate(set(c['categoria'] for c in categorias_productos if c['categoria'])):
                        local_cursor.execute("""
                            INSERT INTO categorias (id, nombre, descripcion, activo)
                            VALUES (?, ?, ?, ?)
                        """, (i+1, cat, f'Categoría {cat}', 1))
                    logger.info(f"✅ {len(categorias_productos)} categorías creadas desde productos")
                
                # 3. Sincronizar vendedores
                logger.info("👤 Sincronizando vendedores...")
                try:
                    render_cursor.execute("SELECT * FROM vendedores ORDER BY id")
                    vendedores = render_cursor.fetchall()
                    
                    local_cursor.execute("DELETE FROM vendedores")
                    for vend in vendedores:
                        local_cursor.execute("""
                            INSERT INTO vendedores (id, nombre, activo)
                            VALUES (?, ?, ?)
                        """, (vend['id'], vend['nombre'], 1 if vend.get('activo', True) else 0))
                    logger.info(f"✅ {len(vendedores)} vendedores sincronizados")
                except Exception as e:
                    logger.warning(f"⚠️ Error sincronizando vendedores: {e}")
                
                # 4. Sincronizar ventas (últimas 50)
                logger.info("💰 Sincronizando ventas recientes...")
                try:
                    render_cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 50")
                    ventas = render_cursor.fetchall()
                    
                    local_cursor.execute("DELETE FROM ventas")
                    for venta in ventas:
                        local_cursor.execute("""
                            INSERT INTO ventas (id, fecha, total, metodo_pago, vendedor, observaciones, descuento, impuestos)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            venta['id'], venta['fecha'], float(venta['total']),
                            venta.get('metodo_pago', 'Efectivo'), venta.get('vendedor', 'Sistema'),
                            venta.get('observaciones', ''), float(venta.get('descuento', 0)), float(venta.get('impuestos', 0))
                        ))
                    logger.info(f"✅ {len(ventas)} ventas sincronizadas")
                    
                    # 5. Sincronizar detalles de ventas
                    if ventas:
                        venta_ids = [v['id'] for v in ventas]
                        placeholders = ','.join(['%s'] * len(venta_ids))
                        render_cursor.execute(f"SELECT * FROM detalle_ventas WHERE venta_id IN ({placeholders})", venta_ids)
                        detalles = render_cursor.fetchall()
                        
                        local_cursor.execute("DELETE FROM detalle_ventas")
                        for detalle in detalles:
                            subtotal = float(detalle['cantidad']) * float(detalle['precio_unitario'])
                            local_cursor.execute("""
                                INSERT INTO detalle_ventas (id, venta_id, producto_id, cantidad, precio_unitario, subtotal)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                detalle['id'], detalle['venta_id'], detalle['producto_id'],
                                detalle['cantidad'], float(detalle['precio_unitario']), subtotal
                            ))
                        logger.info(f"✅ {len(detalles)} detalles de venta sincronizados")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error sincronizando ventas: {e}")
                
                local_conn.commit()
                logger.info("🎉 Sincronización completa finalizada exitosamente")
                
            render_cursor.close()
            render_conn.close()
            
            self.last_sync_attempt = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización completa: {e}")
            raise
        
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
                    subtotal DECIMAL(10,2) NOT NULL,
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
                
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    rol TEXT DEFAULT 'vendedor',
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insertar datos por defecto si no existen
            cursor.execute("SELECT COUNT(*) FROM vendedores")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO vendedores (nombre, activo) 
                    VALUES ('Sistema', 1), ('Vendedor 1', 1)
                """)
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO usuarios (nombre, email, rol, activo) 
                    VALUES 
                    ('Administrador', 'admin@michaska.com', 'admin', 1),
                    ('Vendedor 1', 'vendedor1@michaska.com', 'vendedor', 1)
                """)
            
            cursor.execute("SELECT COUNT(*) FROM categorias")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO categorias (nombre, descripcion) 
                    VALUES 
                    ('Empapelados', 'Productos empapelados'),
                    ('Elotes', 'Elotes y derivados'),
                    ('Especialidades', 'Especialidades de la casa'),
                    ('Bebidas', 'Bebidas y refrescos'),
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
                            WHEN categoria_id = 1 THEN 'Empapelados'
                            WHEN categoria_id = 2 THEN 'Elotes' 
                            WHEN categoria_id = 3 THEN 'Especialidades'
                            WHEN categoria_id = 4 THEN 'Bebidas'
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
                
                # Verificar y agregar columna subtotal en detalle_ventas
                cursor.execute("PRAGMA table_info(detalle_ventas)")
                detalle_columns = cursor.fetchall()
                detalle_column_names = [col[1] for col in detalle_columns]
                
                if 'subtotal' not in detalle_column_names:
                    cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN subtotal DECIMAL(10,2)")
                    # Actualizar registros existentes con subtotal calculado
                    cursor.execute("""
                        UPDATE detalle_ventas 
                        SET subtotal = cantidad * precio_unitario 
                        WHERE subtotal IS NULL
                    """)
                
            except Exception as e:
                logger.warning(f"Error migrando esquema: {e}")
            
            # Intentar sincronizar con Render si hay conexión
            try:
                if self.check_internet_connection():
                    self._sync_from_render()
            except Exception as e:
                logger.warning(f"No se pudo sincronizar con Render: {e}")
                # Insertar productos de ejemplo si la BD está vacía
                cursor.execute("SELECT COUNT(*) FROM productos")
                if cursor.fetchone()[0] == 0:
                    self._insert_sample_products(cursor)
                    
            conn.commit()
    
    def _sync_from_render(self):
        """Sincronizar datos desde Render"""
        try:
            # Conectar a Render
            render_conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                cursor_factory=RealDictCursor
            )
            
            with sqlite3.connect(self.local_db_path) as local_conn:
                render_cursor = render_conn.cursor()
                local_cursor = local_conn.cursor()
                
                # Sincronizar productos
                render_cursor.execute("SELECT * FROM productos WHERE activo = true ORDER BY id")
                productos = render_cursor.fetchall()
                
                # Limpiar productos existentes
                local_cursor.execute("DELETE FROM productos")
                
                for prod in productos:
                    local_cursor.execute("""
                        INSERT INTO productos 
                        (id, nombre, precio, categoria, stock, descripcion, codigo_barras, activo, fecha_creacion, fecha_modificacion)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prod['id'],
                        prod['nombre'],
                        float(prod['precio']),
                        prod['categoria'] or 'General',
                        prod['stock'] or 0,
                        prod['descripcion'] or '',
                        prod['codigo_barras'] or '',
                        1,
                        prod['fecha_creacion'],
                        prod['fecha_modificacion']
                    ))
                
                # Sincronizar categorías desde productos
                render_cursor.execute("SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL")
                categorias = render_cursor.fetchall()
                
                local_cursor.execute("DELETE FROM categorias")  
                categorias_unicas = set()
                for cat in categorias:
                    if cat['categoria'] and cat['categoria'] not in categorias_unicas:
                        categorias_unicas.add(cat['categoria'])
                        local_cursor.execute("""
                            INSERT INTO categorias (nombre, descripcion, activo)
                            VALUES (?, ?, ?)
                        """, (cat['categoria'], f'Categoría {cat["categoria"]}', 1))
                
                # Sincronizar vendedores si existen
                try:
                    render_cursor.execute("SELECT * FROM vendedores ORDER BY id")
                    vendedores = render_cursor.fetchall()
                    
                    local_cursor.execute("DELETE FROM vendedores")
                    for vend in vendedores:
                        local_cursor.execute("""
                            INSERT INTO vendedores (id, nombre, activo)
                            VALUES (?, ?, ?)
                        """, (vend['id'], vend['nombre'], 1))
                except:
                    pass  # Si no hay tabla vendedores, usar los por defecto
                
                local_conn.commit()
                logger.info(f"✅ Sincronizados {len(productos)} productos desde Render")
                
            render_cursor.close()
            render_conn.close()
            
        except Exception as e:
            logger.warning(f"Error sincronizando desde Render: {e}")
            raise
    
    def _insert_sample_products(self, cursor):
        """Insertar productos de ejemplo si no hay datos"""
        try:
            cursor.execute("""
                INSERT INTO productos (nombre, precio, categoria, stock, descripcion, activo) 
                VALUES 
                ('Salchicha', 90.00, 'Empapelados', 20, 'Empapelado de salchicha', 1),
                ('Carnes Frías', 110.00, 'Empapelados', 20, 'Empapelado de carnes frías', 1),
                ('Elote Crunch', 40.00, 'Elotes', 25, 'Elote con topping crunch', 1),
                ('Chorriada Chica', 65.00, 'Especialidades', 15, 'Chorriada tamaño chico', 1),
                ('Chorriada Mediana', 85.00, 'Especialidades', 15, 'Chorriada tamaño mediano', 1),
                ('Coca Cola', 25.00, 'Bebidas', 50, 'Refresco de cola', 1),
                ('Agua Natural', 15.00, 'Bebidas', 75, 'Agua purificada', 1),
                ('Nachos', 35.00, 'General', 30, 'Nachos con queso', 1)
            """)
            logger.info("✅ Productos de ejemplo insertados en base de datos local")
        except Exception as e:
            logger.warning(f"Error insertando productos de ejemplo: {e}")
    
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
    
    def _adapt_query_for_remote(self, query: str) -> str:
        """Adaptar consulta SQL para compatibilidad PostgreSQL/SQLite"""
        
        # Conversiones específicas de funciones de fecha
        adaptations = {
            # SQLite → PostgreSQL
            "datetime('now', '-7 days')": "CURRENT_DATE - INTERVAL '7 days'",
            "DATE('now', '-7 days')": "CURRENT_DATE - INTERVAL '7 days'",
            "datetime('now')": "NOW()",
            "DATE(fecha)": "fecha::date",
            # Conversiones de boolean comparisons
            "WHERE activo = 1": "WHERE activo = true",
            "WHERE activo = 0": "WHERE activo = false",
            "activo = 1": "activo = true",
            "activo = 0": "activo = false",
        }
        
        adapted_query = query
        for sqlite_func, postgres_func in adaptations.items():
            adapted_query = adapted_query.replace(sqlite_func, postgres_func)
        
        return adapted_query

    def _convert_to_postgres_params(self, query: str, param_count: int = None) -> str:
        """Convertir parámetros SQLite (?) a PostgreSQL ($1, $2, $3, etc.) con validación"""
        if not query or '?' not in query:
            return query
        
        # Contar parámetros reales
        actual_param_count = query.count('?')
        
        if param_count is not None and actual_param_count != param_count:
            logger.warning(f"⚠️ Discrepancia de parámetros: query tiene {actual_param_count}, esperados {param_count}")
        
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
        
        logger.debug(f"🔄 Query convertida: {actual_param_count} parámetros")
        return result

    def _adapt_params_for_remote(self, params: tuple, table_name: str) -> tuple:
        """Adaptar parámetros para PostgreSQL"""
        if not params:
            return params
        
        adapted_params = []
        for param in params:
            # Convertir tipos Decimal a float
            if isinstance(param, Decimal):
                adapted_params.append(float(param))
            # Convertir valores booleanos a enteros para PostgreSQL
            elif isinstance(param, bool):
                adapted_params.append(int(param))
            # Convertir fechas si es necesario
            elif isinstance(param, str) and table_name in ['ventas', 'productos'] and 'fecha' in str(param):
                adapted_params.append(param)
            else:
                adapted_params.append(param)
        
        return tuple(adapted_params)
    
    def _convert_params_for_sqlite(self, params: tuple) -> tuple:
        """Convertir parámetros para SQLite (manejar Decimal y otros tipos)"""
        converted_params = []
        for param in params:
            if isinstance(param, Decimal):
                converted_params.append(float(param))
            else:
                converted_params.append(param)
        return tuple(converted_params)
    
    @contextmanager
    def get_connection(self, prefer_remote: bool = True) -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
        """Obtener conexión híbrida inteligente"""
        
        # Si se prefiere remota Y está disponible Y hay internet
        if prefer_remote and self.remote_available and self.check_internet_connection():
            render_conn = None
            try:
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432),
                    cursor_factory=RealDictCursor
                )
                logger.info("🌐 Usando base de datos remota (PostgreSQL)")
                try:
                    yield render_conn
                finally:
                    if render_conn:
                        render_conn.close()
                return
            except Exception as e:
                logger.warning(f"⚠️ Error en conexión remota, fallback a local: {e}")
                self.remote_available = False
                if render_conn:
                    try:
                        render_conn.close()
                    except:
                        pass
        
        # Usar base de datos local como fallback
        logger.info("💾 Usando base de datos local (SQLite)")
        with sqlite3.connect(self.local_db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn
    
    def execute_query(self, query: str, params: tuple = (), prefer_remote: bool = True) -> List[Dict[str, Any]]:
        """Ejecutar consulta con modo híbrido inteligente"""
        
        # Verificar si es una consulta que solo debe ejecutarse localmente
        if self._is_local_only_query(query):
            prefer_remote = False
            
        try:
            with self.get_connection(prefer_remote) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL - adaptar consulta y parámetros
                    try:
                        adapted_query = self._adapt_query_for_remote(query)
                        postgres_query = self._convert_to_postgres_params(adapted_query)
                        adapted_params = self._adapt_params_for_remote(params, "")
                        
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute(postgres_query, adapted_params)
                            result = cursor.fetchall()
                            return [dict(row) for row in result]
                    except Exception as e:
                        logger.warning(f"⚠️ Error en consulta remota: {e}")
                        if not prefer_remote:
                            raise  # Si ya estamos en local, relanzar error
                        # Fallback a local si hay error en remoto
                        logger.info("🔄 Reintentando con base de datos local...")
                        return self.execute_query(query, params, prefer_remote=False)
                else:
                    # SQLite - usar consulta original
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"❌ Error ejecutando consulta '{query[:50]}...': {e}")
            
            # Fallback final a local si aún no se ha intentado
            if prefer_remote and not self._is_local_only_query(query):
                try:
                    logger.info("🔄 Último intento con base de datos local...")
                    return self.execute_query(query, params, prefer_remote=False)
                except Exception as fallback_error:
                    logger.error(f"❌ Error también en fallback local: {fallback_error}")
            
            return []
    
    def execute_update(self, query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
        """Ejecutar escritura con sincronización híbrida robusta"""
        local_result = None
        remote_result = None
        operation_success = False
        
        # 1. Siempre escribir en local primero (para garantizar disponibilidad)
        try:
            logger.info("💾 Ejecutando operación en base de datos local...")
            
            # Convertir parámetros para SQLite
            local_params = self._convert_params_for_sqlite(params)
            
            with sqlite3.connect(self.local_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, local_params)
                conn.commit()
                local_result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                operation_success = True
                logger.info(f"✅ Operación local exitosa (ID/Rows: {local_result})")
        except Exception as e:
            logger.error(f"❌ Error en operación local: {e}")
            return None
        
        # 2. Intentar ejecutar en remoto si está disponible
        if self.remote_available and self.check_internet_connection():
            try:
                logger.info("🌐 Ejecutando operación en base de datos remota...")
                
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
                
                with render_conn.cursor() as cursor:
                    adapted_query = self._adapt_query_for_remote(query)
                    postgres_query = self._convert_to_postgres_params(adapted_query)
                    adapted_params = self._adapt_params_for_remote(params, sync_data.get('table', '') if sync_data else '')
                    
                    cursor.execute(postgres_query, adapted_params)
                    render_conn.commit()
                    remote_result = cursor.rowcount
                    logger.info(f"✅ Operación remota exitosa (Rows: {remote_result})")
                
                render_conn.close()
                
            except Exception as e:
                logger.warning(f"⚠️ Error en operación remota, agregando a cola: {e}")
                # Agregar a cola de sincronización si falla operación remota
                if sync_data and self.sync_enabled:
                    self._add_to_sync_queue_robust(sync_data, query, params)
        else:
            # Agregar a cola de sincronización para cuando haya conexión
            if sync_data and self.sync_enabled:
                self._add_to_sync_queue_robust(sync_data, query, params)
                logger.info("📝 Operación agregada a cola de sincronización")
        
        return local_result
    
    def _add_to_sync_queue_robust(self, sync_data: Dict, original_query: str, original_params: tuple):
        """Agregar operación a la cola de sincronización con contexto completo"""
        try:
            # Limpiar datos para serialización JSON
            cleaned_data = self._clean_data_for_json(sync_data.get('data', {}))
            cleaned_params = self._clean_params_for_json(original_params)
            
            # Enriquecer datos de sincronización con contexto
            enhanced_sync_data = {
                'table': sync_data.get('table', ''),
                'operation': sync_data.get('operation', ''),
                'data': cleaned_data,
                'original_query': original_query,
                'original_params': cleaned_params,
                'timestamp': datetime.now().isoformat()
            }
            
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data, timestamp, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                """, (
                    enhanced_sync_data['table'], 
                    enhanced_sync_data['operation'], 
                    json.dumps(enhanced_sync_data)
                ))
                conn.commit()
                logger.info(f"📝 Operación {enhanced_sync_data['operation']} en {enhanced_sync_data['table']} agregada a cola")
        except Exception as e:
            logger.error(f"❌ Error agregando a cola de sincronización: {e}")
    
    def _clean_data_for_json(self, data: Dict) -> Dict:
        """Limpiar datos para que sean serializables en JSON"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                cleaned[key] = float(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, bool):
                # Convertir booleanos a enteros para PostgreSQL
                cleaned[key] = 1 if value else 0
            elif hasattr(value, '__dict__'):
                # Objeto complejo - convertir a dict simple
                cleaned[key] = str(value)
            else:
                cleaned[key] = value
        return cleaned
    
    def _clean_params_for_json(self, params: tuple) -> list:
        """Limpiar parámetros para que sean serializables en JSON"""
        if not params:
            return []
        
        cleaned = []
        for param in params:
            if isinstance(param, Decimal):
                cleaned.append(float(param))
            elif isinstance(param, datetime):
                cleaned.append(param.isoformat())
            elif isinstance(param, bool):
                # Convertir booleanos a enteros para PostgreSQL
                cleaned.append(1 if param else 0)
            elif hasattr(param, '__dict__'):
                cleaned.append(str(param))
            else:
                cleaned.append(param)
        return cleaned
    
    def execute_crud_operation(self, operation: str, table: str, data: Dict, where_clause: str = None) -> Optional[int]:
        """Ejecutar operación CRUD con sincronización automática"""
        try:
            if operation.upper() == 'INSERT':
                return self._execute_insert(table, data)
            elif operation.upper() == 'UPDATE':
                return self._execute_update(table, data, where_clause)
            elif operation.upper() == 'DELETE':
                return self._execute_delete(table, data, where_clause)
            else:
                logger.error(f"❌ Operación no soportada: {operation}")
                return None
        except Exception as e:
            logger.error(f"❌ Error en operación CRUD {operation}: {e}")
            return None
    
    def _execute_insert(self, table: str, data: Dict) -> Optional[int]:
        """Ejecutar inserción con sincronización"""
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        values = [data[col] for col in columns]
        
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        sync_data = {
            'table': table,
            'operation': 'INSERT',
            'data': data
        }
        
        return self.execute_update(query, tuple(values), sync_data)
    
    def _execute_update(self, table: str, data: Dict, where_clause: str) -> Optional[int]:
        """Ejecutar actualización con sincronización"""
        set_clauses = [f"{col} = ?" for col in data.keys()]
        values = list(data.values())
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        sync_data = {
            'table': table,
            'operation': 'UPDATE',
            'data': data
        }
        
        return self.execute_update(query, tuple(values), sync_data)
    
    def _execute_delete(self, table: str, data: Dict, where_clause: str) -> Optional[int]:
        """Ejecutar eliminación con sincronización"""
        query = f"DELETE FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        sync_data = {
            'table': table,
            'operation': 'DELETE',
            'data': data
        }
        
        return self.execute_update(query, (), sync_data)
    
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
        """Procesar cola de sincronización pendiente con manejo robusto"""
        try:
            with sqlite3.connect(self.local_db_path) as local_conn:
                local_cursor = local_conn.cursor()
                local_cursor.execute("""
                    SELECT id, table_name, operation, data, attempts
                    FROM sync_queue 
                    WHERE status = 'pending' AND attempts < 5
                    ORDER BY timestamp ASC
                    LIMIT 20
                """)
                
                pending_items = local_cursor.fetchall()
                
                if not pending_items:
                    return
                
                logger.info(f"🔄 Sincronizando {len(pending_items)} elementos pendientes")
                
                # Conectar a base de datos remota con URL completa
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
                
                with render_conn.cursor() as remote_cursor:
                    for item in pending_items:
                        try:
                            item_id, table_name, operation, data_json, attempts = item
                            
                            # Deserializar datos del JSON de manera robusta
                            try:
                                parsed_data = json.loads(data_json)
                                
                                # Si es el formato completo con metadata, extraer solo los datos
                                if isinstance(parsed_data, dict) and 'data' in parsed_data:
                                    data = parsed_data['data']
                                else:
                                    data = parsed_data
                                    
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.error(f"❌ Error deserializando JSON para item {item_id}: {e}")
                                logger.error(f"   Datos problemáticos: {data_json[:100]}...")
                                
                                # Marcar como fallido e incrementar intentos - USAR LOCAL CURSOR
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET status = 'failed', attempts = attempts + 1 
                                    WHERE id = ?
                                """, (item_id,))
                                continue
                            
                            success = False
                            
                            if operation == 'INSERT':
                                success = self._sync_insert_robust(remote_cursor, table_name, data)
                            elif operation == 'UPDATE':
                                success = self._sync_update_robust(remote_cursor, table_name, data)
                            elif operation == 'DELETE':
                                success = self._sync_delete_robust(remote_cursor, table_name, data)
                            
                            if success:
                                # Marcar como sincronizado - USAR LOCAL CURSOR
                                local_cursor.execute("""
                                    UPDATE sync_queue 
                                    SET status = 'completed' 
                                    WHERE id = ?
                                """, (item_id,))
                                logger.info(f"✅ Sincronizado: {operation} en {table_name}")
                            else:
                                raise Exception(f"Operación {operation} falló")
                                
                        except Exception as e:
                            logger.error(f"❌ Error sincronizando item {item_id}: {e}")
                            # Actualizar sync_queue - USAR LOCAL CURSOR
                            local_cursor.execute("""
                                UPDATE sync_queue 
                                SET attempts = attempts + 1,
                                    status = CASE WHEN attempts >= 4 THEN 'failed' ELSE 'pending' END
                                WHERE id = ?
                            """, (item_id,))
                    
                    render_conn.commit()
                    local_conn.commit()
                    
                render_conn.close()
                        
        except Exception as e:
            logger.error(f"❌ Error procesando cola de sincronización: {e}")
    
    def _sync_insert_robust(self, cursor, table_name: str, data: Dict) -> bool:
        """Inserción robusta con validación de duplicados"""
        try:
            # Adaptar nombres de tabla
            adapted_table = self._adapt_table_name(table_name)
            
            # Verificar si ya existe (evitar duplicados)
            if 'id' in data:
                cursor.execute(f"SELECT id FROM {adapted_table} WHERE id = %s", (data['id'],))
                if cursor.fetchone():
                    logger.info(f"🔄 Registro {data['id']} ya existe en {adapted_table}, actualizando...")
                    return self._sync_update_robust(cursor, table_name, data)
            
            # Adaptar datos para PostgreSQL
            adapted_data = self._adapt_data_for_remote(data, table_name)
            
            if not adapted_data:
                logger.error("❌ No se pudieron adaptar los datos")
                return False
            
            # Construir query de inserción con validación de tipos
            columns = list(adapted_data.keys())
            placeholders = ['%s'] * len(columns)
            values = []
            
            # Validar y preparar valores
            for col in columns:
                value = adapted_data[col]
                # Convertir diccionarios y listas a JSON string si es necesario
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
            
            query = f"INSERT INTO {adapted_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en inserción robusta: {e}")
            return False
    
    def _sync_update_robust(self, cursor, table_name: str, data: Dict) -> bool:
        """Actualización robusta con verificación de existencia"""
        try:
            adapted_table = self._adapt_table_name(table_name)
            
            if 'id' not in data:
                logger.error("❌ No se puede actualizar sin ID")
                return False
            
            # Verificar si existe el registro
            cursor.execute(f"SELECT id FROM {adapted_table} WHERE id = %s", (data['id'],))
            if not cursor.fetchone():
                logger.info(f"🔄 Registro {data['id']} no existe en {adapted_table}, insertando...")
                return self._sync_insert_robust(cursor, table_name, data)
            
            # Adaptar datos con validación mejorada
            adapted_data = self._adapt_data_for_remote(data, table_name)
            
            if not adapted_data:
                logger.error("❌ No se pudieron adaptar los datos")
                return False
            
            # Construir query de actualización con validación de tipos
            set_clauses = []
            values = []
            
            # Filtrar campos válidos
            metadata_fields = ['original_query', 'original_params', 'timestamp', 'metadata', 'tags', 'sync_status']
            
            for col, value in adapted_data.items():
                if col != 'id' and col not in metadata_fields:
                    # Verificar que no sea expresión SQL
                    if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                        logger.warning(f"⚠️ Campo {col} contiene expresión SQL, omitiendo: {value}")
                        continue
                    
                    set_clauses.append(f"{col} = %s")
                    # Convertir diccionarios y listas a JSON string si es necesario
                    if isinstance(value, (dict, list)):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
            
            # Verificar que hay campos para actualizar
            if not set_clauses:
                logger.warning(f"⚠️ No hay campos válidos para actualizar en {adapted_table}")
                return True  # Considerar exitoso si no hay nada que actualizar
            
            values.append(adapted_data['id'])
            
            query = f"UPDATE {adapted_table} SET {', '.join(set_clauses)} WHERE id = %s"
            cursor.execute(query, values)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en actualización robusta: {e}")
            return False
    
    def _sync_delete_robust(self, cursor, table_name: str, data: Dict) -> bool:
        """Eliminación robusta con verificación"""
        try:
            adapted_table = self._adapt_table_name(table_name)
            
            if 'id' not in data:
                logger.error("❌ No se puede eliminar sin ID")
                return False
            
            query = f"DELETE FROM {adapted_table} WHERE id = %s"
            cursor.execute(query, (data['id'],))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en eliminación robusta: {e}")
            return False
    
    def _adapt_table_name(self, table_name: str) -> str:
        """Adaptar nombres de tabla para PostgreSQL"""
        adaptations = {
            'items_venta': 'detalle_ventas'
        }
        return adaptations.get(table_name, table_name)
    
    def _adapt_data_for_remote(self, data: Dict, table_name: str) -> Dict:
        """Adaptar datos completos para PostgreSQL con manejo robusto"""
        if not isinstance(data, dict):
            logger.error(f"❌ Datos no son un diccionario: {type(data)}")
            return {}
        
        adapted_data = {}
        
        try:
            for key, value in data.items():
                # Saltear valores None o campos de metadata
                if key in ['original_query', 'original_params', 'timestamp', 'metadata', 'tags'] or value is None:
                    continue
                
                # Convertir Decimal a float siempre
                if isinstance(value, Decimal):
                    value = float(value)
                
                # Adaptaciones específicas por tabla y campo
                if table_name == 'productos':
                    if key == 'categoria_id':
                        # Convertir ID de categoría a nombre si es necesario
                        if isinstance(value, int):
                            adapted_data['categoria'] = self._get_categoria_name(value)
                        else:
                            adapted_data['categoria'] = str(value) if value else 'General'
                    elif key == 'activo':
                        # Convertir boolean a entero para PostgreSQL
                        if isinstance(value, bool):
                            adapted_data[key] = 1 if value else 0
                        elif isinstance(value, str):
                            adapted_data[key] = 1 if value.lower() in ('true', '1', 'yes', 'on') else 0
                        else:
                            # Para valores numéricos
                            try:
                                adapted_data[key] = 1 if int(value) else 0
                            except:
                                adapted_data[key] = 1 if bool(value) else 0
                    elif key == 'precio':
                        adapted_data[key] = float(value) if value is not None else 0.0
                    elif key in ['stock', 'stock_minimo']:
                        # Verificar si es una expresión SQL (contiene operadores o funciones)
                        if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                            logger.warning(f"⚠️ Omitiendo campo {key} con expresión SQL: {value}")
                            continue  # Saltar este campo
                        else:
                            try:
                                adapted_data[key] = int(float(value)) if value is not None else 0
                            except (ValueError, TypeError):
                                adapted_data[key] = 0
                    # Eliminar campos que no existen en el schema remoto
                    elif key not in ['stock_reduction', 'last_updated', 'sync_status']:
                        adapted_data[key] = value
                
                elif table_name in ['categorias', 'vendedores']:
                    if key == 'activo':
                        # Convertir boolean a entero para PostgreSQL
                        if isinstance(value, bool):
                            adapted_data[key] = 1 if value else 0
                        elif isinstance(value, str):
                            adapted_data[key] = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            adapted_data[key] = bool(int(value)) if str(value).isdigit() else bool(value)
                    else:
                        adapted_data[key] = value
                
                elif table_name == 'ventas':
                    if key in ['total', 'descuento', 'impuestos']:
                        adapted_data[key] = float(value) if value is not None else 0.0
                    elif key == 'vendedor_id':
                        adapted_data[key] = int(value) if value is not None else 1
                    else:
                        adapted_data[key] = value
                
                elif table_name == 'detalle_ventas':
                    if key in ['precio_unitario', 'subtotal']:
                        adapted_data[key] = float(value) if value is not None else 0.0
                    elif key in ['cantidad', 'venta_id', 'producto_id']:
                        # Asegurar que cantidad sea siempre entero, nunca boolean
                        if isinstance(value, bool):
                            adapted_data[key] = 1 if value else 0
                        elif isinstance(value, str):
                            if value.lower() in ('true', 'false'):
                                adapted_data[key] = 1 if value.lower() == 'true' else 0
                            elif any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                                logger.warning(f"⚠️ Omitiendo campo {key} con expresión SQL: {value}")
                                continue  # Saltar este campo
                            else:
                                try:
                                    adapted_data[key] = int(float(value))
                                except (ValueError, TypeError):
                                    adapted_data[key] = 0
                        else:
                            try:
                                adapted_data[key] = int(float(value)) if value is not None else 0
                            except (ValueError, TypeError):
                                adapted_data[key] = 0
                    # Filtrar campos que no existen en el schema remoto
                    elif key not in ['stock_reduction', 'last_updated', 'sync_status']:
                        adapted_data[key] = value
                
                else:
                    # Para cualquier otra tabla, filtrar campos problemáticos
                    if key not in ['stock_reduction', 'last_updated', 'sync_status']:
                        adapted_data[key] = value
        
        except Exception as e:
            logger.error(f"❌ Error adaptando datos para {table_name}: {e}")
            return {}
        
        return adapted_data
    
    def _get_categoria_name(self, categoria_id: int) -> str:
        """Obtener nombre de categoría por ID"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre FROM categorias WHERE id = ?", (categoria_id,))
                result = cursor.fetchone()
                return result[0] if result else 'General'
        except:
            return 'General'
    
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
    
    def _sync_remote_to_local(self) -> bool:
        """Sincronizar cambios remotos a base de datos local"""
        try:
            if not self.check_database_connection():
                logger.warning("No hay conexión remota para sincronizar")
                return False
            
            logger.info("🔄 Sincronización remoto → local (modo básico)")
            
            # Por ahora, implementación básica que verifica conectividad
            # En futuras versiones se puede implementar sincronización bidireccional completa
            render_conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                cursor_factory=RealDictCursor
            )
            
            with render_conn.cursor() as cursor:
                # Test simple para verificar conexión
                cursor.execute("SELECT COUNT(*) FROM productos")
                count = cursor.fetchone()
                logger.info(f"✅ Conexión remota verificada: {count[0] if count else 0} productos")
            
            render_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando remoto a local: {e}")
            return False

    def force_sync(self) -> bool:
        """Forzar sincronización manual bidireccional"""
        if not self.check_database_connection():
            logger.warning("No hay conexión a internet para sincronizar")
            return False
        
        try:
            # 1. Sincronizar pendientes locales a remoto
            logger.info("🔄 Sincronizando cambios locales a remoto...")
            self._process_sync_queue()
            
            # 2. Sincronizar cambios remotos a local
            logger.info("🔄 Sincronizando cambios remotos a local...")
            self._sync_remote_to_local()
            
            logger.info("✅ Sincronización bidireccional completada")
            return True
        except Exception as e:
            logger.error(f"❌ Error en sincronización forzada: {e}")
            return False
    
    def force_sync_now(self) -> bool:
        """Forzar sincronización inmediata solo de pendientes críticos"""
        if not self.check_database_connection():
            logger.warning("No hay conexión a internet para sincronizar")
            return False
        
        try:
            logger.info("⚡ Sincronización inmediata de operaciones críticas...")
            
            # Solo procesar elementos críticos de la cola
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, operation, table_name, data, created_at 
                    FROM sync_queue 
                    WHERE status = 'pending' 
                    ORDER BY created_at 
                    LIMIT 10
                """)
                items = cursor.fetchall()
                
                if items:
                    success_count = 0
                    for item in items:
                        if self._sync_single_item(item):
                            success_count += 1
                    
                    logger.info(f"⚡ Sincronización inmediata: {success_count}/{len(items)} elementos")
                    return success_count > 0
                else:
                    logger.info("⚡ No hay elementos pendientes para sincronizar")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error en sincronización inmediata: {e}")
            return False

    def _sync_single_item(self, item):
        """Sincronizar un solo ítem de la cola"""
        try:
            item_id, operation, table_name, data_json = item
            
            # Deserializar datos
            data = json.loads(data_json)
            
            if operation == 'INSERT':
                return self._sync_insert_robust(None, table_name, data)
            elif operation == 'UPDATE':
                return self._sync_update_robust(None, table_name, data)
            elif operation == 'DELETE':
                return self._sync_delete_robust(None, table_name, data)
            else:
                logger.warning(f"Operación no soportada en cola: {operation}")
                return False
        except Exception as e:
            logger.error(f"Error sincronizando ítem de cola {item_id}: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema híbrido"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'local_db': {
                'available': os.path.exists(self.local_db_path),
                'size_mb': round(os.path.getsize(self.local_db_path) / 1024 / 1024, 2) if os.path.exists(self.local_db_path) else 0,
                'tables': {}
            },
            'remote_db': {
                'available': self.remote_available,
                'last_sync': self.last_sync_attempt.isoformat() if self.last_sync_attempt else None,
                'schema_cached': len(self.remote_schema_cache) > 0
            },
            'internet': self.check_internet_connection(),
            'sync': self.get_sync_status()
        }
        
        # Obtener estadísticas de tablas locales
        if status['local_db']['available']:
            try:
                with sqlite3.connect(self.local_db_path) as conn:
                    cursor = conn.cursor()
                    tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
                    
                    for table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            status['local_db']['tables'][table] = count
                        except:
                            status['local_db']['tables'][table] = 0
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas locales: {e}")
        
        return status
    
    def force_full_sync(self) -> bool:
        """Forzar sincronización completa bidireccional"""
        try:
            logger.info("🔄 Iniciando sincronización completa forzada...")
            
            if not self.remote_available:
                self._validate_remote_structure()
            
            if self.remote_available:
                # Sincronizar desde remoto a local
                self._sync_from_render_complete()
                
                # Procesar cola pendiente (de local a remoto)
                self._process_sync_queue()
                
                logger.info("✅ Sincronización completa forzada exitosa")
                return True
            else:
                logger.warning("⚠️ No se puede sincronizar: base remota no disponible")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en sincronización forzada: {e}")
            return False
    
    def get_sync_status(self) -> Dict:
        """Obtener estado de sincronización mejorado"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'")
                pending = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'completed'")
                completed = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE attempts >= 3")
                failed = cursor.fetchone()[0]
                
                # Obtener operaciones recientes
                cursor.execute("""
                    SELECT table_name, operation, timestamp 
                    FROM sync_queue 
                    WHERE status = 'pending' 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                recent_pending = [dict(zip(['table', 'operation', 'timestamp'], row)) for row in cursor.fetchall()]
                
                return {
                    'enabled': self.sync_enabled,
                    'online': self.is_online,
                    'remote_available': self.remote_available,
                    'pending': pending,
                    'completed': completed,
                    'failed': failed,
                    'recent_pending': recent_pending,
                    'last_sync': self.last_sync_attempt.isoformat() if self.last_sync_attempt else None
                }
        except Exception as e:
            logger.error(f"Error obteniendo estado de sync: {e}")
            return {
                'enabled': False, 'online': False, 'remote_available': False,
                'pending': 0, 'completed': 0, 'failed': 0, 'recent_pending': [], 'last_sync': None
            }
    
    def _is_local_only_query(self, query: str) -> bool:
        """Determinar si una consulta debe ejecutarse solo localmente"""
        if not query:
            return False
            
        local_only_tables = ['sync_queue', 'usuarios']
        query_lower = query.lower().strip()
        
        # Verificar si la consulta menciona tablas que solo existen localmente
        for table in local_only_tables:
            if f' {table} ' in f' {query_lower} ' or f' {table}.' in query_lower:
                return True
        
        return False
    
    def _get_local_table_columns(self, table_name: str) -> set:
        """Obtener columnas que existen en una tabla local"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                return {col[1] for col in columns_info}  # col[1] es el nombre de la columna
        except Exception as e:
            logger.error(f"Error obteniendo columnas de {table_name}: {e}")
            return set()

    def _validate_update_query(self, table_name: str, data: Dict, where_clause: str = None) -> tuple:
        """Validar y construir query UPDATE segura"""
        if not data or not isinstance(data, dict):
            logger.error("❌ Datos inválidos para UPDATE")
            return None, None
        
        # Filtrar campos válidos (no vacíos, no metadata)
        valid_fields = {}
        metadata_fields = ['original_query', 'original_params', 'timestamp', 'metadata', 'tags', 'sync_status']
        
        for key, value in data.items():
            # Saltar campos de metadata y valores None
            if key in metadata_fields or value is None:
                continue
            
            # Saltar campos que contienen expresiones SQL
            if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                logger.warning(f"⚠️ Campo {key} contiene expresión SQL, omitiendo: {value}")
                continue
            
            # Saltar campo 'id' para SET clause pero mantenerlo para WHERE
            if key != 'id':
                valid_fields[key] = value
        
        if not valid_fields:
            logger.warning(f"⚠️ No hay campos válidos para actualizar en {table_name}")
            return None, None
        
        # Construir SET clause
        set_clauses = []
        values = []
        
        for col, value in valid_fields.items():
            set_clauses.append(f"{col} = ?")
            
            # Convertir tipos apropiadamente
            if isinstance(value, Decimal):
                values.append(float(value))
            elif isinstance(value, bool) and table_name in ['productos', 'categorias', 'vendedores']:
                # Convertir boolean a int para campos activo
                values.append(1 if value else 0)
            else:
                values.append(value)
        
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)}"
        
        # Agregar WHERE clause
        if where_clause:
            query += f" WHERE {where_clause}"
        elif 'id' in data:
            query += " WHERE id = ?"
            values.append(data['id'])
        else:
            logger.error("❌ No se puede hacer UPDATE sin WHERE clause")
            return None, None
        
        return query, tuple(values)

    def _convert_boolean_safely(self, value, field_name: str, table_name: str) -> any:
        """Convertir valores boolean de manera segura según contexto"""
        
        # Campos que requieren enteros (no boolean)
        integer_fields = {
            'productos': ['stock', 'cantidad', 'producto_id'],
            'detalle_ventas': ['cantidad', 'venta_id', 'producto_id'],
            'ventas': ['vendedor_id'],
            'categorias': ['id'],
            'vendedores': ['id']
        }
        
        # Campos que requieren boolean (PostgreSQL) o int (SQLite)
        boolean_fields = {
            'productos': ['activo'],
            'categorias': ['activo'],
            'vendedores': ['activo']
        }
        
        if isinstance(value, bool):
            # Si el campo requiere entero y tenemos boolean
            if table_name in integer_fields and field_name in integer_fields[table_name]:
                result = 1 if value else 0
                logger.debug(f"🔄 Boolean→Int: {table_name}.{field_name} {value} → {result}")
                return result
            
            # Si el campo es boolean válido
            elif table_name in boolean_fields and field_name in boolean_fields[table_name]:
                # Para SQLite usar int, para PostgreSQL usar boolean
                result = 1 if value else 0  # Siempre usar int por compatibilidad
                logger.debug(f"🔄 Boolean: {table_name}.{field_name} {value} → {result}")
                return result
            
            else:
                # Campo desconocido, convertir a int por seguridad
                return 1 if value else 0
        
        elif isinstance(value, str):
            # String que representa boolean
            if value.lower() in ('true', '1', 'yes', 'on'):
                return 1 if table_name in integer_fields and field_name in integer_fields[table_name] else 1
            elif value.lower() in ('false', '0', 'no', 'off'):
                return 0
            else:
                # String normal
                return value
        
        # Valor no boolean, retornar tal como está
        return value
    
    @contextmanager
    def get_connection(self, prefer_remote: bool = True) -> Generator[Union[sqlite3.Connection, psycopg2.extensions.connection], None, None]:
        """Obtener conexión híbrida inteligente"""
        
        # Si se prefiere remota Y está disponible Y hay internet
        if prefer_remote and self.remote_available and self.check_internet_connection():
            render_conn = None
            try:
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432),
                    cursor_factory=RealDictCursor
                )
                logger.info("🌐 Usando base de datos remota (PostgreSQL)")
                try:
                    yield render_conn
                finally:
                    if render_conn:
                        render_conn.close()
                return
            except Exception as e:
                logger.warning(f"⚠️ Error en conexión remota, fallback a local: {e}")
                self.remote_available = False
                if render_conn:
                    try:
                        render_conn.close()
                    except:
                        pass
        
        # Usar base de datos local como fallback
        logger.info("💾 Usando base de datos local (SQLite)")
        with sqlite3.connect(self.local_db_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn
    
    def execute_query(self, query: str, params: tuple = (), prefer_remote: bool = True) -> List[Dict[str, Any]]:
        """Ejecutar consulta con modo híbrido inteligente"""
        
        # Verificar si es una consulta que solo debe ejecutarse localmente
        if self._is_local_only_query(query):
            prefer_remote = False
            
        try:
            with self.get_connection(prefer_remote) as conn:
                if isinstance(conn, psycopg2.extensions.connection):
                    # PostgreSQL - adaptar consulta y parámetros
                    try:
                        adapted_query = self._adapt_query_for_remote(query)
                        postgres_query = self._convert_to_postgres_params(adapted_query)
                        adapted_params = self._adapt_params_for_remote(params, "")
                        
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            cursor.execute(postgres_query, adapted_params)
                            result = cursor.fetchall()
                            return [dict(row) for row in result]
                    except Exception as e:
                        logger.warning(f"⚠️ Error en consulta remota: {e}")
                        if not prefer_remote:
                            raise  # Si ya estamos en local, relanzar error
                        # Fallback a local si hay error en remoto
                        logger.info("🔄 Reintentando con base de datos local...")
                        return self.execute_query(query, params, prefer_remote=False)
                else:
                    # SQLite - usar consulta original
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"❌ Error ejecutando consulta '{query[:50]}...': {e}")
            
            # Fallback final a local si aún no se ha intentado
            if prefer_remote and not self._is_local_only_query(query):
                try:
                    logger.info("🔄 Último intento con base de datos local...")
                    return self.execute_query(query, params, prefer_remote=False)
                except Exception as fallback_error:
                    logger.error(f"❌ Error también en fallback local: {fallback_error}")
            
            return []
    
    def execute_update(self, query: str, params: tuple = (), sync_data: Dict = None) -> Optional[int]:
        """Ejecutar escritura con sincronización híbrida robusta"""
        local_result = None
        remote_result = None
        operation_success = False
        
        # 1. Siempre escribir en local primero (para garantizar disponibilidad)
        try:
            logger.info("💾 Ejecutando operación en base de datos local...")
            
            # Convertir parámetros para SQLite
            local_params = self._convert_params_for_sqlite(params)
            
            with sqlite3.connect(self.local_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, local_params)
                conn.commit()
                local_result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                operation_success = True
                logger.info(f"✅ Operación local exitosa (ID/Rows: {local_result})")
        except Exception as e:
            logger.error(f"❌ Error en operación local: {e}")
            return None
        
        # 2. Intentar ejecutar en remoto si está disponible
        if self.remote_available and self.check_internet_connection():
            try:
                logger.info("🌐 Ejecutando operación en base de datos remota...")
                
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
                
                with render_conn.cursor() as cursor:
                    adapted_query = self._adapt_query_for_remote(query)
                    postgres_query = self._convert_to_postgres_params(adapted_query)
                    adapted_params = self._adapt_params_for_remote(params, sync_data.get('table', '') if sync_data else '')
                    
                    cursor.execute(postgres_query, adapted_params)
                    render_conn.commit()
                    remote_result = cursor.rowcount
                    logger.info(f"✅ Operación remota exitosa (Rows: {remote_result})")
                
                render_conn.close()
                
            except Exception as e:
                logger.warning(f"⚠️ Error en operación remota, agregando a cola: {e}")
                # Agregar a cola de sincronización si falla operación remota
                if sync_data and self.sync_enabled:
                    self._add_to_sync_queue_robust(sync_data, query, params)
        else:
            # Agregar a cola de sincronización para cuando haya conexión
            if sync_data and self.sync_enabled:
                self._add_to_sync_queue_robust(sync_data, query, params)
                logger.info("📝 Operación agregada a cola de sincronización")
        
        return local_result
    
    def _add_to_sync_queue_robust(self, sync_data: Dict, original_query: str, original_params: tuple):
        """Agregar operación a la cola de sincronización con contexto completo"""
        try:
            # Limpiar datos para serialización JSON
            cleaned_data = self._clean_data_for_json(sync_data.get('data', {}))
            cleaned_params = self._clean_params_for_json(original_params)
            
            # Enriquecer datos de sincronización con contexto
            enhanced_sync_data = {
                'table': sync_data.get('table', ''),
                'operation': sync_data.get('operation', ''),
                'data': cleaned_data,
                'original_query': original_query,
                'original_params': cleaned_params,
                'timestamp': datetime.now().isoformat()
            }
            
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_queue (table_name, operation, data, timestamp, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                """, (
                    enhanced_sync_data['table'], 
                    enhanced_sync_data['operation'], 
                    json.dumps(enhanced_sync_data)
                ))
                conn.commit()
                logger.info(f"📝 Operación {enhanced_sync_data['operation']} en {enhanced_sync_data['table']} agregada a cola")
        except Exception as e:
            logger.error(f"❌ Error agregando a cola de sincronización: {e}")
    
    def _clean_data_for_json(self, data: Dict) -> Dict:
        """Limpiar datos para que sean serializables en JSON"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                cleaned[key] = float(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, bool):
                # Convertir booleanos a enteros para PostgreSQL
                cleaned[key] = 1 if value else 0
            elif hasattr(value, '__dict__'):
                # Objeto complejo - convertir a dict simple
                cleaned[key] = str(value)
            else:
                cleaned[key] = value
        return cleaned
    
    def _clean_params_for_json(self, params: tuple) -> list:
        """Limpiar parámetros para que sean serializables en JSON"""
        if not params:
            return []
        
        cleaned = []
        for param in params:
            if isinstance(param, Decimal):
                cleaned.append(float(param))
            elif isinstance(param, datetime):
                cleaned.append(param.isoformat())
            elif isinstance(param
"""
Base de datos SQLite para desarrollo local
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator, Dict, Any, List, Optional
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Archivo de base de datos SQLite
DB_FILE = "mi_chas_k_local.db"

@contextmanager
def get_sqlite_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager para conexiones SQLite"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de conexión SQLite: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query_sqlite(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecutar una consulta SQL de lectura en SQLite"""
    try:
        with get_sqlite_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Error ejecutando consulta SQLite: {e}")
        raise

def execute_update_sqlite(query: str, params: tuple = ()) -> Optional[int]:
    """Ejecutar una consulta SQL de escritura en SQLite"""
    try:
        with get_sqlite_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Si es un INSERT, obtener el ID
            if 'INSERT' in query.upper() and 'RETURNING' not in query.upper():
                result_id = cursor.lastrowid
                conn.commit()
                return result_id
            else:
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        logger.error(f"Error ejecutando actualización SQLite: {e}")
        raise

def init_sqlite_database():
    """Inicializar base de datos SQLite para desarrollo"""
    try:
        logger.info("Inicializando base de datos SQLite para desarrollo...")
        
        with get_sqlite_connection() as conn:
            cursor = conn.cursor()
            
            # Crear tabla de categorías
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    descripcion TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar categorías por defecto
            categorias_default = [
                ('Chascas', 'Nuestros productos principales: chascas tradicionales'),
                ('DoriChascas', 'Chascas especiales con frituras populares'),
                ('Empapelados', 'Tortillas rellenas y empapeladas al gusto'),
                ('Elotes', 'Elotes preparados en diferentes estilos'),
                ('Especialidades', 'Productos especiales y combinaciones únicas'),
                ('Extras', 'Porciones adicionales y complementos')
            ]
            
            for nombre, descripcion in categorias_default:
                cursor.execute("""
                    INSERT OR IGNORE INTO categorias (nombre, descripcion) 
                    VALUES (?, ?)
                """, (nombre, descripcion))
            
            # Crear tabla de productos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    categoria TEXT DEFAULT 'Chascas',
                    precio REAL NOT NULL,
                    descripcion TEXT,
                    stock INTEGER DEFAULT 0,
                    codigo_barras TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de ventas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total REAL NOT NULL,
                    metodo_pago TEXT DEFAULT 'Efectivo',
                    descuento REAL DEFAULT 0,
                    impuestos REAL DEFAULT 0,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vendedor TEXT,
                    observaciones TEXT
                )
            """)
            
            # Crear tabla de detalle de ventas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER,
                    producto_id INTEGER,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """)
            
            # Crear tabla de gastos diarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gastos_diarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL,
                    categoria TEXT DEFAULT 'Operación',
                    descripcion TEXT,
                    comprobante TEXT,
                    vendedor TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de cortes de caja
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cortes_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL UNIQUE,
                    dinero_inicial REAL DEFAULT 0,
                    dinero_final REAL DEFAULT 0,
                    ventas_efectivo REAL DEFAULT 0,
                    ventas_tarjeta REAL DEFAULT 0,
                    total_gastos REAL DEFAULT 0,
                    diferencia REAL DEFAULT 0,
                    observaciones TEXT,
                    vendedor TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de vendedores
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    activo BOOLEAN DEFAULT 1,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de configuración
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave TEXT NOT NULL UNIQUE,
                    valor TEXT,
                    descripcion TEXT,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar vendedores por defecto
            vendedores_default = [
                ('Gerente',),
                ('Empleado 1',),
                ('Empleado 2',),
                ('Encargado',)
            ]
            
            for vendedor in vendedores_default:
                cursor.execute("""
                    INSERT OR IGNORE INTO vendedores (nombre) VALUES (?)
                """, vendedor)
            
            # Verificar si hay productos
            cursor.execute("SELECT COUNT(*) FROM productos")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Insertando productos del menú Mi Chas-K...")
                productos = [
                    # Chascas
                    ('Chasca Mini', 'Chascas', 20.00, 'Chasca pequeña tradicional', 50),
                    ('Chasca Chica', 'Chascas', 25.00, 'Chasca chica tradicional', 50),
                    ('Chasca Chica Plus', 'Chascas', 35.00, 'Chasca chica con extras', 50),
                    ('Chasca Mediana', 'Chascas', 50.00, 'Chasca mediana tradicional', 50),
                    ('Chasca Grande', 'Chascas', 60.00, 'Chasca grande tradicional', 50),
                    
                    # DoriChascas
                    ('DoriChasca', 'DoriChascas', 65.00, 'Chasca con doritos', 30),
                    ('TostiChasca', 'DoriChascas', 65.00, 'Chasca con tostitos', 30),
                    ('ChetoChasca', 'DoriChascas', 65.00, 'Chasca con cheetos', 30),
                    ('RuffleChasca', 'DoriChascas', 65.00, 'Chasca con ruffles', 30),
                    ('SabriChasca', 'DoriChascas', 65.00, 'Chasca con sabritas', 30),
                    
                    # Empapelados
                    ('Champiñones', 'Empapelados', 95.00, 'Empapelado de champiñones', 20),
                    ('Bisteck', 'Empapelados', 110.00, 'Empapelado de bisteck', 20),
                    ('Salchicha', 'Empapelados', 90.00, 'Empapelado de salchicha', 20),
                    ('Tocino', 'Empapelados', 90.00, 'Empapelado de tocino', 20),
                    ('3 quesos', 'Empapelados', 95.00, 'Empapelado de tres quesos', 20),
                    ('Carnes Frías', 'Empapelados', 110.00, 'Empapelado de carnes frías', 20),
                    
                    # Elotes
                    ('Elote sencillo', 'Elotes', 30.00, 'Elote sencillo preparado', 40),
                    ('½ Elote', 'Elotes', 18.00, 'Medio elote preparado', 40),
                    ('Elote Amarillo', 'Elotes', 38.00, 'Elote amarillo especial', 30),
                    ('Elote Asado', 'Elotes', 35.00, 'Elote asado tradicional', 30),
                    
                    # Especialidades
                    ('Elote Capricho', 'Especialidades', 50.00, 'Elote especial capricho', 20),
                    ('Chorriada Chica', 'Especialidades', 65.00, 'Chorriada tamaño chico', 15),
                    ('Maruchasca', 'Especialidades', 70.00, 'Maruchan chasca', 25),
                    
                    # Extras
                    ('Porción extra 30', 'Extras', 30.00, 'Porción extra grande', 100),
                    ('Porción extra 15', 'Extras', 15.00, 'Porción extra mediana', 100)
                ]
                
                cursor.executemany("""
                    INSERT INTO productos (nombre, categoria, precio, descripcion, stock) 
                    VALUES (?, ?, ?, ?, ?)
                """, productos)
            
            # Insertar configuraciones básicas
            configuraciones = [
                ('nombre_negocio', 'Mi Chas-K', 'Nombre del negocio'),
                ('moneda', 'MXN', 'Moneda del sistema'),
                ('direccion', '', 'Dirección del negocio'),
                ('telefono', '', 'Teléfono del negocio'),
                ('mensaje_ticket', 'Gracias por su compra', 'Mensaje en los tickets')
            ]
            
            for clave, valor, desc in configuraciones:
                cursor.execute("""
                    INSERT OR IGNORE INTO configuracion (clave, valor, descripcion) 
                    VALUES (?, ?, ?)
                """, (clave, valor, desc))
            
            conn.commit()
            logger.info("Base de datos SQLite inicializada correctamente")
            
    except Exception as e:
        logger.error(f"Error inicializando SQLite: {e}")
        raise

def reset_sqlite_database():
    """Resetea la base de datos SQLite eliminando el archivo"""
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            logger.info("Base de datos SQLite eliminada")
        init_sqlite_database()
        logger.info("Base de datos SQLite recreada")
    except Exception as e:
        logger.error(f"Error reseteando SQLite: {e}")
        raise

"""
Conexión y manejo de base de datos PostgreSQL para producción en Render
Versión: 2.1.0 - Corregida inicialización global
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Dict, Any, List, Optional
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estado del módulo - usar diccionario para evitar problemas de import
_module_state = {
    'initialized': False
}

# Configuración de base de datos desde variables de entorno
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'chaskabd'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD') or os.getenv('DB_PASS', ''),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# También soportar DATABASE_URL completa
DATABASE_URL = os.getenv('DATABASE_URL')

def is_database_initialized() -> bool:
    """Retorna el estado de inicialización de la base de datos"""
    return _module_state.get('initialized', False)

def set_database_initialized(status: bool = True):
    """Establece el estado de inicialización de la base de datos"""
    _module_state['initialized'] = status

@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager para conexiones a la base de datos PostgreSQL"""
    conn = None
    try:
        if DATABASE_URL:
            # Usar URL completa si está disponible (Render)
            logger.info(f"Conectando con DATABASE_URL...")
            conn = psycopg2.connect(DATABASE_URL)
        else:
            # Usar configuración individual (desarrollo local)
            logger.info(f"Conectando con configuración individual: {DB_CONFIG['host']}")
            conn = psycopg2.connect(**DB_CONFIG)
        
        conn.autocommit = False
        yield conn
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de conexión a la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecutar una consulta SQL de lectura"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return [dict(row) for row in result]
                
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {e}")
        raise

def execute_update(query: str, params: tuple = ()) -> Optional[int]:
    """Ejecutar una consulta SQL de escritura"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                # Si es un INSERT con RETURNING, obtener el ID
                if 'RETURNING' in query.upper():
                    result = cursor.fetchone()
                    conn.commit()
                    return result[0] if result else None
                else:
                    conn.commit()
                    return cursor.rowcount
                    
    except Exception as e:
        logger.error(f"Error ejecutando actualización: {e}")
        raise

def test_connection() -> bool:
    """Prueba la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
    except Exception as e:
        logger.error(f"Error de conexión: {e}")
        return False

def is_production_environment() -> bool:
    """Detecta si estamos en entorno de producción"""
    return os.getenv('DATABASE_URL') is not None or os.getenv('RENDER') is not None

def init_database():
    """Inicializar la base de datos con las tablas necesarias para PostgreSQL"""
    logger.info("🔧 Iniciando función init_database...")
    logger.info(f"🔍 Estado del módulo: {_module_state}")
    
    try:
        # Evitar múltiples inicializaciones
        if is_database_initialized():
            logger.info("Base de datos ya inicializada, omitiendo...")
            return
        
        # Verificar si estamos en producción
        if not is_production_environment():
            logger.warning("⚠️ Entorno de desarrollo detectado sin DATABASE_URL")
            logger.warning("⚠️ Para desarrollo local, necesitas PostgreSQL instalado o usa SQLite")
            set_database_initialized(False)
            return
        
        # Probar conexión primero
        if not test_connection():
            logger.error("No se puede establecer conexión con la base de datos")
            raise Exception("Conexión a base de datos fallida")
        
        logger.info("Iniciando inicialización de base de datos...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                logger.info("Conectado exitosamente, creando tablas...")
                
                # Crear tabla de categorías
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categorias (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        descripcion TEXT,
                        activo BOOLEAN DEFAULT TRUE,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insertar categorías ANTES que productos
                categorias_inicial = [
                    ('Chascas', 'Nuestros productos principales: chascas tradicionales'),
                    ('DoriChascas', 'Chascas especiales con frituras populares'),
                    ('Empapelados', 'Tortillas rellenas y empapeladas al gusto'),
                    ('Elotes', 'Elotes preparados en diferentes estilos'),
                    ('Especialidades', 'Productos especiales y combinaciones únicas'),
                    ('Extras', 'Porciones adicionales y complementos')
                ]
                
                # Verificar e insertar categorías
                for nombre, descripcion in categorias_inicial:
                    cursor.execute("""
                        INSERT INTO categorias (nombre, descripcion) 
                        VALUES (%s, %s) 
                        ON CONFLICT (nombre) DO NOTHING
                    """, (nombre, descripcion))
                
                logger.info("Categorías verificadas e insertadas")
                
                # Crear tabla de productos con relación a categorías
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS productos (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(200) NOT NULL,
                        categoria VARCHAR(100) DEFAULT 'Chascas',
                        precio DECIMAL(10,2) NOT NULL,
                        descripcion TEXT,
                        stock INTEGER DEFAULT 0,
                        codigo_barras VARCHAR(50),
                        activo BOOLEAN DEFAULT TRUE,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (categoria) REFERENCES categorias(nombre) ON DELETE SET DEFAULT
                    )
                """)
                
                logger.info("Tabla de productos creada con relación a categorías")
                
                # Crear tabla de ventas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ventas (
                        id SERIAL PRIMARY KEY,
                        total DECIMAL(10,2) NOT NULL,
                        metodo_pago VARCHAR(50) DEFAULT 'Efectivo',
                        descuento DECIMAL(10,2) DEFAULT 0,
                        impuestos DECIMAL(10,2) DEFAULT 0,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vendedor VARCHAR(100),
                        observaciones TEXT
                    )
                """)
                
                # Crear tabla de detalle de ventas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detalle_ventas (
                        id SERIAL PRIMARY KEY,
                        venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
                        producto_id INTEGER REFERENCES productos(id),
                        cantidad INTEGER NOT NULL,
                        precio_unitario DECIMAL(10,2) NOT NULL,
                        subtotal DECIMAL(10,2) NOT NULL
                    )
                """)
                
                # Crear tabla de configuración
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS configuracion (
                        id SERIAL PRIMARY KEY,
                        clave VARCHAR(100) NOT NULL UNIQUE,
                        valor TEXT,
                        descripcion TEXT,
                        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear tabla de gastos diarios
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS gastos_diarios (
                        id SERIAL PRIMARY KEY,
                        fecha DATE NOT NULL,
                        concepto VARCHAR(200) NOT NULL,
                        monto DECIMAL(10,2) NOT NULL,
                        categoria VARCHAR(50) DEFAULT 'Operación',
                        descripcion TEXT,
                        comprobante VARCHAR(100),
                        vendedor VARCHAR(100),
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear tabla de cortes de caja
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cortes_caja (
                        id SERIAL PRIMARY KEY,
                        fecha DATE NOT NULL UNIQUE,
                        dinero_inicial DECIMAL(10,2) DEFAULT 0,
                        dinero_final DECIMAL(10,2) DEFAULT 0,
                        ventas_efectivo DECIMAL(10,2) DEFAULT 0,
                        ventas_tarjeta DECIMAL(10,2) DEFAULT 0,
                        total_gastos DECIMAL(10,2) DEFAULT 0,
                        diferencia DECIMAL(10,2) DEFAULT 0,
                        observaciones TEXT,
                        vendedor VARCHAR(100),
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear tabla de vendedores
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vendedores (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        activo BOOLEAN DEFAULT TRUE,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear índices para optimizar consultas
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos_diarios(fecha)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cortes_fecha ON cortes_caja(fecha)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(DATE(fecha))")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendedores_activo ON vendedores(activo)")
                
                logger.info("Tablas creadas exitosamente, verificando datos...")
                
                # Verificar si ya hay datos iniciales
                cursor.execute("SELECT COUNT(*) FROM productos")
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                logger.info(f"Productos existentes: {count}")
                
                if count == 0:
                    logger.info("Insertando datos iniciales...")
                    # Insertar productos del menú Mi Chas-K
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
                        ('Cubano', 'Empapelados', 110.00, 'Empapelado estilo cubano', 20),
                        ('Arrachera', 'Empapelados', 110.00, 'Empapelado de arrachera', 15),
                        ('Camarones', 'Empapelados', 110.00, 'Empapelado de camarones', 15),
                        
                        # Elotes
                        ('Elote sencillo', 'Elotes', 30.00, 'Elote sencillo preparado', 40),
                        ('½ Elote', 'Elotes', 18.00, 'Medio elote preparado', 40),
                        ('Elote Amarillo', 'Elotes', 38.00, 'Elote amarillo especial', 30),
                        ('Elote Asado', 'Elotes', 35.00, 'Elote asado tradicional', 30),
                        ('Elote Crunch', 'Elotes', 40.00, 'Elote con topping crunch', 25),
                        
                        # Especialidades
                        ('Elote Capricho', 'Especialidades', 50.00, 'Elote especial capricho', 20),
                        ('Chorriada Chica', 'Especialidades', 65.00, 'Chorriada tamaño chico', 15),
                        ('Chorriada Mediana', 'Especialidades', 85.00, 'Chorriada tamaño mediano', 15),
                        ('Chorriada Grande', 'Especialidades', 130.00, 'Chorriada tamaño grande', 10),
                        ('Maruchasca', 'Especialidades', 70.00, 'Maruchan chasca', 25),
                        ('Maruchasca Enpolvada', 'Especialidades', 90.00, 'Maruchan chasca enpolvada', 20),
                        ('Maruchasca Especial', 'Especialidades', 110.00, 'Maruchan chasca especial', 15),
                        ('Maruchasca Suprema', 'Especialidades', 140.00, 'Maruchan chasca suprema', 10),
                        ('Sabrimaruchan', 'Especialidades', 95.00, 'Sabrimaruchan especial', 15),
                        
                        # Extras
                        ('Porción extra 30', 'Extras', 30.00, 'Porción extra grande', 100),
                        ('Porción extra 15', 'Extras', 15.00, 'Porción extra mediana', 100),
                        ('Porción extra 10', 'Extras', 10.00, 'Porción extra pequeña', 100)
                    ]
                    
                    cursor.executemany("""
                        INSERT INTO productos (nombre, categoria, precio, descripcion, stock) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, productos)
                    
                    logger.info("Productos del menú Mi Chas-K insertados exitosamente")
                    
                    # Insertar vendedores por defecto
                    vendedores_default = [
                        ('Gerente',),
                        ('Empleado 1',),
                        ('Empleado 2',),
                        ('Encargado',)
                    ]
                    
                    cursor.executemany("""
                        INSERT INTO vendedores (nombre) 
                        VALUES (%s) 
                        ON CONFLICT (nombre) DO NOTHING
                    """, vendedores_default)
                    
                    # Insertar configuraciones básicas
                    configuraciones = [
                        ('nombre_negocio', 'Mi Chas-K', 'Nombre del negocio'),
                        ('moneda', 'MXN', 'Moneda del sistema'),
                        ('direccion', '', 'Dirección del negocio'),
                        ('telefono', '', 'Teléfono del negocio'),
                        ('mensaje_ticket', 'Gracias por su compra', 'Mensaje en los tickets')
                    ]
                    
                    # Verificar si las configuraciones ya existen
                    for clave, valor, desc in configuraciones:
                        cursor.execute("""
                            INSERT INTO configuracion (clave, valor, descripcion) 
                            VALUES (%s, %s, %s) 
                            ON CONFLICT (clave) DO NOTHING
                        """, (clave, valor, desc))
                    
                    logger.info("Datos iniciales insertados exitosamente")
                
                conn.commit()
                logger.info("Base de datos PostgreSQL inicializada correctamente")
                set_database_initialized(True)
                
    except Exception as e:
        logger.error(f"Error inicializando la base de datos: {e}")
        # Asegurar que la variable global se reinicie en caso de error
        set_database_initialized(False)
        raise

def verificar_y_reparar_categorias():
    """Verifica que las categorías existan y las crea si faltan"""
    try:
        logger.info("Verificando categorías del sistema...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Verificar si existen categorías
                cursor.execute("SELECT COUNT(*) as count FROM categorias WHERE activo = TRUE")
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                if count == 0:
                    logger.warning("No se encontraron categorías activas, creando categorías por defecto...")
                    
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
                            INSERT INTO categorias (nombre, descripcion, activo) 
                            VALUES (%s, %s, TRUE) 
                            ON CONFLICT (nombre) DO UPDATE SET activo = TRUE
                        """, (nombre, descripcion))
                    
                    conn.commit()
                    logger.info("Categorías por defecto creadas exitosamente")
                else:
                    logger.info(f"Se encontraron {count} categorías activas")
                
                # Verificar que todos los productos tengan categorías válidas
                cursor.execute("""
                    SELECT DISTINCT categoria FROM productos 
                    WHERE categoria NOT IN (SELECT nombre FROM categorias WHERE activo = TRUE)
                """)
                categorias_huerfanas = cursor.fetchall()
                
                if categorias_huerfanas:
                    logger.warning(f"Encontradas categorías huérfanas: {[c[0] for c in categorias_huerfanas]}")
                    
                    # Actualizar productos con categorías inválidas a "Chascas"
                    cursor.execute("""
                        UPDATE productos 
                        SET categoria = 'Chascas' 
                        WHERE categoria NOT IN (SELECT nombre FROM categorias WHERE activo = TRUE)
                    """)
                    conn.commit()
                    logger.info("Productos con categorías inválidas actualizados a 'Chascas'")
                
    except Exception as e:
        logger.error(f"Error al verificar/reparar categorías: {e}")

"""
Conexión dual: PostgreSQL (producción) y SQLite (desarrollo)
Detecta automáticamente qué base de datos usar según el entorno
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Dict, Any, List, Optional, Union
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar tipo de base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None
USE_SQLITE = not USE_POSTGRES

# Configuración PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'chaskabd'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Configuración SQLite
SQLITE_DB_PATH = os.path.join(
    os.path.dirname(__file__), 
    'michaska_local.db'
)

# Estado del módulo
_module_state = {
    'initialized': False,
    'db_type': 'postgres' if USE_POSTGRES else 'sqlite'
}

logger.info(f"🔧 Base de datos configurada: {_module_state['db_type'].upper()}")
if USE_SQLITE:
    logger.info(f"📂 SQLite: {SQLITE_DB_PATH}")


@contextmanager
def get_db_connection() -> Generator[Union[psycopg2.extensions.connection, sqlite3.Connection], None, None]:
    """Context manager para conexiones - soporte dual PostgreSQL/SQLite"""
    conn = None
    try:
        if USE_POSTGRES:
            # Conexión PostgreSQL (producción)
            if DATABASE_URL:
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            else:
                conn = psycopg2.connect(**DB_CONFIG)
            conn.autocommit = False
        else:
            # Conexión SQLite (desarrollo local)
            conn = sqlite3.connect(SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row  # Retornar filas como diccionarios
        
        yield conn
        
        if USE_POSTGRES:
            conn.commit()
        else:
            conn.commit()
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error de conexión a la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecutar una consulta SQL de lectura - compatible con ambas BD"""
    try:
        # Convertir placeholders si es necesario
        if USE_SQLITE and '%s' in query:
            query = query.replace('%s', '?')
        
        with get_db_connection() as conn:
            if USE_POSTGRES:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    return [dict(row) for row in result]
            else:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                return [dict(row) for row in result]
                
    except Exception as e:
        logger.error(f"Error ejecutando query: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_update(query: str, params: tuple = ()) -> int:
    """Ejecutar una consulta SQL de escritura (INSERT, UPDATE, DELETE)"""
    try:
        # Convertir placeholders si es necesario
        if USE_SQLITE and '%s' in query:
            query = query.replace('%s', '?')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if USE_POSTGRES:
                rowcount = cursor.rowcount
            else:
                rowcount = cursor.rowcount
            
            conn.commit()
            cursor.close()
            return rowcount
            
    except Exception as e:
        logger.error(f"Error ejecutando update: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_insert(query: str, params: tuple = ()) -> Optional[int]:
    """Ejecutar INSERT y retornar el ID generado"""
    try:
        # Convertir placeholders y RETURNING si es necesario
        if USE_SQLITE:
            if '%s' in query:
                query = query.replace('%s', '?')
            # SQLite no soporta RETURNING, lo manejamos diferente
            if 'RETURNING' in query.upper():
                query = query.split('RETURNING')[0].strip()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if USE_POSTGRES:
                # PostgreSQL con RETURNING
                if 'RETURNING' in query.upper():
                    result = cursor.fetchone()
                    inserted_id = result[0] if result else None
                else:
                    inserted_id = cursor.lastrowid
            else:
                # SQLite usa lastrowid
                inserted_id = cursor.lastrowid
            
            conn.commit()
            cursor.close()
            return inserted_id
            
    except Exception as e:
        logger.error(f"Error ejecutando insert: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def test_connection() -> bool:
    """Probar la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute("SELECT 1")
            else:
                cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
            logger.info(f"✅ Conexión exitosa a {db_type}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error de conexión: {e}")
        return False


def is_production() -> bool:
    """Detecta si estamos en entorno de producción"""
    return os.getenv('DATABASE_URL') is not None or os.getenv('RENDER') is not None


def get_db_type() -> str:
    """Retorna el tipo de base de datos en uso"""
    return _module_state['db_type']


# Funciones para compatibilidad con código existente
def is_database_initialized() -> bool:
    """Retorna el estado de inicialización de la base de datos"""
    return _module_state.get('initialized', False)


def set_database_initialized(status: bool = True):
    """Establece el estado de inicialización de la base de datos"""
    _module_state['initialized'] = status


if __name__ == '__main__':
    # Test de conexión
    print(f"Tipo de BD: {get_db_type()}")
    print(f"Producción: {is_production()}")
    test_connection()

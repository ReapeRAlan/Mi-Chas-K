"""
Configuración principal para PostgreSQL directo
Sistema optimizado para tablets - MiChaska
"""
import os
from database.connection_direct_simple import DirectPostgreSQLAdapter
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Singleton del adaptador
_db_adapter = None

def get_db_adapter():
    """Obtener instancia única del adaptador de base de datos"""
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = DirectPostgreSQLAdapter()
    return _db_adapter

def test_database_connection():
    """Probar conexión a la base de datos"""
    try:
        adapter = get_db_adapter()
        result = adapter.execute_query("SELECT 1 as test")
        return len(result) > 0
    except Exception as e:
        logging.error(f"Error en conexión de prueba: {e}")
        return False

# Función de compatibilidad para código existente
def get_db_connection():
    """Función de compatibilidad para código existente"""
    return get_db_adapter().get_connection()

# Funciones de compatibilidad adicionales
def test_connection():
    """Función de compatibilidad"""
    return test_database_connection()

def get_postgres_connection():
    """Función de compatibilidad"""
    return get_db_connection()

def is_database_initialized():
    """Función de compatibilidad"""
    return test_database_connection()

def set_database_initialized(status=True):
    """Función de compatibilidad"""
    pass

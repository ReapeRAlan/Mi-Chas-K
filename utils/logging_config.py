"""
Configuración de logging para el sistema MiChaska
"""
import logging
import os
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configuración básica
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Para consola
        ]
    )
    
    # Logger específico para la aplicación
    logger = logging.getLogger('michaska')
    
    return logger

def log_database_operation(operation: str, success: bool, details: str = ""):
    """Log específico para operaciones de base de datos"""
    logger = logging.getLogger('michaska.db')
    
    if success:
        logger.info(f"✅ {operation} - {details}")
    else:
        logger.error(f"❌ {operation} - {details}")

def log_performance(operation: str, duration: float, details: str = ""):
    """Log de rendimiento"""
    logger = logging.getLogger('michaska.performance')
    
    if duration > 1.0:  # Operaciones que toman más de 1 segundo
        logger.warning(f"⚠️ {operation} tomó {duration:.2f}s - {details}")
    else:
        logger.debug(f"⏱️ {operation} completado en {duration:.3f}s - {details}")

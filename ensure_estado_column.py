#!/usr/bin/env python3
"""
Script para asegurar que la columna 'estado' existe en la tabla ventas
"""

import os
import psycopg2
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Función principal para asegurar que existe la columna estado"""
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        logger.error("❌ DATABASE_URL no encontrada")
        return False
    
    try:
        logger.info("🔧 Conectando a la base de datos...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Verificar si la columna estado existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'ventas' AND column_name = 'estado'
            )
        """)
        
        estado_exists = cursor.fetchone()[0]
        
        if not estado_exists:
            logger.info("⚠️ Columna 'estado' no existe, creándola...")
            cursor.execute("ALTER TABLE ventas ADD COLUMN estado VARCHAR(20) DEFAULT 'Completada'")
            conn.commit()
            logger.info("✅ Columna 'estado' creada exitosamente")
        else:
            logger.info("✅ Columna 'estado' ya existe")
        
        # Verificar columnas finales
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ventas'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Columnas en tabla ventas: {', '.join(columns)}")
        
        conn.close()
        logger.info("✅ Proceso completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

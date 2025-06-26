#!/usr/bin/env python3
"""
Script para investigar la estructura de la base de datos remota
y corregir los problemas de sincronización
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def investigate_remote_database():
    """Investigar estructura de la base de datos remota"""
    print("🔍 INVESTIGANDO ESTRUCTURA DE BASE DE DATOS REMOTA")
    print("=" * 60)
    
    try:
        # Conectar usando DATABASE_URL o variables individuales
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
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Obtener todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"📊 Tablas encontradas: {tables}")
        
        # 2. Analizar estructura de cada tabla principal
        main_tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
        
        for table in main_tables:
            if table in tables:
                print(f"\n📋 ESTRUCTURA DE TABLA: {table.upper()}")
                print("-" * 40)
                
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cursor.fetchall()
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"  {col['column_name']:<20} {col['data_type']:<15} {nullable}{default}")
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  📊 Total registros: {count}")
        
        # 3. Verificar tipos específicos problemáticos
        print(f"\n🔍 VERIFICANDO TIPOS PROBLEMÁTICOS")
        print("-" * 40)
        
        for table in ['productos', 'categorias', 'vendedores']:
            if table in tables:
                cursor.execute("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'activo'
                """, (table,))
                
                result = cursor.fetchone()
                if result:
                    print(f"  {table}.activo: {result['data_type']}")
        
        # 4. Verificar algunos registros de ejemplo
        print(f"\n📄 REGISTROS DE EJEMPLO")
        print("-" * 40)
        
        cursor.execute("SELECT id, nombre, activo FROM productos LIMIT 3")
        productos = cursor.fetchall()
        for prod in productos:
            print(f"  Producto ID {prod['id']}: {prod['nombre']} (activo: {prod['activo']} - tipo: {type(prod['activo'])})")
        
        conn.close()
        print("\n✅ Investigación completada")
        return True
        
    except Exception as e:
        print(f"❌ Error investigando BD remota: {e}")
        return False

def create_direct_database_adapter():
    """Crear adaptador directo sin híbrido"""
    content = '''"""
Adaptador Directo a PostgreSQL - Sin modo híbrido
Optimizado para tablets y conexión directa
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DirectDatabaseAdapter:
    """Adaptador directo a PostgreSQL sin modo híbrido"""
    
    def __init__(self):
        self.connection_params = self._get_connection_params()
        self._test_connection()
    
    def _get_connection_params(self):
        """Obtener parámetros de conexión"""
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return {'dsn': database_url}
        else:
            return {
                'host': os.getenv('DB_HOST'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'port': os.getenv('DB_PORT', 5432)
            }
    
    def _test_connection(self):
        """Probar conexión inicial"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    logger.info("✅ Conexión a PostgreSQL exitosa")
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise
    
    def get_connection(self):
        """Obtener conexión directa a PostgreSQL"""
        if 'dsn' in self.connection_params:
            return psycopg2.connect(
                self.connection_params['dsn'],
                cursor_factory=RealDictCursor
            )
        else:
            return psycopg2.connect(
                **self.connection_params,
                cursor_factory=RealDictCursor
            )
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Ejecutar query SELECT"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error en query: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> Optional[int]:
        """Ejecutar INSERT/UPDATE/DELETE"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ Error en update: {e}")
            conn.rollback()
            return None
    
    def _adapt_value_for_postgres(self, value, field_name: str = ""):
        """Adaptar valor para PostgreSQL"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bool):
            return value  # PostgreSQL acepta boolean directamente
        elif field_name == 'activo' and isinstance(value, (int, str)):
            # Convertir a boolean para campo activo
            return bool(int(value))
        elif value is None:
            return None
        else:
            return value
    
    # === MÉTODOS ESPECÍFICOS PARA CADA TABLA ===
    
    def get_productos(self, activos_only: bool = True) -> List[Dict]:
        """Obtener productos"""
        where_clause = "WHERE activo = true" if activos_only else ""
        query = f"SELECT * FROM productos {where_clause} ORDER BY nombre"
        return self.execute_query(query)
    
    def get_producto_by_id(self, producto_id: int) -> Optional[Dict]:
        """Obtener producto por ID"""
        query = "SELECT * FROM productos WHERE id = %s"
        result = self.execute_query(query, (producto_id,))
        return result[0] if result else None
    
    def insert_producto(self, data: Dict) -> Optional[int]:
        """Insertar nuevo producto"""
        # Adaptar datos
        adapted_data = {}
        for key, value in data.items():
            adapted_data[key] = self._adapt_value_for_postgres(value, key)
        
        columns = list(adapted_data.keys())
        placeholders = ['%s'] * len(columns)
        values = list(adapted_data.values())
        
        query = f"""
            INSERT INTO productos ({', '.join(columns)}) 
            VALUES ({', '.join(placeholders)}) 
            RETURNING id
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, values)
                    conn.commit()
                    return cursor.fetchone()['id']
        except Exception as e:
            logger.error(f"❌ Error insertando producto: {e}")
            return None
    
    def update_producto(self, producto_id: int, data: Dict) -> bool:
        """Actualizar producto"""
        # Filtrar campos válidos y adaptar valores
        valid_data = {}
        for key, value in data.items():
            if key != 'id' and value is not None:
                valid_data[key] = self._adapt_value_for_postgres(value, key)
        
        if not valid_data:
            return False
        
        set_clauses = [f"{key} = %s" for key in valid_data.keys()]
        values = list(valid_data.values()) + [producto_id]
        
        query = f"UPDATE productos SET {', '.join(set_clauses)} WHERE id = %s"
        
        result = self.execute_update(query, values)
        return result is not None and result > 0
    
    def update_stock(self, producto_id: int, nueva_cantidad: int) -> bool:
        """Actualizar stock de producto"""
        query = "UPDATE productos SET stock = %s WHERE id = %s"
        result = self.execute_update(query, (nueva_cantidad, producto_id))
        return result is not None and result > 0
    
    def reduce_stock(self, producto_id: int, cantidad: int) -> bool:
        """Reducir stock de producto"""
        query = "UPDATE productos SET stock = stock - %s WHERE id = %s AND stock >= %s"
        result = self.execute_update(query, (cantidad, producto_id, cantidad))
        return result is not None and result > 0
    
    def get_categorias(self) -> List[Dict]:
        """Obtener categorías"""
        query = "SELECT * FROM categorias WHERE activo = true ORDER BY nombre"
        return self.execute_query(query)
    
    def get_vendedores(self) -> List[Dict]:
        """Obtener vendedores"""
        query = "SELECT * FROM vendedores WHERE activo = true ORDER BY nombre"
        return self.execute_query(query)
    
    def insert_venta(self, venta_data: Dict, detalles: List[Dict]) -> Optional[int]:
        """Insertar venta completa con detalles"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Insertar venta
                    venta_columns = list(venta_data.keys())
                    venta_placeholders = ['%s'] * len(venta_columns)
                    venta_values = [self._adapt_value_for_postgres(v) for v in venta_data.values()]
                    
                    venta_query = f"""
                        INSERT INTO ventas ({', '.join(venta_columns)}) 
                        VALUES ({', '.join(venta_placeholders)}) 
                        RETURNING id
                    """
                    
                    cursor.execute(venta_query, venta_values)
                    venta_id = cursor.fetchone()['id']
                    
                    # 2. Insertar detalles
                    for detalle in detalles:
                        detalle_data = dict(detalle)
                        detalle_data['venta_id'] = venta_id
                        
                        detalle_columns = list(detalle_data.keys())
                        detalle_placeholders = ['%s'] * len(detalle_columns)
                        detalle_values = [self._adapt_value_for_postgres(v) for v in detalle_data.values()]
                        
                        detalle_query = f"""
                            INSERT INTO detalle_ventas ({', '.join(detalle_columns)}) 
                            VALUES ({', '.join(detalle_placeholders)})
                        """
                        
                        cursor.execute(detalle_query, detalle_values)
                        
                        # 3. Reducir stock
                        cursor.execute("""
                            UPDATE productos 
                            SET stock = stock - %s 
                            WHERE id = %s AND stock >= %s
                        """, (detalle['cantidad'], detalle['producto_id'], detalle['cantidad']))
                    
                    conn.commit()
                    return venta_id
                    
        except Exception as e:
            logger.error(f"❌ Error insertando venta: {e}")
            return None
    
    def get_ventas_recientes(self, limit: int = 50) -> List[Dict]:
        """Obtener ventas recientes"""
        query = """
            SELECT v.*, COUNT(dv.id) as items_count
            FROM ventas v
            LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
            GROUP BY v.id
            ORDER BY v.fecha DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_detalle_venta(self, venta_id: int) -> List[Dict]:
        """Obtener detalle de una venta"""
        query = """
            SELECT dv.*, p.nombre as producto_nombre
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
            ORDER BY dv.id
        """
        return self.execute_query(query, (venta_id,))
    
    def get_productos_con_stock_bajo(self, limite: int = 10) -> List[Dict]:
        """Obtener productos con stock bajo"""
        query = """
            SELECT * FROM productos 
            WHERE activo = true AND stock <= %s 
            ORDER BY stock ASC, nombre
        """
        return self.execute_query(query, (limite,))
    
    def get_estadisticas_ventas(self, dias: int = 7) -> Dict:
        """Obtener estadísticas de ventas"""
        query = """
            SELECT 
                COUNT(*) as total_ventas,
                COALESCE(SUM(total), 0) as ingresos_totales,
                COALESCE(AVG(total), 0) as ticket_promedio
            FROM ventas 
            WHERE fecha >= CURRENT_DATE - INTERVAL '%s days'
        """
        
        result = self.execute_query(query, (dias,))
        return result[0] if result else {
            'total_ventas': 0,
            'ingresos_totales': 0,
            'ticket_promedio': 0
        }
    
    def search_productos(self, termino: str) -> List[Dict]:
        """Buscar productos por nombre o código"""
        query = """
            SELECT * FROM productos 
            WHERE activo = true 
            AND (
                LOWER(nombre) LIKE LOWER(%s) 
                OR codigo_barras LIKE %s
            )
            ORDER BY nombre
            LIMIT 20
        """
        termino_like = f"%{termino}%"
        return self.execute_query(query, (termino_like, termino_like))

# Instancia global
db_adapter = DirectDatabaseAdapter()

# Funciones de compatibilidad
def get_db_connection():
    return db_adapter.get_connection()

def execute_query(query, params=None):
    return db_adapter.execute_query(query, params or ())
'''
    
    with open('/home/ghost/Escritorio/Mi-Chas-K/database/connection_direct.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Adaptador directo creado: connection_direct.py")

if __name__ == '__main__':
    investigate_remote_database()
    create_direct_database_adapter()

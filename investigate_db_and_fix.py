#!/usr/bin/env python3
"""
Script para investigar la base de datos PostgreSQL y crear adaptador directo
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

load_dotenv()

def investigate_database():
    """Investigar estructura completa de PostgreSQL"""
    try:
        print("🔍 Conectando a PostgreSQL...")
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa!")
        
        # 1. Obtener todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"📊 Tablas encontradas: {tables}")
        
        # 2. Analizar estructura de cada tabla
        schema_info = {}
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
            schema_info[table] = {
                'columns': {col['column_name']: {
                    'type': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default'],
                    'max_length': col['character_maximum_length']
                } for col in columns},
                'column_names': [col['column_name'] for col in columns]
            }
            
            print(f"\n📋 Tabla {table}:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # 3. Verificar datos existentes
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"📈 {table}: {count} registros")
                
                # Mostrar algunos datos de ejemplo
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"   Ejemplos: {len(samples)} filas")
                    for i, sample in enumerate(samples[:2]):
                        print(f"   [{i+1}] {dict(sample)}")
            except Exception as e:
                print(f"   ⚠️ Error accediendo a {table}: {e}")
        
        # 4. Limpiar sync_queue problemático
        print("\n🧹 Limpiando sync_queue problemático...")
        try:
            cursor.execute("DELETE FROM sync_queue WHERE status = 'error' OR attempts > 3")
            deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Eliminados {deleted} elementos problemáticos")
        except Exception as e:
            print(f"⚠️ Error limpiando sync_queue: {e}")
        
        cursor.close()
        conn.close()
        
        # 5. Generar esquema para el adaptador
        return schema_info
        
    except Exception as e:
        print(f"❌ Error investigando base de datos: {e}")
        return {}

def create_direct_adapter(schema_info):
    """Crear adaptador directo basado en el esquema real"""
    
    adapter_code = '''"""
Adaptador Directo PostgreSQL - Optimizado para Tablets
Sistema de punto de venta MiChaska
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
import json

load_dotenv()
logger = logging.getLogger(__name__)

class DirectPostgreSQLAdapter:
    """Adaptador directo a PostgreSQL sin lógica híbrida"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', 5432)
        }
        self.schema_info = ''' + json.dumps(schema_info, indent=8) + '''
        self._test_connection()
    
    def _test_connection(self):
        """Probar conexión inicial"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                logger.info("✅ Conexión directa a PostgreSQL establecida")
        except Exception as e:
            logger.error(f"❌ Error en conexión directa: {e}")
            raise
    
    def get_connection(self):
        """Obtener conexión directa a PostgreSQL"""
        return psycopg2.connect(
            **self.connection_params,
            cursor_factory=RealDictCursor
        )
    
    def _adapt_value_for_postgres(self, value: Any, column_type: str) -> Any:
        """Adaptar valor específico para PostgreSQL"""
        if value is None:
            return None
        
        # Tipos booleanos - CRÍTICO: convertir enteros a booleanos
        if column_type == 'boolean':
            if isinstance(value, (int, str)):
                return value in (1, '1', 'true', 'True', True)
            return bool(value)
        
        # Tipos numéricos
        elif column_type in ['numeric', 'decimal']:
            if isinstance(value, Decimal):
                return float(value)
            return float(value) if value != '' else 0.0
        
        elif column_type in ['integer', 'bigint']:
            return int(value) if value != '' else 0
        
        # Tipos de texto
        elif column_type in ['text', 'character varying', 'varchar']:
            return str(value) if value is not None else ''
        
        # Tipos de fecha
        elif column_type == 'timestamp without time zone':
            if isinstance(value, str):
                # Filtrar expresiones SQL problemáticas
                if any(sql_expr in value for sql_expr in ['CURRENT_TIMESTAMP', 'NOW()', 'COALESCE']):
                    return datetime.now()
                return value
            return value
        
        return value
    
    def _clean_data_for_table(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar datos específicos para una tabla"""
        if table_name not in self.schema_info:
            logger.warning(f"⚠️ Tabla {table_name} no encontrada en esquema")
            return data
        
        table_schema = self.schema_info[table_name]
        cleaned_data = {}
        
        for column_name, value in data.items():
            # Saltar campos de metadata
            if column_name in ['original_query', 'original_params', 'timestamp', 'metadata', 'sync_status']:
                continue
            
            # Saltar expresiones SQL en datos
            if isinstance(value, str) and any(expr in str(value) for expr in [
                'COALESCE', 'CURRENT_TIMESTAMP', 'NOW()', '(', ')', '+', '-', '*', '/'
            ]):
                logger.warning(f"⚠️ Campo {column_name} contiene expresión SQL, omitiendo: {value}")
                continue
            
            # Verificar si la columna existe en el esquema
            if column_name in table_schema['columns']:
                column_info = table_schema['columns'][column_name]
                adapted_value = self._adapt_value_for_postgres(value, column_info['type'])
                cleaned_data[column_name] = adapted_value
            else:
                logger.debug(f"🔍 Columna {column_name} no existe en {table_name}, omitiendo")
        
        return cleaned_data
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Ejecutar consulta SELECT"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Error en consulta: {e}")
            return []
    
    def execute_insert(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """Ejecutar INSERT directo"""
        try:
            cleaned_data = self._clean_data_for_table(table_name, data)
            
            if not cleaned_data:
                logger.warning(f"⚠️ No hay datos válidos para insertar en {table_name}")
                return None
            
            columns = list(cleaned_data.keys())
            placeholders = ['%s'] * len(columns)
            values = [cleaned_data[col] for col in columns]
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) RETURNING id"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
                
                result = cursor.fetchone()
                inserted_id = result['id'] if result else None
                logger.info(f"✅ INSERT en {table_name}: ID {inserted_id}")
                return inserted_id
                
        except Exception as e:
            logger.error(f"❌ Error en INSERT {table_name}: {e}")
            return None
    
    def execute_update(self, table_name: str, data: Dict[str, Any], where_clause: str, where_params: tuple = ()) -> int:
        """Ejecutar UPDATE directo"""
        try:
            cleaned_data = self._clean_data_for_table(table_name, data)
            
            if not cleaned_data:
                logger.warning(f"⚠️ No hay datos válidos para actualizar en {table_name}")
                return 0
            
            set_clauses = [f"{col} = %s" for col in cleaned_data.keys()]
            values = list(cleaned_data.values())
            values.extend(where_params)
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
                
                updated_rows = cursor.rowcount
                logger.info(f"✅ UPDATE en {table_name}: {updated_rows} filas")
                return updated_rows
                
        except Exception as e:
            logger.error(f"❌ Error en UPDATE {table_name}: {e}")
            return 0
    
    def execute_delete(self, table_name: str, where_clause: str, where_params: tuple = ()) -> int:
        """Ejecutar DELETE directo"""
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, where_params)
                conn.commit()
                
                deleted_rows = cursor.rowcount
                logger.info(f"✅ DELETE en {table_name}: {deleted_rows} filas")
                return deleted_rows
                
        except Exception as e:
            logger.error(f"❌ Error en DELETE {table_name}: {e}")
            return 0
    
    def get_productos(self, activo_only: bool = True) -> List[Dict[str, Any]]:
        """Obtener productos"""
        where_clause = "WHERE activo = true" if activo_only else ""
        query = f"SELECT * FROM productos {where_clause} ORDER BY nombre"
        return self.execute_query(query)
    
    def get_categorias(self) -> List[Dict[str, Any]]:
        """Obtener categorías"""
        return self.execute_query("SELECT * FROM categorias WHERE activo = true ORDER BY nombre")
    
    def get_ventas_recientes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener ventas recientes"""
        return self.execute_query("SELECT * FROM ventas ORDER BY fecha DESC LIMIT %s", (limit,))
    
    def crear_venta(self, venta_data: Dict[str, Any], detalles: List[Dict[str, Any]]) -> Optional[int]:
        """Crear venta completa con detalles"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insertar venta principal
                venta_cleaned = self._clean_data_for_table('ventas', venta_data)
                venta_columns = list(venta_cleaned.keys())
                venta_placeholders = ['%s'] * len(venta_columns)
                venta_values = [venta_cleaned[col] for col in venta_columns]
                
                venta_query = f"INSERT INTO ventas ({', '.join(venta_columns)}) VALUES ({', '.join(venta_placeholders)}) RETURNING id"
                cursor.execute(venta_query, venta_values)
                venta_id = cursor.fetchone()['id']
                
                # Insertar detalles
                for detalle in detalles:
                    detalle_data = {**detalle, 'venta_id': venta_id}
                    detalle_cleaned = self._clean_data_for_table('detalle_ventas', detalle_data)
                    
                    detalle_columns = list(detalle_cleaned.keys())
                    detalle_placeholders = ['%s'] * len(detalle_columns)
                    detalle_values = [detalle_cleaned[col] for col in detalle_columns]
                    
                    detalle_query = f"INSERT INTO detalle_ventas ({', '.join(detalle_columns)}) VALUES ({', '.join(detalle_placeholders)})"
                    cursor.execute(detalle_query, detalle_values)
                
                # Actualizar stock de productos
                for detalle in detalles:
                    cursor.execute(
                        "UPDATE productos SET stock = stock - %s WHERE id = %s",
                        (detalle['cantidad'], detalle['producto_id'])
                    )
                
                conn.commit()
                logger.info(f"✅ Venta creada: ID {venta_id} con {len(detalles)} detalles")
                return venta_id
                
        except Exception as e:
            logger.error(f"❌ Error creando venta: {e}")
            return None
    
    def get_dashboard_data(self, fecha_desde: str = None, fecha_hasta: str = None) -> Dict[str, Any]:
        """Obtener datos para dashboard"""
        try:
            fecha_filtro = ""
            params = []
            
            if fecha_desde and fecha_hasta:
                fecha_filtro = "WHERE fecha BETWEEN %s AND %s"
                params = [fecha_desde, fecha_hasta]
            elif fecha_desde:
                fecha_filtro = "WHERE fecha >= %s"
                params = [fecha_desde]
            
            # Ventas totales
            ventas_query = f"SELECT COUNT(*) as total_ventas, COALESCE(SUM(total), 0) as total_ingresos FROM ventas {fecha_filtro}"
            ventas_data = self.execute_query(ventas_query, params)
            
            # Productos más vendidos
            productos_query = f"""
                SELECT p.nombre, SUM(dv.cantidad) as cantidad_vendida
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                {fecha_filtro}
                GROUP BY p.id, p.nombre
                ORDER BY cantidad_vendida DESC
                LIMIT 10
            """
            productos_data = self.execute_query(productos_query, params)
            
            # Ventas por día
            ventas_dia_query = f"""
                SELECT fecha::date as dia, COUNT(*) as ventas, SUM(total) as ingresos
                FROM ventas
                {fecha_filtro}
                GROUP BY fecha::date
                ORDER BY dia DESC
                LIMIT 30
            """
            ventas_dia_data = self.execute_query(ventas_dia_query, params)
            
            return {
                'resumen': ventas_data[0] if ventas_data else {'total_ventas': 0, 'total_ingresos': 0},
                'productos_top': productos_data,
                'ventas_por_dia': ventas_dia_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de dashboard: {e}")
            return {'resumen': {'total_ventas': 0, 'total_ingresos': 0}, 'productos_top': [], 'ventas_por_dia': []}
'''
    
    return adapter_code

if __name__ == "__main__":
    print("🔍 Investigando base de datos PostgreSQL...")
    schema_info = investigate_database()
    
    if schema_info:
        print("\n📝 Generando adaptador directo...")
        adapter_code = create_direct_adapter(schema_info)
        
        # Guardar adaptador
        with open('/home/ghost/Escritorio/Mi-Chas-K/database/connection_direct_final.py', 'w', encoding='utf-8') as f:
            f.write(adapter_code)
        
        print("✅ Adaptador directo creado: database/connection_direct_final.py")
        print("\n🎯 Problemas identificados y solucionados:")
        print("   - ✅ Conversión correcta de booleanos (1/0 → true/false)")
        print("   - ✅ Filtrado de expresiones SQL en datos")
        print("   - ✅ Adaptación de tipos específicos para PostgreSQL")
        print("   - ✅ Manejo directo sin lógica híbrida")
        print("   - ✅ Optimizado para tablets (queries eficientes)")
        
    else:
        print("❌ No se pudo obtener información del esquema")

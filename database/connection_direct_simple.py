"""
Adaptador Directo PostgreSQL - Optimizado para Tablets
Sistema de punto de venta MiChaska - Versión Simplificada
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

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
        
        # Esquema simplificado - tipos principales
        self.boolean_columns = {
            'categorias': ['activo'],
            'productos': ['activo'],
            'vendedores': ['activo']
        }
        
        self.numeric_columns = {
            'productos': ['precio', 'stock'],
            'ventas': ['total', 'descuento', 'impuestos'],
            'detalle_ventas': ['cantidad', 'precio_unitario', 'subtotal'],
            'cortes_caja': ['dinero_inicial', 'dinero_final', 'ventas_efectivo', 'ventas_tarjeta', 'total_gastos', 'diferencia'],
            'gastos_diarios': ['monto']
        }
        
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
    
    def _adapt_value_for_postgres(self, table_name: str, column_name: str, value: Any) -> Any:
        """Adaptar valor específico para PostgreSQL"""
        if value is None:
            return None
        
        # Filtrar expresiones SQL problemáticas
        if isinstance(value, str) and any(expr in str(value) for expr in [
            'COALESCE', 'CURRENT_TIMESTAMP', 'NOW()', 'GREATEST', 'LEAST', '(', ')', '+', '-', '*', '/'
        ]):
            logger.warning(f"⚠️ Campo {column_name} contiene expresión SQL, usando valor por defecto")
            if column_name in self.boolean_columns.get(table_name, []):
                return True
            elif column_name in self.numeric_columns.get(table_name, []):
                return 0
            else:
                return None
        
        # Tipos booleanos - CRÍTICO: convertir enteros a booleanos
        if column_name in self.boolean_columns.get(table_name, []):
            if isinstance(value, (int, str)):
                return value in (1, '1', 'true', 'True', True)
            return bool(value)
        
        # Tipos numéricos
        if column_name in self.numeric_columns.get(table_name, []):
            try:
                if isinstance(value, Decimal):
                    return float(value)
                return float(value) if str(value).strip() != '' else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        # Tipos de fecha
        if 'fecha' in column_name.lower() and isinstance(value, str):
            if any(sql_expr in value for sql_expr in ['CURRENT_TIMESTAMP', 'NOW()', 'COALESCE']):
                return datetime.now()
        
        return value
    
    def _clean_data_for_table(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar datos específicos para una tabla"""
        cleaned_data = {}
        
        for column_name, value in data.items():
            # Saltar campos de metadata
            if column_name in ['original_query', 'original_params', 'timestamp', 'metadata', 'sync_status']:
                continue
            
            # Adaptar valor
            adapted_value = self._adapt_value_for_postgres(table_name, column_name, value)
            
            # Solo incluir si no es None o si es un campo requerido
            if adapted_value is not None:
                cleaned_data[column_name] = adapted_value
        
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
            logger.error(f"   Query: {query}")
            logger.error(f"   Params: {params}")
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
            logger.error(f"   Data: {data}")
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
            logger.error(f"   Data: {data}")
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

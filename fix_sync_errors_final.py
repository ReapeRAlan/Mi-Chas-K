#!/usr/bin/env python3
"""
Script definitivo para corregir todos los errores críticos de sincronización
entre SQLite local y PostgreSQL remoto.

PROBLEMAS A RESOLVER:
1. Violaciones de foreign keys (orden incorrecto)
2. Parámetros PostgreSQL mal formateados ($1, $2, etc.)
3. Expresiones SQL en campos de datos
4. UPDATEs vacíos después de filtrar campos problemáticos
5. Conversiones boolean/integer incorrectas
"""

import os
import sys
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from decimal import Decimal
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncErrorFixer:
    def __init__(self):
        self.local_db_path = 'sistema_facturacion.db'
        self.remote_available = False
        self._check_remote_connection()
    
    def _check_remote_connection(self):
        """Verificar conexión remota"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                conn.close()
                self.remote_available = True
                logger.info("✅ Conexión remota verificada")
            else:
                # Usar variables de entorno individuales
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
                conn.close()
                self.remote_available = True
                logger.info("✅ Conexión remota verificada (variables individuales)")
        except Exception as e:
            logger.warning(f"⚠️ Sin conexión remota: {e}")
            self.remote_available = False
    
    def analyze_sync_queue(self):
        """Analizar problemas en la cola de sincronización"""
        logger.info("🔍 Analizando cola de sincronización...")
        
        problems = {
            'foreign_key_violations': [],
            'parameter_mismatches': [],
            'sql_expressions': [],
            'empty_updates': [],
            'boolean_issues': []
        }
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, table_name, operation, data, status, attempts
                    FROM sync_queue 
                    WHERE status = 'pending'
                    ORDER BY id
                """)
                
                items = cursor.fetchall()
                logger.info(f"📊 Analizando {len(items)} elementos en cola...")
                
                for item in items:
                    item_id, table_name, operation, data_json, status, attempts = item
                    
                    try:
                        data = json.loads(data_json)
                        
                        # 1. Verificar violaciones de foreign key
                        if self._check_foreign_key_violation(table_name, operation, data):
                            problems['foreign_key_violations'].append({
                                'id': item_id, 'table': table_name, 'operation': operation
                            })
                        
                        # 2. Verificar problemas de parámetros
                        if self._check_parameter_issues(data):
                            problems['parameter_mismatches'].append({
                                'id': item_id, 'table': table_name, 'data': data
                            })
                        
                        # 3. Verificar expresiones SQL
                        sql_expressions = self._find_sql_expressions(data)
                        if sql_expressions:
                            problems['sql_expressions'].append({
                                'id': item_id, 'table': table_name, 'expressions': sql_expressions
                            })
                        
                        # 4. Verificar UPDATEs vacíos potenciales
                        if operation == 'UPDATE' and self._would_be_empty_update(data, table_name):
                            problems['empty_updates'].append({
                                'id': item_id, 'table': table_name, 'data': data
                            })
                        
                        # 5. Verificar problemas de boolean
                        boolean_issues = self._find_boolean_issues(data, table_name)
                        if boolean_issues:
                            problems['boolean_issues'].append({
                                'id': item_id, 'table': table_name, 'issues': boolean_issues
                            })
                        
                    except Exception as e:
                        logger.error(f"❌ Error analizando item {item_id}: {e}")
                
                # Mostrar resumen
                self._show_analysis_summary(problems)
                return problems
                
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            return problems
    
    def _check_foreign_key_violation(self, table_name, operation, data):
        """Verificar si habría violación de foreign key"""
        if operation != 'INSERT':
            return False
        
        data_dict = data.get('data', {}) if isinstance(data, dict) else {}
        
        # detalle_ventas requiere que exista la venta
        if table_name == 'detalle_ventas' and 'venta_id' in data_dict:
            venta_id = data_dict['venta_id']
            # Verificar si la venta existe localmente
            try:
                with sqlite3.connect(self.local_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM ventas WHERE id = ?", (venta_id,))
                    if not cursor.fetchone():
                        return True
            except:
                return True
        
        # productos requiere categoría válida
        if table_name == 'productos' and 'categoria' in data_dict:
            categoria = data_dict['categoria']
            if not categoria or categoria == '':
                return True
        
        return False
    
    def _check_parameter_issues(self, data):
        """Verificar problemas de parámetros"""
        if not isinstance(data, dict):
            return False
        
        # Buscar queries con placeholders mal formateados
        original_query = data.get('original_query', '')
        original_params = data.get('original_params', [])
        
        if original_query and '?' in original_query:
            param_count = original_query.count('?')
            actual_params = len(original_params) if original_params else 0
            
            if param_count != actual_params:
                return True
        
        return False
    
    def _find_sql_expressions(self, data):
        """Encontrar expresiones SQL en los datos"""
        expressions = []
        
        data_dict = data.get('data', {}) if isinstance(data, dict) else {}
        
        for key, value in data_dict.items():
            if isinstance(value, str):
                if any(expr in value for expr in ['COALESCE', '(', ')', '+', '-', '*', '/', 'SELECT']):
                    expressions.append(f"{key}: {value}")
        
        return expressions
    
    def _would_be_empty_update(self, data, table_name):
        """Verificar si el UPDATE sería vacío después del filtrado"""
        data_dict = data.get('data', {}) if isinstance(data, dict) else {}
        
        metadata_fields = ['original_query', 'original_params', 'timestamp', 'metadata', 'tags', 'sync_status']
        valid_fields = 0
        
        for key, value in data_dict.items():
            if key in metadata_fields or value is None or key == 'id':
                continue
            
            # Verificar si es expresión SQL
            if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                continue
            
            valid_fields += 1
        
        return valid_fields == 0
    
    def _find_boolean_issues(self, data, table_name):
        """Encontrar problemas de conversión boolean"""
        issues = []
        data_dict = data.get('data', {}) if isinstance(data, dict) else {}
        
        # Campos que requieren enteros
        integer_fields = {
            'productos': ['stock', 'cantidad', 'producto_id'],
            'detalle_ventas': ['cantidad', 'venta_id', 'producto_id'],
            'ventas': ['vendedor_id']
        }
        
        # Campos boolean
        boolean_fields = {
            'productos': ['activo'],
            'categorias': ['activo'],
            'vendedores': ['activo']
        }
        
        for key, value in data_dict.items():
            if isinstance(value, bool):
                # Si es boolean pero debería ser entero
                if table_name in integer_fields and key in integer_fields[table_name]:
                    issues.append(f"{key}: boolean en campo entero")
                # Si es boolean en campo boolean pero mal convertido
                elif table_name in boolean_fields and key in boolean_fields[table_name]:
                    if not isinstance(value, (int, bool)):
                        issues.append(f"{key}: tipo incorrecto para boolean")
        
        return issues
    
    def _show_analysis_summary(self, problems):
        """Mostrar resumen del análisis"""
        logger.info("=" * 60)
        logger.info("📊 RESUMEN DE PROBLEMAS DETECTADOS")
        logger.info("=" * 60)
        
        for problem_type, items in problems.items():
            count = len(items)
            if count > 0:
                logger.info(f"🔴 {problem_type.replace('_', ' ').title()}: {count} elementos")
                for item in items[:3]:  # Mostrar solo los primeros 3
                    logger.info(f"   - ID {item['id']}: {item.get('table', 'N/A')}")
                if count > 3:
                    logger.info(f"   ... y {count - 3} más")
            else:
                logger.info(f"✅ {problem_type.replace('_', ' ').title()}: 0 elementos")
        
        logger.info("=" * 60)
    
    def fix_sync_queue(self):
        """Corregir todos los problemas en la cola de sincronización"""
        logger.info("🔧 Iniciando corrección de cola de sincronización...")
        
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # 1. Reordenar por dependencias de foreign keys
                logger.info("📋 Paso 1: Reordenando por dependencias...")
                self._reorder_by_dependencies(cursor)
                
                # 2. Limpiar expresiones SQL
                logger.info("🧹 Paso 2: Limpiando expresiones SQL...")
                self._clean_sql_expressions(cursor)
                
                # 3. Corregir parámetros
                logger.info("🔧 Paso 3: Corrigiendo parámetros...")
                self._fix_parameters(cursor)
                
                # 4. Corregir conversiones boolean
                logger.info("🔄 Paso 4: Corrigiendo conversiones boolean...")
                self._fix_boolean_conversions(cursor)
                
                # 5. Eliminar UPDATEs vacíos
                logger.info("🗑️ Paso 5: Eliminando UPDATEs vacíos...")
                self._remove_empty_updates(cursor)
                
                conn.commit()
                logger.info("✅ Corrección de cola completada")
                
        except Exception as e:
            logger.error(f"❌ Error corrigiendo cola: {e}")
    
    def _reorder_by_dependencies(self, cursor):
        """Reordenar elementos respetando foreign keys"""
        # Orden de prioridad (menor número = mayor prioridad)
        priority_order = {
            'categorias': 1,
            'vendedores': 2, 
            'productos': 3,
            'ventas': 4,
            'detalle_ventas': 5
        }
        
        # Obtener todos los elementos pendientes
        cursor.execute("""
            SELECT id, table_name, operation, data 
            FROM sync_queue 
            WHERE status = 'pending'
            ORDER BY id
        """)
        
        items = cursor.fetchall()
        
        # Reordenar y actualizar timestamps
        for i, item in enumerate(items):
            item_id, table_name, operation, data = item
            
            # Calcular nueva prioridad
            table_priority = priority_order.get(table_name, 6)
            operation_priority = 0 if operation == 'INSERT' else 1 if operation == 'UPDATE' else 2
            
            # Nuevo timestamp basado en prioridad
            new_timestamp = datetime.now().replace(
                microsecond=table_priority * 100000 + operation_priority * 10000 + i
            )
            
            cursor.execute("""
                UPDATE sync_queue 
                SET timestamp = ? 
                WHERE id = ?
            """, (new_timestamp.isoformat(), item_id))
    
    def _clean_sql_expressions(self, cursor):
        """Limpiar expresiones SQL de los datos"""
        cursor.execute("""
            SELECT id, table_name, operation, data 
            FROM sync_queue 
            WHERE status = 'pending'
        """)
        
        items = cursor.fetchall()
        
        for item in items:
            item_id, table_name, operation, data_json = item
            
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                # Limpiar expresiones SQL
                cleaned_data = {}
                for key, value in data_dict.items():
                    if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', '*', '/']):
                        logger.info(f"🧹 Removiendo expresión SQL: {key} = {value}")
                        continue
                    cleaned_data[key] = value
                
                # Actualizar datos limpios
                data['data'] = cleaned_data
                
                cursor.execute("""
                    UPDATE sync_queue 
                    SET data = ? 
                    WHERE id = ?
                """, (json.dumps(data), item_id))
                
            except Exception as e:
                logger.error(f"❌ Error limpiando item {item_id}: {e}")
    
    def _fix_parameters(self, cursor):
        """Corregir problemas de parámetros"""
        cursor.execute("""
            SELECT id, table_name, operation, data 
            FROM sync_queue 
            WHERE status = 'pending'
        """)
        
        items = cursor.fetchall()
        
        for item in items:
            item_id, table_name, operation, data_json = item
            
            try:
                data = json.loads(data_json)
                
                # Reconstruir query y parámetros correctos
                if operation == 'INSERT':
                    data = self._rebuild_insert_data(data, table_name)
                elif operation == 'UPDATE':
                    data = self._rebuild_update_data(data, table_name)
                
                cursor.execute("""
                    UPDATE sync_queue 
                    SET data = ? 
                    WHERE id = ?
                """, (json.dumps(data), item_id))
                
            except Exception as e:
                logger.error(f"❌ Error corrigiendo parámetros item {item_id}: {e}")
    
    def _rebuild_insert_data(self, data, table_name):
        """Reconstruir datos de INSERT correctamente"""
        data_dict = data.get('data', {})
        
        # Filtrar campos válidos
        valid_data = {}
        metadata_fields = ['original_query', 'original_params', 'timestamp', 'metadata', 'tags']
        
        for key, value in data_dict.items():
            if key not in metadata_fields and value is not None:
                valid_data[key] = value
        
        if valid_data:
            # Reconstruir query
            columns = list(valid_data.keys())
            placeholders = ['?' for _ in columns]
            values = list(valid_data.values())
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            data['original_query'] = query
            data['original_params'] = values
            data['data'] = valid_data
        
        return data
    
    def _rebuild_update_data(self, data, table_name):
        """Reconstruir datos de UPDATE correctamente"""
        data_dict = data.get('data', {})
        
        # Filtrar campos válidos
        valid_data = {}
        metadata_fields = ['original_query', 'original_params', 'timestamp', 'metadata', 'tags']
        
        for key, value in data_dict.items():
            if key not in metadata_fields and value is not None and key != 'id':
                valid_data[key] = value
        
        if valid_data and 'id' in data_dict:
            # Reconstruir query
            set_clauses = [f"{key} = ?" for key in valid_data.keys()]
            values = list(valid_data.values()) + [data_dict['id']]
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
            
            data['original_query'] = query
            data['original_params'] = values
            data['data'] = {**valid_data, 'id': data_dict['id']}
        
        return data
    
    def _fix_boolean_conversions(self, cursor):
        """Corregir conversiones boolean"""
        cursor.execute("""
            SELECT id, table_name, operation, data 
            FROM sync_queue 
            WHERE status = 'pending'
        """)
        
        items = cursor.fetchall()
        
        for item in items:
            item_id, table_name, operation, data_json = item
            
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                # Campos que requieren conversión específica
                boolean_fields = ['activo']
                integer_fields = {
                    'productos': ['stock', 'cantidad', 'producto_id'],
                    'detalle_ventas': ['cantidad', 'venta_id', 'producto_id'],
                    'ventas': ['vendedor_id']
                }
                
                fixed_data = {}
                for key, value in data_dict.items():
                    if isinstance(value, bool):
                        if key in boolean_fields:
                            # Boolean a entero para compatibilidad
                            fixed_data[key] = 1 if value else 0
                        elif table_name in integer_fields and key in integer_fields[table_name]:
                            # Boolean que debería ser entero
                            fixed_data[key] = 1 if value else 0
                        else:
                            fixed_data[key] = value
                    else:
                        fixed_data[key] = value
                
                data['data'] = fixed_data
                
                cursor.execute("""
                    UPDATE sync_queue 
                    SET data = ? 
                    WHERE id = ?
                """, (json.dumps(data), item_id))
                
            except Exception as e:
                logger.error(f"❌ Error corrigiendo boolean item {item_id}: {e}")
    
    def _remove_empty_updates(self, cursor):
        """Eliminar UPDATEs que serían vacíos"""
        cursor.execute("""
            SELECT id, table_name, operation, data 
            FROM sync_queue 
            WHERE status = 'pending' AND operation = 'UPDATE'
        """)
        
        items = cursor.fetchall()
        removed_count = 0
        
        for item in items:
            item_id, table_name, operation, data_json = item
            
            try:
                data = json.loads(data_json)
                
                if self._would_be_empty_update(data, table_name):
                    cursor.execute("""
                        UPDATE sync_queue 
                        SET status = 'skipped', 
                            attempts = 999 
                        WHERE id = ?
                    """, (item_id,))
                    removed_count += 1
                    logger.info(f"🗑️ Marcado como omitido UPDATE vacío: ID {item_id}")
                
            except Exception as e:
                logger.error(f"❌ Error verificando UPDATE vacío item {item_id}: {e}")
        
        logger.info(f"🗑️ Total UPDATEs vacíos omitidos: {removed_count}")
    
    def test_sync_with_remote(self):
        """Probar sincronización con base remota"""
        if not self.remote_available:
            logger.warning("⚠️ No hay conexión remota para probar")
            return False
        
        logger.info("🧪 Probando sincronización con base remota...")
        
        try:
            # Conectar a remoto
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                render_conn = psycopg2.connect(database_url)
            else:
                render_conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    database=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
            
            with sqlite3.connect(self.local_db_path) as local_conn:
                local_cursor = local_conn.cursor()
                
                # Obtener algunos elementos para probar
                local_cursor.execute("""
                    SELECT id, table_name, operation, data 
                    FROM sync_queue 
                    WHERE status = 'pending'
                    ORDER BY timestamp
                    LIMIT 5
                """)
                
                test_items = local_cursor.fetchall()
                
                if not test_items:
                    logger.info("✅ No hay elementos para probar")
                    return True
                
                success_count = 0
                
                with render_conn.cursor() as remote_cursor:
                    for item in test_items:
                        item_id, table_name, operation, data_json = item
                        
                        try:
                            data = json.loads(data_json)
                            
                            if operation == 'INSERT':
                                if self._test_insert(remote_cursor, table_name, data):
                                    success_count += 1
                            elif operation == 'UPDATE':
                                if self._test_update(remote_cursor, table_name, data):
                                    success_count += 1
                            
                        except Exception as e:
                            logger.error(f"❌ Error probando item {item_id}: {e}")
                
                # Rollback todas las operaciones de prueba
                render_conn.rollback()
                logger.info(f"🧪 Prueba completada: {success_count}/{len(test_items)} exitosos")
                
                return success_count == len(test_items)
            
        except Exception as e:
            logger.error(f"❌ Error en prueba de sincronización: {e}")
            return False
        finally:
            if 'render_conn' in locals():
                render_conn.close()
    
    def _test_insert(self, cursor, table_name, data):
        """Probar inserción remota"""
        try:
            data_dict = data.get('data', {})
            
            # Adaptar datos
            adapted_data = self._adapt_data_for_postgres(data_dict, table_name)
            
            if not adapted_data:
                return False
            
            columns = list(adapted_data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(adapted_data.values())
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            cursor.execute(query, values)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error en prueba INSERT {table_name}: {e}")
            return False
    
    def _test_update(self, cursor, table_name, data):
        """Probar actualización remota"""
        try:
            data_dict = data.get('data', {})
            
            if 'id' not in data_dict:
                return False
            
            adapted_data = self._adapt_data_for_postgres(data_dict, table_name)
            
            set_clauses = []
            values = []
            
            for key, value in adapted_data.items():
                if key != 'id':
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return True  # UPDATE vacío es "exitoso"
            
            values.append(adapted_data['id'])
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = %s"
            
            cursor.execute(query, values)
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error en prueba UPDATE {table_name}: {e}")
            return False
    
    def _adapt_data_for_postgres(self, data, table_name):
        """Adaptar datos para PostgreSQL"""
        adapted = {}
        
        for key, value in data.items():
            # Convertir Decimal a float
            if isinstance(value, Decimal):
                adapted[key] = float(value)
            # Convertir boolean apropiadamente
            elif isinstance(value, bool):
                if key == 'activo':
                    adapted[key] = value  # PostgreSQL acepta boolean
                else:
                    adapted[key] = 1 if value else 0
            # Saltar valores None
            elif value is not None:
                adapted[key] = value
        
        return adapted
    
    def run_full_fix(self):
        """Ejecutar corrección completa"""
        logger.info("🚀 INICIANDO CORRECCIÓN COMPLETA DE ERRORES DE SINCRONIZACIÓN")
        logger.info("=" * 70)
        
        # 1. Analizar problemas
        problems = self.analyze_sync_queue()
        
        if not any(problems.values()):
            logger.info("✅ No se detectaron problemas en la cola")
            return True
        
        # 2. Corregir problemas
        self.fix_sync_queue()
        
        # 3. Probar con remoto si está disponible
        if self.remote_available:
            if self.test_sync_with_remote():
                logger.info("✅ Prueba de sincronización remota exitosa")
            else:
                logger.warning("⚠️ Algunos elementos aún tienen problemas")
        
        # 4. Mostrar estado final
        self._show_final_status()
        
        logger.info("=" * 70)
        logger.info("🎉 CORRECCIÓN COMPLETA FINALIZADA")
        
        return True
    
    def _show_final_status(self):
        """Mostrar estado final de la cola"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
                status_counts = cursor.fetchall()
                
                logger.info("📊 ESTADO FINAL DE LA COLA:")
                for status, count in status_counts:
                    logger.info(f"   {status}: {count} elementos")
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado final: {e}")

def main():
    """Función principal"""
    print("🔧 CORRECTOR DE ERRORES CRÍTICOS DE SINCRONIZACIÓN")
    print("=" * 60)
    
    fixer = SyncErrorFixer()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--analyze-only':
        fixer.analyze_sync_queue()
    else:
        fixer.run_full_fix()

if __name__ == "__main__":
    main()

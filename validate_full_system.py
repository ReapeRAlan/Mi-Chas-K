#!/usr/bin/env python3
"""
Validador Completo del Sistema Mi-Chas-K
Verifica toda la estructura de la base de datos remota PostgreSQL
y valida que se pueden realizar todas las operaciones CRUD desde local
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
import logging
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Validador completo del sistema híbrido"""
    
    def __init__(self):
        self.local_db_path = os.path.join(os.getcwd(), 'data', 'local_database.db')
        self.validation_results = {
            'remote_connection': False,
            'local_connection': False,
            'schema_validation': {},
            'data_validation': {},
            'crud_operations': {},
            'compatibility': {}
        }
    
    def validate_remote_connection(self):
        """Validar conexión a base de datos remota"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("❌ DATABASE_URL no configurada")
                return False
            
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ Conexión remota exitosa: {version}")
                self.validation_results['remote_connection'] = True
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error conectando a base remota: {e}")
            return False
    
    def validate_local_connection(self):
        """Validar conexión a base de datos local"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sqlite_version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ Conexión local exitosa: SQLite {version}")
                self.validation_results['local_connection'] = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Error conectando a base local: {e}")
            return False
    
    def validate_remote_schema(self):
        """Validar esquema completo de la base remota"""
        try:
            database_url = os.getenv('DATABASE_URL')
            with psycopg2.connect(database_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    
                    # Obtener todas las tablas
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name
                    """)
                    
                    tables = cursor.fetchall()
                    logger.info(f"📋 Tablas encontradas en Render: {[t['table_name'] for t in tables]}")
                    
                    # Validar cada tabla
                    for table in tables:
                        table_name = table['table_name']
                        schema_info = self._validate_table_schema(cursor, table_name)
                        data_info = self._validate_table_data(cursor, table_name)
                        
                        self.validation_results['schema_validation'][table_name] = schema_info
                        self.validation_results['data_validation'][table_name] = data_info
                        
                        logger.info(f"📊 {table_name}: {schema_info['column_count']} columnas, {data_info['row_count']} registros")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error validando esquema remoto: {e}")
            return False
    
    def _validate_table_schema(self, cursor, table_name):
        """Validar esquema de una tabla específica"""
        try:
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
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            schema_info = {
                'column_count': len(columns),
                'columns': {},
                'primary_key': None,
                'foreign_keys': []
            }
            
            for col in columns:
                schema_info['columns'][col['column_name']] = {
                    'type': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default'],
                    'max_length': col['character_maximum_length']
                }
            
            # Obtener primary key
            cursor.execute("""
                SELECT column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s 
                    AND tc.constraint_type = 'PRIMARY KEY'
            """, (table_name,))
            
            pk_result = cursor.fetchone()
            if pk_result:
                schema_info['primary_key'] = pk_result['column_name']
            
            # Obtener foreign keys
            cursor.execute("""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = %s 
                    AND tc.constraint_type = 'FOREIGN KEY'
            """, (table_name,))
            
            fks = cursor.fetchall()
            for fk in fks:
                schema_info['foreign_keys'].append({
                    'column': fk['column_name'],
                    'references_table': fk['foreign_table_name'],
                    'references_column': fk['foreign_column_name']
                })
            
            return schema_info
            
        except Exception as e:
            logger.error(f"❌ Error validando esquema de {table_name}: {e}")
            return {'error': str(e)}
    
    def _validate_table_data(self, cursor, table_name):
        """Validar datos de una tabla específica"""
        try:
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count_result = cursor.fetchone()
            row_count = count_result['count'] if count_result else 0
            
            data_info = {
                'row_count': row_count,
                'sample_data': [],
                'data_types_found': {}
            }
            
            if row_count > 0:
                # Obtener muestra de datos
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_rows = cursor.fetchall()
                
                for row in sample_rows:
                    row_dict = dict(row)
                    # Convertir tipos especiales para JSON
                    for key, value in row_dict.items():
                        if isinstance(value, Decimal):
                            row_dict[key] = float(value)
                        elif isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                        elif hasattr(value, 'isoformat'):  # date objects
                            row_dict[key] = value.isoformat()
                        elif value is None:
                            row_dict[key] = None
                        else:
                            row_dict[key] = str(value)  # Convertir otros tipos a string
                    
                    data_info['sample_data'].append(row_dict)
                
                # Analizar tipos de datos encontrados
                if sample_rows:
                    first_row = sample_rows[0]
                    for column_name, value in first_row.items():
                        data_info['data_types_found'][column_name] = type(value).__name__
            
            return data_info
            
        except Exception as e:
            logger.error(f"❌ Error validando datos de {table_name}: {e}")
            return {'error': str(e)}
    
    def validate_crud_operations(self):
        """Validar que se pueden realizar operaciones CRUD"""
        try:
            # Importar el adaptador
            from database.connection_adapter import db_adapter
            
            crud_results = {}
            
            # Test 1: CREATE - Crear una categoría de prueba
            logger.info("🔄 Probando operación CREATE...")
            test_categoria = {
                'nombre': f'Test_CRUD_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'descripcion': 'Categoría de prueba para validación CRUD',
                'activo': True
            }
            
            result = db_adapter.execute_update("""
                INSERT INTO categorias (nombre, descripcion, activo)
                VALUES (?, ?, ?)
            """, (test_categoria['nombre'], test_categoria['descripcion'], test_categoria['activo']))
            
            crud_results['create'] = result is not None
            logger.info(f"✅ CREATE: {'Exitoso' if crud_results['create'] else 'Fallido'}")
            
            # Test 2: READ - Leer categorías
            logger.info("🔄 Probando operación READ...")
            categorias = db_adapter.execute_query("SELECT * FROM categorias WHERE nombre LIKE 'Test_CRUD_%'")
            crud_results['read'] = len(categorias) > 0
            logger.info(f"✅ READ: {'Exitoso' if crud_results['read'] else 'Fallido'} - {len(categorias)} categorías encontradas")
            
            # Test 3: UPDATE - Actualizar la categoría de prueba
            if categorias:
                logger.info("🔄 Probando operación UPDATE...")
                test_id = categorias[0]['id']
                result = db_adapter.execute_update("""
                    UPDATE categorias 
                    SET descripcion = 'Categoría actualizada por validación CRUD'
                    WHERE id = ?
                """, (test_id,))
                
                crud_results['update'] = result is not None
                logger.info(f"✅ UPDATE: {'Exitoso' if crud_results['update'] else 'Fallido'}")
                
                # Test 4: DELETE - Eliminar la categoría de prueba
                logger.info("🔄 Probando operación DELETE...")
                result = db_adapter.execute_update("DELETE FROM categorias WHERE id = ?", (test_id,))
                crud_results['delete'] = result is not None
                logger.info(f"✅ DELETE: {'Exitoso' if crud_results['delete'] else 'Fallido'}")
            
            # Test 5: Operaciones complejas - Crear un producto con relaciones
            logger.info("🔄 Probando operaciones complejas...")
            
            # Crear producto de prueba
            test_producto = {
                'nombre': f'Producto_Test_{datetime.now().strftime("%H%M%S")}',
                'precio': 99.99,
                'categoria': 'General',
                'stock': 50,
                'descripcion': 'Producto de prueba para validación',
                'activo': True
            }
            
            producto_id = db_adapter.execute_update("""
                INSERT INTO productos (nombre, precio, categoria, stock, descripcion, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                test_producto['nombre'],
                test_producto['precio'],
                test_producto['categoria'],
                test_producto['stock'],
                test_producto['descripcion'],
                test_producto['activo']
            ))
            
            if producto_id:
                # Crear venta de prueba
                venta_id = db_adapter.execute_update("""
                    INSERT INTO ventas (total, metodo_pago, vendedor, observaciones)
                    VALUES (?, ?, ?, ?)
                """, (199.98, 'Efectivo', 'Sistema', 'Venta de prueba para validación'))
                
                if venta_id:
                    # Crear detalle de venta
                    detalle_id = db_adapter.execute_update("""
                        INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (venta_id, producto_id, 2, test_producto['precio'], test_producto['precio'] * 2))
                    
                    crud_results['complex_operations'] = detalle_id is not None
                    
                    # Limpiar datos de prueba
                    db_adapter.execute_update("DELETE FROM detalle_ventas WHERE id = ?", (detalle_id,))
                    db_adapter.execute_update("DELETE FROM ventas WHERE id = ?", (venta_id,))
                
                db_adapter.execute_update("DELETE FROM productos WHERE id = ?", (producto_id,))
            
            logger.info(f"✅ OPERACIONES COMPLEJAS: {'Exitoso' if crud_results.get('complex_operations', False) else 'Fallido'}")
            
            self.validation_results['crud_operations'] = crud_results
            return all(crud_results.values())
            
        except Exception as e:
            logger.error(f"❌ Error validando operaciones CRUD: {e}")
            return False
    
    def validate_compatibility(self):
        """Validar compatibilidad entre esquemas local y remoto"""
        try:
            # Comparar esquemas de tablas principales
            main_tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
            compatibility_results = {}
            
            for table in main_tables:
                # Obtener esquema local
                with sqlite3.connect(self.local_db_path) as local_conn:
                    cursor = local_conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table})")
                    local_columns = cursor.fetchall()
                    local_schema = {col[1]: col[2] for col in local_columns}  # nombre: tipo
                
                # Obtener esquema remoto
                remote_schema = self.validation_results['schema_validation'].get(table, {}).get('columns', {})
                
                # Comparar
                compatibility = {
                    'local_columns': list(local_schema.keys()),
                    'remote_columns': list(remote_schema.keys()),
                    'common_columns': [],
                    'local_only': [],
                    'remote_only': [],
                    'type_conflicts': []
                }
                
                for col in local_schema:
                    if col in remote_schema:
                        compatibility['common_columns'].append(col)
                        # Validar tipos (simplificado)
                        local_type = local_schema[col].upper()
                        remote_type = remote_schema[col]['type'].upper()
                        if not self._types_compatible(local_type, remote_type):
                            compatibility['type_conflicts'].append({
                                'column': col,
                                'local_type': local_type,
                                'remote_type': remote_type
                            })
                    else:
                        compatibility['local_only'].append(col)
                
                for col in remote_schema:
                    if col not in local_schema:
                        compatibility['remote_only'].append(col)
                
                compatibility_results[table] = compatibility
                
                # Log de compatibilidad
                logger.info(f"🔍 {table}: {len(compatibility['common_columns'])} columnas comunes, "
                           f"{len(compatibility['local_only'])} solo local, "
                           f"{len(compatibility['remote_only'])} solo remoto, "
                           f"{len(compatibility['type_conflicts'])} conflictos de tipo")
            
            self.validation_results['compatibility'] = compatibility_results
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validando compatibilidad: {e}")
            return False
    
    def _types_compatible(self, local_type, remote_type):
        """Verificar si los tipos de datos son compatibles"""
        # Mapeo de tipos compatibles
        type_mapping = {
            'TEXT': ['CHARACTER VARYING', 'VARCHAR', 'TEXT', 'CHAR'],
            'INTEGER': ['INTEGER', 'BIGINT', 'SMALLINT'],
            'REAL': ['NUMERIC', 'DECIMAL', 'DOUBLE PRECISION', 'REAL'],
            'BOOLEAN': ['BOOLEAN', 'BOOL'],
            'TIMESTAMP': ['TIMESTAMP', 'DATETIME', 'DATE']
        }
        
        for local_base, remote_types in type_mapping.items():
            if local_base in local_type:
                return any(remote_t in remote_type for remote_t in remote_types)
        
        return local_type == remote_type
    
    def generate_report(self):
        """Generar reporte completo de validación"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'validation_results': self.validation_results,
                'summary': {
                    'total_score': 0,
                    'max_score': 5,
                    'status': 'UNKNOWN',
                    'recommendations': []
                }
            }
            
            # Calcular puntaje
            score = 0
            if self.validation_results['remote_connection']:
                score += 1
            if self.validation_results['local_connection']:
                score += 1
            if self.validation_results['schema_validation']:
                score += 1
            if self.validation_results['crud_operations']:
                score += 1
            if self.validation_results['compatibility']:
                score += 1
            
            report['summary']['total_score'] = score
            
            # Determinar estado
            if score >= 4:
                report['summary']['status'] = 'EXCELENTE'
            elif score >= 3:
                report['summary']['status'] = 'BUENO'
            elif score >= 2:
                report['summary']['status'] = 'REGULAR'
            else:
                report['summary']['status'] = 'CRÍTICO'
            
            # Generar recomendaciones
            if not self.validation_results['remote_connection']:
                report['summary']['recommendations'].append("Verificar configuración de DATABASE_URL")
            
            if not self.validation_results['local_connection']:
                report['summary']['recommendations'].append("Verificar integridad de base de datos local")
            
            # Guardar reporte
            report_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 Reporte guardado en: {report_path}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte: {e}")
            return None
    
    def run_full_validation(self):
        """Ejecutar validación completa del sistema"""
        logger.info("🚀 Iniciando validación completa del sistema Mi-Chas-K")
        logger.info("=" * 60)
        
        # 1. Conexiones
        logger.info("1️⃣ Validando conexiones...")
        self.validate_remote_connection()
        self.validate_local_connection()
        
        # 2. Esquema remoto
        if self.validation_results['remote_connection']:
            logger.info("2️⃣ Validando esquema remoto...")
            self.validate_remote_schema()
        
        # 3. Operaciones CRUD
        logger.info("3️⃣ Validando operaciones CRUD...")
        self.validate_crud_operations()
        
        # 4. Compatibilidad
        logger.info("4️⃣ Validando compatibilidad...")
        self.validate_compatibility()
        
        # 5. Generar reporte
        logger.info("5️⃣ Generando reporte...")
        report = self.generate_report()
        
        # Resumen final
        logger.info("=" * 60)
        logger.info("📋 RESUMEN DE VALIDACIÓN")
        logger.info("=" * 60)
        
        if report:
            logger.info(f"🎯 Estado: {report['summary']['status']}")
            logger.info(f"📊 Puntaje: {report['summary']['total_score']}/{report['summary']['max_score']}")
            
            if report['summary']['recommendations']:
                logger.info("💡 Recomendaciones:")
                for rec in report['summary']['recommendations']:
                    logger.info(f"   - {rec}")
        
        logger.info("✅ Validación completa finalizada")
        return report

def main():
    """Función principal"""
    validator = SystemValidator()
    report = validator.run_full_validation()
    
    if report and report['summary']['status'] in ['EXCELENTE', 'BUENO']:
        print("\n🎉 ¡Sistema validado exitosamente!")
        print("El sistema está listo para operaciones CRUD completas.")
    else:
        print("\n⚠️ Se encontraron problemas en la validación.")
        print("Revisa el reporte para más detalles.")

if __name__ == "__main__":
    main()

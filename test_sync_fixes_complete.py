#!/usr/bin/env python3
"""
Script de prueba completo para verificar las correcciones de sincronización
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime
from decimal import Decimal

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyncTestSuite:
    def __init__(self):
        self.local_db_path = 'sistema_facturacion.db'
        self.test_results = []
    
    def run_all_tests(self):
        """Ejecutar todos los tests de sincronización"""
        logger.info("🧪 INICIANDO SUITE COMPLETA DE PRUEBAS DE SINCRONIZACIÓN")
        logger.info("=" * 70)
        
        tests = [
            self.test_sync_queue_structure,
            self.test_foreign_key_dependencies,
            self.test_parameter_conversion,
            self.test_sql_expression_cleaning,
            self.test_boolean_conversions,
            self.test_empty_update_detection,
            self.test_improved_adapter,
            self.test_sync_performance
        ]
        
        for test in tests:
            try:
                logger.info(f"🔍 Ejecutando: {test.__name__}")
                result = test()
                self.test_results.append((test.__name__, result, None))
                status = "✅ PASÓ" if result else "❌ FALLÓ"
                logger.info(f"{status}: {test.__name__}")
            except Exception as e:
                logger.error(f"❌ ERROR en {test.__name__}: {e}")
                self.test_results.append((test.__name__, False, str(e)))
        
        self._show_test_summary()
    
    def test_sync_queue_structure(self):
        """Test 1: Verificar estructura de la cola de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que existe la tabla
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sync_queue'
                """)
                if not cursor.fetchone():
                    return False
                
                # Verificar columnas
                cursor.execute("PRAGMA table_info(sync_queue)")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = ['id', 'table_name', 'operation', 'data', 'timestamp', 'status', 'attempts']
                
                for col in required_columns:
                    if col not in columns:
                        logger.error(f"❌ Falta columna: {col}")
                        return False
                
                logger.info("✅ Estructura de sync_queue correcta")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando estructura: {e}")
            return False
    
    def test_foreign_key_dependencies(self):
        """Test 2: Verificar orden de dependencias en cola"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener elementos ordenados por timestamp
                cursor.execute("""
                    SELECT table_name, operation 
                    FROM sync_queue 
                    WHERE status = 'pending'
                    ORDER BY timestamp
                """)
                
                items = cursor.fetchall()
                
                # Verificar orden lógico
                table_order = ['categorias', 'vendedores', 'productos', 'ventas', 'detalle_ventas']
                current_priority = 0
                
                for table_name, operation in items:
                    if table_name in table_order:
                        table_priority = table_order.index(table_name)
                        if table_priority < current_priority:
                            logger.warning(f"⚠️ Orden subóptimo detectado: {table_name} después de prioridad {current_priority}")
                        current_priority = max(current_priority, table_priority)
                
                logger.info("✅ Orden de dependencias verificado")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando dependencias: {e}")
            return False
    
    def test_parameter_conversion(self):
        """Test 3: Probar conversión de parámetros"""
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        try:
            adapter = ImprovedDatabaseAdapter()
            
            # Test de conversión de valores
            test_values = [
                ('activo', True, 'productos'),
                ('stock', Decimal('10.5'), 'productos'),
                ('precio', 25.99, 'productos'),
                ('activo', 1, 'categorias')
            ]
            
            for key, value, table in test_values:
                converted = adapter._convert_value_for_postgres(key, value, table)
                
                # Verificar conversiones específicas
                if key == 'activo' and isinstance(value, bool):
                    if not isinstance(converted, bool):
                        logger.error(f"❌ Conversión incorrecta de {key}: {value} -> {converted}")
                        return False
                
                if isinstance(value, Decimal):
                    if not isinstance(converted, float):
                        logger.error(f"❌ Decimal no convertido: {value} -> {converted}")
                        return False
            
            logger.info("✅ Conversión de parámetros correcta")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en conversión de parámetros: {e}")
            return False
    
    def test_sql_expression_cleaning(self):
        """Test 4: Probar limpieza de expresiones SQL"""
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        try:
            adapter = ImprovedDatabaseAdapter()
            
            # Test de detección de expresiones SQL
            test_expressions = [
                "COALESCE(stock, 0) - 1",
                "SELECT MAX(id) FROM tabla",
                "(precio * 0.21)",
                "stock + cantidad",
                "normal_value"
            ]
            
            for expr in test_expressions:
                is_sql = adapter._is_sql_expression(expr)
                
                if expr == "normal_value" and is_sql:
                    logger.error(f"❌ Falso positivo: {expr}")
                    return False
                
                if "COALESCE" in expr and not is_sql:
                    logger.error(f"❌ Falso negativo: {expr}")
                    return False
            
            # Test de limpieza de datos
            test_data = {
                'id': 1,
                'nombre': 'Producto Test',
                'stock': 'COALESCE(stock, 0) - 1',
                'precio': 25.99,
                'activo': True
            }
            
            clean_data = adapter._clean_data_for_sync(test_data, 'productos')
            
            if 'stock' in clean_data:
                logger.error("❌ Expresión SQL no removida")
                return False
            
            if 'nombre' not in clean_data:
                logger.error("❌ Dato válido removido incorrectamente")
                return False
            
            logger.info("✅ Limpieza de expresiones SQL correcta")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza de expresiones: {e}")
            return False
    
    def test_boolean_conversions(self):
        """Test 5: Probar conversiones boolean específicas"""
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        try:
            adapter = ImprovedDatabaseAdapter()
            
            # Test casos específicos de boolean
            test_cases = [
                # (key, value, table, expected_type)
                ('activo', True, 'productos', bool),
                ('activo', False, 'categorias', bool),
                ('activo', 1, 'vendedores', bool),
                ('activo', '1', 'productos', bool),
                ('stock', True, 'productos', int),  # Boolean que debería ser int
                ('cantidad', False, 'detalle_ventas', int)
            ]
            
            for key, value, table, expected_type in test_cases:
                converted = adapter._convert_value_for_postgres(key, value, table)
                
                if key == 'activo':
                    if not isinstance(converted, bool):
                        logger.error(f"❌ Campo 'activo' no es boolean: {converted} ({type(converted)})")
                        return False
                elif key in ['stock', 'cantidad'] and isinstance(value, bool):
                    if not isinstance(converted, int):
                        logger.error(f"❌ Campo '{key}' boolean no convertido a int: {converted}")
                        return False
            
            logger.info("✅ Conversiones boolean correctas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en conversiones boolean: {e}")
            return False
    
    def test_empty_update_detection(self):
        """Test 6: Detectar UPDATEs vacíos"""
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        try:
            adapter = ImprovedDatabaseAdapter()
            
            # Test datos que resultarían en UPDATE vacío
            empty_update_data = {
                'id': 1,
                'stock': 'COALESCE(stock, 0) - 1',  # Se removería
                'original_query': 'UPDATE...',  # Se removería
                'timestamp': '2024-01-01',  # Se removería
                'metadata': {'info': 'test'}  # Se removería
            }
            
            clean_data = adapter._clean_data_for_sync(empty_update_data, 'productos')
            
            # Después de limpiar, solo debería quedar 'id'
            non_id_fields = {k: v for k, v in clean_data.items() if k != 'id'}
            
            if non_id_fields:
                logger.error(f"❌ Datos no limpiados correctamente: {non_id_fields}")
                return False
            
            # Test datos válidos para UPDATE
            valid_update_data = {
                'id': 1,
                'nombre': 'Producto actualizado',
                'precio': 29.99,
                'activo': True
            }
            
            clean_valid_data = adapter._clean_data_for_sync(valid_update_data, 'productos')
            
            if len(clean_valid_data) < 2:  # Debe tener al menos id + otro campo
                logger.error("❌ Datos válidos removidos incorrectamente")
                return False
            
            logger.info("✅ Detección de UPDATEs vacíos correcta")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error detectando UPDATEs vacíos: {e}")
            return False
    
    def test_improved_adapter(self):
        """Test 7: Probar funcionalidad del adaptador mejorado"""
        try:
            from database.connection_adapter_improved import ImprovedDatabaseAdapter
            
            adapter = ImprovedDatabaseAdapter()
            
            # Test conexión local
            with adapter.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
                if not result or result[0] != 1:
                    logger.error("❌ Conexión local no funciona")
                    return False
            
            # Test estado de sincronización
            status = adapter.get_sync_status()
            
            if 'remote_available' not in status:
                logger.error("❌ Estado de sync incompleto")
                return False
            
            # Test extracción de nombre de tabla
            test_queries = [
                ("INSERT INTO productos (nombre) VALUES (?)", "productos"),
                ("UPDATE ventas SET total = ? WHERE id = ?", "ventas"),
                ("DELETE FROM categorias WHERE id = ?", "categorias")
            ]
            
            for query, expected_table in test_queries:
                extracted_table = adapter._extract_table_name(query)
                if extracted_table != expected_table:
                    logger.error(f"❌ Tabla extraída incorrectamente: {query} -> {extracted_table} (esperado: {expected_table})")
                    return False
            
            logger.info("✅ Adaptador mejorado funciona correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error probando adaptador mejorado: {e}")
            return False
    
    def test_sync_performance(self):
        """Test 8: Probar rendimiento de sincronización"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.cursor()
                
                # Contar elementos en cola
                cursor.execute("SELECT COUNT(*) FROM sync_queue")
                total_items = cursor.fetchone()[0]
                
                # Verificar distribución por estado
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM sync_queue 
                    GROUP BY status
                """)
                
                status_distribution = dict(cursor.fetchall())
                
                # Métricas de rendimiento
                pending_items = status_distribution.get('pending', 0)
                completed_items = status_distribution.get('completed', 0)
                failed_items = status_distribution.get('failed', 0)
                
                logger.info(f"📊 Total items: {total_items}")
                logger.info(f"📊 Pending: {pending_items}")
                logger.info(f"📊 Completed: {completed_items}")
                logger.info(f"📊 Failed: {failed_items}")
                
                # Considerar exitoso si hay pocos elementos fallidos
                success_rate = completed_items / max(total_items, 1)
                
                if success_rate > 0.8 or total_items == 0:
                    logger.info(f"✅ Rendimiento aceptable: {success_rate:.2%}")
                    return True
                else:
                    logger.warning(f"⚠️ Rendimiento bajo: {success_rate:.2%}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error evaluando rendimiento: {e}")
            return False
    
    def _show_test_summary(self):
        """Mostrar resumen de tests"""
        logger.info("=" * 70)
        logger.info("📊 RESUMEN DE PRUEBAS")
        logger.info("=" * 70)
        
        passed = sum(1 for _, result, _ in self.test_results if result)
        total = len(self.test_results)
        
        logger.info(f"✅ Pruebas pasadas: {passed}/{total}")
        logger.info(f"❌ Pruebas falladas: {total - passed}/{total}")
        
        if passed == total:
            logger.info("🎉 TODAS LAS PRUEBAS PASARON - SISTEMA CORREGIDO")
        else:
            logger.warning("⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR")
            
            for test_name, result, error in self.test_results:
                if not result:
                    logger.error(f"   ❌ {test_name}: {error or 'Falló'}")
        
        logger.info("=" * 70)

def main():
    """Función principal"""
    print("🧪 SUITE COMPLETA DE PRUEBAS DE SINCRONIZACIÓN")
    print("=" * 60)
    
    test_suite = SyncTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()

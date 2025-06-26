#!/usr/bin/env python3
"""
Script directo para resolver errores críticos de sincronización
"""

import sqlite3
import json
import re
from datetime import datetime

def fix_sync_issues():
    """Corregir problemas críticos directamente"""
    print("🔧 Iniciando corrección directa de errores...")
    
    try:
        # Conectar a BD local
        conn = sqlite3.connect('sistema_facturacion.db')
        cursor = conn.cursor()
        
        # 1. Limpiar expresiones SQL problemáticas
        print("🧹 Limpiando expresiones SQL...")
        cursor.execute("SELECT id, data FROM sync_queue WHERE status = 'pending'")
        items = cursor.fetchall()
        
        cleaned_count = 0
        for item_id, data_json in items:
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                # Limpiar campos problemáticos
                clean_data = {}
                for key, value in data_dict.items():
                    # Saltar metadatos
                    if key in ['original_query', 'original_params', 'timestamp', 'metadata', 'tags']:
                        continue
                    
                    # Saltar expresiones SQL
                    if isinstance(value, str) and any(op in str(value) for op in ['COALESCE', '(', ')', '+', '-', 'SELECT']):
                        print(f"  🗑️ Removiendo expresión SQL: {key} = {value}")
                        continue
                    
                    # Convertir boolean apropiadamente
                    if isinstance(value, bool):
                        if key == 'activo':
                            clean_data[key] = value  # Mantener como boolean
                        else:
                            clean_data[key] = 1 if value else 0  # Convertir a entero
                    elif value is not None:
                        clean_data[key] = value
                
                # Actualizar datos limpios
                data['data'] = clean_data
                cursor.execute("UPDATE sync_queue SET data = ? WHERE id = ?", 
                             (json.dumps(data), item_id))
                cleaned_count += 1
                
            except Exception as e:
                print(f"  ❌ Error limpiando item {item_id}: {e}")
        
        print(f"✅ Limpiados {cleaned_count} elementos")
        
        # 2. Marcar UPDATEs vacíos como omitidos
        print("🗑️ Marcando UPDATEs vacíos como omitidos...")
        cursor.execute("""
            SELECT id, table_name, data 
            FROM sync_queue 
            WHERE status = 'pending' AND operation = 'UPDATE'
        """)
        
        update_items = cursor.fetchall()
        skipped_count = 0
        
        for item_id, table_name, data_json in update_items:
            try:
                data = json.loads(data_json)
                data_dict = data.get('data', {})
                
                # Contar campos válidos (excluyendo id)
                valid_fields = 0
                for key, value in data_dict.items():
                    if key != 'id' and value is not None:
                        valid_fields += 1
                
                if valid_fields == 0:
                    cursor.execute("""
                        UPDATE sync_queue 
                        SET status = 'skipped' 
                        WHERE id = ?
                    """, (item_id,))
                    skipped_count += 1
                    print(f"  🗑️ UPDATE vacío omitido: ID {item_id}")
                
            except Exception as e:
                print(f"  ❌ Error verificando UPDATE {item_id}: {e}")
        
        print(f"✅ Omitidos {skipped_count} UPDATEs vacíos")
        
        # 3. Reordenar por dependencias
        print("📋 Reordenando por dependencias...")
        
        # Definir orden de prioridad
        priority_order = {
            'categorias': 1,
            'vendedores': 2,
            'productos': 3,
            'ventas': 4,
            'detalle_ventas': 5
        }
        
        cursor.execute("""
            SELECT id, table_name, operation
            FROM sync_queue 
            WHERE status = 'pending'
            ORDER BY id
        """)
        
        pending_items = cursor.fetchall()
        
        for i, (item_id, table_name, operation) in enumerate(pending_items):
            # Calcular nueva prioridad
            table_priority = priority_order.get(table_name, 6)
            operation_priority = 0 if operation == 'INSERT' else 1 if operation == 'UPDATE' else 2
            
            # Nuevo timestamp con prioridad
            new_timestamp = datetime.now().replace(
                microsecond=table_priority * 100000 + operation_priority * 10000 + i
            )
            
            cursor.execute("""
                UPDATE sync_queue 
                SET timestamp = ? 
                WHERE id = ?
            """, (new_timestamp.isoformat(), item_id))
        
        print(f"✅ Reordenados {len(pending_items)} elementos")
        
        # 4. Mostrar estado final
        cursor.execute("SELECT status, COUNT(*) FROM sync_queue GROUP BY status")
        final_status = cursor.fetchall()
        
        print("📊 Estado final de la cola:")
        for status, count in final_status:
            print(f"  {status}: {count} elementos")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        print("🎉 Corrección completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en corrección: {e}")
        return False

def test_adapter_integration():
    """Probar integración con adaptador mejorado"""
    print("\n🧪 Probando adaptador mejorado...")
    
    try:
        # Importar adaptador mejorado
        import sys
        sys.path.append('/home/ghost/Escritorio/Mi-Chas-K')
        
        from database.connection_adapter_improved import ImprovedDatabaseAdapter
        
        # Crear instancia
        adapter = ImprovedDatabaseAdapter()
        
        # Probar conexión
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] == 1:
                print("✅ Conexión local funciona")
            else:
                print("❌ Problema con conexión local")
                return False
        
        # Probar estado de sync
        status = adapter.get_sync_status()
        print(f"📊 Estado de sincronización: {status}")
        
        # Probar limpieza de datos
        test_data = {
            'id': 1,
            'nombre': 'Test',
            'stock': 'COALESCE(stock, 0) - 1',  # Expresión SQL
            'activo': True
        }
        
        clean_data = adapter._clean_data_for_sync(test_data, 'productos')
        
        if 'stock' not in clean_data:
            print("✅ Limpieza de expresiones SQL funciona")
        else:
            print("❌ Expresiones SQL no se limpiaron")
            return False
        
        if 'activo' in clean_data and isinstance(clean_data['activo'], bool):
            print("✅ Conversión boolean funciona")
        else:
            print("❌ Conversión boolean falló")
            return False
        
        print("🎉 Adaptador mejorado funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando adaptador: {e}")
        return False

if __name__ == '__main__':
    print("🚀 CORRECCIÓN DIRECTA DE ERRORES CRÍTICOS")
    print("=" * 50)
    
    # Ejecutar corrección
    if fix_sync_issues():
        # Probar adaptador
        test_adapter_integration()
    else:
        print("❌ La corrección falló")

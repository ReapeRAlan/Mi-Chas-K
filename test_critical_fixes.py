#!/usr/bin/env python3
"""
Test crítico para verificar que los errores de tipos y sincronización están resueltos
"""

import sys
import os
sys.path.append(os.getcwd())

from database.connection_adapter import DatabaseAdapter
from datetime import datetime
from decimal import Decimal
import json

def test_decimal_json_serialization():
    """Test: Los Decimals deben convertirse a float para JSON"""
    print("🧪 Test: Serialización JSON de Decimals...")
    
    adapter = DatabaseAdapter()
    
    # Test data con Decimal
    test_data = {
        'precio': Decimal('18.50'),
        'total': Decimal('37.00'),
        'descuento': Decimal('0.00')
    }
    
    # Limpiar para JSON
    cleaned = adapter._clean_data_for_json(test_data)
    
    try:
        json.dumps(cleaned)  # Debe funcionar sin error
        print("✅ Serialización JSON de Decimals: OK")
        return True
    except Exception as e:
        print(f"❌ Error serialización JSON: {e}")
        return False

def test_boolean_conversion():
    """Test: Los booleanos deben convertirse correctamente"""
    print("🧪 Test: Conversión de booleanos...")
    
    adapter = DatabaseAdapter()
    
    # Test params con boolean
    test_params = (True, False, 1, 0, 'true', 'false')
    
    # Limpiar para JSON
    cleaned = adapter._clean_params_for_json(test_params)
    
    # Verificar conversiones
    expected = [1, 0, 1, 0, 'true', 'false']  # True/False -> 1/0
    
    if cleaned[:2] == [1, 0]:
        print("✅ Conversión de booleanos: OK")
        return True
    else:
        print(f"❌ Error conversión booleanos. Esperado: {expected[:2]}, Obtenido: {cleaned[:2]}")
        return False

def test_data_adaptation():
    """Test: Adaptación de datos para remoto"""
    print("🧪 Test: Adaptación de datos para PostgreSQL...")
    
    adapter = DatabaseAdapter()
    
    # Test data con tipos mixtos
    test_data = {
        'cantidad': True,  # Este causaba el error
        'precio': Decimal('18.50'),
        'activo': 1,
        'stock_reduction': 5,  # Este campo no existe en remoto
        'nombre': 'Test Product'
    }
    
    # Adaptar para detalle_ventas
    adapted = adapter._adapt_data_for_remote(test_data, 'detalle_ventas')
    
    # Verificar conversiones
    if adapted.get('cantidad') == 1 and isinstance(adapted.get('precio'), float):
        if 'stock_reduction' not in adapted:  # Campo debe ser eliminado
            print("✅ Adaptación de datos: OK")
            return True
    
    print(f"❌ Error adaptación. Datos adaptados: {adapted}")
    return False

def test_venta_simulation():
    """Test: Simulación de venta completa"""
    print("🧪 Test: Simulación de venta completa...")
    
    try:
        adapter = DatabaseAdapter()
        
        # Simular venta
        venta_data = {
            'fecha': datetime.now(),
            'total': Decimal('50.00'),
            'metodo_pago': 'Efectivo',
            'vendedor': 'Sistema Test',
            'observaciones': 'Test venta',
            'descuento': Decimal('0.00')
        }
        
        # Simular detalle venta
        detalle_data = {
            'venta_id': 999,
            'producto_id': 1,
            'cantidad': 2,  # Entero, no boolean
            'precio_unitario': Decimal('25.00'),
            'subtotal': Decimal('50.00')
        }
        
        # Probar adaptación
        venta_adapted = adapter._adapt_data_for_remote(venta_data, 'ventas')
        detalle_adapted = adapter._adapt_data_for_remote(detalle_data, 'detalle_ventas')
        
        # Verificar tipos
        if (isinstance(venta_adapted.get('total'), float) and 
            isinstance(detalle_adapted.get('cantidad'), int) and
            isinstance(detalle_adapted.get('precio_unitario'), float)):
            print("✅ Simulación de venta: OK")
            return True
        else:
            print(f"❌ Error tipos en venta: {venta_adapted}, {detalle_adapted}")
            return False
            
    except Exception as e:
        print(f"❌ Error simulación venta: {e}")
        return False

def main():
    """Ejecutar todos los tests críticos"""
    print("🚀 Iniciando tests críticos de corrección de errores...\n")
    
    tests = [
        test_decimal_json_serialization,
        test_boolean_conversion,
        test_data_adaptation,
        test_venta_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Resultados: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los errores críticos han sido corregidos!")
        return True
    else:
        print("⚠️ Algunos errores aún persisten")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

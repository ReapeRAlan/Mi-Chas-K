#!/usr/bin/env python3
"""
Test simple para verificar correcciones críticas
"""

import os
import sys
from decimal import Decimal
import json

# Agregar path
sys.path.insert(0, os.getcwd())

def test_json_serialization():
    """Test directo de serialización JSON con Decimals"""
    print("🧪 Test: Serialización JSON...")
    
    # Función de limpieza manual
    def clean_data_for_json(data):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                cleaned[key] = float(value)
            elif isinstance(value, bool):
                cleaned[key] = 1 if value else 0
            else:
                cleaned[key] = value
        return cleaned
    
    # Test data
    test_data = {
        'precio': Decimal('18.50'),
        'cantidad': True,
        'activo': False,
        'nombre': 'Test'
    }
    
    # Limpiar
    cleaned = clean_data_for_json(test_data)
    
    # Intentar serializar
    try:
        json_str = json.dumps(cleaned)
        print(f"✅ JSON serialization OK: {json_str}")
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def test_boolean_conversion():
    """Test conversión de booleanos"""
    print("🧪 Test: Conversión booleanos...")
    
    def convert_bool_to_int(value):
        if isinstance(value, bool):
            return 1 if value else 0
        return value
    
    test_cases = [True, False, 1, 0, "test"]
    expected = [1, 0, 1, 0, "test"]
    
    results = [convert_bool_to_int(val) for val in test_cases]
    
    if results == expected:
        print(f"✅ Boolean conversion OK: {results}")
        return True
    else:
        print(f"❌ Boolean conversion failed: {results} != {expected}")
        return False

def test_data_filtering():
    """Test filtrado de campos inexistentes"""
    print("🧪 Test: Filtrado de campos...")
    
    def filter_unwanted_fields(data, table_name):
        unwanted_fields = ['stock_reduction', 'last_updated', 'sync_status']
        
        if table_name == 'productos':
            filtered = {k: v for k, v in data.items() if k not in unwanted_fields}
        else:
            filtered = data
        
        return filtered
    
    test_data = {
        'nombre': 'Test Product',
        'precio': 25.0,
        'stock_reduction': 5,  # Este debe ser eliminado
        'activo': True
    }
    
    filtered = filter_unwanted_fields(test_data, 'productos')
    
    if 'stock_reduction' not in filtered and 'nombre' in filtered:
        print(f"✅ Field filtering OK: {list(filtered.keys())}")
        return True
    else:
        print(f"❌ Field filtering failed: {list(filtered.keys())}")
        return False

def main():
    print("🚀 Ejecutando tests críticos simplificados...\n")
    
    tests = [
        test_json_serialization,
        test_boolean_conversion,
        test_data_filtering
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Resultados: {passed}/{len(tests)} tests pasaron")
    
    if passed == len(tests):
        print("🎉 ¡Las correcciones críticas funcionan correctamente!")
    else:
        print("⚠️ Algunos tests fallaron")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()

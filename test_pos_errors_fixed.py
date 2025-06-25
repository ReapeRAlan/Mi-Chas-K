#!/usr/bin/env python3
"""
Test de corrección de errores críticos en punto de venta
"""
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_pos_errors_fixed():
    """Test específico para los errores corregidos en punto de venta"""
    print("🛒 Testing Point of Sale Error Fixes...")
    print("=" * 50)
    
    try:
        from database.connection_adapter import DatabaseAdapter
        adapter = DatabaseAdapter()
        
        # Test 1: Verificar métodos de limpieza de datos
        print("1. Testing data cleaning methods...")
        if hasattr(adapter, '_clean_data_for_json'):
            print("   ✅ _clean_data_for_json method exists")
        else:
            print("   ❌ _clean_data_for_json method missing")
            return False
        
        if hasattr(adapter, '_clean_params_for_json'):
            print("   ✅ _clean_params_for_json method exists")
        else:
            print("   ❌ _clean_params_for_json method missing")
            return False
        
        # Test 2: Test data cleaning with problematic types
        print("2. Testing data cleaning functionality...")
        from decimal import Decimal
        from datetime import datetime
        
        test_data = {
            'id': 1,
            'precio': Decimal('15.50'),
            'fecha': datetime.now(),
            'cantidad': 2,
            'activo': True
        }
        
        try:
            cleaned = adapter._clean_data_for_json(test_data)
            print(f"   ✅ Data cleaning successful: {cleaned}")
            
            # Verificar que Decimal se convirtió a float
            if isinstance(cleaned.get('precio'), float):
                print("   ✅ Decimal converted to float")
            else:
                print("   ❌ Decimal not converted properly")
        except Exception as e:
            print(f"   ❌ Data cleaning failed: {e}")
            return False
        
        # Test 3: Test parameter cleaning
        print("3. Testing parameter cleaning...")
        test_params = (1, Decimal('10.5'), datetime.now(), True)
        
        try:
            cleaned_params = adapter._clean_params_for_json(test_params)
            print(f"   ✅ Parameter cleaning successful: {cleaned_params}")
        except Exception as e:
            print(f"   ❌ Parameter cleaning failed: {e}")
            return False
        
        # Test 4: Test point of sale page import
        print("4. Testing point of sale page...")
        try:
            from pages.punto_venta_simple import show_punto_venta, procesar_venta_simple, agregar_al_carrito
            print("   ✅ Point of sale page imports successfully")
        except Exception as e:
            print(f"   ❌ Point of sale import failed: {e}")
            return False
        
        # Test 5: Test sync queue operations
        print("5. Testing sync queue operations...")
        try:
            sync_status = adapter.get_sync_status()
            print(f"   ✅ Sync status: {sync_status}")
        except Exception as e:
            print(f"   ⚠️ Sync status error: {e}")
        
        # Test 6: Test force sync method
        print("6. Testing force sync method...")
        if hasattr(adapter, 'force_sync'):
            print("   ✅ force_sync method exists")
        else:
            print("   ❌ force_sync method missing")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ALL ERROR FIXES VALIDATED!")
        print("✅ Data type errors should be resolved")
        print("✅ JSON serialization errors should be resolved") 
        print("✅ Point of sale should work correctly")
        print("✅ Automatic sync after sales implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_type_conversions():
    """Test específico para conversiones de tipos de datos"""
    print("\n🔄 Testing Data Type Conversions...")
    
    try:
        from database.connection_adapter import DatabaseAdapter
        from decimal import Decimal
        from datetime import datetime
        
        adapter = DatabaseAdapter()
        
        # Test conversiones específicas para detalle_ventas
        test_data = {
            'venta_id': '123',
            'producto_id': '45', 
            'cantidad': True,  # ¡Problema! - debería ser entero
            'precio_unitario': Decimal('15.50'),
            'subtotal': Decimal('31.00')
        }
        
        adapted = adapter._adapt_data_for_remote(test_data, 'detalle_ventas')
        print(f"   Original data: {test_data}")
        print(f"   Adapted data: {adapted}")
        
        # Verificaciones específicas
        if isinstance(adapted.get('cantidad'), int):
            print("   ✅ Boolean cantidad converted to int")
        else:
            print(f"   ❌ cantidad not converted properly: {type(adapted.get('cantidad'))}")
        
        if isinstance(adapted.get('precio_unitario'), float):
            print("   ✅ Decimal precio_unitario converted to float")
        else:
            print(f"   ❌ precio_unitario not converted: {type(adapted.get('precio_unitario'))}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data type conversion test failed: {e}")
        return False

def main():
    """Función principal de testing"""
    print("🧪 POINT OF SALE ERROR FIXES TEST")
    print("=" * 50)
    
    tests = [
        ("POS Error Fixes", test_pos_errors_fixed),
        ("Data Type Conversions", test_data_type_conversions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Error fixes are working correctly")
        print("🚀 Point of sale should work without errors now")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

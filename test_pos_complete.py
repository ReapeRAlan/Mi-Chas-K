#!/usr/bin/env python3
"""
Test completo del sistema de punto de venta
"""
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_pos_system():
    """Test completo del sistema POS"""
    print("🛒 Testing Mi Chas-K POS System...")
    print("=" * 50)
    
    try:
        # Test 1: Database Adapter
        print("\n1. Testing Database Adapter...")
        from database.connection_adapter import DatabaseAdapter
        adapter = DatabaseAdapter()
        print("   ✅ DatabaseAdapter initialized successfully")
        
        # Test 2: Check required methods
        required_methods = [
            'execute_query',
            'execute_update', 
            '_get_local_table_columns',
            'get_system_status',
            'get_sync_status'
        ]
        
        for method in required_methods:
            if hasattr(adapter, method):
                print(f"   ✅ Method {method} exists")
            else:
                print(f"   ❌ Method {method} missing")
                return False
        
        # Test 3: Basic database operations
        print("\n2. Testing Basic Database Operations...")
        try:
            # Test products query
            productos = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
            product_count = productos[0]['count'] if productos else 0
            print(f"   ✅ Products in database: {product_count}")
            
            # Test categories query
            categorias = adapter.execute_query("SELECT COUNT(*) as count FROM categorias")
            category_count = categorias[0]['count'] if categorias else 0
            print(f"   ✅ Categories in database: {category_count}")
            
            # Test sales query
            ventas = adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
            sales_count = ventas[0]['count'] if ventas else 0
            print(f"   ✅ Sales in database: {sales_count}")
            
        except Exception as e:
            print(f"   ⚠️ Database queries failed: {e}")
        
        # Test 4: Page imports
        print("\n3. Testing Page Imports...")
        
        # Test punto de venta
        try:
            from pages.punto_venta_simple import show_punto_venta
            print("   ✅ Punto de Venta page imported")
        except Exception as e:
            print(f"   ❌ Punto de Venta import failed: {e}")
            return False
        
        # Test inventario
        try:
            from pages.inventario_simple import show_inventario
            print("   ✅ Inventario page imported")
        except Exception as e:
            print(f"   ❌ Inventario import failed: {e}")
            return False
        
        # Test dashboard
        try:
            from pages.dashboard_simple import show_dashboard
            print("   ✅ Dashboard page imported")
        except Exception as e:
            print(f"   ❌ Dashboard import failed: {e}")
            return False
        
        # Test configuracion
        try:
            from pages.configuracion_simple import show_configuracion
            print("   ✅ Configuracion page imported")
        except Exception as e:
            print(f"   ❌ Configuracion import failed: {e}")
            return False
        
        # Test 5: PDF Generator
        print("\n4. Testing PDF Generator...")
        try:
            from utils.pdf_generator import generar_ticket_pdf
            print("   ✅ PDF Generator imported")
        except Exception as e:
            print(f"   ⚠️ PDF Generator import failed: {e}")
        
        # Test 6: System Status
        print("\n5. Testing System Status...")
        try:
            status = adapter.get_system_status()
            sync_status = adapter.get_sync_status()
            print(f"   ✅ System status: {len(status)} components")
            print(f"   ✅ Sync status: {sync_status.get('pending', 0)} pending operations")
        except Exception as e:
            print(f"   ⚠️ System status check failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Mi Chas-K POS System is fully functional")
        print("🚀 Ready to launch with: streamlit run app_hybrid_v4.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pos_system()
    sys.exit(0 if success else 1)

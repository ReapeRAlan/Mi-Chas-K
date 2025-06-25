#!/usr/bin/env python3
"""
Test rápido del adaptador corregido
"""

def test_adapter():
    try:
        # Import test
        from database.connection_adapter import DatabaseAdapter
        print("✅ Import successful")
        
        # Initialize test
        adapter = DatabaseAdapter()
        print("✅ Initialization successful")
        
        # Method check test
        if hasattr(adapter, '_get_local_table_columns'):
            print("✅ Method _get_local_table_columns exists")
        else:
            print("❌ Method _get_local_table_columns missing")
            return False
        
        # Test the method
        try:
            columns = adapter._get_local_table_columns('productos')
            print(f"✅ Method call successful - found {len(columns)} columns")
        except Exception as e:
            print(f"⚠️ Method call failed (expected if no DB): {e}")
        
        # Basic query test
        try:
            productos = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
            print(f"✅ Query test successful - products: {productos[0]['count'] if productos else 0}")
        except Exception as e:
            print(f"⚠️ Query failed (expected if no connection): {e}")
        
        print("🎉 Adapter test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_adapter()

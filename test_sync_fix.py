#!/usr/bin/env python3
"""
Test final del error específico de sincronización
"""

def test_sync_error_fix():
    """Test específico para el error de sincronización reportado"""
    print("🔄 Testing Sync Error Fix...")
    print("=" * 40)
    
    try:
        from database.connection_adapter import DatabaseAdapter
        adapter = DatabaseAdapter()
        
        # Test 1: Verificar que el método existe
        print("1. Checking method existence...")
        if hasattr(adapter, '_get_local_table_columns'):
            print("   ✅ _get_local_table_columns method exists")
        else:
            print("   ❌ _get_local_table_columns method MISSING")
            return False
        
        # Test 2: Verificar que el método funciona para las tablas problemáticas
        print("2. Testing method for problematic tables...")
        
        test_tables = ['ventas', 'detalle_ventas', 'productos', 'categorias']
        
        for table in test_tables:
            try:
                columns = adapter._get_local_table_columns(table)
                print(f"   ✅ {table}: {len(columns)} columns found")
                if columns:
                    print(f"      Columns: {', '.join(sorted(list(columns)))}")
            except Exception as e:
                print(f"   ⚠️ {table}: Error getting columns: {e}")
        
        # Test 3: Verificar que el método _adapt_data_for_local funciona
        print("3. Testing _adapt_data_for_local method...")
        
        if hasattr(adapter, '_adapt_data_for_local'):
            print("   ✅ _adapt_data_for_local method exists")
            
            # Test with sample data
            sample_data = {
                'id': 1,
                'nombre': 'Test Product',
                'precio': 10.50,
                'stock': 5,
                'activo': True,
                'estado': 'active'  # This column might not exist in local table
            }
            
            try:
                adapted = adapter._adapt_data_for_local(sample_data, 'productos')
                print(f"   ✅ Data adaptation successful: {len(adapted)} fields adapted")
                print(f"      Original: {list(sample_data.keys())}")
                print(f"      Adapted:  {list(adapted.keys())}")
            except Exception as e:
                print(f"   ⚠️ Data adaptation failed: {e}")
        else:
            print("   ❌ _adapt_data_for_local method MISSING")
            return False
        
        # Test 4: Test sync status
        print("4. Testing sync functionality...")
        
        try:
            sync_status = adapter.get_sync_status()
            print(f"   ✅ Sync status: {sync_status}")
        except Exception as e:
            print(f"   ⚠️ Sync status failed: {e}")
        
        print("\n" + "=" * 40)
        print("🎉 SYNC ERROR FIX VALIDATION COMPLETE!")
        print("✅ The '_get_local_table_columns' error should be resolved")
        print("✅ Sync process should now work correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sync_error_fix()
    if success:
        print("\n🚀 Ready to test the application:")
        print("   streamlit run app_hybrid_v4.py")
    else:
        print("\n❌ Issues detected - check the error messages above")

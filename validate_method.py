#!/usr/bin/env python3
"""
Validación específica del error reportado
"""

def validate_adapter_method():
    """Validar que el método _get_local_table_columns existe y funciona"""
    print("🔍 Validando método _get_local_table_columns...")
    
    try:
        # Import adapter
        from database.connection_adapter import DatabaseAdapter
        adapter = DatabaseAdapter()
        
        # Check if method exists
        if hasattr(adapter, '_get_local_table_columns'):
            print("✅ Método _get_local_table_columns encontrado")
            
            # Test the method call
            try:
                columns = adapter._get_local_table_columns('productos')
                print(f"✅ Método funciona correctamente - columnas encontradas: {len(columns)}")
                if columns:
                    print(f"   Columnas: {', '.join(sorted(columns))}")
                return True
            except Exception as e:
                print(f"❌ Error ejecutando método: {e}")
                return False
        else:
            print("❌ Método _get_local_table_columns NO ENCONTRADO")
            # Show available methods
            methods = [m for m in dir(adapter) if m.startswith('_get_')]
            print(f"   Métodos disponibles que empiezan con '_get_': {methods}")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando DatabaseAdapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = validate_adapter_method()
    if success:
        print("\n🎉 VALIDACIÓN EXITOSA - El error debería estar resuelto")
    else:
        print("\n❌ VALIDACIÓN FALLIDA - El error persiste")

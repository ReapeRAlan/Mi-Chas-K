#!/usr/bin/env python3
"""
Script de prueba e inicialización para MiChaska
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Prueba la inicialización de la base de datos"""
    print("🔧 Inicializando base de datos...")
    try:
        from database.connection import init_database
        init_database()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        return False

def test_models():
    """Prueba los modelos de datos"""
    print("🧪 Probando modelos de datos...")
    try:
        from database.models import Producto, Categoria, Carrito
        
        # Probar obtener productos
        productos = Producto.get_all()
        print(f"✅ Productos encontrados: {len(productos)}")
        
        # Probar carrito
        carrito = Carrito()
        print("✅ Carrito creado correctamente")
        
        return True
    except Exception as e:
        print(f"❌ Error en modelos: {e}")
        return False

def test_utils():
    """Prueba las utilidades"""
    print("🛠️ Probando utilidades...")
    try:
        from utils.helpers import format_currency, format_datetime
        from datetime import datetime
        
        # Probar formateo de moneda
        currency_test = format_currency(123.45)
        print(f"✅ Formato moneda: {currency_test}")
        
        # Probar formateo de fecha
        date_test = format_datetime(datetime.now())
        print(f"✅ Formato fecha: {date_test}")
        
        return True
    except Exception as e:
        print(f"❌ Error en utilidades: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del Sistema MiChaska\n")
    
    tests = [
        ("Base de datos", test_database),
        ("Modelos", test_models),
        ("Utilidades", test_utils)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n--- Prueba: {name} ---")
        if test_func():
            passed += 1
        print("")
    
    print("=" * 50)
    print(f"Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        print("\n🚀 Para ejecutar el sistema:")
        print("   streamlit run app.py")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

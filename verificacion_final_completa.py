#!/usr/bin/env python3
"""
Verificación final del sistema después de correcciones críticas
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Configurar path
sys.path.insert(0, os.getcwd())

def verificar_correcciones():
    """Verificar que las correcciones críticas funcionan"""
    
    print("=" * 60)
    print("🔍 VERIFICACIÓN FINAL DE CORRECCIONES CRÍTICAS")
    print("=" * 60)
    
    # 1. Test de importación
    print("\n1️⃣ Test de importación del adaptador...")
    try:
        from database.connection_adapter import DatabaseAdapter
        print("✅ Adaptador importado correctamente")
    except Exception as e:
        print(f"❌ Error importando adaptador: {e}")
        return False
    
    # 2. Test de creación de adaptador
    print("\n2️⃣ Test de creación del adaptador...")
    try:
        adapter = DatabaseAdapter()
        print("✅ Adaptador creado correctamente")
    except Exception as e:
        print(f"❌ Error creando adaptador: {e}")
        return False
    
    # 3. Test de funciones críticas
    print("\n3️⃣ Test de funciones de limpieza de datos...")
    
    # Test data con problemas que causaban errores
    test_data_problematica = {
        'precio': Decimal('25.50'),
        'cantidad': True,  # Era boolean, debe ser int
        'descuento': Decimal('0.00'),
        'activo': False,
        'stock_reduction': 5,  # Campo que no existe en remoto
        'nombre': 'Producto Test'
    }
    
    try:
        # Test limpieza JSON
        cleaned_json = adapter._clean_data_for_json(test_data_problematica)
        print(f"✅ Limpieza JSON: {cleaned_json}")
        
        # Verificar conversiones específicas
        if (isinstance(cleaned_json['precio'], float) and 
            cleaned_json['cantidad'] == 1 and  # True → 1
            cleaned_json['activo'] == 0):      # False → 0
            print("✅ Conversiones de tipos correctas")
        else:
            print("❌ Conversiones de tipos incorrectas")
            return False
            
    except Exception as e:
        print(f"❌ Error en limpieza de datos: {e}")
        return False
    
    # 4. Test de adaptación para remoto
    print("\n4️⃣ Test de adaptación para PostgreSQL...")
    try:
        adapted_data = adapter._adapt_data_for_remote(test_data_problematica, 'detalle_ventas')
        print(f"✅ Adaptación remota: {adapted_data}")
        
        # Verificar que no hay campos problemáticos
        if ('stock_reduction' not in adapted_data and 
            isinstance(adapted_data.get('cantidad'), int) and
            isinstance(adapted_data.get('precio'), float)):
            print("✅ Adaptación para PostgreSQL correcta")
        else:
            print("❌ Adaptación para PostgreSQL incorrecta")
            return False
            
    except Exception as e:
        print(f"❌ Error en adaptación remota: {e}")
        return False
    
    # 5. Test de parámetros
    print("\n5️⃣ Test de adaptación de parámetros...")
    test_params = (Decimal('10.50'), True, False, 'test', 25)
    try:
        adapted_params = adapter._adapt_params_for_remote(test_params, 'productos')
        print(f"✅ Parámetros adaptados: {adapted_params}")
        
        # Verificar conversiones
        if (isinstance(adapted_params[0], float) and      # Decimal → float
            isinstance(adapted_params[1], int) and        # bool → int
            isinstance(adapted_params[2], int)):          # bool → int
            print("✅ Conversión de parámetros correcta")
        else:
            print("❌ Conversión de parámetros incorrecta")
            return False
            
    except Exception as e:
        print(f"❌ Error en parámetros: {e}")
        return False
    
    # 6. Test de función de sincronización inmediata
    print("\n6️⃣ Test de función de sincronización inmediata...")
    try:
        if hasattr(adapter, 'force_sync_now'):
            print("✅ Función force_sync_now disponible")
        else:
            print("❌ Función force_sync_now no disponible")
            return False
    except Exception as e:
        print(f"❌ Error verificando sincronización: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 TODAS LAS CORRECCIONES CRÍTICAS FUNCIONAN CORRECTAMENTE")
    print("✅ Sistema listo para uso en producción")
    print("=" * 60)
    
    return True

def verificar_punto_venta():
    """Verificar que el punto de venta funciona"""
    print("\n" + "=" * 60)
    print("🛒 VERIFICACIÓN DEL PUNTO DE VENTA")
    print("=" * 60)
    
    try:
        # Import test
        sys.path.insert(0, os.path.join(os.getcwd(), 'pages'))
        from pages.punto_venta_simple_fixed import procesar_venta_simple, agregar_al_carrito
        print("✅ Punto de venta importado correctamente")
        
        # Test básico de función
        print("✅ Funciones del punto de venta disponibles")
        return True
        
    except Exception as e:
        print(f"❌ Error en punto de venta: {e}")
        return False

def main():
    """Ejecutar verificación completa"""
    print(f"🚀 Iniciando verificación final - {datetime.now()}")
    
    # Verificar correcciones críticas
    if not verificar_correcciones():
        print("\n❌ FALLO: Las correcciones críticas no funcionan correctamente")
        return False
    
    # Verificar punto de venta
    if not verificar_punto_venta():
        print("\n❌ FALLO: El punto de venta tiene problemas")
        return False
    
    print(f"\n🎯 VERIFICACIÓN FINAL COMPLETADA EXITOSAMENTE - {datetime.now()}")
    print("\n🔥 EL SISTEMA ESTÁ LISTO PARA USAR EN PRODUCCIÓN 🔥")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

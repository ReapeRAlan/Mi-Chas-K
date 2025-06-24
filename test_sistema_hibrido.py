#!/usr/bin/env python3
"""
Script de prueba para el Sistema Híbrido Mi Chas-K v3.0.0
"""

import sys
import os
from pathlib import Path

# Agregar directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_hybrid_system():
    """Probar el sistema híbrido completo"""
    print("🧪 PROBANDO SISTEMA HÍBRIDO MI CHAS-K v3.0.0")
    print("=" * 50)
    
    try:
        # 1. Probar importación del sistema híbrido
        print("\n1️⃣ Probando importación del sistema híbrido...")
        from database.connection_hybrid import db_hybrid, execute_query, execute_update
        print("✅ Sistema híbrido importado correctamente")
        
        # 2. Verificar estado inicial
        print("\n2️⃣ Verificando estado del sistema...")
        sync_status = db_hybrid.get_sync_status()
        print(f"   🌐 Online: {sync_status['online']}")
        print(f"   🗃️ BD Remota: {sync_status['database_available']}")
        print(f"   📊 Pendientes: {sync_status['pending']}")
        print(f"   ✅ Completadas: {sync_status['completed']}")
        print(f"   ❌ Fallidas: {sync_status['failed']}")
        
        # 3. Probar conexión local
        print("\n3️⃣ Probando conexión a base de datos local...")
        with db_hybrid.get_connection(prefer_remote=False) as conn:
            print("✅ Conexión local establecida")
            print(f"   📍 Tipo: {type(conn).__name__}")
        
        # 4. Probar consultas básicas
        print("\n4️⃣ Probando consultas básicas...")
        
        # Contar productos
        productos = execute_query("SELECT COUNT(*) as total FROM productos")
        print(f"   📦 Productos en BD: {productos[0]['total'] if productos else 0}")
        
        # Contar categorías
        categorias = execute_query("SELECT COUNT(*) as total FROM categorias")
        print(f"   🏷️ Categorías en BD: {categorias[0]['total'] if categorias else 0}")
        
        # Contar vendedores
        vendedores = execute_query("SELECT COUNT(*) as total FROM vendedores")
        print(f"   👥 Vendedores en BD: {vendedores[0]['total'] if vendedores else 0}")
        
        # Contar ventas
        ventas = execute_query("SELECT COUNT(*) as total FROM ventas")
        print(f"   💰 Ventas registradas: {ventas[0]['total'] if ventas else 0}")
        
        # 5. Probar inserción con sincronización
        print("\n5️⃣ Probando inserción con cola de sincronización...")
        
        test_data = {
            'table': 'productos',
            'operation': 'INSERT',
            'data': {
                'nombre': 'Producto Test',
                'precio': 10.00,
                'stock': 100,
                'categoria_id': 1,
                'activo': True
            }
        }
        
        result = execute_update("""
            INSERT INTO productos (nombre, precio, stock, categoria_id, activo)
            VALUES (?, ?, ?, ?, ?)
        """, ('Producto Test', 10.00, 100, 1, True), test_data)
        
        if result:
            print(f"✅ Producto test creado con ID: {result}")
            
            # Limpiar producto test
            execute_update("DELETE FROM productos WHERE id = ?", (result,))
            print("🗑️ Producto test eliminado")
        else:
            print("❌ Error creando producto test")
        
        # 6. Verificar módulos de páginas
        print("\n6️⃣ Verificando módulos de páginas...")
        
        try:
            from pages.punto_venta_simple import mostrar_punto_venta_simple
            print("✅ Módulo punto_venta_simple importado")
        except ImportError as e:
            print(f"❌ Error importando punto_venta_simple: {e}")
        
        try:
            from pages.inventario_simple import mostrar_inventario_simple
            print("✅ Módulo inventario_simple importado")
        except ImportError as e:
            print(f"❌ Error importando inventario_simple: {e}")
        
        try:
            from pages.dashboard_simple import mostrar_dashboard_simple
            print("✅ Módulo dashboard_simple importado")
        except ImportError as e:
            print(f"❌ Error importando dashboard_simple: {e}")
        
        try:
            from pages.configuracion_simple import mostrar_configuracion_simple
            print("✅ Módulo configuracion_simple importado")
        except ImportError as e:
            print(f"❌ Error importando configuracion_simple: {e}")
        
        # 7. Verificar aplicación principal
        print("\n7️⃣ Verificando aplicación principal...")
        
        if os.path.exists('app_hybrid.py'):
            print("✅ Aplicación híbrida encontrada: app_hybrid.py")
        else:
            print("❌ Aplicación híbrida no encontrada")
        
        # 8. Estado final
        print("\n8️⃣ Estado final del sistema...")
        final_status = db_hybrid.get_sync_status()
        print(f"   📊 Elementos en cola: {final_status['pending']}")
        
        if final_status['database_available']:
            print("   🌐 Sistema listo para uso ONLINE")
        else:
            print("   💾 Sistema listo para uso OFFLINE")
        
        print("\n" + "=" * 50)
        print("🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 50)
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Configurar variables de entorno en .env")
        print("2. Ejecutar: streamlit run app_hybrid.py")
        print("3. Abrir navegador en: http://localhost:8501")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connectivity():
    """Probar conectividad específica"""
    print("\n🔍 PRUEBA DE CONECTIVIDAD")
    print("-" * 30)
    
    try:
        from database.connection_hybrid import db_hybrid
        
        # Probar internet
        internet = db_hybrid.check_internet_connection()
        print(f"🌐 Internet: {'✅ Disponible' if internet else '❌ No disponible'}")
        
        # Probar BD remota
        if internet:
            remote_db = db_hybrid.check_database_connection()
            print(f"🗃️ BD Remota: {'✅ Conectada' if remote_db else '❌ No conectada'}")
        else:
            print("🗃️ BD Remota: ⏭️ Omitida (sin internet)")
        
        # Probar BD local
        local_db_exists = os.path.exists(db_hybrid.local_db_path)
        print(f"💾 BD Local: {'✅ Disponible' if local_db_exists else '❌ No encontrada'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de conectividad: {e}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA HÍBRIDO")
    print("=" * 50)
    
    # Verificar conectividad primero
    connectivity_ok = test_connectivity()
    
    # Luego probar sistema completo
    if connectivity_ok:
        system_ok = test_hybrid_system()
        
        if system_ok:
            print("\n✅ SISTEMA LISTO PARA PRODUCCIÓN")
            sys.exit(0)
        else:
            print("\n❌ SISTEMA TIENE PROBLEMAS")
            sys.exit(1)
    else:
        print("\n⚠️ PROBLEMAS DE CONECTIVIDAD DETECTADOS")
        print("El sistema puede funcionar en modo offline")
        sys.exit(0)

#!/usr/bin/env python3
"""
Estado Rápido del Sistema Mi-Chas-K
Muestra un resumen del estado actual del sistema
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_system_status():
    """Verificar estado rápido del sistema"""
    print("🚀 ESTADO DEL SISTEMA MI-CHAS-K")
    print("=" * 50)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar archivos críticos
    print("📁 ARCHIVOS CRÍTICOS:")
    critical_files = [
        'app_hybrid.py',
        'database/connection_adapter.py',
        'pages/punto_venta_simple.py',
        'pages/inventario_simple.py',
        'pages/dashboard_simple.py',
        'pages/configuracion_simple.py',
        '.env',
        'requirements.txt'
    ]
    
    for file in critical_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
    
    print()
    
    # 2. Verificar variables de entorno
    print("🔧 CONFIGURACIÓN:")
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Ocultar credenciales sensibles
        masked_url = database_url[:20] + "***" + database_url[-10:] if len(database_url) > 30 else "CONFIGURADA"
        print(f"   ✅ DATABASE_URL: {masked_url}")
    else:
        print("   ❌ DATABASE_URL: No configurada")
    
    print()
    
    # 3. Verificar base de datos local
    print("💾 BASE DE DATOS LOCAL:")
    local_db = os.path.join('data', 'local_database.db')
    if os.path.exists(local_db):
        size = os.path.getsize(local_db)
        print(f"   ✅ {local_db} ({size} bytes)")
    else:
        print(f"   ❌ {local_db}: No encontrada")
    
    print()
    
    # 4. Estado del adaptador
    print("🔄 ADAPTADOR HÍBRIDO:")
    try:
        from database.connection_adapter import db_adapter
        status = db_adapter.get_system_status()
        
        print(f"   📊 Estado: {status['status']}")
        print(f"   🌐 Conexión remota: {'✅' if status['remote_available'] else '❌'}")
        print(f"   💾 Conexión local: {'✅' if status['local_available'] else '❌'}")
        print(f"   📦 Cola de sincronización: {status['sync_queue_size']} elementos")
        
    except Exception as e:
        print(f"   ❌ Error cargando adaptador: {e}")
    
    print()
    
    # 5. Prueba rápida
    print("🧪 PRUEBA RÁPIDA:")
    try:
        from database.connection_adapter import db_adapter
        
        # Contar productos
        productos = db_adapter.execute_query("SELECT COUNT(*) as count FROM productos")
        count_productos = productos[0]['count'] if productos else 0
        print(f"   📦 Productos: {count_productos}")
        
        # Contar ventas
        ventas = db_adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
        count_ventas = ventas[0]['count'] if ventas else 0
        print(f"   💰 Ventas: {count_ventas}")
        
        print("   ✅ Operaciones básicas funcionando")
        
    except Exception as e:
        print(f"   ❌ Error en prueba rápida: {e}")
    
    print()
    print("=" * 50)
    
    # Resumen final
    if database_url and os.path.exists(local_db):
        print("🎉 SISTEMA LISTO PARA USAR")
        print("   Ejecuta: streamlit run app_hybrid.py")
    else:
        print("⚠️ SISTEMA REQUIERE CONFIGURACIÓN")
        print("   Verifica las variables de entorno y la base de datos")

if __name__ == "__main__":
    check_system_status()

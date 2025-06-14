#!/usr/bin/env python3
"""
Prueba final del sistema de ventas con fechas México
Simula ventas completas para verificar que se guardan con fecha correcta
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection
from database.models import Venta, Producto, Categoria
from utils.timezone_utils import get_mexico_datetime
from datetime import datetime, timezone, timedelta
import time

def setup_test_data():
    """Configura datos de prueba"""
    
    print("🔧 Configurando datos de prueba...")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Crear categoría de prueba si no existe
            categoria_test = Categoria(nombre="Test Fechas", descripcion="Categoría para pruebas de fechas")
            categoria_test.save()
            
            # Crear producto de prueba si no existe
            cursor.execute("SELECT id FROM productos WHERE nombre = %s", ("Producto Test Fecha",))
            producto_existe = cursor.fetchone()
            
            if not producto_existe:
                producto_test = Producto(
                    nombre="Producto Test Fecha",
                    descripcion="Producto para pruebas de fechas",
                    precio=10.00,
                    stock=1000,
                    categoria_id=categoria_test.id,
                    codigo_barras="TEST_FECHA_001"
                )
                producto_test.save()
        
        print("✅ Datos de prueba configurados")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando datos: {e}")
        return False

def test_venta_completa():
    """Prueba una venta completa y verifica la fecha"""
    
    print("\n" + "=" * 60)
    print("🛒 PRUEBA DE VENTA COMPLETA")
    print("=" * 60)
    
    try:
        # 1. Obtener fecha ANTES de crear la venta
        fecha_antes = get_mexico_datetime()
        print(f"📅 Fecha antes de venta: {fecha_antes}")
        
        # 2. Obtener producto de prueba
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM productos WHERE nombre = %s", ("Producto Test Fecha",))
            producto_row = cursor.fetchone()
            
            if not producto_row:
                print("❌ No se encontró producto de prueba")
                return False
            
            producto_id = producto_row[0]
        
        # 3. Crear y procesar venta
        print("💳 Creando venta...")
        
        venta = Venta(
            vendedor="Test Automated",
            metodo_pago="efectivo",
            productos_data=[{
                'id': producto_id,
                'nombre': 'Producto Test Fecha',
                'precio': 10.00,
                'cantidad': 2
            }]
        )
        
        # Verificar fecha ANTES de guardar
        print(f"🕐 Fecha en objeto venta antes de save: {venta.fecha}")
        
        # Guardar venta
        venta.save()
        
        # 4. Verificar fecha DESPUÉS de guardar
        fecha_despues = get_mexico_datetime()
        print(f"📅 Fecha después de venta: {fecha_despues}")
        print(f"🆔 ID de venta creada: {venta.id}")
        
        # 5. Leer la venta desde la base de datos
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fecha FROM ventas WHERE id = %s", (venta.id,))
            fecha_db_row = cursor.fetchone()
            
            if not fecha_db_row:
                print("❌ No se encontró la venta en la base de datos")
                return False
            
            fecha_db_str = fecha_db_row[0]
            fecha_db = datetime.fromisoformat(fecha_db_str)
            
            print(f"💾 Fecha en BD: {fecha_db}")
            
            # 6. Verificar que la fecha es correcta (México)
            diferencia_antes = abs((fecha_db - fecha_antes).total_seconds())
            diferencia_despues = abs((fecha_db - fecha_despues).total_seconds())
            
            print(f"⏱️  Diferencia con fecha antes: {diferencia_antes:.2f}s")
            print(f"⏱️  Diferencia con fecha después: {diferencia_despues:.2f}s")
            
            # La fecha debe estar entre antes y después (máximo 10 segundos de tolerancia)
            if diferencia_antes > 10 or diferencia_despues > 10:
                print("❌ FALLA: Fecha de venta fuera de rango esperado")
                return False
            
            # 7. Verificar que es hora de México (no UTC)
            utc_actual = datetime.now(timezone.utc)
            diferencia_utc = abs((fecha_db - utc_actual.replace(tzinfo=None)).total_seconds())
            
            # La diferencia con UTC debe ser de aproximadamente 6 horas (21600 segundos)
            if not (20000 < diferencia_utc < 23000):  # Entre ~5.5 y ~6.5 horas
                print(f"❌ FALLA: Fecha no es México (UTC-6). Diferencia con UTC: {diferencia_utc/3600:.2f}h")
                return False
            
            print("✅ ÉXITO: Venta creada con fecha México correcta")
            
            # 8. Limpiar venta de prueba
            cursor.execute("DELETE FROM venta_productos WHERE venta_id = %s", (venta.id,))
            cursor.execute("DELETE FROM ventas WHERE id = %s", (venta.id,))
            conn.commit()
        
        print("🧹 Venta de prueba eliminada")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de venta: {e}")
        return False

def test_multiples_ventas():
    """Prueba múltiples ventas rápidas para verificar consistencia"""
    
    print("\n" + "=" * 60)
    print("🔄 PRUEBA DE MÚLTIPLES VENTAS")
    print("=" * 60)
    
    ventas_ids = []
    fechas_ventas = []
    
    try:
        # Obtener producto de prueba
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM productos WHERE nombre = %s", ("Producto Test Fecha",))
            producto_row = cursor.fetchone()
            producto_id = producto_row[0]
        
        # Crear 5 ventas rápidas
        for i in range(5):
            print(f"💳 Creando venta {i+1}/5...")
            
            venta = Venta(
                vendedor=f"Test Auto {i+1}",
                metodo_pago="efectivo",
                productos_data=[{
                    'id': producto_id,
                    'nombre': 'Producto Test Fecha',
                    'precio': 10.00,
                    'cantidad': 1
                }]
            )
            
            venta.save()
            ventas_ids.append(venta.id)
            fechas_ventas.append(venta.fecha)
            
            print(f"   📅 Fecha: {venta.fecha}")
            
            time.sleep(0.5)  # Pausa corta entre ventas
        
        # Verificar que todas las fechas están en el mismo día México
        fechas_dias = [f.date() for f in fechas_ventas]
        dias_unicos = set(fechas_dias)
        
        print(f"\n📊 ANÁLISIS DE {len(fechas_ventas)} VENTAS:")
        print(f"   Días únicos: {len(dias_unicos)}")
        print(f"   Primera fecha: {fechas_ventas[0]}")
        print(f"   Última fecha: {fechas_ventas[-1]}")
        
        if len(dias_unicos) > 1:
            print("⚠️  Advertencia: Ventas en diferentes días (puede ser normal si es medianoche)")
        
        # Verificar que todas son hora México
        utc_actual = datetime.now(timezone.utc)
        for i, fecha in enumerate(fechas_ventas):
            diferencia_utc = abs((fecha - utc_actual.replace(tzinfo=None)).total_seconds())
            if not (20000 < diferencia_utc < 23000):
                print(f"❌ FALLA: Venta {i+1} no es hora México")
                return False
        
        print("✅ ÉXITO: Todas las ventas tienen fecha México correcta")
        
        # Limpiar ventas de prueba
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for venta_id in ventas_ids:
                cursor.execute("DELETE FROM venta_productos WHERE venta_id = %s", (venta_id,))
                cursor.execute("DELETE FROM ventas WHERE id = %s", (venta_id,))
            conn.commit()
        
        print("🧹 Ventas de prueba eliminadas")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba múltiples ventas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas completas del sistema de ventas...")
    
    exito_setup = setup_test_data()
    if not exito_setup:
        print("💥 Fallo en configuración, abortando pruebas")
        sys.exit(1)
    
    exito_venta = test_venta_completa()
    exito_multiples = test_multiples_ventas()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN FINAL")
    print("=" * 60)
    print(f"   Setup datos:         {'✅ PASS' if exito_setup else '❌ FAIL'}")
    print(f"   Venta completa:      {'✅ PASS' if exito_venta else '❌ FAIL'}")
    print(f"   Múltiples ventas:    {'✅ PASS' if exito_multiples else '❌ FAIL'}")
    
    if exito_setup and exito_venta and exito_multiples:
        print("\n🎉 SISTEMA DE VENTAS COMPLETAMENTE FUNCIONAL")
        print("   ✅ Fechas México siempre correctas")
        print("   ✅ Ventas se guardan sin errores")
        print("   ✅ Consistencia en múltiples operaciones")
        sys.exit(0)
    else:
        print("\n💥 ALGUNAS PRUEBAS FALLARON")
        print("   Revisar la implementación del sistema de ventas")
        sys.exit(1)

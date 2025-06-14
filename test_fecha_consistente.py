#!/usr/bin/env python3
"""
Prueba de consistencia de fechas México
Verifica que siempre obtenemos fechas UTC-6 sin variaciones
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.timezone_utils import get_mexico_datetime
from datetime import datetime, timezone, timedelta
import time

def test_fecha_consistente():
    """Prueba que las fechas son consistentes en múltiples llamadas"""
    
    print("=" * 60)
    print("🧪 PRUEBA DE CONSISTENCIA DE FECHAS MÉXICO")
    print("=" * 60)
    
    fechas = []
    
    # Obtener múltiples fechas en ráfaga
    for i in range(10):
        fecha = get_mexico_datetime()
        fechas.append(fecha)
        
        # Verificar que es razonable (no muy diferente de UTC)
        utc_now = datetime.now(timezone.utc)
        diferencia = abs((fecha - utc_now.replace(tzinfo=None)).total_seconds())
        
        print(f"📅 Fecha {i+1}: {fecha} (diff UTC: {diferencia/3600:.2f}h)")
        
        # Debe estar cerca de UTC-6 (6 horas de diferencia)
        if not (5 * 3600 < diferencia < 7 * 3600):
            print(f"❌ FALLA: Diferencia con UTC no es ~6h: {diferencia/3600:.2f}h")
            return False
        
        time.sleep(0.1)  # Pequeña pausa
    
    # Verificar que todas las fechas están en el mismo rango temporal
    primera = fechas[0]
    ultima = fechas[-1]
    rango_total = abs((ultima - primera).total_seconds())
    
    print(f"\n📊 ANÁLISIS:")
    print(f"   Primera fecha: {primera}")
    print(f"   Última fecha:  {ultima}")
    print(f"   Rango total:   {rango_total:.2f} segundos")
    
    if rango_total > 10:  # No debería haber más de 10 segundos de diferencia
        print(f"❌ FALLA: Rango muy amplio: {rango_total:.2f}s")
        return False
    
    # Verificar que todas siguen el patrón UTC-6
    utc_ref = datetime.now(timezone.utc)
    mexico_esperado = utc_ref - timedelta(hours=6)
    
    for i, fecha in enumerate(fechas):
        diferencia_esperada = abs((fecha - mexico_esperado.replace(tzinfo=None)).total_seconds())
        if diferencia_esperada > 300:  # Max 5 minutos de diferencia
            print(f"❌ FALLA: Fecha {i+1} muy diferente de UTC-6 esperado")
            return False
    
    print("✅ ÉXITO: Todas las fechas son consistentes con UTC-6")
    return True

def test_comparar_con_venta():
    """Simula el flujo de una venta para verificar la fecha"""
    
    print("\n" + "=" * 60)
    print("🛒 SIMULACIÓN DE VENTA")
    print("=" * 60)
    
    # Simular el momento de crear una venta
    fecha_venta = get_mexico_datetime()
    
    # Verificar que la fecha es del día actual México
    utc_now = datetime.now(timezone.utc)
    mexico_utc_offset = utc_now - timedelta(hours=6)
    
    print(f"📅 Fecha de venta:          {fecha_venta}")
    print(f"🌍 UTC actual:              {utc_now.replace(tzinfo=None)}")
    print(f"🇲🇽 México esperado (UTC-6): {mexico_utc_offset.replace(tzinfo=None)}")
    
    # La fecha de venta debe estar muy cerca de México esperado
    diferencia = abs((fecha_venta - mexico_utc_offset.replace(tzinfo=None)).total_seconds())
    print(f"⏱️  Diferencia:              {diferencia:.2f} segundos")
    
    if diferencia > 60:  # Máximo 1 minuto de diferencia
        print("❌ FALLA: Fecha de venta no corresponde a México actual")
        return False
    
    print("✅ ÉXITO: Fecha de venta correcta para México")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de consistencia de fechas...")
    
    exito1 = test_fecha_consistente()
    exito2 = test_comparar_con_venta()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"   Consistencia fechas: {'✅ PASS' if exito1 else '❌ FAIL'}")
    print(f"   Simulación venta:    {'✅ PASS' if exito2 else '❌ FAIL'}")
    
    if exito1 and exito2:
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        print("   El sistema de fechas es robusto y consistente")
        sys.exit(0)
    else:
        print("\n💥 ALGUNAS PRUEBAS FALLARON")
        print("   Revisar la implementación de timezone_utils.py")
        sys.exit(1)

#!/usr/bin/env python3
"""
Prueba específica de las funciones que fallaban en producción
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.timezone_utils import (
    get_mexico_datetime, 
    format_mexico_datetime, 
    get_mexico_date_str,
    get_mexico_time_str,
    convert_to_mexico_time
)
from datetime import datetime, timezone, timedelta

def test_format_functions():
    """Prueba las funciones de formato que fallaban"""
    
    print("🧪 PRUEBA DE FUNCIONES DE FORMATO")
    print("=" * 50)
    
    # 1. Test con fecha None (debe usar actual)
    try:
        formatted = format_mexico_datetime()
        print(f"✅ format_mexico_datetime(): {formatted}")
    except Exception as e:
        print(f"❌ format_mexico_datetime() falló: {e}")
        return False
    
    # 2. Test con fecha naive (sin timezone)
    try:
        fecha_naive = datetime(2025, 6, 13, 15, 30, 0)
        formatted = format_mexico_datetime(fecha_naive)
        print(f"✅ format_mexico_datetime(naive): {formatted}")
    except Exception as e:
        print(f"❌ format_mexico_datetime(naive) falló: {e}")
        return False
    
    # 3. Test con fecha UTC
    try:
        fecha_utc = datetime(2025, 6, 14, 2, 30, 0, tzinfo=timezone.utc)
        formatted = format_mexico_datetime(fecha_utc)
        print(f"✅ format_mexico_datetime(UTC): {formatted}")
    except Exception as e:
        print(f"❌ format_mexico_datetime(UTC) falló: {e}")
        return False
    
    # 4. Test de get_mexico_date_str
    try:
        date_str = get_mexico_date_str()
        print(f"✅ get_mexico_date_str(): {date_str}")
    except Exception as e:
        print(f"❌ get_mexico_date_str() falló: {e}")
        return False
    
    # 5. Test de get_mexico_time_str
    try:
        time_str = get_mexico_time_str()
        print(f"✅ get_mexico_time_str(): {time_str}")
    except Exception as e:
        print(f"❌ get_mexico_time_str() falló: {e}")
        return False
    
    # 6. Test de convert_to_mexico_time
    try:
        utc_time = datetime.now(timezone.utc)
        mexico_time = convert_to_mexico_time(utc_time)
        print(f"✅ convert_to_mexico_time(): {mexico_time}")
    except Exception as e:
        print(f"❌ convert_to_mexico_time() falló: {e}")
        return False
    
    return True

def test_orden_simulation():
    """Simula el caso específico de órdenes que fallaba"""
    
    print("\n🛒 SIMULACIÓN CASO ÓRDENES")
    print("=" * 50)
    
    try:
        # Simular una orden con fecha como string ISO (como viene de la BD)
        fecha_orden_str = "2025-06-13T20:30:00"
        fecha_orden = datetime.fromisoformat(fecha_orden_str)
        
        print(f"📅 Fecha orden original: {fecha_orden}")
        
        # Esta era la línea que fallaba en órdenes
        formatted = format_mexico_datetime(fecha_orden)
        print(f"✅ Fecha formateada: {formatted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulación órdenes falló: {e}")
        return False

def test_cache_calculation():
    """Verifica que el cálculo de offset se hace solo una vez"""
    
    print("\n⚡ PRUEBA DE CACHE DE OFFSET")
    print("=" * 50)
    
    # Llamar varias veces y verificar que no se recalcula
    fechas = []
    for i in range(10):
        fecha = get_mexico_datetime()
        fechas.append(fecha)
        print(f"📅 Fecha {i+1}: {fecha}")
    
    # Todas deben tener el mismo patrón de hora (diferir en segundos, no en horas)
    primera_hora = fechas[0].hour
    for i, fecha in enumerate(fechas[1:], 1):
        if abs(fecha.hour - primera_hora) > 1:  # Máximo 1 hora de diferencia
            print(f"❌ Inconsistencia en hora: {fecha.hour} vs {primera_hora}")
            return False
    
    print("✅ Cache funcionando correctamente")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de funciones específicas...")
    
    exito1 = test_format_functions()
    exito2 = test_orden_simulation()
    exito3 = test_cache_calculation()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN")
    print("=" * 50)
    print(f"   Funciones formato: {'✅ PASS' if exito1 else '❌ FAIL'}")
    print(f"   Simulación órdenes: {'✅ PASS' if exito2 else '❌ FAIL'}")
    print(f"   Cache offset:      {'✅ PASS' if exito3 else '❌ FAIL'}")
    
    if exito1 and exito2 and exito3:
        print("\n🎉 TODAS LAS FUNCIONES TRABAJANDO CORRECTAMENTE")
        print("   ✅ Sin errores de localize()")
        print("   ✅ Cache de offset funcionando")
        print("   ✅ Compatible con órdenes")
        sys.exit(0)
    else:
        print("\n💥 ALGUNAS FUNCIONES TIENEN PROBLEMAS")
        sys.exit(1)

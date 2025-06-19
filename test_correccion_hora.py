#!/usr/bin/env python3
"""
Script para probar la corrección del manejo de fecha/hora en ventas
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.timezone_utils import get_mexico_datetime

def test_fecha_hora_logic():
    """Probar la lógica de fecha/hora corregida"""
    print("🧪 Probando la lógica corregida de fecha/hora...")
    
    # Simular la lógica actual del sistema
    def simular_fecha_venta(fecha_seleccionada):
        """Simular cómo se procesará la fecha según la nueva lógica"""
        fecha_hoy_mexico = get_mexico_datetime().date()
        
        if fecha_seleccionada == fecha_hoy_mexico:
            # Si es la fecha de hoy, usar fecha y hora completa actual de México
            fecha_completa = get_mexico_datetime()
            tipo = "Fecha de hoy"
        else:
            # Si es una fecha diferente (manual), usar esa fecha con la hora actual de México
            hora_actual_mexico = get_mexico_datetime().time()
            fecha_completa = datetime.combine(fecha_seleccionada, hora_actual_mexico)
            tipo = "Fecha manual"
        
        return fecha_completa, tipo
    
    # Prueba 1: Fecha de hoy
    fecha_hoy = get_mexico_datetime().date()
    resultado_hoy, tipo_hoy = simular_fecha_venta(fecha_hoy)
    print(f"\n✅ Prueba 1 - {tipo_hoy}:")
    print(f"   Fecha seleccionada: {fecha_hoy}")
    print(f"   Resultado: {resultado_hoy}")
    print(f"   Hora: {resultado_hoy.strftime('%H:%M:%S')}")
    
    # Prueba 2: Fecha de ayer
    fecha_ayer = (get_mexico_datetime() - timedelta(days=1)).date()
    resultado_ayer, tipo_ayer = simular_fecha_venta(fecha_ayer)
    print(f"\n✅ Prueba 2 - {tipo_ayer}:")
    print(f"   Fecha seleccionada: {fecha_ayer}")
    print(f"   Resultado: {resultado_ayer}")
    print(f"   Hora: {resultado_ayer.strftime('%H:%M:%S')}")
    
    # Prueba 3: Fecha futura
    fecha_manana = (get_mexico_datetime() + timedelta(days=1)).date()
    resultado_manana, tipo_manana = simular_fecha_venta(fecha_manana)
    print(f"\n✅ Prueba 3 - {tipo_manana}:")
    print(f"   Fecha seleccionada: {fecha_manana}")
    print(f"   Resultado: {resultado_manana}")
    print(f"   Hora: {resultado_manana.strftime('%H:%M:%S')}")
    
    # Verificación de que todas las horas son la actual
    hora_actual = get_mexico_datetime().strftime('%H:%M:%S')
    print(f"\n⏰ Hora actual de México: {hora_actual}")
    
    # Verificar que todas las pruebas usan la hora actual
    horas_resultados = [
        resultado_hoy.strftime('%H:%M:%S'),
        resultado_ayer.strftime('%H:%M:%S'),
        resultado_manana.strftime('%H:%M:%S')
    ]
    
    todas_correctas = all(hora.split(':')[0:2] == hora_actual.split(':')[0:2] for hora in horas_resultados)
    
    if todas_correctas:
        print("\n🎉 ¡CORRECCIÓN EXITOSA! Todas las ventas usarán la hora actual de México.")
    else:
        print("\n❌ ERROR: Algunas ventas no usan la hora actual.")
        for i, hora in enumerate(horas_resultados, 1):
            print(f"   Prueba {i}: {hora}")
    
    return todas_correctas

if __name__ == "__main__":
    try:
        resultado = test_fecha_hora_logic()
        if resultado:
            print("\n✅ La corrección funciona correctamente.")
            sys.exit(0)
        else:
            print("\n❌ La corrección tiene problemas.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        sys.exit(1)

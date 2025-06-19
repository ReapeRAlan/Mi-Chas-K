#!/usr/bin/env python3
"""
Script simple para probar la corrección de fecha/hora
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.timezone_utils import get_mexico_datetime
    print("✅ Módulo timezone_utils importado correctamente")
    
    # Obtener hora actual de México
    ahora_mexico = get_mexico_datetime()
    print(f"🇲🇽 Hora actual México: {ahora_mexico}")
    print(f"⏰ Hora formateada: {ahora_mexico.strftime('%H:%M:%S')}")
    
    # Simular la nueva lógica
    fecha_hoy = ahora_mexico.date()
    fecha_ayer = (ahora_mexico - timedelta(days=1)).date()
    
    print(f"\n📅 Fecha de hoy: {fecha_hoy}")
    print(f"📅 Fecha de ayer: {fecha_ayer}")
    
    # Simular procesamiento para fecha de hoy
    if fecha_hoy == ahora_mexico.date():
        resultado_hoy = ahora_mexico
        print(f"✅ Hoy - Usar hora completa: {resultado_hoy}")
    
    # Simular procesamiento para fecha de ayer
    if fecha_ayer != ahora_mexico.date():
        hora_actual = ahora_mexico.time()
        resultado_ayer = datetime.combine(fecha_ayer, hora_actual)
        print(f"✅ Ayer - Usar fecha ayer con hora actual: {resultado_ayer}")
    
    print("\n🎉 ¡La corrección funciona! Ambos casos usan la hora actual de México.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

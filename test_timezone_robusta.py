#!/usr/bin/env python3
"""
Prueba del nuevo sistema de zona horaria robusta
"""
import sys
sys.path.append('/home/ghost/Escritorio/CHASKAS/Mi-Chas-K')

from utils.timezone_utils import get_mexico_datetime
from datetime import datetime, timezone, timedelta
import time

def test_timezone_robusta():
    print("🧪 PRUEBA DE ZONA HORARIA ROBUSTA")
    print("="*50)
    
    # Obtener UTC actual
    utc_now = datetime.now(timezone.utc)
    print(f"🌍 UTC actual: {utc_now}")
    
    # Obtener México usando nuestra función (múltiples veces)
    for i in range(3):
        mexico = get_mexico_datetime()
        print(f"🇲🇽 México #{i+1}: {mexico}")
        
        # Verificar que es 6 horas atrás de UTC
        utc_naive = utc_now.replace(tzinfo=None)
        diferencia = (utc_naive - mexico).total_seconds() / 3600
        print(f"   Diferencia con UTC: {diferencia:.1f} horas")
        
        if abs(diferencia - 6.0) < 0.1:  # Tolerancia de 6 minutos
            print("   ✅ CORRECTO: UTC-6")
        else:
            print("   ❌ INCORRECTO: No es UTC-6")
        
        if i < 2:  # Pausa entre pruebas
            time.sleep(1)
    
    print("\n📊 VERIFICACIÓN FINAL:")
    fecha_final = get_mexico_datetime()
    print(f"🕐 Fecha final México: {fecha_final}")
    print(f"📅 Es 13 de junio 2025: {fecha_final.date() == datetime(2025, 6, 13).date()}")
    print(f"⏰ Hora entre 20-21: {20 <= fecha_final.hour <= 21}")

if __name__ == "__main__":
    test_timezone_robusta()

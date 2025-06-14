#!/usr/bin/env python3
"""
Prueba rápida de fecha/hora México
"""
import sys
sys.path.append('/home/ghost/Escritorio/CHASKAS/Mi-Chas-K')

from utils.timezone_utils import get_mexico_datetime
from datetime import datetime, timezone, timedelta
import pytz

def test_timezone():
    print("🕐 PRUEBA DE ZONA HORARIA MÉXICO")
    print("="*50)
    
    # Hora actual del sistema (UTC)
    utc_now = datetime.utcnow()
    print(f"🌍 Hora UTC del sistema: {utc_now}")
    
    # Hora México usando pytz directo
    mexico_tz = pytz.timezone('America/Mexico_City')
    mexico_direct = datetime.now(mexico_tz)
    print(f"🇲🇽 Hora México (pytz directo): {mexico_direct}")
    
    # Hora México usando nuestra función
    mexico_our_func = get_mexico_datetime()
    print(f"🛠️  Hora México (nuestra función): {mexico_our_func}")
    
    # Verificar diferencia
    utc_with_tz = utc_now.replace(tzinfo=timezone.utc)
    mexico_with_tz = utc_with_tz.astimezone(mexico_tz)
    print(f"✅ Hora México (conversión manual): {mexico_with_tz}")
    
    print("\n📊 ANÁLISIS:")
    print(f"   - Diferencia UTC vs México: {(mexico_with_tz.replace(tzinfo=None) - utc_now).total_seconds()/3600:.1f} horas")
    print(f"   - Es 13 de junio 2025: {mexico_our_func.date() == datetime(2025, 6, 13).date()}")
    print(f"   - Hora aproximada: {mexico_our_func.hour}:{mexico_our_func.minute:02d}")

if __name__ == "__main__":
    test_timezone()

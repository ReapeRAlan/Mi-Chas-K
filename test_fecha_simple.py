#!/usr/bin/env python3
"""
Prueba simple de fecha México
Verifica que el sistema de fechas esté funcionando correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.timezone_utils import get_mexico_datetime
from datetime import datetime, timezone, timedelta

def main():
    print("🧪 PRUEBA SIMPLE DE FECHA MÉXICO")
    print("=" * 50)
    
    # Obtener fecha México múltiples veces
    fechas = []
    for i in range(5):
        fecha = get_mexico_datetime()
        fechas.append(fecha)
        print(f"📅 Fecha {i+1}: {fecha}")
    
    # Verificar consistencia
    primera = fechas[0]
    ultima = fechas[-1]
    diferencia = abs((ultima - primera).total_seconds())
    
    print(f"\n📊 ANÁLISIS:")
    print(f"   Diferencia temporal: {diferencia:.2f} segundos")
    
    # Verificar que es hora México (UTC-6)
    utc_now = datetime.now(timezone.utc)
    mexico_esperado = utc_now - timedelta(hours=6)
    
    diferencia_esperada = abs((primera - mexico_esperado.replace(tzinfo=None)).total_seconds())
    
    print(f"   UTC actual: {utc_now.replace(tzinfo=None)}")
    print(f"   México esperado: {mexico_esperado.replace(tzinfo=None)}")
    print(f"   Diferencia: {diferencia_esperada:.2f} segundos")
    
    if diferencia_esperada < 60:  # Menos de 1 minuto
        print("✅ ÉXITO: Sistema de fechas México funcionando correctamente")
        return True
    else:
        print("❌ FALLA: Sistema de fechas no está en UTC-6")
        return False

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)

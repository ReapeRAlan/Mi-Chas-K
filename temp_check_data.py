#!/usr/bin/env python3
"""Script temporal para consultar datos reales de la base de datos"""

import sys
import os
sys.path.append('.')

from database.connection import get_db_connection
from database.models import *
import sqlite3
from datetime import datetime

def check_database():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
        
        print('=== DATOS REALES DE LA BASE DE DATOS ===')
        print()
        
        # Verificar ventas
        cursor.execute('''
            SELECT SUM(total) as total_ventas, 
                   SUM(CASE WHEN metodo_pago = "efectivo" THEN total ELSE 0 END) as efectivo,
                   SUM(CASE WHEN metodo_pago = "tarjeta" THEN total ELSE 0 END) as tarjeta,
                   SUM(CASE WHEN metodo_pago = "transferencia" THEN total ELSE 0 END) as transferencia 
            FROM ventas 
            WHERE DATE(fecha) = "2025-01-13"
        ''')
        ventas = cursor.fetchone()
        
        print('📊 VENTAS DEL DÍA 2025-01-13:')
        print(f'Total ventas: ${ventas[0]:.2f}' if ventas[0] else 'Total ventas: $0.00')
        print(f'Efectivo: ${ventas[1]:.2f}' if ventas[1] else 'Efectivo: $0.00')
        print(f'Tarjeta: ${ventas[2]:.2f}' if ventas[2] else 'Tarjeta: $0.00')
        print(f'Transferencia: ${ventas[3]:.2f}' if ventas[3] else 'Transferencia: $0.00')
        print()
        
        # Verificar gastos
        cursor.execute('''
            SELECT SUM(monto) as total_gastos 
            FROM gastos 
            WHERE DATE(fecha) = "2025-01-13"
        ''')
        gastos = cursor.fetchone()
        
        print('💸 GASTOS DEL DÍA:')
        print(f'Total gastos: ${gastos[0]:.2f}' if gastos[0] else 'Total gastos: $0.00')
        print()
        
        # Verificar cortes de caja
        cursor.execute('''
            SELECT * FROM cortes_caja 
            WHERE DATE(fecha) = "2025-01-13" 
            ORDER BY fecha DESC LIMIT 1
        ''')
        corte = cursor.fetchone()
        
        if corte:
            print('💰 ÚLTIMO CORTE DE CAJA:')
            print(f'Dinero inicial: ${corte[2]:.2f}')
            print(f'Dinero final: ${corte[3]:.2f}')
            print(f'Ventas efectivo: ${corte[4]:.2f}')
            print(f'Ventas tarjeta: ${corte[5]:.2f}')
            print(f'Gastos: ${corte[6]:.2f}')
            print()
        else:
            print('❌ No hay cortes de caja para esta fecha')
            print()
        
        # CÁLCULO CORRECTO SEGÚN ESPECIFICACIONES
        if ventas[0] and gastos[0] and corte:
            print('🧮 CÁLCULO CORRECTO:')
            print()
            
            # Lado Sistema: Ingresos Totales - Gastos
            ingresos_totales = ventas[0] or 0
            gastos_sistema = gastos[0] or 0
            resultado_sistema = ingresos_totales - gastos_sistema
            
            print('📈 LADO SISTEMA:')
            print(f'Ingresos Totales: ${ingresos_totales:.2f}')
            print(f'Gastos: ${gastos_sistema:.2f}')
            print(f'Resultado Sistema: ${resultado_sistema:.2f}')
            print()
            
            # Lado Caja: Dinero Final - Dinero Inicial - Gastos
            dinero_final = corte[3] or 0
            dinero_inicial = corte[2] or 0
            gastos_caja = corte[6] or 0
            resultado_caja = dinero_final - dinero_inicial - gastos_caja
            
            print('💰 LADO CAJA:')
            print(f'Dinero Final: ${dinero_final:.2f}')
            print(f'Dinero Inicial: ${dinero_inicial:.2f}')
            print(f'Gastos: ${gastos_caja:.2f}')
            print(f'Resultado Caja: ${resultado_caja:.2f}')
            print()
            
            # Diferencia
            diferencia = resultado_sistema - resultado_caja
            print('📊 DIFERENCIA:')
            print(f'Sistema - Caja = ${resultado_sistema:.2f} - ${resultado_caja:.2f} = ${diferencia:.2f}')
            print()
            
            if diferencia > 0:
                print('✅ Sobrante en sistema (más ingresos de los esperados)')
            elif diferencia < 0:
                print('⚠️ Faltante en sistema (menos ingresos de los esperados)')
            else:
                print('✅ Cuadre perfecto')
                
        # No necesitamos cerrar la conexión porque usamos context manager
        
    except Exception as e:
        print(f'Error: {e}')
        print('Intentando con SQLite...')
        
        # Intentar con SQLite si hay problemas
        try:
            conn = sqlite3.connect('database/sistema_pos.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = cursor.fetchall()
            print(f'Tablas disponibles: {tables}')
            
            conn.close()
        except Exception as e2:
            print(f'Error SQLite: {e2}')

if __name__ == "__main__":
    check_database()

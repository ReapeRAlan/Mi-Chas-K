#!/usr/bin/env python3
"""
Script para consultar datos reales de la base de datos PostgreSQL en Render
y validar la lógica del dashboard
"""

import psycopg2
import pandas as pd
from datetime import datetime, date
import os

# Credenciales de la base de datos en Render
DB_CONFIG = {
    'host': 'dpg-d13oam8dl3ps7392hfu0-a.oregon-postgres.render.com',
    'database': 'chaskabd',
    'user': 'admin',
    'password': 'wkxMvaYK9HZaSWCsMn2aZJA3EMC9wLNu',
    'port': '5432'
}

def connect_to_render_db():
    """Conectar a la base de datos PostgreSQL en Render"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conexión exitosa a la base de datos PostgreSQL en Render")
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def check_tables_structure(conn):
    """Verificar la estructura de las tablas"""
    try:
        cursor = conn.cursor()
        
        # Listar todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print("\n📋 Tablas disponibles:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Estructura de tabla ventas
        print("\n🏗️ Estructura tabla 'ventas':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'ventas'
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Estructura de tabla cortes_caja
        print("\n🏗️ Estructura tabla 'cortes_caja':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'cortes_caja'
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Estructura de tabla gastos_diarios
        print("\n🏗️ Estructura tabla 'gastos_diarios':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'gastos_diarios'
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")

def check_data_for_date(conn, fecha_consulta):
    """Consultar datos específicos para una fecha"""
    try:
        cursor = conn.cursor()
        
        print(f"\n📊 Datos para la fecha: {fecha_consulta}")
        print("=" * 50)
        
        # 1. Ventas del día
        cursor.execute("""
            SELECT 
                COUNT(*) as total_ventas,
                SUM(total) as ingresos_totales,
                MIN(fecha) as primera_venta,
                MAX(fecha) as ultima_venta
            FROM ventas 
            WHERE DATE(fecha) = %s
        """, (fecha_consulta,))
        
        venta_data = cursor.fetchone()
        if venta_data:
            print(f"💰 VENTAS:")
            print(f"  - Total de ventas: {venta_data[0] or 0}")
            print(f"  - Ingresos totales: ${venta_data[1] or 0:.2f}")
            print(f"  - Primera venta: {venta_data[2] or 'N/A'}")
            print(f"  - Última venta: {venta_data[3] or 'N/A'}")
        
        # 2. Gastos del día
        cursor.execute("""
            SELECT 
                SUM(monto) as total_gastos,
                COUNT(*) as num_gastos
            FROM gastos_diarios 
            WHERE DATE(fecha) = %s
        """, (fecha_consulta,))
        
        gastos_data = cursor.fetchone()
        total_gastos = gastos_data[0] or 0 if gastos_data else 0
        num_gastos = gastos_data[1] or 0 if gastos_data else 0
        
        print(f"\n💸 GASTOS:")
        print(f"  - Total de gastos: ${total_gastos:.2f}")
        print(f"  - Número de gastos: {num_gastos}")
        
        # 3. Corte de caja del día
        cursor.execute("""
            SELECT 
                dinero_inicial,
                dinero_final,
                diferencia,
                observaciones,
                fecha
            FROM cortes_caja 
            WHERE DATE(fecha) = %s
            ORDER BY fecha DESC
            LIMIT 1
        """, (fecha_consulta,))
        
        corte_data = cursor.fetchone()
        if corte_data:
            print(f"\n💼 CORTE DE CAJA:")
            print(f"  - Dinero inicial: ${corte_data[0] or 0:.2f}")
            print(f"  - Dinero final: ${corte_data[1] or 0:.2f}")
            print(f"  - Diferencia registrada: ${corte_data[2] or 0:.2f}")
            print(f"  - Observaciones: {corte_data[3] or 'Sin observaciones'}")
            print(f"  - Fecha: {corte_data[4] or 'N/A'}")
        else:
            print(f"\n💼 CORTE DE CAJA: No hay datos para esta fecha")
        
        # 4. Cálculo de la lógica correcta
        if venta_data and corte_data:
            print(f"\n🧮 CÁLCULO DE LA LÓGICA CORRECTA:")
            print("=" * 40)
            
            # Datos del sistema
            ingresos_sistema = venta_data[1] or 0
            gastos_sistema = total_gastos
            resultado_sistema = ingresos_sistema - gastos_sistema
            
            # Datos de la caja física
            dinero_inicial = corte_data[0] or 0
            dinero_final = corte_data[1] or 0
            resultado_caja = dinero_final - dinero_inicial - gastos_sistema
            
            # Diferencia
            diferencia_calculada = resultado_sistema - resultado_caja
            diferencia_registrada = corte_data[2] or 0
            
            print(f"📈 LADO SISTEMA:")
            print(f"  - Ingresos totales: ${ingresos_sistema:.2f}")
            print(f"  - Gastos: ${gastos_sistema:.2f}")
            print(f"  - Resultado sistema: ${resultado_sistema:.2f}")
            
            print(f"\n💰 LADO CAJA FÍSICA:")
            print(f"  - Dinero inicial: ${dinero_inicial:.2f}")
            print(f"  - Dinero final: ${dinero_final:.2f}")
            print(f"  - Gastos: ${gastos_sistema:.2f}")
            print(f"  - Resultado caja: ${resultado_caja:.2f}")
            
            print(f"\n⚖️ DIFERENCIA:")
            print(f"  - Diferencia calculada: ${diferencia_calculada:.2f}")
            print(f"  - Diferencia registrada: ${diferencia_registrada:.2f}")
            print(f"  - ¿Coinciden?: {'✅ SÍ' if abs(diferencia_calculada - diferencia_registrada) < 0.01 else '❌ NO'}")
            
            if abs(diferencia_calculada - diferencia_registrada) >= 0.01:
                print(f"  - Discrepancia: ${abs(diferencia_calculada - diferencia_registrada):.2f}")
        
        # 5. Listado detallado de ventas
        print(f"\n📋 DETALLE DE VENTAS:")
        cursor.execute("""
            SELECT 
                id,
                fecha,
                total,
                metodo_pago,
                vendedor
            FROM ventas 
            WHERE DATE(fecha) = %s
            ORDER BY fecha
        """, (fecha_consulta,))
        
        ventas_detalle = cursor.fetchall()
        if ventas_detalle:
            for venta in ventas_detalle:
                print(f"  - ID: {venta[0]}, Hora: {venta[1].strftime('%H:%M:%S') if venta[1] else 'N/A'}, Total: ${venta[2]:.2f}, Pago: {venta[3] or 'N/A'}, Vendedor: {venta[4] or 'N/A'}")
        else:
            print("  - No hay ventas registradas para esta fecha")
        
        # 6. Listado detallado de gastos
        print(f"\n💸 DETALLE DE GASTOS:")
        cursor.execute("""
            SELECT 
                id,
                fecha,
                monto,
                descripcion,
                categoria
            FROM gastos_diarios 
            WHERE DATE(fecha) = %s
            ORDER BY fecha
        """, (fecha_consulta,))
        
        gastos_detalle = cursor.fetchall()
        if gastos_detalle:
            for gasto in gastos_detalle:
                print(f"  - ID: {gasto[0]}, Hora: {gasto[1].strftime('%H:%M:%S') if gasto[1] else 'N/A'}, Monto: ${gasto[2]:.2f}, Desc: {gasto[3] or 'N/A'}, Cat: {gasto[4] or 'N/A'}")
        else:
            print("  - No hay gastos registrados para esta fecha")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error consultando datos: {e}")

def main():
    """Función principal"""
    print("🔍 CONSULTANDO DATOS REALES DE LA BASE DE DATOS EN RENDER")
    print("=" * 60)
    
    # Conectar a la base de datos
    conn = connect_to_render_db()
    if not conn:
        return
    
    try:
        # Verificar estructura de tablas
        check_tables_structure(conn)
        
        # Consultar datos para fechas específicas
        fechas_consulta = [
            '2025-01-13',  # Fecha de ejemplo
            '2025-01-14',  # Fecha actual
            '2025-01-12',  # Fecha anterior
        ]
        
        for fecha in fechas_consulta:
            check_data_for_date(conn, fecha)
            print("\n" + "=" * 60)
        
    finally:
        conn.close()
        print("\n🔐 Conexión cerrada")

if __name__ == "__main__":
    main()

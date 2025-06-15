#!/usr/bin/env python3
"""
Script para consultar todas las fechas con datos y mostrar un resumen general
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

def get_all_dates_with_data(conn):
    """Obtener todas las fechas que tienen datos"""
    try:
        cursor = conn.cursor()
        
        print("\n📅 FECHAS CON DATOS EN EL SISTEMA:")
        print("=" * 50)
        
        # Fechas con ventas
        cursor.execute("""
            SELECT DISTINCT DATE(fecha) as fecha, COUNT(*) as num_ventas, SUM(total) as total_ventas
            FROM ventas 
            WHERE fecha IS NOT NULL
            GROUP BY DATE(fecha)
            ORDER BY fecha DESC
            LIMIT 10
        """)
        
        fechas_ventas = cursor.fetchall()
        if fechas_ventas:
            print("💰 FECHAS CON VENTAS:")
            for fecha_data in fechas_ventas:
                print(f"  - {fecha_data[0]}: {fecha_data[1]} ventas, Total: ${fecha_data[2]:.2f}")
        else:
            print("💰 No hay fechas con ventas registradas")
        
        # Fechas con gastos
        cursor.execute("""
            SELECT DISTINCT fecha, COUNT(*) as num_gastos, SUM(monto) as total_gastos
            FROM gastos_diarios
            GROUP BY fecha
            ORDER BY fecha DESC
            LIMIT 10
        """)
        
        fechas_gastos = cursor.fetchall()
        if fechas_gastos:
            print("\n💸 FECHAS CON GASTOS:")
            for fecha_data in fechas_gastos:
                print(f"  - {fecha_data[0]}: {fecha_data[1]} gastos, Total: ${fecha_data[2]:.2f}")
        else:
            print("\n💸 No hay fechas con gastos registrados")
        
        # Fechas con cortes de caja
        cursor.execute("""
            SELECT fecha, dinero_inicial, dinero_final, diferencia, observaciones
            FROM cortes_caja
            ORDER BY fecha DESC
            LIMIT 10
        """)
        
        fechas_cortes = cursor.fetchall()
        if fechas_cortes:
            print("\n💼 FECHAS CON CORTES DE CAJA:")
            for fecha_data in fechas_cortes:
                print(f"  - {fecha_data[0]}: Inicial: ${fecha_data[1] or 0:.2f}, Final: ${fecha_data[2] or 0:.2f}, Dif: ${fecha_data[3] or 0:.2f}")
        else:
            print("\n💼 No hay fechas con cortes de caja registrados")
        
        cursor.close()
        
        # Retornar la primera fecha con datos para análisis detallado
        if fechas_ventas:
            return fechas_ventas[0][0]
        elif fechas_gastos:
            return fechas_gastos[0][0]
        elif fechas_cortes:
            return fechas_cortes[0][0]
        else:
            return None
        
    except Exception as e:
        print(f"❌ Error obteniendo fechas: {e}")
        return None

def create_test_data(conn):
    """Crear datos de prueba para validar la lógica"""
    try:
        cursor = conn.cursor()
        
        print("\n🧪 CREANDO DATOS DE PRUEBA:")
        print("=" * 40)
        
        fecha_hoy = date.today()
        
        # 1. Insertar una venta de prueba
        cursor.execute("""
            INSERT INTO ventas (total, fecha, metodo_pago, vendedor, observaciones)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (150.75, fecha_hoy, 'efectivo', 'Test User', 'Venta de prueba para validar lógica'))
        
        venta_id = cursor.fetchone()[0]
        print(f"✅ Venta de prueba creada - ID: {venta_id}, Total: $150.75")
        
        # 2. Insertar un gasto de prueba
        cursor.execute("""
            INSERT INTO gastos_diarios (fecha, monto, concepto, descripcion, categoria, vendedor)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (fecha_hoy, 25.50, 'Materiales', 'Gasto de prueba para validar lógica', 'Operativo', 'Test User'))
        
        gasto_id = cursor.fetchone()[0]
        print(f"✅ Gasto de prueba creado - ID: {gasto_id}, Monto: $25.50")
        
        # 3. Insertar un corte de caja de prueba
        cursor.execute("""
            INSERT INTO cortes_caja (fecha, dinero_inicial, dinero_final, total_gastos, diferencia, vendedor, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (fecha_hoy, 100.00, 225.25, 25.50, 0.00, 'Test User', 'Corte de prueba para validar lógica'))
        
        corte_id = cursor.fetchone()[0]
        print(f"✅ Corte de caja de prueba creado - ID: {corte_id}")
        
        conn.commit()
        print("✅ Datos de prueba guardados exitosamente")
        
        return fecha_hoy
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        conn.rollback()
        return None

def analyze_fecha_detallada(conn, fecha_consulta):
    """Análisis detallado para una fecha específica"""
    try:
        cursor = conn.cursor()
        
        print(f"\n🔍 ANÁLISIS DETALLADO PARA: {fecha_consulta}")
        print("=" * 50)
        
        # 1. Ventas del día
        cursor.execute("""
            SELECT 
                COUNT(*) as total_ventas,
                SUM(total) as ingresos_totales,
                SUM(CASE WHEN metodo_pago = 'efectivo' THEN total ELSE 0 END) as ventas_efectivo,
                SUM(CASE WHEN metodo_pago = 'tarjeta' THEN total ELSE 0 END) as ventas_tarjeta
            FROM ventas 
            WHERE DATE(fecha) = %s
        """, (fecha_consulta,))
        
        venta_data = cursor.fetchone()
        
        # 2. Gastos del día
        cursor.execute("""
            SELECT 
                SUM(monto) as total_gastos,
                COUNT(*) as num_gastos
            FROM gastos_diarios 
            WHERE fecha = %s
        """, (fecha_consulta,))
        
        gastos_data = cursor.fetchone()
        
        # 3. Corte de caja del día
        cursor.execute("""
            SELECT 
                dinero_inicial,
                dinero_final,
                ventas_efectivo,
                ventas_tarjeta,
                total_gastos,
                diferencia,
                observaciones
            FROM cortes_caja 
            WHERE fecha = %s
            ORDER BY fecha_registro DESC
            LIMIT 1
        """, (fecha_consulta,))
        
        corte_data = cursor.fetchone()
        
        # Mostrar datos
        if venta_data:
            ingresos_totales = venta_data[1] or 0
            ventas_efectivo = venta_data[2] or 0
            ventas_tarjeta = venta_data[3] or 0
            print(f"💰 VENTAS DEL SISTEMA:")
            print(f"  - Total de ventas: {venta_data[0] or 0}")
            print(f"  - Ingresos totales: ${ingresos_totales:.2f}")
            print(f"  - Ventas en efectivo: ${ventas_efectivo:.2f}")
            print(f"  - Ventas con tarjeta: ${ventas_tarjeta:.2f}")
        else:
            ingresos_totales = ventas_efectivo = ventas_tarjeta = 0
            print(f"💰 VENTAS DEL SISTEMA: No hay datos")
        
        if gastos_data:
            total_gastos = gastos_data[0] or 0
            print(f"\n💸 GASTOS DEL SISTEMA:")
            print(f"  - Total de gastos: ${total_gastos:.2f}")
            print(f"  - Número de gastos: {gastos_data[1] or 0}")
        else:
            total_gastos = 0
            print(f"\n💸 GASTOS DEL SISTEMA: No hay datos")
        
        if corte_data:
            dinero_inicial = corte_data[0] or 0
            dinero_final = corte_data[1] or 0
            diferencia_registrada = corte_data[5] or 0
            
            print(f"\n💼 CORTE DE CAJA:")
            print(f"  - Dinero inicial: ${dinero_inicial:.2f}")
            print(f"  - Dinero final: ${dinero_final:.2f}")
            print(f"  - Diferencia registrada: ${diferencia_registrada:.2f}")
            print(f"  - Observaciones: {corte_data[6] or 'Sin observaciones'}")
            
            # CÁLCULO CORRECTO DE LA LÓGICA
            print(f"\n🧮 VALIDACIÓN DE LA LÓGICA CONTABLE:")
            print("=" * 40)
            
            # Lado sistema: Ingresos - Gastos
            resultado_sistema = ingresos_totales - total_gastos
            
            # Lado caja: (Dinero final - Dinero inicial) - Gastos
            # Esto representa cuánto dinero "sobró" en la caja después de descontar gastos
            resultado_caja = (dinero_final - dinero_inicial) - total_gastos
            
            # Diferencia: Sistema - Caja
            diferencia_calculada = resultado_sistema - resultado_caja
            
            print(f"📊 LADO SISTEMA (Lo que debería haber):")
            print(f"  - Ingresos totales: ${ingresos_totales:.2f}")
            print(f"  - Gastos: ${total_gastos:.2f}")
            print(f"  - Resultado sistema: ${resultado_sistema:.2f}")
            
            print(f"\n💰 LADO CAJA FÍSICA (Lo que hay realmente):")
            print(f"  - Dinero inicial: ${dinero_inicial:.2f}")
            print(f"  - Dinero final: ${dinero_final:.2f}")
            print(f"  - Incremento en caja: ${dinero_final - dinero_inicial:.2f}")
            print(f"  - Gastos: ${total_gastos:.2f}")
            print(f"  - Resultado caja: ${resultado_caja:.2f}")
            
            print(f"\n⚖️ DIFERENCIA (Sistema - Caja):")
            print(f"  - Diferencia calculada: ${diferencia_calculada:.2f}")
            print(f"  - Diferencia registrada: ${diferencia_registrada:.2f}")
            
            # Análisis de la diferencia
            if abs(diferencia_calculada) < 0.01:
                print(f"  - ✅ Análisis: Caja cuadrada perfectamente")
            elif diferencia_calculada > 0:
                print(f"  - ⚠️  Análisis: Falta dinero en caja (${diferencia_calculada:.2f})")
            else:
                print(f"  - 💰 Análisis: Sobra dinero en caja (${abs(diferencia_calculada):.2f})")
            
            # Verificar si coincide con lo registrado
            if abs(diferencia_calculada - diferencia_registrada) < 0.01:
                print(f"  - ✅ Registro: La diferencia registrada es correcta")
            else:
                print(f"  - ❌ Registro: Discrepancia de ${abs(diferencia_calculada - diferencia_registrada):.2f}")
        
        else:
            print(f"\n💼 CORTE DE CAJA: No hay datos para esta fecha")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error en análisis detallado: {e}")

def main():
    """Función principal"""
    print("🔍 ANÁLISIS COMPLETO DE LA BASE DE DATOS EN RENDER")
    print("=" * 60)
    
    # Conectar a la base de datos
    conn = connect_to_render_db()
    if not conn:
        return
    
    try:
        # 1. Mostrar fechas con datos existentes
        fecha_para_analizar = get_all_dates_with_data(conn)
        
        # 2. Crear datos de prueba si no hay datos
        if not fecha_para_analizar:
            print("\n⚠️  No hay datos existentes. Creando datos de prueba...")
            fecha_para_analizar = create_test_data(conn)
        
        # 3. Análisis detallado de una fecha
        if fecha_para_analizar:
            analyze_fecha_detallada(conn, fecha_para_analizar)
        
    finally:
        conn.close()
        print("\n🔐 Conexión cerrada")

if __name__ == "__main__":
    main()

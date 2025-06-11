"""
Página del dashboard con estadísticas y reportes
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.models import Venta, Producto
from database.connection import execute_query
from utils.helpers import format_currency, get_date_range_options

def mostrar_dashboard():
    """Página principal del dashboard"""
    st.title("📊 Dashboard de Ventas")
    
    # Selector de período
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        opciones_fecha = get_date_range_options()
        periodo_seleccionado = st.selectbox(
            "Período a analizar:",
            list(opciones_fecha.keys())
        )
        fecha_inicio, fecha_fin = opciones_fecha[periodo_seleccionado]
    
    with col2:
        fecha_inicio_custom = st.date_input("Desde:", value=fecha_inicio)
    
    with col3:
        fecha_fin_custom = st.date_input("Hasta:", value=fecha_fin)
    
    # Usar fechas personalizadas si son diferentes
    if fecha_inicio_custom != fecha_inicio or fecha_fin_custom != fecha_fin:
        fecha_inicio, fecha_fin = fecha_inicio_custom, fecha_fin_custom
    
    # Obtener datos del período
    ventas = Venta.get_by_fecha(str(fecha_inicio), str(fecha_fin))
    
    if not ventas:
        st.warning(f"No hay ventas registradas en el período del {fecha_inicio} al {fecha_fin}")
        return
    
    # Métricas principales
    mostrar_metricas_principales(ventas)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_grafico_ventas_diarias(ventas, fecha_inicio, fecha_fin)
        mostrar_grafico_metodos_pago(ventas)
    
    with col2:
        mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin)
        mostrar_grafico_horarios_venta(ventas)
    
    # Tabla de ventas recientes
    mostrar_ventas_recientes(ventas)
    
    # Botón para generar reporte
    if st.button("📄 Generar Reporte PDF", type="primary"):
        generar_reporte_pdf(fecha_inicio, fecha_fin)

def mostrar_metricas_principales(ventas):
    """Muestra las métricas principales del período"""
    st.subheader("📈 Métricas del Período")
    
    total_ventas = len(ventas)
    ingresos_totales = sum(venta.total for venta in ventas)
    promedio_venta = ingresos_totales / total_ventas if total_ventas > 0 else 0
    
    # Comparar con período anterior
    fecha_inicio = datetime.now().date() - timedelta(days=7)  # Última semana como ejemplo
    fecha_fin = datetime.now().date()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Ventas",
            value=total_ventas,
            delta=None
        )
    
    with col2:
        st.metric(
            label="Ingresos Totales",
            value=format_currency(ingresos_totales),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Promedio por Venta",
            value=format_currency(promedio_venta),
            delta=None
        )
    
    with col4:
        # Calcular productos con stock bajo
        productos_stock_bajo = len([p for p in Producto.get_all() if p.stock <= 5])
        st.metric(
            label="Stock Bajo (≤5)",
            value=productos_stock_bajo,
            delta=None
        )

def mostrar_grafico_ventas_diarias(ventas, fecha_inicio, fecha_fin):
    """Muestra el gráfico de ventas por día"""
    st.subheader("📅 Ventas por Día")
    
    # Agrupar ventas por día
    ventas_por_dia = {}
    current_date = fecha_inicio
    
    # Inicializar todos los días con 0
    while current_date <= fecha_fin:
        ventas_por_dia[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Sumar ventas reales
    for venta in ventas:
        if isinstance(venta.fecha, str):
            fecha_venta = datetime.fromisoformat(venta.fecha).date()
        else:
            fecha_venta = venta.fecha.date()
        
        fecha_key = fecha_venta.strftime('%Y-%m-%d')
        if fecha_key in ventas_por_dia:
            ventas_por_dia[fecha_key] += venta.total
    
    # Crear DataFrame
    df_ventas = pd.DataFrame([
        {'Fecha': fecha, 'Total': total}
        for fecha, total in ventas_por_dia.items()
    ])
    
    if not df_ventas.empty:
        fig = px.line(
            df_ventas, 
            x='Fecha', 
            y='Total',
            title='Evolución de Ventas Diarias',
            markers=True
        )
        fig.update_layout(xaxis_title="Fecha", yaxis_title="Total (MXN)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de ventas diarias para mostrar")

def mostrar_grafico_metodos_pago(ventas):
    """Muestra el gráfico de métodos de pago"""
    st.subheader("💳 Métodos de Pago")
    
    # Agrupar por método de pago
    metodos_pago = {}
    for venta in ventas:
        metodo = venta.metodo_pago
        metodos_pago[metodo] = metodos_pago.get(metodo, 0) + venta.total
    
    if metodos_pago:
        df_metodos = pd.DataFrame([
            {'Método': metodo, 'Total': total}
            for metodo, total in metodos_pago.items()
        ])
        
        fig = px.pie(
            df_metodos,
            values='Total',
            names='Método',
            title='Distribución por Método de Pago'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de métodos de pago para mostrar")

def mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin):
    """Muestra los productos más vendidos"""
    st.subheader("🏆 Productos Más Vendidos")
    
    # Consulta para obtener productos más vendidos
    query = """
        SELECT p.nombre, SUM(dv.cantidad) as cantidad_vendida, SUM(dv.subtotal) as total_vendido
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE DATE(v.fecha) BETWEEN %s AND %s
        GROUP BY p.id, p.nombre
        ORDER BY cantidad_vendida DESC
        LIMIT 10
    """
    
    rows = execute_query(query, (str(fecha_inicio), str(fecha_fin)))
    
    if rows:
        df_productos = pd.DataFrame([
            {
                'Producto': row['nombre'],
                'Cantidad': row['cantidad_vendida'],
                'Total': row['total_vendido']
            }
            for row in rows
        ])
        
        fig = px.bar(
            df_productos,
            x='Cantidad',
            y='Producto',
            orientation='h',
            title='Top 10 Productos por Cantidad'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de productos para mostrar")

def mostrar_grafico_horarios_venta(ventas):
    """Muestra las ventas por horario"""
    st.subheader("🕐 Ventas por Horario")
    
    # Agrupar por hora
    ventas_por_hora = {}
    for i in range(24):
        ventas_por_hora[i] = 0
    
    for venta in ventas:
        if isinstance(venta.fecha, str):
            fecha_venta = datetime.fromisoformat(venta.fecha)
        else:
            fecha_venta = venta.fecha
        
        hora = fecha_venta.hour
        ventas_por_hora[hora] += venta.total
    
    df_horas = pd.DataFrame([
        {'Hora': f"{hora:02d}:00", 'Total': total}
        for hora, total in ventas_por_hora.items()
        if total > 0
    ])
    
    if not df_horas.empty:
        fig = px.bar(
            df_horas,
            x='Hora',
            y='Total',
            title='Ventas por Hora del Día'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de horarios para mostrar")

def mostrar_ventas_recientes(ventas):
    """Muestra la tabla de ventas recientes"""
    st.subheader("📋 Ventas del Período")
    
    # Preparar datos para la tabla
    data = []
    for venta in ventas[-20:]:  # Últimas 20 ventas
        if isinstance(venta.fecha, str):
            fecha_venta = datetime.fromisoformat(venta.fecha)
        else:
            fecha_venta = venta.fecha
        
        data.append({
            "ID": venta.id,
            "Fecha": fecha_venta.strftime('%d/%m/%Y'),
            "Hora": fecha_venta.strftime('%H:%M'),
            "Total": f"{venta.total:.2f} MXN",
            "Método": venta.metodo_pago,
            "Vendedor": venta.vendedor or "-"
        })
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay ventas para mostrar")

def generar_reporte_pdf(fecha_inicio, fecha_fin):
    """Genera y ofrece descarga del reporte en PDF"""
    try:
        from utils.pdf_generator import TicketGenerator
        
        # Obtener ventas del período
        ventas = Venta.get_by_fecha(str(fecha_inicio), str(fecha_fin))
        
        if not ventas:
            st.warning("No hay ventas en el período seleccionado")
            return
        
        # Crear un reporte simple por ahora
        st.success("✅ Funcionalidad de reporte PDF en desarrollo!")
        st.info("Por ahora puedes exportar los datos mostrados en la pantalla.")
        
        # Mostrar resumen exportable
        total_ventas = len(ventas)
        ingresos_totales = sum(venta.total for venta in ventas)
        
        st.markdown(f"""
        **Resumen del período {fecha_inicio} - {fecha_fin}:**
        - Total de ventas: {total_ventas}
        - Ingresos totales: {format_currency(ingresos_totales)}
        - Promedio por venta: {format_currency(ingresos_totales / total_ventas if total_ventas > 0 else 0)}
        """)
            
    except Exception as e:
        st.error(f"❌ Error al generar reporte: {str(e)}")

# Función principal para ejecutar la página
def main():
    mostrar_dashboard()

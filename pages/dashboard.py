"""
Página del dashboard con estadísticas, reportes y gestión de gastos
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.models import Venta, Producto, GastoDiario, CorteCaja, Vendedor
from database.connection import execute_query
from utils.helpers import format_currency, get_date_range_options
from utils.timezone_utils import get_mexico_date_str, get_mexico_datetime

def mostrar_dashboard():
    """Página principal del dashboard"""
    st.title("📊 Dashboard Mi Chas-K")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Análisis de Ventas", 
        "💰 Gestión de Gastos", 
        "📋 Corte de Caja",
        "📊 Resumen Financiero"
    ])
    
    with tab1:
        mostrar_analisis_ventas()
    
    with tab2:
        mostrar_gestion_gastos()
    
    with tab3:
        mostrar_corte_caja()
    
    with tab4:
        mostrar_resumen_financiero()

def mostrar_analisis_ventas():
    """Análisis de ventas con gráficos y métricas"""
    st.subheader("📈 Análisis de Ventas")
    
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
        fecha_inicio_custom = st.date_input("Desde:", value=fecha_inicio, key="dashboard_fecha_inicio")
    
    with col3:
        fecha_fin_custom = st.date_input("Hasta:", value=fecha_fin, key="dashboard_fecha_fin")
    
    # Usar fechas personalizadas si son diferentes
    if fecha_inicio_custom != fecha_inicio or fecha_fin_custom != fecha_fin:
        fecha_inicio, fecha_fin = fecha_inicio_custom, fecha_fin_custom
    
    # Obtener datos del período
    ventas = Venta.get_by_fecha(str(fecha_inicio), str(fecha_fin))
    
    if not ventas:
        st.warning(f"No hay ventas registradas en el período del {fecha_inicio} al {fecha_fin}")
        return
    
    # Métricas principales
    mostrar_metricas_ventas(ventas)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_grafico_ventas_diarias(ventas)
        mostrar_grafico_metodos_pago(ventas)
    
    with col2:
        mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin)
        mostrar_grafico_vendedores(ventas)

def mostrar_gestion_gastos():
    """Gestión de gastos diarios"""
    st.subheader("💰 Gestión de Gastos")
    
    # Selector de fecha
    fecha_seleccionada = st.date_input(
        "Fecha:",
        value=datetime.now().date(),
        key="fecha_gastos"
    )
    fecha_str = str(fecha_seleccionada)
    
    # Pestañas para gastos
    tab1, tab2 = st.tabs(["➕ Agregar Gasto", "📋 Ver Gastos"])
    
    with tab1:
        agregar_gasto(fecha_str)
    
    with tab2:
        ver_gastos(fecha_str)

def agregar_gasto(fecha: str):
    """Formulario para agregar gastos"""
    st.write("### ➕ Registrar Nuevo Gasto")
    
    with st.form("agregar_gasto"):
        col1, col2 = st.columns(2)
        
        with col1:
            concepto = st.text_input("Concepto del gasto*:", placeholder="Ej: Compra de ingredientes")
            monto = st.number_input("Monto*:", min_value=0.01, step=0.01)
            
            categorias_gasto = ["Operación", "Compras", "Servicios", "Mantenimiento", "Otros"]
            categoria = st.selectbox("Categoría*:", categorias_gasto)
        
        with col2:
            vendedores = Vendedor.get_nombres_activos()
            vendedor = st.selectbox("Quien realizó el gasto:", vendedores if vendedores else ["Sin especificar"])
            
            comprobante = st.text_input("Número de comprobante:", placeholder="Factura/Ticket #")
            descripcion = st.text_area("Descripción adicional:")
        
        submitted = st.form_submit_button("💾 Registrar Gasto", type="primary")
        
        if submitted:
            if concepto and monto > 0:
                try:
                    gasto = GastoDiario(
                        fecha=fecha,
                        concepto=concepto,
                        monto=monto,
                        categoria=categoria,
                        descripcion=descripcion,
                        comprobante=comprobante,
                        vendedor=vendedor
                    )
                    gasto.save()
                    st.success("✅ Gasto registrado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar gasto: {str(e)}")
            else:
                st.error("Por favor completa los campos obligatorios (concepto y monto)")

def ver_gastos(fecha: str):
    """Mostrar gastos del día"""
    st.write(f"### 📋 Gastos del {fecha}")
    
    gastos = GastoDiario.get_by_fecha(fecha)
    
    if not gastos:
        st.info("No hay gastos registrados para esta fecha")
        return
    
    # Resumen por categorías
    df_gastos = pd.DataFrame([{
        'ID': g.id,
        'Concepto': g.concepto,
        'Monto': g.monto,
        'Categoría': g.categoria,
        'Vendedor': g.vendedor,
        'Comprobante': g.comprobante or '',
        'Descripción': g.descripcion[:50] + '...' if g.descripcion and len(g.descripcion) > 50 else g.descripcion or ''
    } for g in gastos])
    
    # Métricas de gastos
    total_gastos = sum(g.monto for g in gastos)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    with col2:
        gastos_por_categoria = df_gastos.groupby('Categoría')['Monto'].sum()
        categoria_mayor = gastos_por_categoria.idxmax() if not gastos_por_categoria.empty else "N/A"
        st.metric("Categoría Principal", categoria_mayor)
    
    with col3:
        promedio_gasto = total_gastos / len(gastos) if gastos else 0
        st.metric("Promedio por Gasto", f"${promedio_gasto:,.2f}")
    
    # Gráfico de gastos por categoría
    if not df_gastos.empty:
        fig_gastos = px.pie(
            df_gastos, 
            values='Monto', 
            names='Categoría',
            title="Distribución de Gastos por Categoría"
        )
        st.plotly_chart(fig_gastos, use_container_width=True)
    
    # Tabla de gastos
    st.dataframe(df_gastos, use_container_width=True)

def mostrar_corte_caja():
    """Realizar corte de caja diario"""
    st.subheader("📋 Corte de Caja")
    
    # Selector de fecha
    fecha_seleccionada = st.date_input(
        "Fecha del corte:",
        value=datetime.now().date(),
        key="fecha_corte"
    )
    fecha_str = str(fecha_seleccionada)
    
    # Verificar si ya existe corte para esta fecha
    corte_existente = CorteCaja.get_by_fecha(fecha_str)
    
    if corte_existente:
        st.warning(f"Ya existe un corte de caja para el {fecha_str}")
        mostrar_corte_existente(corte_existente)
        return
    
    # Obtener datos automáticos del día
    ventas_dia = Venta.get_by_fecha(fecha_str, fecha_str)
    gastos_dia = GastoDiario.get_by_fecha(fecha_str)
    
    # Calcular totales automáticos
    ventas_efectivo = sum(v.total for v in ventas_dia if v.metodo_pago == "Efectivo")
    ventas_tarjeta = sum(v.total for v in ventas_dia if v.metodo_pago in ["Tarjeta", "Transferencia"])
    total_gastos = sum(g.monto for g in gastos_dia)
    
    # Formulario de corte
    with st.form("corte_caja"):
        st.write("### 💰 Información del Corte")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Datos Automáticos:**")
            st.metric("Ventas en Efectivo", f"${ventas_efectivo:,.2f}")
            st.metric("Ventas con Tarjeta", f"${ventas_tarjeta:,.2f}")
            st.metric("Total Gastos", f"${total_gastos:,.2f}")
        
        with col2:
            st.write("**Datos a Capturar:**")
            dinero_inicial = st.number_input(
                "Dinero inicial en caja:", 
                min_value=0.0, 
                step=0.01,
                help="¿Con cuánto dinero inició el día?"
            )
            
            dinero_final = st.number_input(
                "Dinero final en caja:", 
                min_value=0.0, 
                step=0.01,
                help="¿Cuánto dinero hay físicamente en la caja?"
            )
            
            vendedores = Vendedor.get_nombres_activos()
            vendedor = st.selectbox("Quien realiza el corte:", vendedores if vendedores else ["Sin especificar"])
        
        observaciones = st.text_area("Observaciones:", placeholder="Notas adicionales sobre el corte...")
        
        # Cálculo previo
        dinero_esperado = dinero_inicial + ventas_efectivo - total_gastos
        diferencia = dinero_final - dinero_esperado
        
        if dinero_inicial > 0 and dinero_final > 0:
            st.write("### 📊 Cálculo Preliminar")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Dinero Esperado", f"${dinero_esperado:,.2f}")
            
            with col2:
                st.metric("Dinero Real", f"${dinero_final:,.2f}")
            
            with col3:
                color = "normal" if abs(diferencia) < 1 else "inverse"
                st.metric("Diferencia", f"${diferencia:,.2f}", delta=diferencia if diferencia != 0 else None)
        
        submitted = st.form_submit_button("💾 Guardar Corte de Caja", type="primary")
        
        if submitted:
            if dinero_inicial >= 0 and dinero_final >= 0:
                try:
                    corte = CorteCaja(
                        fecha=fecha_str,
                        dinero_inicial=dinero_inicial,
                        dinero_final=dinero_final,
                        ventas_efectivo=ventas_efectivo,
                        ventas_tarjeta=ventas_tarjeta,
                        total_gastos=total_gastos,
                        observaciones=observaciones,
                        vendedor=vendedor
                    )
                    corte.save()
                    st.success("✅ Corte de caja guardado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar corte: {str(e)}")
            else:
                st.error("Por favor completa todos los campos requeridos")

def mostrar_corte_existente(corte: CorteCaja):
    """Muestra un corte de caja existente"""
    st.write("### 📋 Corte Existente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Dinero Inicial", f"${corte.dinero_inicial:,.2f}")
        st.metric("Ventas Efectivo", f"${corte.ventas_efectivo:,.2f}")
        st.metric("Total Gastos", f"${corte.total_gastos:,.2f}")
    
    with col2:
        st.metric("Dinero Final", f"${corte.dinero_final:,.2f}")
        st.metric("Ventas Tarjeta", f"${corte.ventas_tarjeta:,.2f}")
        color = "normal" if abs(corte.diferencia) < 1 else "inverse"
        st.metric("Diferencia", f"${corte.diferencia:,.2f}")
    
    if corte.observaciones:
        st.write(f"**Observaciones:** {corte.observaciones}")
    
    st.write(f"**Realizado por:** {corte.vendedor}")

def mostrar_resumen_financiero():
    """Resumen financiero con inversiones y ganancias"""
    st.subheader("📊 Resumen Financiero")
    
    # Selector de período
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde:", value=datetime.now().date() - timedelta(days=30), key="resumen_fecha_inicio")
    
    with col2:
        fecha_fin = st.date_input("Hasta:", value=datetime.now().date(), key="resumen_fecha_fin")
    
    # Obtener datos del período
    fecha_inicio_str = str(fecha_inicio)
    fecha_fin_str = str(fecha_fin)
    
    ventas = Venta.get_by_fecha(fecha_inicio_str, fecha_fin_str)
    total_ventas = sum(v.total for v in ventas)
    
    # Gastos por categoría
    query_gastos = """
        SELECT categoria, SUM(monto) as total
        FROM gastos_diarios 
        WHERE fecha BETWEEN %s AND %s 
        GROUP BY categoria
    """
    gastos_categoria = execute_query(query_gastos, (fecha_inicio_str, fecha_fin_str))
    total_gastos = sum(float(g['total']) for g in gastos_categoria)
    
    # Métricas principales
    ganancia_bruta = total_ventas - total_gastos
    margen = (ganancia_bruta / total_ventas * 100) if total_ventas > 0 else 0
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ventas", f"${total_ventas:,.2f}")
    
    with col2:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    with col3:
        st.metric("Ganancia Bruta", f"${ganancia_bruta:,.2f}", delta=ganancia_bruta)
    
    with col4:
        st.metric("Margen (%)", f"{margen:.1f}%")
    
    # Gráficos comparativos
    if gastos_categoria:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de gastos por categoría
            df_gastos_cat = pd.DataFrame(gastos_categoria)
            fig_gastos = px.pie(
                df_gastos_cat,
                values='total',
                names='categoria',
                title="Distribución de Gastos por Categoría"
            )
            st.plotly_chart(fig_gastos, use_container_width=True)
        
        with col2:
            # Gráfico de ingresos vs gastos
            datos_comparativo = pd.DataFrame({
                'Concepto': ['Ingresos', 'Gastos', 'Ganancia'],
                'Monto': [total_ventas, total_gastos, ganancia_bruta],
                'Color': ['green', 'red', 'blue']
            })
            
            fig_comp = px.bar(
                datos_comparativo,
                x='Concepto',
                y='Monto',
                color='Color',
                title="Comparativo Financiero"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

# Funciones auxiliares para gráficos (existentes)
def mostrar_metricas_ventas(ventas):
    """Muestra las métricas principales de ventas"""
    total_ventas = len(ventas)
    total_ingresos = sum(venta.total for venta in ventas)
    promedio_venta = total_ingresos / total_ventas if total_ventas > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ventas", total_ventas)
    
    with col2:
        st.metric("Ingresos Totales", format_currency(total_ingresos))
    
    with col3:
        st.metric("Promedio por Venta", format_currency(promedio_venta))
    
    with col4:
        # Ventas de hoy
        ventas_hoy = len([v for v in ventas if v.fecha.date() == datetime.now().date()])
        st.metric("Ventas Hoy", ventas_hoy)

def mostrar_grafico_ventas_diarias(ventas):
    """Gráfico de ventas por día"""
    if not ventas:
        return
    
    # Agrupar ventas por día
    ventas_por_dia = {}
    for venta in ventas:
        fecha = venta.fecha.date()
        if fecha not in ventas_por_dia:
            ventas_por_dia[fecha] = {'count': 0, 'total': 0}
        ventas_por_dia[fecha]['count'] += 1
        ventas_por_dia[fecha]['total'] += venta.total
    
    # Crear DataFrame
    df = pd.DataFrame([
        {'Fecha': fecha, 'Ventas': data['count'], 'Ingresos': data['total']}
        for fecha, data in ventas_por_dia.items()
    ])
    
    if not df.empty:
        fig = px.line(df, x='Fecha', y='Ingresos', title='Ingresos por Día')
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_metodos_pago(ventas):
    """Gráfico de métodos de pago"""
    if not ventas:
        return
        
    metodos = {}
    for venta in ventas:
        metodo = venta.metodo_pago
        if metodo not in metodos:
            metodos[metodo] = 0
        metodos[metodo] += venta.total
    
    if metodos:
        fig = px.pie(
            values=list(metodos.values()),
            names=list(metodos.keys()),
            title='Distribución por Método de Pago'
        )
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin):
    """Gráfico de productos más vendidos"""
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
    
    resultados = execute_query(query, (str(fecha_inicio), str(fecha_fin)))
    
    if resultados:
        df = pd.DataFrame(resultados)
        fig = px.bar(
            df, 
            x='nombre', 
            y='cantidad_vendida',
            title='Top 10 Productos Más Vendidos'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_vendedores(ventas):
    """Gráfico de ventas por vendedor"""
    if not ventas:
        return
        
    vendedores = {}
    for venta in ventas:
        vendedor = venta.vendedor or "Sin especificar"
        if vendedor not in vendedores:
            vendedores[vendedor] = {'count': 0, 'total': 0}
        vendedores[vendedor]['count'] += 1
        vendedores[vendedor]['total'] += venta.total
    
    if vendedores:
        df = pd.DataFrame([
            {'Vendedor': vendedor, 'Ventas': data['count'], 'Total': data['total']}
            for vendedor, data in vendedores.items()
        ])
        
        fig = px.bar(
            df,
            x='Vendedor',
            y='Total',
            title='Ventas por Vendedor'
        )
        st.plotly_chart(fig, use_container_width=True)

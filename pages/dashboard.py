"""
Dashboard - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import pandas as pd
from database.connection_optimized import get_db_adapter

def show_dashboard():
    """Mostrar dashboard optimizado para tablets"""
    
    # CSS adicional para dashboard
    st.markdown("""
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .metric-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        .chart-container {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        # Controles de fecha optimizados para tablets
        st.subheader("📊 Dashboard de Ventas")
        
        col_fecha1, col_fecha2, col_btn = st.columns([1, 1, 1])
        
        with col_fecha1:
            fecha_desde = st.date_input(
                "📅 Desde:",
                value=date.today() - timedelta(days=30),
                key="fecha_desde_dashboard"
            )
        
        with col_fecha2:
            fecha_hasta = st.date_input(
                "📅 Hasta:",
                value=date.today(),
                key="fecha_hasta_dashboard"
            )
        
        with col_btn:
            if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
                st.rerun()
        
        # Obtener datos
        dashboard_data = adapter.get_dashboard_data(
            fecha_desde.strftime('%Y-%m-%d'),
            fecha_hasta.strftime('%Y-%m-%d')
        )
        
        # Métricas principales - optimizadas para tablets
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ventas = dashboard_data['resumen']['total_ventas']
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🛒 Total Ventas</div>
                <div class="metric-value">{total_ventas}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_ingresos = dashboard_data['resumen']['total_ingresos']
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💰 Ingresos</div>
                <div class="metric-value">${total_ingresos:.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            promedio_venta = total_ingresos / max(total_ventas, 1)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📈 Promedio</div>
                <div class="metric-value">${promedio_venta:.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            productos_vendidos = sum(item['cantidad_vendida'] for item in dashboard_data['productos_top'])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📦 Productos</div>
                <div class="metric-value">{productos_vendidos}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráficos en dos columnas para tablets
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("📈 Ventas por Día")
            
            if dashboard_data['ventas_por_dia']:
                df_ventas = pd.DataFrame(dashboard_data['ventas_por_dia'])
                df_ventas['dia'] = pd.to_datetime(df_ventas['dia'])
                
                fig_ventas = px.line(
                    df_ventas,
                    x='dia',
                    y='ingresos',
                    title='Ingresos Diarios',
                    labels={'dia': 'Fecha', 'ingresos': 'Ingresos ($)'},
                    color_discrete_sequence=['#667eea']
                )
                
                fig_ventas.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    font=dict(size=12)
                )
                
                st.plotly_chart(fig_ventas, use_container_width=True)
            else:
                st.info("📊 No hay datos de ventas para mostrar")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_der:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("🏆 Productos Más Vendidos")
            
            if dashboard_data['productos_top']:
                df_productos = pd.DataFrame(dashboard_data['productos_top'][:8])  # Top 8 para tablets
                
                fig_productos = px.bar(
                    df_productos,
                    x='cantidad_vendida',
                    y='nombre',
                    orientation='h',
                    title='Top Productos',
                    labels={'cantidad_vendida': 'Cantidad', 'nombre': 'Producto'},
                    color='cantidad_vendida',
                    color_continuous_scale='Blues'
                )
                
                fig_productos.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    font=dict(size=10),
                    yaxis={'categoryorder': 'total ascending'}
                )
                
                st.plotly_chart(fig_productos, use_container_width=True)
            else:
                st.info("📊 No hay datos de productos para mostrar")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección de estadísticas detalladas
        st.markdown("---")
        st.subheader("📋 Estadísticas Detalladas")
        
        # Tabs optimizadas para tablets
        tab1, tab2, tab3 = st.tabs(["📊 Resumen", "🕐 Por Horas", "📦 Inventario"])
        
        with tab1:
            col_est1, col_est2 = st.columns(2)
            
            with col_est1:
                st.markdown("**📈 Métricas de Periodo:**")
                dias_periodo = (fecha_hasta - fecha_desde).days + 1
                ventas_por_dia = total_ventas / max(dias_periodo, 1)
                ingresos_por_dia = total_ingresos / max(dias_periodo, 1)
                
                st.metric("📅 Días en período", dias_periodo)
                st.metric("🛒 Ventas/día promedio", f"{ventas_por_dia:.1f}")
                st.metric("💰 Ingresos/día promedio", f"${ingresos_por_dia:.2f}")
            
            with col_est2:
                st.markdown("**🎯 Análisis de Productos:**")
                productos_activos = len(adapter.get_productos())
                categorias_activas = len(adapter.get_categorias())
                
                st.metric("📦 Productos activos", productos_activos)
                st.metric("🏷️ Categorías activas", categorias_activas)
                
                if dashboard_data['productos_top']:
                    producto_estrella = dashboard_data['productos_top'][0]
                    st.metric("⭐ Producto estrella", producto_estrella['nombre'])
        
        with tab2:
            st.markdown("**🕐 Análisis por Horarios**")
            
            # Obtener ventas con horas
            try:
                ventas_horas = adapter.execute_query("""
                    SELECT 
                        EXTRACT(HOUR FROM fecha) as hora,
                        COUNT(*) as ventas,
                        SUM(total) as ingresos
                    FROM ventas 
                    WHERE fecha BETWEEN %s AND %s
                    GROUP BY EXTRACT(HOUR FROM fecha)
                    ORDER BY hora
                """, (fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d')))
                
                if ventas_horas:
                    df_horas = pd.DataFrame(ventas_horas)
                    
                    fig_horas = px.bar(
                        df_horas,
                        x='hora',
                        y='ventas',
                        title='Ventas por Hora del Día',
                        labels={'hora': 'Hora', 'ventas': 'Número de Ventas'},
                        color='ventas',
                        color_continuous_scale='Viridis'
                    )
                    
                    fig_horas.update_layout(height=400)
                    st.plotly_chart(fig_horas, use_container_width=True)
                else:
                    st.info("📊 No hay datos de ventas por horas")
                    
            except Exception as e:
                st.error(f"Error obteniendo datos por horas: {e}")
        
        with tab3:
            st.markdown("**📦 Estado del Inventario**")
            
            productos = adapter.get_productos(activo_only=False)
            if productos:
                df_productos = pd.DataFrame(productos)
                
                # Productos con stock bajo
                stock_bajo = df_productos[df_productos['stock'] <= 5]
                if not stock_bajo.empty:
                    st.warning(f"⚠️ {len(stock_bajo)} productos con stock bajo:")
                    for _, producto in stock_bajo.iterrows():
                        st.write(f"- {producto['nombre']}: {producto['stock']} unidades")
                
                # Productos sin stock
                sin_stock = df_productos[df_productos['stock'] == 0]
                if not sin_stock.empty:
                    st.error(f"🔴 {len(sin_stock)} productos sin stock:")
                    for _, producto in sin_stock.iterrows():
                        st.write(f"- {producto['nombre']}")
                
                # Resumen de inventario
                col_inv1, col_inv2, col_inv3 = st.columns(3)
                
                with col_inv1:
                    total_productos = len(df_productos)
                    st.metric("📦 Total productos", total_productos)
                
                with col_inv2:
                    productos_activos = len(df_productos[df_productos['activo'] == True])
                    st.metric("✅ Productos activos", productos_activos)
                
                with col_inv3:
                    valor_inventario = (df_productos['precio'] * df_productos['stock']).sum()
                    st.metric("💰 Valor inventario", f"${valor_inventario:.2f}")
            else:
                st.info("📦 No hay productos en el inventario")
        
    except Exception as e:
        st.error(f"❌ Error en dashboard: {e}")
        st.error("Verifique la conexión a la base de datos")

if __name__ == "__main__":
    show_dashboard()

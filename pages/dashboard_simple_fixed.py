"""
Dashboard Simplificado - Versión Funcional
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def show_dashboard(adapter):
    """Dashboard simplificado"""
    
    st.title("📊 Dashboard de Ventas")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Estadísticas básicas
        with col1:
            productos_count = adapter.execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = 1")
            st.metric("📦 Productos", productos_count[0]['count'] if productos_count else 0)
        
        with col2:
            ventas_count = adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
            st.metric("💰 Ventas Total", ventas_count[0]['count'] if ventas_count else 0)
        
        with col3:
            ventas_hoy = adapter.execute_query("""
                SELECT COUNT(*) as count FROM ventas 
                WHERE DATE(fecha) = DATE('now')
            """)
            st.metric("🛒 Ventas Hoy", ventas_hoy[0]['count'] if ventas_hoy else 0)
        
        with col4:
            total_vendido = adapter.execute_query("""
                SELECT COALESCE(SUM(total), 0) as total FROM ventas
            """)
            st.metric("💵 Total Vendido", f"${total_vendido[0]['total']:,.2f}" if total_vendido else "$0.00")
        
    except Exception as e:
        st.error(f"Error cargando métricas: {e}")
    
    # Gráficos simples
    st.subheader("📈 Ventas Recientes")
    
    try:
        ventas_recientes = adapter.execute_query("""
            SELECT DATE(fecha) as fecha, SUM(total) as total
            FROM ventas 
            WHERE fecha >= datetime('now', '-7 days')
            GROUP BY DATE(fecha)
            ORDER BY fecha DESC
        """)
        
        if ventas_recientes:
            df = pd.DataFrame(ventas_recientes)
            st.bar_chart(df.set_index('fecha'))
        else:
            st.info("No hay ventas recientes para mostrar")
    
    except Exception as e:
        st.error(f"Error cargando gráfico: {e}")
    
    # Tabla de ventas recientes
    st.subheader("📄 Ventas Recientes")
    
    try:
        ventas_tabla = adapter.execute_query("""
            SELECT fecha, total, vendedor, metodo_pago
            FROM ventas 
            ORDER BY fecha DESC 
            LIMIT 20
        """)
        
        if ventas_tabla:
            df = pd.DataFrame(ventas_tabla)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay ventas registradas")
    
    except Exception as e:
        st.error(f"Error cargando tabla: {e}")
    
    # Productos más vendidos
    st.subheader("🏆 Productos Más Vendidos")
    
    try:
        productos_top = adapter.execute_query("""
            SELECT p.nombre, SUM(dv.cantidad) as total_vendido
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            GROUP BY p.id, p.nombre
            ORDER BY total_vendido DESC
            LIMIT 10
        """)
        
        if productos_top:
            df = pd.DataFrame(productos_top)
            st.bar_chart(df.set_index('nombre'))
        else:
            st.info("No hay datos de productos vendidos")
    
    except Exception as e:
        st.error(f"Error cargando productos top: {e}")

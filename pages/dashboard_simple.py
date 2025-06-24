"""
Dashboard Simplificado
Versión 3.1.0 - Con Adaptador Compatible
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.connection_adapter import execute_query

def mostrar_dashboard_simple():
    """Dashboard simplificado de ventas"""
    
    st.title("📊 Dashboard de Ventas")
    
    # Botón volver
    if st.button("← Volver al inicio"):
        st.session_state.page = 'main'
        st.rerun()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Ventas de hoy
        ventas_hoy = execute_query("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        
        # Ventas del mes
        ventas_mes = execute_query("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM ventas 
            WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND EXTRACT(MONTH FROM fecha) = EXTRACT(MONTH FROM CURRENT_DATE)
        """)
        
        # Productos más vendidos
        productos_top = execute_query("""
            SELECT p.nombre, SUM(dv.cantidad) as vendidos
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v ON dv.venta_id = v.id
            WHERE DATE(v.fecha) = CURRENT_DATE
            GROUP BY p.id, p.nombre
            ORDER BY vendidos DESC
            LIMIT 5
        """)
        
        with col1:
            st.metric(
                "Ventas Hoy", 
                ventas_hoy[0]['total'] if ventas_hoy else 0
            )
        
        with col2:
            monto_hoy = ventas_hoy[0]['monto'] if ventas_hoy else 0
            st.metric(
                "Ingresos Hoy", 
                f"${monto_hoy:,.2f}"
            )
        
        with col3:
            st.metric(
                "Ventas del Mes", 
                ventas_mes[0]['total'] if ventas_mes else 0
            )
        
        with col4:
            monto_mes = ventas_mes[0]['monto'] if ventas_mes else 0
            st.metric(
                "Ingresos del Mes", 
                f"${monto_mes:,.2f}"
            )
    
    except Exception as e:
        st.error(f"Error cargando métricas: {e}")
    
    st.markdown("---")
    
    # Dos columnas para reportes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Productos Más Vendidos (Hoy)")
        
        if productos_top:
            for producto in productos_top:
                st.write(f"• **{producto['nombre']}**: {producto['vendidos']} unidades")
        else:
            st.info("No hay ventas registradas hoy")
    
    with col2:
        st.subheader("📈 Ventas Recientes")
        
        try:
            ventas_recientes = execute_query("""
                SELECT fecha, total, vendedor, metodo_pago
                FROM ventas 
                ORDER BY fecha DESC 
                LIMIT 10
            """)
            
            if ventas_recientes:
                for venta in ventas_recientes:
                    fecha = venta['fecha']
                    if isinstance(fecha, str):
                        try:
                            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                            fecha_str = fecha.strftime('%d/%m %H:%M')
                        except:
                            fecha_str = str(fecha)[:16]
                    else:
                        fecha_str = str(fecha)[:16]
                    
                    st.write(f"• {fecha_str} - ${venta['total']:,.2f} - {venta['vendedor']} ({venta['metodo_pago']})")
            else:
                st.info("No hay ventas registradas")
        
        except Exception as e:
            st.error(f"Error cargando ventas recientes: {e}")
    
    st.markdown("---")
    
    # Resumen por método de pago
    st.subheader("💳 Ventas por Método de Pago (Hoy)")
    
    try:
        metodos_pago = execute_query("""
            SELECT metodo_pago, COUNT(*) as cantidad, SUM(total) as monto
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE
            GROUP BY metodo_pago
            ORDER BY monto DESC
        """)
        
        if metodos_pago:
            col1, col2, col3 = st.columns(3)
            
            for i, metodo in enumerate(metodos_pago):
                with [col1, col2, col3][i % 3]:
                    st.metric(
                        metodo['metodo_pago'],
                        f"${metodo['monto']:,.2f}",
                        f"{metodo['cantidad']} ventas"
                    )
        else:
            st.info("No hay ventas por método de pago hoy")
    
    except Exception as e:
        st.error(f"Error cargando métodos de pago: {e}")
    
    # Opciones adicionales
    st.markdown("---")
    st.subheader("🔧 Opciones")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Ver Todas las Ventas"):
            mostrar_todas_ventas()
    
    with col2:
        if st.button("🔄 Actualizar Datos"):
            st.rerun()
    
    with col3:
        if st.button("📊 Exportar Reporte"):
            exportar_reporte()

def mostrar_todas_ventas():
    """Mostrar tabla de todas las ventas"""
    st.subheader("📄 Historial de Ventas")
    
    try:
        ventas = execute_query("""
            SELECT fecha, total, vendedor, metodo_pago, observaciones
            FROM ventas 
            ORDER BY fecha DESC 
            LIMIT 50
        """)
        
        if ventas:
            df = pd.DataFrame(ventas)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay ventas registradas")
    
    except Exception as e:
        st.error(f"Error cargando ventas: {e}")

def exportar_reporte():
    """Exportar reporte simple"""
    try:
        ventas = execute_query("""
            SELECT fecha, total, vendedor, metodo_pago
            FROM ventas 
            ORDER BY fecha DESC
        """)
        
        if ventas:
            df = pd.DataFrame(ventas)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"reporte_ventas_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos para exportar")
    
    except Exception as e:
        st.error(f"Error exportando: {e}")

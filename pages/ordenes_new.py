"""
Órdenes - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from database.connection_optimized import get_db_adapter

def show_ordenes():
    """Mostrar gestión de órdenes optimizada para tablets"""
    
    # CSS adicional para órdenes
    st.markdown("""
    <style>
        .orden-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 0.5rem;
        }
        .orden-completada { border-left: 4px solid #28a745; }
        .orden-pendiente { border-left: 4px solid #ffc107; }
        .orden-cancelada { border-left: 4px solid #dc3545; }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        st.subheader("📋 Gestión de Órdenes")
        
        # Pestañas principales
        tab1, tab2, tab3 = st.tabs(["📋 Lista de Ventas", "📊 Análisis", "🔍 Buscar"])
        
        with tab1:
            mostrar_lista_ventas(adapter)
        
        with tab2:
            mostrar_analisis_ventas(adapter)
        
        with tab3:
            mostrar_buscar_ventas(adapter)
    
    except Exception as e:
        st.error(f"❌ Error en órdenes: {e}")

def mostrar_lista_ventas(adapter):
    """Mostrar lista de ventas recientes"""
    
    # Filtros de fecha
    col_fecha1, col_fecha2, col_filtro = st.columns(3)
    
    with col_fecha1:
        fecha_desde = st.date_input(
            "📅 Desde:",
            value=date.today() - timedelta(days=7),
            key="ordenes_fecha_desde"
        )
    
    with col_fecha2:
        fecha_hasta = st.date_input(
            "📅 Hasta:",
            value=date.today(),
            key="ordenes_fecha_hasta"
        )
    
    with col_filtro:
        metodo_filtro = st.selectbox(
            "💳 Método:",
            ["Todos", "Efectivo", "Tarjeta", "Transferencia"],
            key="ordenes_metodo_filtro"
        )
    
    # Obtener ventas
    try:
        query = """
            SELECT v.*, COUNT(dv.id) as items_count
            FROM ventas v
            LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
            WHERE v.fecha BETWEEN %s AND %s
        """
        params = [fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d 23:59:59')]
        
        if metodo_filtro != "Todos":
            query += " AND v.metodo_pago = %s"
            params.append(metodo_filtro)
        
        query += " GROUP BY v.id ORDER BY v.fecha DESC LIMIT 50"
        
        ventas = adapter.execute_query(query, params)
        
        if ventas:
            st.markdown(f"**📋 {len(ventas)} ventas encontradas**")
            
            # Mostrar ventas
            for venta in ventas:
                mostrar_venta_card(adapter, venta)
        else:
            st.info("📭 No se encontraron ventas en el período seleccionado")
    
    except Exception as e:
        st.error(f"❌ Error obteniendo ventas: {e}")

def mostrar_venta_card(adapter, venta):
    """Mostrar tarjeta de venta"""
    
    # Determinar clase CSS según estado
    estado = venta.get('estado', 'Completada')
    if estado == 'Completada':
        css_class = "orden-completada"
        estado_icon = "✅"
    elif estado == 'Pendiente':
        css_class = "orden-pendiente"
        estado_icon = "🟡"
    else:
        css_class = "orden-cancelada"
        estado_icon = "❌"
    
    with st.container():
        st.markdown(f'<div class="orden-card {css_class}">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            fecha_formateada = venta['fecha'].strftime('%Y-%m-%d %H:%M:%S') if venta['fecha'] else 'N/A'
            st.markdown(f"**🛒 Venta #{venta['id']}**")
            st.markdown(f"📅 {fecha_formateada}")
            st.markdown(f"👤 {venta.get('vendedor', 'N/A')}")
        
        with col2:
            st.markdown(f"**💰 ${venta['total']:.2f}**")
            st.markdown(f"💳 {venta.get('metodo_pago', 'N/A')}")
        
        with col3:
            st.markdown(f"**{estado_icon} {estado}**")
            st.markdown(f"📦 {venta.get('items_count', 0)} items")
        
        with col4:
            if st.button("👁️ Ver", key=f"ver_venta_{venta['id']}", use_container_width=True):
                mostrar_detalle_venta(adapter, venta['id'])
        
        # Mostrar observaciones si las hay
        if venta.get('observaciones'):
            st.markdown(f"📝 *{venta['observaciones']}*")
        
        st.markdown('</div>', unsafe_allow_html=True)

def mostrar_detalle_venta(adapter, venta_id):
    """Mostrar detalles de una venta específica"""
    
    try:
        # Obtener detalles de la venta
        venta_query = "SELECT * FROM ventas WHERE id = %s"
        venta = adapter.execute_query(venta_query, (venta_id,))
        
        if not venta:
            st.error("❌ Venta no encontrada")
            return
        
        venta = venta[0]
        
        # Obtener items de la venta
        items_query = """
            SELECT dv.*, p.nombre, p.categoria
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
            ORDER BY dv.id
        """
        items = adapter.execute_query(items_query, (venta_id,))
        
        # Mostrar en modal/expander
        with st.expander(f"📄 Detalle de Venta #{venta_id}", expanded=True):
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown("**📋 Información General:**")
                fecha_formateada = venta['fecha'].strftime('%Y-%m-%d %H:%M:%S') if venta['fecha'] else 'N/A'
                st.write(f"📅 **Fecha:** {fecha_formateada}")
                st.write(f"👤 **Vendedor:** {venta.get('vendedor', 'N/A')}")
                st.write(f"💳 **Método de pago:** {venta.get('metodo_pago', 'N/A')}")
                st.write(f"📊 **Estado:** {venta.get('estado', 'Completada')}")
            
            with col_info2:
                st.markdown("**💰 Totales:**")
                st.write(f"💰 **Subtotal:** ${venta['total'] - venta.get('impuestos', 0) + venta.get('descuento', 0):.2f}")
                if venta.get('descuento', 0) > 0:
                    st.write(f"🎯 **Descuento:** -${venta['descuento']:.2f}")
                if venta.get('impuestos', 0) > 0:
                    st.write(f"📊 **Impuestos:** ${venta['impuestos']:.2f}")
                st.write(f"💰 **TOTAL:** ${venta['total']:.2f}")
            
            # Mostrar items
            if items:
                st.markdown("**📦 Productos:**")
                
                # Crear tabla de items
                items_data = []
                for item in items:
                    items_data.append({
                        'Producto': item['nombre'],
                        'Categoría': item.get('categoria', 'N/A'),
                        'Cantidad': item['cantidad'],
                        'Precio Unit.': f"${item['precio_unitario']:.2f}",
                        'Subtotal': f"${item['subtotal']:.2f}"
                    })
                
                df_items = pd.DataFrame(items_data)
                st.dataframe(df_items, use_container_width=True, hide_index=True)
            
            # Observaciones
            if venta.get('observaciones'):
                st.markdown("**📝 Observaciones:**")
                st.write(venta['observaciones'])
    
    except Exception as e:
        st.error(f"❌ Error obteniendo detalles: {e}")

def mostrar_analisis_ventas(adapter):
    """Mostrar análisis de ventas"""
    
    st.markdown("**📊 Análisis de Ventas**")
    
    # Período de análisis
    col_periodo1, col_periodo2 = st.columns(2)
    
    with col_periodo1:
        fecha_desde_analisis = st.date_input(
            "📅 Desde:",
            value=date.today() - timedelta(days=30),
            key="analisis_fecha_desde"
        )
    
    with col_periodo2:
        fecha_hasta_analisis = st.date_input(
            "📅 Hasta:",
            value=date.today(),
            key="analisis_fecha_hasta"
        )
    
    try:
        # Obtener datos para análisis
        analisis_query = """
            SELECT 
                DATE(fecha) as dia,
                metodo_pago,
                COUNT(*) as num_ventas,
                SUM(total) as total_ventas,
                AVG(total) as promedio_venta
            FROM ventas 
            WHERE fecha BETWEEN %s AND %s
            GROUP BY DATE(fecha), metodo_pago
            ORDER BY dia DESC
        """
        
        datos_analisis = adapter.execute_query(
            analisis_query,
            (fecha_desde_analisis.strftime('%Y-%m-%d'), fecha_hasta_analisis.strftime('%Y-%m-%d 23:59:59'))
        )
        
        if datos_analisis:
            df_analisis = pd.DataFrame(datos_analisis)
            
            # Métricas generales
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            
            total_ventas_periodo = df_analisis['num_ventas'].sum()
            total_ingresos_periodo = df_analisis['total_ventas'].sum()
            promedio_general = df_analisis['promedio_venta'].mean()
            dias_activos = df_analisis['dia'].nunique()
            
            with col_met1:
                st.metric("🛒 Total Ventas", total_ventas_periodo)
            
            with col_met2:
                st.metric("💰 Total Ingresos", f"${total_ingresos_periodo:.2f}")
            
            with col_met3:
                st.metric("📈 Promedio/Venta", f"${promedio_general:.2f}")
            
            with col_met4:
                st.metric("📅 Días Activos", dias_activos)
            
            # Análisis por método de pago
            st.markdown("---")
            st.markdown("**💳 Análisis por Método de Pago**")
            
            metodo_resumen = df_analisis.groupby('metodo_pago').agg({
                'num_ventas': 'sum',
                'total_ventas': 'sum',
                'promedio_venta': 'mean'
            }).reset_index()
            
            for _, metodo in metodo_resumen.iterrows():
                porcentaje = (metodo['total_ventas'] / total_ingresos_periodo) * 100
                st.write(f"💳 **{metodo['metodo_pago']}**: {metodo['num_ventas']} ventas - ${metodo['total_ventas']:.2f} ({porcentaje:.1f}%)")
            
            # Top días
            st.markdown("---")
            st.markdown("**🏆 Mejores Días del Período**")
            
            dias_resumen = df_analisis.groupby('dia').agg({
                'num_ventas': 'sum',
                'total_ventas': 'sum'
            }).reset_index().sort_values('total_ventas', ascending=False)
            
            for i, dia in dias_resumen.head(5).iterrows():
                st.write(f"📅 **{dia['dia']}**: {dia['num_ventas']} ventas - ${dia['total_ventas']:.2f}")
        
        else:
            st.info("📊 No hay datos para el período seleccionado")
    
    except Exception as e:
        st.error(f"❌ Error en análisis: {e}")

def mostrar_buscar_ventas(adapter):
    """Mostrar búsqueda avanzada de ventas"""
    
    st.markdown("**🔍 Búsqueda Avanzada**")
    
    # Formulario de búsqueda
    with st.form("busqueda_ventas"):
        col_busq1, col_busq2 = st.columns(2)
        
        with col_busq1:
            id_venta = st.text_input("🆔 ID de Venta:", placeholder="Ej: 123")
            vendedor_busq = st.text_input("👤 Vendedor:", placeholder="Nombre del vendedor")
            producto_busq = st.text_input("📦 Producto:", placeholder="Nombre del producto")
        
        with col_busq2:
            metodo_busq = st.selectbox("💳 Método:", ["Todos", "Efectivo", "Tarjeta", "Transferencia"])
            monto_min = st.number_input("💰 Monto mínimo:", min_value=0.0, step=0.01)
            monto_max = st.number_input("💰 Monto máximo:", min_value=0.0, step=0.01)
        
        if st.form_submit_button("🔍 Buscar", use_container_width=True, type="primary"):
            realizar_busqueda_avanzada(adapter, {
                'id_venta': id_venta,
                'vendedor': vendedor_busq,
                'producto': producto_busq,
                'metodo': metodo_busq,
                'monto_min': monto_min,
                'monto_max': monto_max
            })

def realizar_busqueda_avanzada(adapter, criterios):
    """Realizar búsqueda avanzada con criterios específicos"""
    
    try:
        # Construir query dinámicamente
        query = """
            SELECT DISTINCT v.*, COUNT(dv.id) as items_count
            FROM ventas v
            LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
            LEFT JOIN productos p ON dv.producto_id = p.id
            WHERE 1=1
        """
        params = []
        
        if criterios['id_venta']:
            query += " AND v.id = %s"
            params.append(int(criterios['id_venta']))
        
        if criterios['vendedor']:
            query += " AND LOWER(v.vendedor) LIKE %s"
            params.append(f"%{criterios['vendedor'].lower()}%")
        
        if criterios['producto']:
            query += " AND LOWER(p.nombre) LIKE %s"
            params.append(f"%{criterios['producto'].lower()}%")
        
        if criterios['metodo'] != "Todos":
            query += " AND v.metodo_pago = %s"
            params.append(criterios['metodo'])
        
        if criterios['monto_min'] > 0:
            query += " AND v.total >= %s"
            params.append(criterios['monto_min'])
        
        if criterios['monto_max'] > 0:
            query += " AND v.total <= %s"
            params.append(criterios['monto_max'])
        
        query += " GROUP BY v.id ORDER BY v.fecha DESC LIMIT 100"
        
        resultados = adapter.execute_query(query, params)
        
        if resultados:
            st.success(f"🔍 Encontradas {len(resultados)} ventas")
            
            for venta in resultados:
                mostrar_venta_card(adapter, venta)
        else:
            st.info("🔍 No se encontraron ventas con los criterios especificados")
    
    except Exception as e:
        st.error(f"❌ Error en búsqueda: {e}")

if __name__ == "__main__":
    show_ordenes()

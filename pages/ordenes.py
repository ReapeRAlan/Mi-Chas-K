"""
Órdenes/Ventas - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database.connection_optimized import get_db_adapter

def show_ordenes():
    """Mostrar gestión de órdenes/ventas optimizada para tablets"""
    
    # CSS adicional para órdenes
    st.markdown("""
    <style>
        .venta-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 0.8rem;
        }
        .venta-completada {
            border-left: 4px solid #28a745;
        }
        .venta-pendiente {
            border-left: 4px solid #ffc107;
        }
        .venta-cancelada {
            border-left: 4px solid #dc3545;
        }
        .venta-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .venta-total {
            font-size: 1.2rem;
            font-weight: bold;
            color: #28a745;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        st.subheader("📋 Gestión de Ventas")
        
        # Tabs principales
        tab1, tab2, tab3 = st.tabs(["📋 Ver Ventas", "🔍 Buscar Venta", "📊 Análisis"])
        
        with tab1:
            mostrar_lista_ventas(adapter)
        
        with tab2:
            buscar_venta_especifica(adapter)
        
        with tab3:
            analisis_ventas(adapter)
    
    except Exception as e:
        st.error(f"❌ Error en órdenes: {e}")

def mostrar_lista_ventas(adapter):
    """Mostrar lista de ventas con filtros"""
    
    # Controles de filtro
    col_fecha1, col_fecha2, col_vendedor, col_metodo = st.columns(4)
    
    with col_fecha1:
        fecha_desde = st.date_input(
            "📅 Desde:",
            value=date.today() - timedelta(days=7),
            key="ventas_fecha_desde"
        )
    
    with col_fecha2:
        fecha_hasta = st.date_input(
            "📅 Hasta:",
            value=date.today(),
            key="ventas_fecha_hasta"
        )
    
    with col_vendedor:
        vendedores = adapter.execute_query("SELECT DISTINCT vendedor FROM ventas WHERE vendedor IS NOT NULL ORDER BY vendedor")
        vendedor_nombres = ['Todos'] + [v['vendedor'] for v in vendedores]
        vendedor_filtro = st.selectbox(
            "👤 Vendedor:",
            vendedor_nombres,
            key="ventas_vendedor_filtro"
        )
    
    with col_metodo:
        metodos = adapter.execute_query("SELECT DISTINCT metodo_pago FROM ventas WHERE metodo_pago IS NOT NULL ORDER BY metodo_pago")
        metodo_nombres = ['Todos'] + [m['metodo_pago'] for m in metodos]
        metodo_filtro = st.selectbox(
            "💳 Método:",
            metodo_nombres,
            key="ventas_metodo_filtro"
        )
    
    # Construir query con filtros
    where_conditions = ["fecha BETWEEN %s AND %s"]
    params = [fecha_desde.strftime('%Y-%m-%d'), fecha_hasta.strftime('%Y-%m-%d')]
    
    if vendedor_filtro != 'Todos':
        where_conditions.append("vendedor = %s")
        params.append(vendedor_filtro)
    
    if metodo_filtro != 'Todos':
        where_conditions.append("metodo_pago = %s")
        params.append(metodo_filtro)
    
    where_clause = " AND ".join(where_conditions)
    
    # Obtener ventas
    ventas_query = f"""
        SELECT id, fecha, total, metodo_pago, vendedor, observaciones, estado
        FROM ventas
        WHERE {where_clause}
        ORDER BY fecha DESC
        LIMIT 50
    """
    
    ventas = adapter.execute_query(ventas_query, params)
    
    # Mostrar resumen
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    
    with col_res1:
        st.metric("📋 Total Ventas", len(ventas))
    
    with col_res2:
        total_ingresos = sum(float(v['total']) for v in ventas)
        st.metric("💰 Ingresos", f"${total_ingresos:.2f}")
    
    with col_res3:
        promedio = total_ingresos / max(len(ventas), 1)
        st.metric("📈 Promedio", f"${promedio:.2f}")
    
    with col_res4:
        efectivo_ventas = len([v for v in ventas if v['metodo_pago'] == 'Efectivo'])
        st.metric("💵 Efectivo", f"{efectivo_ventas}")
    
    st.markdown("---")
    
    # Mostrar ventas
    if ventas:
        for venta in ventas:
            mostrar_venta_card(venta, adapter)
    else:
        st.info("📭 No se encontraron ventas en el período seleccionado")

def mostrar_venta_card(venta, adapter):
    """Mostrar tarjeta de venta individual"""
    
    # Determinar clase CSS según estado
    estado = venta.get('estado', 'Completada')
    if estado == 'Completada':
        css_class = "venta-completada"
        icono_estado = "✅"
    elif estado == 'Pendiente':
        css_class = "venta-pendiente"
        icono_estado = "⏳"
    else:
        css_class = "venta-cancelada"
        icono_estado = "❌"
    
    # Container de la venta
    with st.container():
        st.markdown(f'<div class="venta-card {css_class}">', unsafe_allow_html=True)
        
        # Header de la venta
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        
        with col_header1:
            fecha_str = venta['fecha'].strftime('%Y-%m-%d %H:%M:%S') if venta['fecha'] else 'N/A'
            st.markdown(f"**🧾 Venta #{venta['id']}** - {fecha_str}")
        
        with col_header2:
            st.markdown(f"**{icono_estado} {estado}**")
        
        with col_header3:
            st.markdown(f'<div class="venta-total">${float(venta["total"]):.2f}</div>', unsafe_allow_html=True)
        
        # Detalles de la venta
        col_det1, col_det2, col_det3, col_det4 = st.columns(4)
        
        with col_det1:
            st.write(f"💳 {venta['metodo_pago'] or 'N/A'}")
        
        with col_det2:
            st.write(f"👤 {venta['vendedor'] or 'N/A'}")
        
        with col_det3:
            # Obtener cantidad de items
            detalles = adapter.execute_query(
                "SELECT COUNT(*) as items FROM detalle_ventas WHERE venta_id = %s",
                (venta['id'],)
            )
            items_count = detalles[0]['items'] if detalles else 0
            st.write(f"📦 {items_count} items")
        
        with col_det4:
            # Botón de detalles
            if st.button("🔍 Ver", key=f"ver_venta_{venta['id']}", help="Ver detalles"):
                st.session_state[f"mostrar_detalles_{venta['id']}"] = True
        
        # Observaciones si existen
        if venta['observaciones']:
            st.write(f"📝 {venta['observaciones']}")
        
        # Mostrar detalles si se solicitó
        if st.session_state.get(f"mostrar_detalles_{venta['id']}", False):
            mostrar_detalles_venta(venta['id'], adapter)
            
            if st.button("❌ Cerrar", key=f"cerrar_venta_{venta['id']}"):
                st.session_state[f"mostrar_detalles_{venta['id']}"] = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def mostrar_detalles_venta(venta_id, adapter):
    """Mostrar detalles específicos de una venta"""
    
    st.markdown("---")
    st.markdown("**📋 Detalles de la Venta:**")
    
    # Obtener detalles
    detalles = adapter.execute_query("""
        SELECT dv.*, p.nombre as producto_nombre
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = %s
        ORDER BY dv.id
    """, (venta_id,))
    
    if detalles:
        # Mostrar en tabla optimizada para tablets
        df_detalles = pd.DataFrame(detalles)
        
        # Crear tabla personalizada
        for detalle in detalles:
            col_prod, col_cant, col_precio, col_subtotal = st.columns([3, 1, 1, 1])
            
            with col_prod:
                st.write(detalle['producto_nombre'])
            
            with col_cant:
                st.write(f"Cant: {detalle['cantidad']}")
            
            with col_precio:
                st.write(f"${float(detalle['precio_unitario']):.2f}")
            
            with col_subtotal:
                st.write(f"**${float(detalle['subtotal']):.2f}**")
    else:
        st.warning("⚠️ No se encontraron detalles para esta venta")

def buscar_venta_especifica(adapter):
    """Buscar venta específica por ID o criterios"""
    
    st.subheader("🔍 Buscar Venta Específica")
    
    # Opciones de búsqueda
    busqueda_tipo = st.radio(
        "Tipo de búsqueda:",
        ["Por ID de Venta", "Por Producto Vendido", "Por Monto"],
        key="tipo_busqueda_venta"
    )
    
    if busqueda_tipo == "Por ID de Venta":
        venta_id = st.number_input(
            "ID de la venta:",
            min_value=1,
            value=1,
            key="busqueda_venta_id"
        )
        
        if st.button("🔍 Buscar", key="buscar_por_id"):
            venta = adapter.execute_query("SELECT * FROM ventas WHERE id = %s", (venta_id,))
            
            if venta:
                st.success(f"✅ Venta encontrada:")
                mostrar_venta_card(venta[0], adapter)
            else:
                st.error(f"❌ No se encontró venta con ID {venta_id}")
    
    elif busqueda_tipo == "Por Producto Vendido":
        productos = adapter.get_productos()
        if productos:
            productos_dict = {p['nombre']: p['id'] for p in productos}
            producto_nombre = st.selectbox(
                "Seleccionar producto:",
                list(productos_dict.keys()),
                key="busqueda_producto_nombre"
            )
            
            if st.button("🔍 Buscar Ventas", key="buscar_por_producto"):
                producto_id = productos_dict[producto_nombre]
                
                ventas_producto = adapter.execute_query("""
                    SELECT DISTINCT v.*
                    FROM ventas v
                    JOIN detalle_ventas dv ON v.id = dv.venta_id
                    WHERE dv.producto_id = %s
                    ORDER BY v.fecha DESC
                    LIMIT 20
                """, (producto_id,))
                
                if ventas_producto:
                    st.success(f"✅ {len(ventas_producto)} ventas encontradas con {producto_nombre}:")
                    for venta in ventas_producto:
                        mostrar_venta_card(venta, adapter)
                else:
                    st.info(f"📭 No se encontraron ventas con {producto_nombre}")
    
    elif busqueda_tipo == "Por Monto":
        col_min, col_max = st.columns(2)
        
        with col_min:
            monto_min = st.number_input(
                "Monto mínimo:",
                min_value=0.0,
                value=0.0,
                step=10.0,
                key="busqueda_monto_min"
            )
        
        with col_max:
            monto_max = st.number_input(
                "Monto máximo:",
                min_value=0.0,
                value=1000.0,
                step=10.0,
                key="busqueda_monto_max"
            )
        
        if st.button("🔍 Buscar por Monto", key="buscar_por_monto"):
            ventas_monto = adapter.execute_query("""
                SELECT * FROM ventas
                WHERE total BETWEEN %s AND %s
                ORDER BY fecha DESC
                LIMIT 30
            """, (monto_min, monto_max))
            
            if ventas_monto:
                st.success(f"✅ {len(ventas_monto)} ventas encontradas entre ${monto_min:.2f} y ${monto_max:.2f}:")
                for venta in ventas_monto:
                    mostrar_venta_card(venta, adapter)
            else:
                st.info(f"📭 No se encontraron ventas en el rango ${monto_min:.2f} - ${monto_max:.2f}")

def analisis_ventas(adapter):
    """Análisis detallado de ventas"""
    
    st.subheader("📊 Análisis de Ventas")
    
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
    
    # Obtener datos para análisis
    ventas_analisis = adapter.execute_query("""
        SELECT 
            DATE(fecha) as dia,
            COUNT(*) as num_ventas,
            SUM(total) as ingresos_dia,
            AVG(total) as promedio_venta,
            metodo_pago,
            vendedor
        FROM ventas
        WHERE fecha BETWEEN %s AND %s
        GROUP BY DATE(fecha), metodo_pago, vendedor
        ORDER BY dia DESC
    """, (fecha_desde_analisis.strftime('%Y-%m-%d'), fecha_hasta_analisis.strftime('%Y-%m-%d')))
    
    if ventas_analisis:
        df_analisis = pd.DataFrame(ventas_analisis)
        
        # Métricas del período
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            total_ventas_periodo = df_analisis['num_ventas'].sum()
            st.metric("📋 Ventas Totales", total_ventas_periodo)
        
        with col_met2:
            ingresos_totales = df_analisis['ingresos_dia'].sum()
            st.metric("💰 Ingresos Totales", f"${ingresos_totales:.2f}")
        
        with col_met3:
            promedio_general = df_analisis['promedio_venta'].mean()
            st.metric("📈 Promedio Venta", f"${promedio_general:.2f}")
        
        with col_met4:
            dias_activos = df_analisis['dia'].nunique()
            ventas_por_dia = total_ventas_periodo / max(dias_activos, 1)
            st.metric("📅 Ventas/Día", f"{ventas_por_dia:.1f}")
        
        # Análisis por método de pago
        st.markdown("---")
        st.markdown("**💳 Análisis por Método de Pago:**")
        
        metodos_stats = df_analisis.groupby('metodo_pago').agg({
            'num_ventas': 'sum',
            'ingresos_dia': 'sum'
        }).reset_index()
        
        for _, metodo in metodos_stats.iterrows():
            col_metodo1, col_metodo2, col_metodo3 = st.columns(3)
            
            with col_metodo1:
                st.write(f"**{metodo['metodo_pago']}**")
            
            with col_metodo2:
                st.write(f"📋 {metodo['num_ventas']} ventas")
            
            with col_metodo3:
                st.write(f"💰 ${metodo['ingresos_dia']:.2f}")
        
        # Análisis por vendedor
        st.markdown("---")
        st.markdown("**👤 Análisis por Vendedor:**")
        
        vendedores_stats = df_analisis.groupby('vendedor').agg({
            'num_ventas': 'sum',
            'ingresos_dia': 'sum',
            'promedio_venta': 'mean'
        }).reset_index()
        
        vendedores_stats = vendedores_stats.sort_values('ingresos_dia', ascending=False)
        
        for _, vendedor in vendedores_stats.iterrows():
            col_vend1, col_vend2, col_vend3, col_vend4 = st.columns(4)
            
            with col_vend1:
                st.write(f"**{vendedor['vendedor']}**")
            
            with col_vend2:
                st.write(f"📋 {vendedor['num_ventas']} ventas")
            
            with col_vend3:
                st.write(f"💰 ${vendedor['ingresos_dia']:.2f}")
            
            with col_vend4:
                st.write(f"📈 ${vendedor['promedio_venta']:.2f} prom.")
    
    else:
        st.info("📭 No hay datos de ventas para el período seleccionado")

if __name__ == "__main__":
    show_ordenes()

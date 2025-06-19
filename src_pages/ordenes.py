"""
Página para gestión de órdenes/ventas existentes
Permite ver, modificar y reimprimir tickets
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.models import Venta, DetalleVenta, Producto, Vendedor
from database.connection import execute_query, execute_update
from utils.helpers import format_currency
from utils.timezone_utils import get_mexico_datetime, get_mexico_date_str, format_mexico_datetime
from utils.pdf_generator import TicketGenerator

def safe_int(value):
    """Convierte valor a int de forma segura, manejando numpy.int64"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def mostrar_ordenes():
    """Página principal de gestión de órdenes"""
    st.title("📋 Gestión de Órdenes")
    
    # CSS para mejorar la interfaz
    st.markdown("""
    <style>
    .action-button {
        width: 100%;
        margin: 2px 0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .view-btn { background-color: #e3f2fd; color: #1565c0; }
    .edit-btn { background-color: #fff3e0; color: #ef6c00; }
    .delete-btn { background-color: #ffebee; color: #c62828; }
    .print-btn { background-color: #e8f5e8; color: #2e7d32; }
    .quick-edit-panel {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #ff6b35;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Pestañas principales - Auto-seleccionar la pestaña de modificar si hay una orden seleccionada
    if 'orden_seleccionada' in st.session_state and st.session_state.orden_seleccionada:
        default_tab = 1  # Pestaña de modificar
    else:
        default_tab = 0  # Pestaña de ver órdenes
    
    tab1, tab2, tab3 = st.tabs(["🔍 Ver Órdenes", "✏️ Modificar Orden", "🆕 Nueva Venta Manual"])
    
    with tab1:
        mostrar_lista_ordenes()
    
    with tab2:
        if 'orden_seleccionada' in st.session_state and st.session_state.orden_seleccionada:
            mostrar_modificar_orden()
        else:
            st.info("💡 Selecciona una orden desde la pestaña 'Ver Órdenes' para modificarla")
            st.markdown("### Funciones disponibles en modificación:")
            st.markdown("""
            - ✏️ **Editar información general** (vendedor, método de pago, observaciones)
            - 🛒 **Agregar nuevos productos** a la orden
            - 📝 **Modificar cantidades** de productos existentes
            - 🗑️ **Eliminar productos** de la orden
            - 🗂️ **Eliminar orden completa** (con confirmación)
            - 🖨️ **Reimprimir ticket** con los cambios
            """)
    
    with tab3:
        mostrar_nueva_venta_manual()

def mostrar_lista_ordenes():
    """Muestra la lista de órdenes con filtros"""
    st.subheader("🔍 Lista de Órdenes")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_desde = st.date_input(
            "Desde:",
            value=get_mexico_datetime().date() - timedelta(days=7)
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Hasta:",
            value=get_mexico_datetime().date()
        )
    
    with col3:
        vendedores = ["Todos"] + Vendedor.get_nombres_activos()
        vendedor_filtro = st.selectbox("Vendedor:", vendedores)
    
    # Obtener órdenes
    query = """
        SELECT v.id, v.total, v.metodo_pago, v.fecha, v.vendedor, v.observaciones,
               COUNT(dv.id) as items_count
        FROM ventas v
        LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
        WHERE DATE(v.fecha) BETWEEN %s AND %s
    """
    params = [str(fecha_desde), str(fecha_hasta)]
    
    if vendedor_filtro != "Todos":
        query += " AND v.vendedor = %s"
        params.append(vendedor_filtro)
    
    query += " GROUP BY v.id, v.total, v.metodo_pago, v.fecha, v.vendedor, v.observaciones"
    query += " ORDER BY v.fecha DESC"
    
    ordenes = execute_query(query, tuple(params))
    
    if not ordenes:
        st.warning("No se encontraron órdenes en el período seleccionado")
        return
    
    # Mostrar estadísticas rápidas
    total_ordenes = len(ordenes)
    total_ventas = sum(float(orden['total']) for orden in ordenes)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Órdenes", total_ordenes)
    with col2:
        st.metric("Total Ventas", f"${total_ventas:,.2f}")
    with col3:
        promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0
        st.metric("Promedio por Orden", f"${promedio:,.2f}")
    
    st.divider()
    
    # Tabla de órdenes
    st.subheader("📋 Órdenes Registradas")
    
    # Crear DataFrame para mostrar
    df_ordenes = []
    for orden in ordenes:
        df_ordenes.append({
            "ID": orden['id'],
            "Fecha": format_mexico_datetime(orden['fecha']),
            "Total": f"${float(orden['total']):,.2f}",
            "Método Pago": orden['metodo_pago'],
            "Items": orden['items_count'],
            "Vendedor": orden['vendedor'] or "Sin especificar",
            "Observaciones": orden['observaciones'][:50] + "..." if orden['observaciones'] and len(orden['observaciones']) > 50 else orden['observaciones'] or ""
        })
    
    df = pd.DataFrame(df_ordenes)
    
    # Mostrar tabla con selección
    if not df.empty:
        evento = st.dataframe(
            df,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Acciones para orden seleccionada
        if evento.selection.rows:
            fila_seleccionada = evento.selection.rows[0]
            orden_id = df.iloc[fila_seleccionada]['ID']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ Ver Detalle", key=f"ver_{orden_id}"):
                    mostrar_detalle_orden(orden_id)
            
            with col2:
                if st.button("✏️ Modificar", key=f"mod_{orden_id}", help="Ir directo a modificar orden"):
                    st.session_state.orden_seleccionada = orden_id
                    st.session_state.auto_switch_tab = True
                    st.rerun()
            
            with col3:
                if st.button("🖨️ Reimprimir", key=f"print_{orden_id}", help="Reimprimir ticket"):
                    reimprimir_ticket(orden_id)
            
            # Panel de acciones rápidas para la orden seleccionada
            if st.session_state.get('show_quick_actions', False) and st.session_state.get('quick_action_orden') == orden_id:
                with st.container():
                    st.markdown('<div class="quick-edit-panel">', unsafe_allow_html=True)
                    st.markdown(f"### ⚡ Acciones Rápidas - Orden #{orden_id}")
                    
                    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
                    
                    with quick_col1:
                        if st.button("🗑️ Eliminar Orden", key=f"quick_delete_{orden_id}", help="Eliminar orden completa"):
                            confirmar_eliminar_orden(orden_id)
                    
                    with quick_col2:
                        if st.button("📋 Duplicar Orden", key=f"quick_duplicate_{orden_id}", help="Crear nueva venta con los mismos productos"):
                            duplicar_orden(orden_id)
                    
                    with quick_col3:
                        if st.button("📧 Enviar por Email", key=f"quick_email_{orden_id}", help="Enviar ticket por email"):
                            st.info("🚧 Función en desarrollo")
                    
                    with quick_col4:
                        if st.button("❌ Cerrar", key=f"quick_close_{orden_id}"):
                            st.session_state.show_quick_actions = False
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Botón para mostrar/ocultar acciones rápidas
            if st.button("⚡ Más Acciones", key=f"more_actions_{orden_id}"):
                st.session_state.show_quick_actions = not st.session_state.get('show_quick_actions', False)
                st.session_state.quick_action_orden = orden_id
                st.rerun()

def mostrar_detalle_orden(orden_id: int):
    """Muestra el detalle completo de una orden"""
    orden_id = safe_int(orden_id)  # Convertir a int seguro
    
    with st.expander(f"📋 Detalle de Orden #{orden_id}", expanded=True):
        # Obtener información de la venta
        venta_query = "SELECT * FROM ventas WHERE id = %s"
        venta_data = execute_query(venta_query, (orden_id,))
        
        if not venta_data:
            st.error("No se encontró la orden")
            return
        
        venta = venta_data[0]
        
        # Información general
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Fecha:** {format_mexico_datetime(venta['fecha'])}")
            st.write(f"**Total:** ${float(venta['total']):,.2f}")
            st.write(f"**Método de Pago:** {venta['metodo_pago']}")
        
        with col2:
            st.write(f"**Vendedor:** {venta['vendedor'] or 'Sin especificar'}")
            st.write(f"**Descuento:** ${float(venta['descuento'] or 0):,.2f}")
            st.write(f"**Impuestos:** ${float(venta['impuestos'] or 0):,.2f}")
        
        if venta['observaciones']:
            st.write(f"**Observaciones:** {venta['observaciones']}")
        
        # Detalle de productos
        st.subheader("📦 Productos")
        
        detalle_query = """
            SELECT dv.*, p.nombre, p.descripcion
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
            ORDER BY dv.id
        """
        detalle_data = execute_query(detalle_query, (orden_id,))
        
        if detalle_data:
            for item in detalle_data:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item['nombre']}**")
                    if item['descripcion']:
                        st.write(f"*{item['descripcion']}*")
                
                with col2:
                    st.write(f"Cantidad: {item['cantidad']}")
                
                with col3:
                    st.write(f"Precio: ${float(item['precio_unitario']):,.2f}")
                
                with col4:
                    st.write(f"Subtotal: ${float(item['subtotal']):,.2f}")
                
                st.divider()

def mostrar_modificar_orden():
    """Permite modificar una orden existente de forma completa"""
    orden_id = safe_int(st.session_state.orden_seleccionada)
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #ff6b35, #f7931e); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
        <h2 style="margin: 0;">✏️ Modificar Orden #{orden_id}</h2>
        <p style="margin: 0.5rem 0 0 0;">Panel completo de edición y gestión de orden</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos actuales
    venta_query = "SELECT * FROM ventas WHERE id = %s"
    venta_data = execute_query(venta_query, (orden_id,))
    
    if not venta_data:
        st.error("❌ No se encontró la orden")
        if st.button("🔙 Volver a lista"):
            st.session_state.orden_seleccionada = None
            st.rerun()
        return
    
    venta = venta_data[0]
    
    # Pestañas de edición
    edit_tab1, edit_tab2, edit_tab3, edit_tab4 = st.tabs([
        "📝 Info General", 
        "🛒 Productos", 
        "➕ Agregar Productos", 
        "🗑️ Acciones"
    ])
    
    with edit_tab1:
        modificar_info_general(orden_id, venta)
    
    with edit_tab2:
        modificar_productos_orden(orden_id)
    
    with edit_tab3:
        agregar_productos_orden(orden_id)
    
    with edit_tab4:
        acciones_orden_avanzadas(orden_id)

def modificar_info_general(orden_id, venta):
    """Modificar información general de la orden"""
    st.subheader("📝 Información General de la Orden")
    
    with st.form(f"info_general_{orden_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Vendedor
            vendedores = Vendedor.get_nombres_activos()
            vendedor_actual = venta['vendedor'] if venta['vendedor'] in vendedores else vendedores[0] if vendedores else ""
            nuevo_vendedor = st.selectbox(
                "👤 Vendedor:",
                vendedores,
                index=vendedores.index(vendedor_actual) if vendedor_actual in vendedores else 0
            )
            
            # Método de pago
            metodos_pago = ["Efectivo", "Tarjeta", "Transferencia", "Mixto"]
            metodo_actual = venta['metodo_pago']
            nuevo_metodo = st.selectbox(
                "💳 Método de Pago:",
                metodos_pago,
                index=metodos_pago.index(metodo_actual) if metodo_actual in metodos_pago else 0
            )
            
            # Fecha (permitir cambiar)
            fecha_actual = venta['fecha'].date() if hasattr(venta['fecha'], 'date') else venta['fecha']
            nueva_fecha = st.date_input(
                "📅 Fecha de la venta:",
                value=fecha_actual,
                help="Puedes cambiar la fecha de la venta"
            )
        
        with col2:
            # Descuento
            descuento_actual = float(venta['descuento'] or 0)
            nuevo_descuento = st.number_input(
                "💰 Descuento ($):",
                min_value=0.0,
                value=descuento_actual,
                step=1.0,
                format="%.2f"
            )
            
            # Impuestos
            impuestos_actual = float(venta['impuestos'] or 0)
            nuevos_impuestos = st.number_input(
                "🏛️ Impuestos ($):",
                min_value=0.0,
                value=impuestos_actual,
                step=1.0,
                format="%.2f"
            )
            
            # Estado (nuevo campo)
            estados = ["Completada", "Pendiente", "Cancelada", "Reembolsada"]
            estado_actual = venta.get('estado', 'Completada')
            nuevo_estado = st.selectbox(
                "📊 Estado:",
                estados,
                index=estados.index(estado_actual) if estado_actual in estados else 0
            )
        
        # Observaciones
        observaciones_actual = venta['observaciones'] or ""
        nuevas_observaciones = st.text_area(
            "📋 Observaciones:",
            value=observaciones_actual,
            height=100,
            help="Notas adicionales sobre la venta"
        )
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
        
        with col2:
            if st.form_submit_button("🔄 Recalcular Total", use_container_width=True):
                recalcular_total_orden(orden_id)
        
        with col3:
            if st.form_submit_button("🖨️ Reimprimir", use_container_width=True):
                reimprimir_ticket(orden_id)
        
        if submitted:
            # Actualizar la información
            try:
                # Crear datetime con la nueva fecha
                from datetime import datetime, time
                nueva_fecha_completa = datetime.combine(nueva_fecha, time())
                
                update_query = """
                    UPDATE ventas 
                    SET vendedor = %s, metodo_pago = %s, fecha = %s, descuento = %s, 
                        impuestos = %s, observaciones = %s, estado = %s
                    WHERE id = %s
                """
                execute_update(update_query, (
                    nuevo_vendedor, nuevo_metodo, nueva_fecha_completa, nuevo_descuento,
                    nuevos_impuestos, nuevas_observaciones, nuevo_estado, orden_id
                ))
                
                st.success("✅ Información actualizada correctamente")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al actualizar: {str(e)}")

def modificar_productos_orden(orden_id):
    """Modificar productos existentes en la orden"""
    st.subheader("🛒 Productos en la Orden")
    
    # Obtener productos actuales
    detalle_query = """
        SELECT dv.*, p.nombre, p.stock, p.precio as precio_actual
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = %s
        ORDER BY dv.id
    """
    detalle_data = execute_query(detalle_query, (orden_id,))
    
    if not detalle_data:
        st.info("📭 No hay productos en esta orden")
        return
    
    # Mostrar cada producto con opciones de edición
    for i, item in enumerate(detalle_data):
        with st.container():
            st.markdown("---")
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{item['nombre']}**")
                st.markdown(f"*Stock disponible: {item['stock']}*")
            
            with col2:
                nueva_cantidad = st.number_input(
                    "Cantidad:",
                    min_value=0,
                    max_value=item['stock'] + item['cantidad'],  # Stock actual + cantidad ya tomada
                    value=int(item['cantidad']),
                    key=f"cantidad_{item['id']}"
                )
            
            with col3:
                nuevo_precio = st.number_input(
                    "Precio ($):",
                    min_value=0.0,
                    value=float(item['precio_unitario']),
                    step=0.01,
                    key=f"precio_{item['id']}"
                )
            
            with col4:
                subtotal = nueva_cantidad * nuevo_precio
                st.markdown(f"**Subtotal:**")
                st.markdown(f"${subtotal:.2f}")
            
            with col5:
                if st.button("💾", key=f"update_{item['id']}", help="Actualizar producto"):
                    actualizar_producto_orden(item['id'], nueva_cantidad, nuevo_precio, item['cantidad'], item['producto_id'])
                
                if st.button("🗑️", key=f"delete_{item['id']}", help="Eliminar producto"):
                    eliminar_producto_orden(item['id'], item['cantidad'], item['producto_id'])

def agregar_productos_orden(orden_id):
    """Agregar nuevos productos a la orden"""
    st.subheader("➕ Agregar Productos a la Orden")
    
    # Obtener productos disponibles
    productos = Producto.get_all()
    
    if not productos:
        st.warning("⚠️ No hay productos disponibles")
        return
    
    # Selector de producto
    productos_options = {f"{p.nombre} - ${p.precio:.2f} (Stock: {p.stock})": p for p in productos if p.stock > 0}
    
    if not productos_options:
        st.warning("⚠️ No hay productos con stock disponible")
        return
    
    with st.form(f"agregar_producto_{orden_id}"):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            producto_seleccionado_key = st.selectbox(
                "🛍️ Seleccionar Producto:",
                list(productos_options.keys())
            )
            producto_seleccionado = productos_options[producto_seleccionado_key]
        
        with col2:
            cantidad = st.number_input(
                "📦 Cantidad:",
                min_value=1,
                max_value=producto_seleccionado.stock,
                value=1
            )
        
        with col3:
            precio = st.number_input(
                "💰 Precio ($):",
                min_value=0.01,
                value=float(producto_seleccionado.precio),
                step=0.01
            )
        
        # Mostrar información del producto
        st.info(f"📋 **Producto:** {producto_seleccionado.nombre} | **Stock:** {producto_seleccionado.stock} | **Subtotal:** ${cantidad * precio:.2f}")
        
        if st.form_submit_button("➕ Agregar a la Orden", use_container_width=True):
            agregar_producto_a_orden(orden_id, producto_seleccionado.id, cantidad, precio)

def acciones_orden_avanzadas(orden_id):
    """Acciones avanzadas para la orden"""
    st.subheader("🗑️ Acciones Avanzadas")
    
    # Información de advertencia
    st.markdown("""
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 5px; padding: 1rem; margin: 1rem 0;">
        <strong>⚠️ Zona de Peligro</strong><br>
        Las siguientes acciones son irreversibles. Úsalas con precaución.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🗑️ Eliminar Orden Completa")
        st.markdown("Elimina permanentemente la orden y restaura el stock de todos los productos.")
        
        # Checkbox de confirmación
        confirmar_eliminar = st.checkbox(
            "Confirmo que quiero eliminar esta orden",
            key=f"confirm_delete_{orden_id}"
        )
        
        if st.button(
            "🗑️ ELIMINAR ORDEN",
            disabled=not confirmar_eliminar,
            help="Esta acción no se puede deshacer",
            use_container_width=True
        ):
            eliminar_orden_completa(orden_id)
    
    with col2:
        st.markdown("### 📋 Duplicar Orden")
        st.markdown("Crea una nueva venta con los mismos productos y cantidades.")
        
        if st.button("📋 Duplicar Orden", use_container_width=True):
            duplicar_orden(orden_id)
        
        st.markdown("### 📊 Estadísticas")
        mostrar_estadisticas_orden(orden_id)
    
    # Botón para volver
    st.markdown("---")
    if st.button("🔙 Volver a Lista de Órdenes", use_container_width=True):
        st.session_state.orden_seleccionada = None
        st.rerun()

# Funciones auxiliares para el sistema de órdenes mejorado

def mostrar_nueva_venta_manual():
    """Permite crear una nueva venta con fecha personalizada"""
    st.subheader("🆕 Nueva Venta Manual")
    st.markdown("Crea una nueva venta especificando fecha y productos manualmente")
    
    # Similar al punto de venta pero con fecha personalizable
    from datetime import date, datetime
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_venta = st.date_input(
            "📅 Fecha de la venta:",
            value=date.today(),
            help="Selecciona la fecha para la nueva venta"
        )
    
    with col2:
        vendedores = Vendedor.get_nombres_activos()
        vendedor = st.selectbox("👤 Vendedor:", vendedores)
    
    # Inicializar carrito para venta manual si no existe
    if 'carrito_manual' not in st.session_state:
        st.session_state.carrito_manual = []
    
    # Selector de productos
    productos = Producto.get_all()
    if productos:
        productos_options = {f"{p.nombre} - ${p.precio:.2f} (Stock: {p.stock})": p for p in productos if p.stock > 0}
        
        if productos_options:
            with st.form("agregar_producto_manual"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    producto_key = st.selectbox("Producto:", list(productos_options.keys()))
                    producto = productos_options[producto_key]
                
                with col2:
                    cantidad = st.number_input("Cantidad:", min_value=1, max_value=producto.stock, value=1)
                
                with col3:
                    precio = st.number_input("Precio:", min_value=0.01, value=float(producto.precio), step=0.01)
                
                if st.form_submit_button("➕ Agregar al Carrito"):
                    st.session_state.carrito_manual.append({
                        'producto_id': producto.id,
                        'nombre': producto.nombre,
                        'cantidad': cantidad,
                        'precio': precio,
                        'subtotal': cantidad * precio
                    })
                    st.success(f"✅ {producto.nombre} agregado al carrito")
                    st.rerun()
    
    # Mostrar carrito manual
    if st.session_state.carrito_manual:
        st.subheader("🛒 Carrito de Venta Manual")
        
        total = 0
        for i, item in enumerate(st.session_state.carrito_manual):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.write(item['nombre'])
            with col2:
                st.write(f"Cantidad: {item['cantidad']}")
            with col3:
                st.write(f"${item['precio']:.2f}")
            with col4:
                st.write(f"${item['subtotal']:.2f}")
            with col5:
                if st.button("🗑️", key=f"remove_manual_{i}"):
                    st.session_state.carrito_manual.pop(i)
                    st.rerun()
            
            total += item['subtotal']
        
        st.markdown(f"### Total: ${total:.2f}")
        
        # Procesar venta manual
        col1, col2 = st.columns(2)
        
        with col1:
            metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Tarjeta", "Transferencia", "Mixto"])
        
        with col2:
            observaciones = st.text_input("Observaciones:")
        
        if st.button("💾 Procesar Venta Manual", use_container_width=True):
            procesar_venta_manual(fecha_venta, vendedor, metodo_pago, observaciones, total)

def procesar_venta_manual(fecha_venta, vendedor, metodo_pago, observaciones, total):
    """Procesa una venta manual con fecha personalizada"""
    try:
        from datetime import datetime, time
        fecha_completa = datetime.combine(fecha_venta, time())
        
        # Crear la venta
        venta_query = """
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones, descuento, impuestos)
            VALUES (%s, %s, %s, %s, %s, 0, 0)
            RETURNING id
        """
        
        venta_result = execute_query(venta_query, (fecha_completa, total, metodo_pago, vendedor, observaciones))
        venta_id = venta_result[0]['id']
        
        # Agregar detalles
        for item in st.session_state.carrito_manual:
            detalle_query = """
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_update(detalle_query, (
                venta_id, item['producto_id'], item['cantidad'], 
                item['precio'], item['subtotal']
            ))
            
            # Actualizar stock
            stock_query = "UPDATE productos SET stock = stock - %s WHERE id = %s"
            execute_update(stock_query, (item['cantidad'], item['producto_id']))
        
        # Limpiar carrito
        st.session_state.carrito_manual = []
        
        st.success(f"✅ Venta manual #{venta_id} creada exitosamente")
        st.info(f"📅 Fecha: {fecha_venta} | 💰 Total: ${total:.2f}")
        
    except Exception as e:
        st.error(f"❌ Error al procesar venta manual: {str(e)}")

def confirmar_eliminar_orden(orden_id):
    """Confirma la eliminación de una orden"""
    if f'confirm_delete_{orden_id}' not in st.session_state:
        st.session_state[f'confirm_delete_{orden_id}'] = False
    
    if st.session_state[f'confirm_delete_{orden_id}']:
        eliminar_orden_completa(orden_id)
    else:
        st.session_state[f'confirm_delete_{orden_id}'] = True
        st.warning("⚠️ Haz clic nuevamente para confirmar la eliminación")
        st.rerun()

def duplicar_orden(orden_id):
    """Duplica una orden existente creando una nueva venta"""
    try:
        # Obtener datos de la orden original
        venta_query = "SELECT * FROM ventas WHERE id = %s"
        venta_data = execute_query(venta_query, (orden_id,))
        
        if not venta_data:
            st.error("❌ Orden no encontrada")
            return
        
        venta_original = venta_data[0]
        
        # Obtener productos de la orden
        detalle_query = """
            SELECT dv.producto_id, dv.cantidad, dv.precio_unitario, dv.subtotal
            FROM detalle_ventas dv
            WHERE dv.venta_id = %s
        """
        detalle_data = execute_query(detalle_query, (orden_id,))
        
        # Crear nueva venta
        nueva_venta_query = """
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones, descuento, impuestos)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        fecha_actual = get_mexico_datetime()
        nueva_venta_result = execute_query(nueva_venta_query, (
            fecha_actual, venta_original['total'], venta_original['metodo_pago'],
            venta_original['vendedor'], f"Copia de orden #{orden_id}",
            venta_original['descuento'], venta_original['impuestos']
        ))
        
        nueva_venta_id = nueva_venta_result[0]['id']
        
        # Copiar productos
        for item in detalle_data:
            detalle_insert = """
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_update(detalle_insert, (
                nueva_venta_id, item['producto_id'], item['cantidad'],
                item['precio_unitario'], item['subtotal']
            ))
            
            # Actualizar stock
            stock_update = "UPDATE productos SET stock = stock - %s WHERE id = %s"
            execute_update(stock_update, (item['cantidad'], item['producto_id']))
        
        st.success(f"✅ Orden duplicada exitosamente. Nueva orden: #{nueva_venta_id}")
        
    except Exception as e:
        st.error(f"❌ Error al duplicar orden: {str(e)}")

def recalcular_total_orden(orden_id):
    """Recalcula el total de una orden basado en sus productos"""
    try:
        # Obtener total de productos
        total_query = """
            SELECT SUM(subtotal) as nuevo_total
            FROM detalle_ventas
            WHERE venta_id = %s
        """
        total_result = execute_query(total_query, (orden_id,))
        nuevo_total = float(total_result[0]['nuevo_total'] or 0)
        
        # Obtener descuentos e impuestos actuales
        venta_query = "SELECT descuento, impuestos FROM ventas WHERE id = %s"
        venta_data = execute_query(venta_query, (orden_id,))
        descuento = float(venta_data[0]['descuento'] or 0)
        impuestos = float(venta_data[0]['impuestos'] or 0)
        
        # Calcular total final
        total_final = nuevo_total - descuento + impuestos
        
        # Actualizar venta
        update_query = "UPDATE ventas SET total = %s WHERE id = %s"
        execute_update(update_query, (total_final, orden_id))
        
        st.success(f"✅ Total recalculado: ${total_final:.2f}")
        
    except Exception as e:
        st.error(f"❌ Error al recalcular total: {str(e)}")

def actualizar_producto_orden(detalle_id, nueva_cantidad, nuevo_precio, cantidad_anterior, producto_id):
    """Actualiza un producto en la orden"""
    try:
        # Calcular nuevo subtotal
        nuevo_subtotal = nueva_cantidad * nuevo_precio
        
        # Actualizar detalle de venta
        update_query = """
            UPDATE detalle_ventas 
            SET cantidad = %s, precio_unitario = %s, subtotal = %s
            WHERE id = %s
        """
        execute_update(update_query, (nueva_cantidad, nuevo_precio, nuevo_subtotal, detalle_id))
        
        # Ajustar stock (devolver cantidad anterior y quitar nueva cantidad)
        diferencia = nueva_cantidad - cantidad_anterior
        stock_query = "UPDATE productos SET stock = stock - %s WHERE id = %s"
        execute_update(stock_query, (diferencia, producto_id))
        
        st.success("✅ Producto actualizado correctamente")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al actualizar producto: {str(e)}")

def eliminar_producto_orden(detalle_id, cantidad, producto_id):
    """Elimina un producto de la orden"""
    try:
        # Eliminar de detalle_ventas
        delete_query = "DELETE FROM detalle_ventas WHERE id = %s"
        execute_update(delete_query, (detalle_id,))
        
        # Devolver stock
        stock_query = "UPDATE productos SET stock = stock + %s WHERE id = %s"
        execute_update(stock_query, (cantidad, producto_id))
        
        st.success("✅ Producto eliminado de la orden")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al eliminar producto: {str(e)}")

def agregar_producto_a_orden(orden_id, producto_id, cantidad, precio):
    """Agrega un nuevo producto a la orden existente"""
    try:
        # Verificar stock
        stock_query = "SELECT stock FROM productos WHERE id = %s"
        stock_data = execute_query(stock_query, (producto_id,))
        
        if not stock_data or stock_data[0]['stock'] < cantidad:
            st.error("❌ Stock insuficiente")
            return
        
        # Calcular subtotal
        subtotal = cantidad * precio
        
        # Agregar a detalle_ventas
        insert_query = """
            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_update(insert_query, (orden_id, producto_id, cantidad, precio, subtotal))
        
        # Actualizar stock
        stock_update = "UPDATE productos SET stock = stock - %s WHERE id = %s"
        execute_update(stock_update, (cantidad, producto_id))
        
        st.success("✅ Producto agregado a la orden")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al agregar producto: {str(e)}")

def eliminar_orden_completa(orden_id):
    """Elimina una orden completa y restaura el stock"""
    try:
        # Obtener productos para restaurar stock
        detalle_query = """
            SELECT producto_id, cantidad
            FROM detalle_ventas
            WHERE venta_id = %s
        """
        detalle_data = execute_query(detalle_query, (orden_id,))
        
        # Restaurar stock
        for item in detalle_data:
            stock_query = "UPDATE productos SET stock = stock + %s WHERE id = %s"
            execute_update(stock_query, (item['cantidad'], item['producto_id']))
        
        # Eliminar detalles
        delete_detalle = "DELETE FROM detalle_ventas WHERE venta_id = %s"
        execute_update(delete_detalle, (orden_id,))
        
        # Eliminar venta
        delete_venta = "DELETE FROM ventas WHERE id = %s"
        execute_update(delete_venta, (orden_id,))
        
        st.success("✅ Orden eliminada completamente")
        st.session_state.orden_seleccionada = None
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error al eliminar orden: {str(e)}")

def mostrar_estadisticas_orden(orden_id):
    """Muestra estadísticas de la orden"""
    try:
        # Obtener estadísticas
        stats_query = """
            SELECT 
                COUNT(*) as total_productos,
                SUM(cantidad) as total_items,
                AVG(precio_unitario) as precio_promedio
            FROM detalle_ventas
            WHERE venta_id = %s
        """
        stats_data = execute_query(stats_query, (orden_id,))
        
        if stats_data:
            stats = stats_data[0]
            st.markdown(f"""
            **📊 Estadísticas de la Orden:**
            - **Productos únicos:** {stats['total_productos']}
            - **Items totales:** {stats['total_items']}
            - **Precio promedio:** ${float(stats['precio_promedio'] or 0):.2f}
            """)
    
    except Exception as e:
        st.error(f"❌ Error al obtener estadísticas: {str(e)}")

def reimprimir_ticket(orden_id):
    """Reimprime el ticket de una orden"""
    try:
        orden_id = safe_int(orden_id)
        
        # Obtener datos de la venta
        venta_query = "SELECT * FROM ventas WHERE id = %s"
        venta_data = execute_query(venta_query, (orden_id,))
        
        if not venta_data:
            st.error("❌ Orden no encontrada")
            return
        
        venta = venta_data[0]
        
        # Obtener detalles de la venta
        detalle_query = """
            SELECT dv.*, p.nombre, p.descripcion
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
            ORDER BY dv.id
        """
        detalle_data = execute_query(detalle_query, (orden_id,))
        
        # Crear estructura de datos para el ticket
        ticket_data = {
            'venta_id': venta['id'],
            'fecha': venta['fecha'],
            'vendedor': venta['vendedor'] or 'Sin especificar',
            'metodo_pago': venta['metodo_pago'],
            'total': float(venta['total']),
            'descuento': float(venta['descuento'] or 0),
            'impuestos': float(venta['impuestos'] or 0),
            'observaciones': venta['observaciones'],
            'productos': []
        }
        
        for item in detalle_data:
            ticket_data['productos'].append({
                'nombre': item['nombre'],
                'descripcion': item['descripcion'] or '',
                'cantidad': item['cantidad'],
                'precio_unitario': float(item['precio_unitario']),
                'subtotal': float(item['subtotal'])
            })
        
        # Generar ticket
        generator = TicketGenerator()
        pdf_buffer = generator.generar_ticket(ticket_data)
        
        if pdf_buffer:
            st.success("✅ Ticket generado exitosamente")
            st.download_button(
                label="📄 Descargar Ticket",
                data=pdf_buffer,
                file_name=f"ticket_reimpreso_{orden_id}_{get_mexico_date_str()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.error("❌ Error al generar el ticket")
            
    except Exception as e:
        st.error(f"❌ Error al reimprimir ticket: {str(e)}")

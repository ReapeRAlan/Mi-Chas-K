"""
Página principal del punto de venta con sistema de múltiples órdenes
"""
import streamlit as st
from datetime import datetime
from database.models import Producto, Categoria, Carrito, Vendedor
from utils.helpers import (
    format_currency, initialize_session_state, show_success_message,
    show_error_message, format_product_display, reset_venta_state
)
from utils.pdf_generator import TicketGenerator
from utils.timezone_utils import get_mexico_datetime
import uuid

def inicializar_ordenes_multiples():
    """Inicializar el sistema de órdenes múltiples"""
    if 'ordenes_multiples' not in st.session_state:
        st.session_state.ordenes_multiples = {}
    if 'orden_activa' not in st.session_state:
        st.session_state.orden_activa = None
    if 'contador_ordenes' not in st.session_state:
        st.session_state.contador_ordenes = 1

def crear_nueva_orden():
    """Crear una nueva orden"""
    orden_id = f"ORDEN-{st.session_state.contador_ordenes:03d}"
    st.session_state.ordenes_multiples[orden_id] = {
        'id': orden_id,
        'carrito': Carrito(),
        'fecha_creacion': get_mexico_datetime(),
        'estado': 'En proceso',
        'cliente': '',
        'observaciones': '',
        'vendedor': '',
        'metodo_pago': 'Efectivo',
        'descuento': 0.0
    }
    st.session_state.contador_ordenes += 1
    st.session_state.orden_activa = orden_id
    return orden_id

def mostrar_punto_venta():
    """Página principal del punto de venta con múltiples órdenes"""
    st.title("🛒 Punto de Venta - Sistema Multi-Orden")
    
    # Aplicar estilos personalizados
    aplicar_estilos_ordenes()
    
    # Inicializar sistema de órdenes múltiples
    inicializar_ordenes_multiples()
    initialize_session_state()
    
    # Verificar si hay una venta procesada para mostrar opciones post-venta
    if st.session_state.get('venta_procesada') and st.session_state.get('show_ticket'):
        mostrar_opciones_post_venta(st.session_state.venta_procesada)
        return
    
    # Panel de configuración de venta (expandible)
    with st.expander("⚙️ Configuración General", expanded=False):
        configurar_venta_avanzada()
    
    # Sistema de órdenes múltiples
    mostrar_gestor_ordenes()
    
    # Layout principal
    if st.session_state.orden_activa:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            mostrar_productos()
        
        with col2:
            mostrar_carrito_orden_activa()
    else:
        st.markdown("""
        <div class="custom-info">
            <h4>🎯 Sistema de Órdenes Múltiples</h4>
            <p>👆 Selecciona una orden existente o crea una nueva para comenzar a agregar productos</p>
            <p>💡 <strong>Ventajas:</strong></p>
            <ul>
                <li>Atiende múltiples clientes simultáneamente</li>
                <li>Los clientes pueden agregar productos hasta el último momento</li>
                <li>Mejor organización y flujo de trabajo</li>
                <li>Reduce tiempos de espera</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def mostrar_gestor_ordenes():
    """Mostrar el gestor de órdenes múltiples"""
    st.markdown("---")
    st.markdown("### 📋 Gestor de Órdenes")
    
    # Botones de gestión
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        if st.button("➕ Nueva Orden", use_container_width=True, type="primary"):
            crear_nueva_orden()
            st.rerun()
    
    with col2:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.session_state.orden_activa and st.button("🗑️ Eliminar Orden Activa", use_container_width=True):
            if st.session_state.orden_activa in st.session_state.ordenes_multiples:
                del st.session_state.ordenes_multiples[st.session_state.orden_activa]
            st.session_state.orden_activa = None
            st.rerun()
    
    with col4:
        if st.button("🧹 Limpiar Todas", use_container_width=True):
            st.session_state.ordenes_multiples = {}
            st.session_state.orden_activa = None
            st.rerun()
    
    # Lista de órdenes activas
    if st.session_state.ordenes_multiples:
        st.markdown("#### 📝 Órdenes Activas:")
        
        # Crear tarjetas de órdenes
        cols = st.columns(min(len(st.session_state.ordenes_multiples), 4))
        
        for idx, (orden_id, orden) in enumerate(st.session_state.ordenes_multiples.items()):
            col_idx = idx % 4
            with cols[col_idx]:
                # Determinar el estado y estilos
                es_activa = orden_id == st.session_state.orden_activa
                total_items = orden['carrito'].cantidad_items
                total_precio = orden['carrito'].total
                estado_clase = "activa" if es_activa else ""
                
                # Tarjeta de orden mejorada
                st.markdown(f"""
                <div class="orden-card {estado_clase}">
                    <div style="text-align: center;">
                        <h3 style="margin: 0; color: {'#dc3545' if es_activa else '#495057'};">
                            {'🎯' if es_activa else '📋'} {orden_id}
                        </h3>
                        <div style="margin: 15px 0;">
                            <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                                <span><strong>Items:</strong></span>
                                <span style="color: #007bff; font-weight: bold;">{total_items}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                                <span><strong>Total:</strong></span>
                                <span style="color: #28a745; font-weight: bold; font-size: 18px;">${total_precio:.2f}</span>
                            </div>
                            <div style="margin: 10px 0;">
                                <span class="estado-badge estado-{'completada' if orden['estado'] == 'Completada' else 'proceso'}">
                                    {orden['estado']}
                                </span>
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #6c757d;">
                            {orden['fecha_creacion'].strftime('%H:%M:%S')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botones de acción
                if st.button(f"{'✅ Activa' if es_activa else '👆 Seleccionar'}", 
                           key=f"select_{orden_id}", 
                           use_container_width=True,
                           disabled=es_activa):
                    st.session_state.orden_activa = orden_id
                    st.rerun()
                
                if total_items > 0:
                    if st.button(f"💳 Pagar", key=f"pay_{orden_id}", use_container_width=True, type="primary"):
                        st.session_state.orden_a_pagar = orden_id
                        st.rerun()
        
        # Panel de pago si hay una orden seleccionada para pagar
        if 'orden_a_pagar' in st.session_state and st.session_state.orden_a_pagar:
            mostrar_panel_pago(st.session_state.orden_a_pagar)
    
    else:
        st.info("💡 No hay órdenes activas. Crea una nueva orden para comenzar.")
    
    st.markdown("---")

def configurar_venta_avanzada():
    """Panel de configuración avanzada para la venta"""
    st.markdown("### 📅 Configuración de Fecha y Vendedor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Permitir cambiar la fecha de la venta
        fecha_venta = st.date_input(
            "📅 Fecha de la venta:",
            value=get_mexico_datetime().date(),
            help="Puedes cambiar la fecha para registrar ventas de días anteriores"
        )
        st.session_state.fecha_venta_personalizada = fecha_venta
    
    with col2:
        # Selector de vendedor
        vendedores = Vendedor.get_nombres_activos()
        if vendedores:
            vendedor_actual = st.session_state.get('vendedor_seleccionado', vendedores[0])
            vendedor = st.selectbox(
                "👤 Vendedor:",
                vendedores,
                index=vendedores.index(vendedor_actual) if vendedor_actual in vendedores else 0
            )
            st.session_state.vendedor_seleccionado = vendedor
        else:
            st.warning("⚠️ No hay vendedores configurados")
            st.session_state.vendedor_seleccionado = "Sistema"
    
    # Información adicional
    if st.session_state.get('fecha_venta_personalizada') != get_mexico_datetime().date():
        st.info(f"📌 La venta se registrará con fecha: **{st.session_state.fecha_venta_personalizada}**")
    
    # Opción de descuento rápido
    col1, col2 = st.columns(2)
    
    with col1:
        descuento_rapido = st.number_input(
            "💰 Descuento rápido ($):",
            min_value=0.0,
            value=0.0,
            step=1.0,
            help="Aplicar descuento directo a la venta"
        )
        st.session_state.descuento_rapido = descuento_rapido
    
    with col2:
        # Observaciones rápidas
        observaciones = st.text_input(
            "📝 Observaciones:",
            placeholder="Notas sobre la venta...",
            help="Comentarios adicionales para la venta"
        )
        st.session_state.observaciones_venta = observaciones

def mostrar_productos():
    """Muestra los productos disponibles con botones grandes"""
    if not st.session_state.orden_activa:
        st.warning("⚠️ Selecciona una orden activa para agregar productos")
        return
    
    st.subheader(f"📦 Productos Disponibles - {st.session_state.orden_activa}")
    
    # Filtro por categoría
    categorias = Categoria.get_nombres_categoria()
    categoria_names = ["Todas"] + categorias
    
    categoria_seleccionada = st.selectbox(
        "Filtrar por categoría:",
        categoria_names,
        key="categoria_filter"
    )
    
    # Obtener productos
    if categoria_seleccionada == "Todas":
        productos = Producto.get_all()
    else:
        productos = Producto.get_by_categoria(categoria_seleccionada)
    
    if not productos:
        st.info("No hay productos disponibles en esta categoría")
        return
    
    # Mostrar productos en grid
    cols = st.columns(3)  # 3 columnas de productos
    
    for idx, producto in enumerate(productos):
        with cols[idx % 3]:
            # Crear botón grande para cada producto
            if producto.stock > 0:
                button_text = format_product_display(
                    producto.nombre, 
                    producto.precio, 
                    producto.stock
                )
                
                if st.button(
                    button_text,
                    key=f"producto_{producto.id}",
                    use_container_width=True,
                    type="primary" if producto.stock > 5 else "secondary"
                ):
                    # Agregar al carrito de la orden activa
                    orden_activa = st.session_state.ordenes_multiples[st.session_state.orden_activa]
                    orden_activa['carrito'].agregar_producto(producto)
                    show_success_message(f"✅ {producto.nombre} agregado a {st.session_state.orden_activa}")
                    # Solo rerun cuando es necesario y resetear estado de venta
                    if st.session_state.get('venta_procesada'):
                        reset_venta_state()
                    st.rerun()
            else:
                # Producto sin stock
                st.button(
                    f"❌ {producto.nombre}\nSIN STOCK",
                    key=f"producto_sin_stock_{producto.id}",
                    use_container_width=True,
                    disabled=True
                )

def mostrar_carrito():
    """Muestra el carrito de compras"""
    st.subheader("🛍️ Carrito de Compras")
    
    carrito = st.session_state.carrito
    
    if not carrito.items:
        st.info("El carrito está vacío")
        return
    
    # Mostrar items del carrito
    for item in carrito.items:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{item.producto.nombre}**")
                st.write(f"Precio: {format_currency(item.producto.precio)}")
            
            with col2:
                # Control de cantidad
                nueva_cantidad = st.number_input(
                    "Cant:",
                    min_value=1,
                    max_value=item.producto.stock,
                    value=item.cantidad,
                    key=f"cantidad_{item.producto.id}"
                )
                
                if nueva_cantidad != item.cantidad:
                    carrito.actualizar_cantidad(item.producto.id, nueva_cantidad)
                    st.rerun()
            
            with col3:
                st.write(f"**{format_currency(item.subtotal)}**")
                
                if st.button("🗑️", key=f"eliminar_{item.producto.id}"):
                    carrito.eliminar_producto(item.producto.id)
                    show_success_message("Producto eliminado del carrito")
                    st.rerun()
        
        st.divider()
    
    # Total del carrito
    st.markdown(f"### Total: {format_currency(carrito.total)}")
    
    # Botones de acción
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpiar Carrito", use_container_width=True):
            carrito.limpiar()
            show_success_message("Carrito limpiado")
            st.rerun()
    
    with col2:
        if st.button("💳 Procesar Venta", use_container_width=True, type="primary"):
            st.session_state.show_form_venta = True
            st.rerun()
    
    # Mostrar formulario de venta si está activado
    if st.session_state.get('show_form_venta', False):
        mostrar_formulario_venta()

def mostrar_formulario_venta():
    """Muestra el formulario para procesar la venta"""
    # Solo mostrar si está habilitado
    if not st.session_state.get('show_form_venta', False):
        return
        
    st.subheader("💳 Procesar Venta")
    
    carrito = st.session_state.carrito
    
    # Manejo de vendedores FUERA del formulario
    vendedores_existentes = Vendedor.get_nombres_activos()
    
    # Verificar si se necesita agregar un nuevo vendedor
    if st.session_state.get('agregar_nuevo_vendedor', False):
        st.write("**Agregar Nuevo Vendedor:**")
        nuevo_vendedor = st.text_input(
            "Nombre del nuevo vendedor:",
            key="nuevo_vendedor_input_form"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Vendedor", key="confirm_vendedor_btn"):
                if nuevo_vendedor and nuevo_vendedor.strip():
                    try:
                        vendedor_obj = Vendedor(nombre=nuevo_vendedor.strip())
                        vendedor_obj.save()
                        show_success_message(f"Vendedor '{nuevo_vendedor}' agregado exitosamente")
                        st.session_state.agregar_nuevo_vendedor = False
                        st.session_state.vendedor_seleccionado = nuevo_vendedor.strip()
                        st.rerun()
                    except Exception as e:
                        show_error_message(f"Error al agregar vendedor: {str(e)}")
                else:
                    show_error_message("Por favor ingresa un nombre válido")
        
        with col2:
            if st.button("❌ Cancelar", key="cancel_vendedor_btn"):
                st.session_state.agregar_nuevo_vendedor = False
                st.rerun()
    
    with st.form("formulario_venta"):
        # Método de pago
        metodo_pago = st.selectbox(
            "Método de pago:",
            ["Efectivo", "Tarjeta", "Transferencia", "QR"]
        )
        
        # Vendedor - menú desplegable con opción de agregar
        vendedores_opciones = vendedores_existentes + ["+ Agregar nuevo vendedor"]
        
        # Usar el vendedor seleccionado previamente si existe
        vendedor_default = st.session_state.get('vendedor_seleccionado', vendedores_opciones[0])
        if vendedor_default not in vendedores_opciones:
            vendedores_opciones.insert(-1, vendedor_default)
        
        vendedor_seleccionado = st.selectbox(
            "Vendedor:",
            vendedores_opciones,
            key="vendedor_select_form",
            index=vendedores_opciones.index(vendedor_default) if vendedor_default in vendedores_opciones else 0
        )
        
        # Si selecciona agregar nuevo vendedor, mostrar el formulario correspondiente
        if vendedor_seleccionado == "+ Agregar nuevo vendedor":
            st.info("👆 Para agregar un nuevo vendedor, confirma este formulario primero y luego usa la opción que aparecerá arriba.")
            vendedor_final = ""
        else:
            vendedor_final = vendedor_seleccionado
        
        # Observaciones - usar las del estado de sesión si existen
        observaciones_default = st.session_state.get('observaciones_venta', '')
        observaciones = st.text_area(
            "Observaciones (opcional):",
            value=observaciones_default,
            help="Se aplicarán las observaciones de la configuración avanzada si están definidas"
        )
        
        # Descuento - combinar descuento rápido con descuento por porcentaje
        descuento_rapido = st.session_state.get('descuento_rapido', 0.0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            descuento_porcentaje = st.number_input(
                "Descuento (%):",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5
            )
        
        with col2:
            descuento_adicional = st.number_input(
                "Descuento adicional ($):",
                min_value=0.0,
                value=descuento_rapido,
                step=1.0,
                help="Se suma al descuento configurado en la sección avanzada"
            )
        
        # Calcular totales
        subtotal = carrito.total
        descuento_porcentaje_monto = subtotal * (descuento_porcentaje / 100)
        descuento_total = descuento_porcentaje_monto + descuento_adicional
        total_final = subtotal - descuento_total
        
        # Validar que el total no sea negativo
        if total_final < 0:
            total_final = 0
            descuento_total = subtotal
        
        st.write(f"**Subtotal:** {format_currency(subtotal)}")
        if descuento_porcentaje_monto > 0:
            st.write(f"**Descuento (%):** -{format_currency(descuento_porcentaje_monto)}")
        if descuento_adicional > 0:
            st.write(f"**Descuento adicional:** -{format_currency(descuento_adicional)}")
        if descuento_total > 0:
            st.write(f"**Descuento total:** -{format_currency(descuento_total)}")
        st.write(f"**Total Final:** {format_currency(total_final)}")
        
        # Mostrar información de fecha personalizada si aplica
        fecha_personalizada = st.session_state.get('fecha_venta_personalizada')
        if fecha_personalizada and fecha_personalizada != get_mexico_datetime().date():
            st.info(f"📅 Esta venta se registrará con fecha: **{fecha_personalizada}**")
        
        # Botón procesar
        submit_venta = st.form_submit_button("✅ Confirmar Venta", type="primary")
        submit_agregar_vendedor = st.form_submit_button("👤 Necesito agregar vendedor") if vendedor_seleccionado == "+ Agregar nuevo vendedor" else False
    
    # Manejar envío del formulario FUERA del form
    if submit_agregar_vendedor:
        st.session_state.agregar_nuevo_vendedor = True
        st.rerun()
    
    if submit_venta:
        try:
            # Validar que hay items en el carrito
            if not carrito.items:
                show_error_message("El carrito está vacío")
                return
            
            # Validar vendedor
            if not vendedor_final:
                show_error_message("Por favor selecciona un vendedor válido")
                return
            
            # Procesar la venta con fecha personalizada
            fecha_venta = st.session_state.get('fecha_venta_personalizada')
            if fecha_venta:
                from datetime import datetime, time
                fecha_completa = datetime.combine(fecha_venta, time())
            else:
                fecha_completa = None
            
            venta = carrito.procesar_venta(
                metodo_pago=metodo_pago,
                vendedor=vendedor_final,
                observaciones=observaciones,
                fecha_personalizada=fecha_completa
            )
            
            if venta:
                # Aplicar descuento si existe
                if descuento_total > 0:
                    from database.connection import execute_update
                    execute_update(
                        "UPDATE ventas SET total = %s, descuento = %s WHERE id = %s",
                        (total_final, descuento_total, venta.id)
                    )
                    venta.total = total_final
                    venta.descuento = descuento_total
                
                # Guardar en session state
                st.session_state.venta_procesada = venta
                st.session_state.show_ticket = True
                st.session_state.show_form_venta = False  # Ocultar formulario
                st.session_state.agregar_nuevo_vendedor = False  # Reset flag
                
                show_success_message(f"¡Venta #{venta.id} procesada exitosamente!")
                st.balloons()
                st.rerun()
            else:
                show_error_message("Error al procesar la venta")
                
        except Exception as e:
            show_error_message(f"Error al procesar la venta: {str(e)}")
    
    # Botón para cancelar (fuera del form también)
    if st.button("❌ Cancelar Venta", key="cancel_venta_btn"):
        st.session_state.show_form_venta = False
        st.session_state.agregar_nuevo_vendedor = False
        st.rerun()

def mostrar_opciones_post_venta(venta):
    """Muestra opciones después de procesar una venta"""
    st.success(f"✅ Venta #{venta.id} procesada exitosamente!")
    
    # Mostrar opciones
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Generar y descargar ticket directamente en memoria
        if st.button("📥 Descargar Ticket", use_container_width=True):
            try:
                with st.spinner("Generando ticket..."):
                    generator = TicketGenerator()
                    pdf_bytes = generator.generar_ticket_memoria(venta)
                    
                    st.download_button(
                        label="📥 Ticket Generado - Hacer clic para descargar",
                        data=pdf_bytes,
                        file_name=f"ticket_{venta.id}_{get_mexico_datetime().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    show_success_message("¡Ticket generado exitosamente! Haz clic en el botón de descarga.")
                    
            except Exception as e:
                show_error_message(f"Error al generar ticket: {str(e)}")
    
    with col2:
        if st.button("🛒 Nueva Venta", use_container_width=True):
            # Limpiar estados relacionados con tickets
            for key in ['ticket_generado', 'ruta_ticket']:
                if key in st.session_state:
                    del st.session_state[key]
            reset_venta_state()
            st.rerun()
    
    with col3:
        if st.button("📊 Ver Dashboard", use_container_width=True):
            st.session_state.selected_page = "Dashboard"
            st.rerun()

def mostrar_carrito_orden_activa():
    """Mostrar carrito de la orden activa"""
    if not st.session_state.orden_activa:
        return
    
    orden = st.session_state.ordenes_multiples[st.session_state.orden_activa]
    carrito = orden['carrito']
    
    st.markdown(f"### 🛒 {orden['id']}")
    st.markdown(f"**Estado:** {orden['estado']}")
    
    # Información de la orden
    with st.expander("ℹ️ Información de la Orden", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            orden['cliente'] = st.text_input("👤 Cliente:", value=orden['cliente'], key=f"cliente_{orden['id']}")
            orden['vendedor'] = st.text_input("👨‍💼 Vendedor:", value=orden['vendedor'], key=f"vendedor_{orden['id']}")
        with col2:
            orden['metodo_pago'] = st.selectbox("💳 Método de Pago:", 
                                              ["Efectivo", "Tarjeta", "Transferencia"], 
                                              index=["Efectivo", "Tarjeta", "Transferencia"].index(orden['metodo_pago']),
                                              key=f"metodo_{orden['id']}")
            orden['descuento'] = st.number_input("💰 Descuento (%):", 
                                               min_value=0.0, max_value=100.0, 
                                               value=orden['descuento'], step=1.0,
                                               key=f"descuento_{orden['id']}")
        orden['observaciones'] = st.text_area("📝 Observaciones:", value=orden['observaciones'], key=f"obs_{orden['id']}")
    
    # Mostrar items del carrito
    if carrito.items:
        st.markdown("#### 📦 Productos en la orden:")
        
        for idx, item in enumerate(carrito.items):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{item.nombre}**")
            with col2:
                nueva_cantidad = st.number_input("Cant.", min_value=1, value=item.cantidad, 
                                               key=f"cant_{orden['id']}_{idx}")
                if nueva_cantidad != item.cantidad:
                    item.cantidad = nueva_cantidad
                    item.subtotal = nueva_cantidad * item.precio
            with col3:
                nuevo_precio = st.number_input("Precio", min_value=0.01, value=item.precio, 
                                             step=0.01, key=f"precio_{orden['id']}_{idx}")
                if nuevo_precio != item.precio:
                    item.precio = nuevo_precio
                    item.subtotal = item.cantidad * nuevo_precio
            with col4:
                st.write(f"${item.subtotal:.2f}")
            with col5:
                if st.button("🗑️", key=f"del_{orden['id']}_{idx}"):
                    carrito.items.pop(idx)
                    st.rerun()
        
        # Totales
        st.markdown("---")
        subtotal = carrito.total
        descuento_amount = subtotal * (orden['descuento'] / 100)
        total_final = subtotal - descuento_amount
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Subtotal:** ${subtotal:.2f}")
            if orden['descuento'] > 0:
                st.markdown(f"**Descuento ({orden['descuento']}%):** -${descuento_amount:.2f}")
        with col2:
            st.markdown(f"**TOTAL:** ${total_final:.2f}")
        
        # Botón de pago
        if st.button(f"💳 Procesar Pago - ${total_final:.2f}", 
                    use_container_width=True, type="primary",
                    key=f"pago_directo_{orden['id']}"):
            st.session_state.orden_a_pagar = orden['id']
            st.rerun()
    
    else:
        st.info("🛒 Carrito vacío. Agrega productos desde el catálogo.")

def mostrar_panel_pago(orden_id):
    """Mostrar panel de pago para una orden específica"""
    orden = st.session_state.ordenes_multiples[orden_id]
    carrito = orden['carrito']
    
    st.markdown("---")
    st.markdown(f"### 💳 Procesando Pago - {orden_id}")
    
    # Resumen de la orden
    subtotal = carrito.total
    descuento_amount = subtotal * (orden['descuento'] / 100)
    total_final = subtotal - descuento_amount
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📋 Resumen del Pedido:")
        st.write(f"**Cliente:** {orden['cliente'] or 'Cliente general'}")
        st.write(f"**Vendedor:** {orden['vendedor'] or 'Sin especificar'}")
        st.write(f"**Método de Pago:** {orden['metodo_pago']}")
        st.write(f"**Items:** {carrito.cantidad_items}")
        
        st.markdown("#### 💰 Totales:")
        st.write(f"**Subtotal:** ${subtotal:.2f}")
        if orden['descuento'] > 0:
            st.write(f"**Descuento ({orden['descuento']}%):** -${descuento_amount:.2f}")
        st.write(f"**TOTAL A PAGAR:** ${total_final:.2f}")
    
    with col2:
        st.markdown("#### 🎯 Confirmar Pago:")
        
        # Fecha de la venta
        fecha_venta = st.date_input("📅 Fecha de la venta:", 
                                   value=get_mexico_datetime().date(),
                                   key=f"fecha_pago_{orden_id}")
        
        # Observaciones finales
        obs_finales = st.text_area("📝 Observaciones finales:", 
                                  value=orden['observaciones'],
                                  key=f"obs_finales_{orden_id}")
        
        # Botones de acción
        col_cancel, col_confirm = st.columns(2)
        
        with col_cancel:
            if st.button("❌ Cancelar", use_container_width=True):
                if 'orden_a_pagar' in st.session_state:
                    del st.session_state.orden_a_pagar
                st.rerun()
        
        with col_confirm:
            if st.button("✅ Confirmar Pago", use_container_width=True, type="primary"):
                procesar_pago_orden(orden_id, fecha_venta, obs_finales)

def procesar_pago_orden(orden_id, fecha_venta, observaciones_finales):
    """Procesar el pago de una orden específica"""
    try:
        orden = st.session_state.ordenes_multiples[orden_id]
        carrito = orden['carrito']
        
        if not carrito.items:
            st.error("❌ No hay productos en la orden")
            return
        
        # Preparar datos para la venta
        from datetime import datetime, time
        fecha_venta_completa = datetime.combine(fecha_venta, time())
        
        # Procesar venta usando el carrito
        venta = carrito.procesar_venta(
            metodo_pago=orden['metodo_pago'],
            vendedor=orden['vendedor'] or "Vendedor",
            observaciones=observaciones_finales,
            fecha_personalizada=fecha_venta_completa
        )
        
        if venta:
            # Actualizar estado de la orden
            orden['estado'] = 'Completada'
            
            # Guardar información de la venta procesada
            st.session_state.venta_procesada = venta
            st.session_state.show_ticket = True
            
            # Limpiar orden de pago
            if 'orden_a_pagar' in st.session_state:
                del st.session_state.orden_a_pagar
            
            # Remover la orden completada de las órdenes activas
            if orden_id in st.session_state.ordenes_multiples:
                del st.session_state.ordenes_multiples[orden_id]
            
            # Si era la orden activa, limpiar
            if st.session_state.orden_activa == orden_id:
                st.session_state.orden_activa = None
            
            st.success(f"✅ Venta procesada exitosamente - Orden {orden_id}")
            st.rerun()
        else:
            st.error("❌ Error al procesar la venta")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el pago: {str(e)}")

def aplicar_estilos_ordenes():
    """Aplicar estilos CSS personalizados para el sistema de órdenes"""
    st.markdown("""
    <style>
    /* Estilos para tarjetas de órdenes */
    .orden-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .orden-card.activa {
        border-color: #dc3545;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%);
        box-shadow: 0 6px 12px rgba(220,53,69,0.2);
    }
    
    .orden-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
    }
    
    /* Botones de productos mejorados */
    .stButton > button {
        border-radius: 10px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        height: 80px !important;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Mejoras para el panel de órdenes */
    .orden-header {
        background: linear-gradient(90deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Separadores mejorados */
    .orden-separator {
        height: 3px;
        background: linear-gradient(90deg, #007bff 0%, #28a745 50%, #dc3545 100%);
        border-radius: 3px;
        margin: 20px 0;
    }
    
    /* Alertas personalizadas */
    .custom-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2196f3;
        margin: 10px 0;
    }
    
    /* Badges de estado */
    .estado-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .estado-proceso {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .estado-completada {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    </style>
    """, unsafe_allow_html=True)

# Función principal para ejecutar la página
def main():
    aplicar_estilos_ordenes()
    mostrar_punto_venta()

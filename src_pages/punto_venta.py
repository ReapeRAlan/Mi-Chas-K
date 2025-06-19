"""
Página principal del punto de venta
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

def mostrar_punto_venta():
    """Página principal del punto de venta"""
    st.title("🛒 Punto de Venta")
    
    # Inicializar estado de sesión
    initialize_session_state()
    
    # Panel de configuración de venta (expandible)
    with st.expander("⚙️ Configuración de Venta", expanded=False):
        configurar_venta_avanzada()
    
    # Verificar si hay una venta procesada para mostrar opciones post-venta
    if st.session_state.get('venta_procesada') and st.session_state.get('show_ticket'):
        mostrar_opciones_post_venta(st.session_state.venta_procesada)
        return
    
    # Layout de dos columnas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mostrar_productos()
    
    with col2:
        mostrar_carrito()

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
    st.subheader("📦 Productos Disponibles")
    
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
                    # Agregar al carrito
                    st.session_state.carrito.agregar_producto(producto)
                    show_success_message(f"✅ {producto.nombre} agregado al carrito")
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
            st.switch_page("pages/dashboard.py")

# Función principal para ejecutar la página
def main():
    mostrar_punto_venta()

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

def mostrar_ordenes():
    """Página principal de gestión de órdenes"""
    st.title("📋 Gestión de Órdenes")
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["🔍 Ver Órdenes", "✏️ Modificar Orden"])
    
    with tab1:
        mostrar_lista_ordenes()
    
    with tab2:
        if 'orden_seleccionada' in st.session_state:
            mostrar_modificar_orden()
        else:
            st.info("Selecciona una orden desde la pestaña 'Ver Órdenes' para modificarla")

def mostrar_lista_ordenes():
    """Muestra la lista de órdenes con filtros"""
    st.subheader("🔍 Lista de Órdenes")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_desde = st.date_input(
            "Desde:",
            value=datetime.now().date() - timedelta(days=7)
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Hasta:",
            value=datetime.now().date()
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
                if st.button("✏️ Modificar", key=f"mod_{orden_id}"):
                    st.session_state.orden_seleccionada = orden_id
                    st.rerun()
            
            with col3:
                if st.button("🖨️ Reimprimir", key=f"print_{orden_id}"):
                    reimprimir_ticket(orden_id)

def mostrar_detalle_orden(orden_id: int):
    """Muestra el detalle completo de una orden"""
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
    """Permite modificar una orden existente"""
    orden_id = st.session_state.orden_seleccionada
    
    st.subheader(f"✏️ Modificar Orden #{orden_id}")
    
    # Obtener datos actuales
    venta_query = "SELECT * FROM ventas WHERE id = %s"
    venta_data = execute_query(venta_query, (orden_id,))
    
    if not venta_data:
        st.error("No se encontró la orden")
        return
    
    venta = venta_data[0]
    
    # Obtener detalle actual
    detalle_query = """
        SELECT dv.*, p.nombre, p.stock
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = %s
    """
    detalle_data = execute_query(detalle_query, (orden_id,))
    
    # Formulario de modificación
    with st.form(f"modificar_orden_{orden_id}"):
        st.write("### 📝 Información General")
        
        col1, col2 = st.columns(2)
        
        with col1:
            vendedores = Vendedor.get_nombres_activos()
            vendedor_actual = venta['vendedor'] if venta['vendedor'] in vendedores else vendedores[0] if vendedores else ""
            nuevo_vendedor = st.selectbox(
                "Vendedor:",
                vendedores,
                index=vendedores.index(vendedor_actual) if vendedor_actual in vendedores else 0
            )
            
            metodos_pago = ["Efectivo", "Tarjeta", "Transferencia", "Mixto"]
            metodo_actual = venta['metodo_pago']
            nuevo_metodo = st.selectbox(
                "Método de Pago:",
                metodos_pago,
                index=metodos_pago.index(metodo_actual) if metodo_actual in metodos_pago else 0
            )
        
        with col2:
            nuevo_descuento = st.number_input(
                "Descuento:",
                min_value=0.0,
                value=float(venta['descuento'] or 0),
                step=0.01
            )
            
            nuevas_observaciones = st.text_area(
                "Observaciones:",
                value=venta['observaciones'] or ""
            )
        
        st.write("### 📦 Productos")
        
        # Mostrar productos actuales con opción de modificar
        productos_modificados = []
        productos_eliminar = []
        
        for i, item in enumerate(detalle_data):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{item['nombre']}**")
                
                with col2:
                    nueva_cantidad = st.number_input(
                        "Cantidad",
                        min_value=0,
                        value=item['cantidad'],
                        key=f"cant_{i}",
                        step=1
                    )
                
                with col3:
                    nuevo_precio = st.number_input(
                        "Precio",
                        min_value=0.0,
                        value=float(item['precio_unitario']),
                        key=f"precio_{i}",
                        step=0.01
                    )
                
                with col4:
                    eliminar = st.checkbox(
                        "Eliminar",
                        key=f"elim_{i}"
                    )
                
                if eliminar:
                    productos_eliminar.append(item['id'])
                elif nueva_cantidad > 0:
                    productos_modificados.append({
                        'id': item['id'],
                        'producto_id': item['producto_id'],
                        'cantidad_original': item['cantidad'],
                        'cantidad_nueva': nueva_cantidad,
                        'precio_original': float(item['precio_unitario']),
                        'precio_nuevo': nuevo_precio,
                        'stock_disponible': item['stock']
                    })
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_modificar = st.form_submit_button("💾 Guardar Cambios", type="primary")
        
        with col2:
            submit_reimprimir = st.form_submit_button("🖨️ Guardar y Reimprimir")
        
        with col3:
            if st.form_submit_button("❌ Cancelar"):
                del st.session_state.orden_seleccionada
                st.rerun()
    
    # Procesar modificaciones
    if submit_modificar or submit_reimprimir:
        try:
            # Calcular nuevo total
            nuevo_total = 0
            
            # Actualizar stock por productos eliminados
            for detalle_id in productos_eliminar:
                # Obtener info del detalle para devolver stock
                detalle_info = execute_query(
                    "SELECT producto_id, cantidad FROM detalle_ventas WHERE id = %s",
                    (detalle_id,)
                )
                if detalle_info:
                    producto_id = detalle_info[0]['producto_id']
                    cantidad_devolver = detalle_info[0]['cantidad']
                    
                    # Devolver stock al producto
                    execute_update(
                        "UPDATE productos SET stock = stock + %s WHERE id = %s",
                        (cantidad_devolver, producto_id)
                    )
                
                # Eliminar detalle
                execute_update("DELETE FROM detalle_ventas WHERE id = %s", (detalle_id,))
            
            # Actualizar productos modificados
            for prod in productos_modificados:
                diferencia_cantidad = prod['cantidad_nueva'] - prod['cantidad_original']
                nuevo_subtotal = prod['cantidad_nueva'] * prod['precio_nuevo']
                nuevo_total += nuevo_subtotal
                
                # Verificar stock suficiente si aumentó la cantidad
                if diferencia_cantidad > 0 and diferencia_cantidad > prod['stock_disponible']:
                    st.error(f"Stock insuficiente para el producto. Disponible: {prod['stock_disponible']}")
                    return
                
                # Actualizar detalle de venta
                execute_update("""
                    UPDATE detalle_ventas 
                    SET cantidad = %s, precio_unitario = %s, subtotal = %s
                    WHERE id = %s
                """, (prod['cantidad_nueva'], prod['precio_nuevo'], nuevo_subtotal, prod['id']))
                
                # Actualizar stock del producto
                execute_update(
                    "UPDATE productos SET stock = stock - %s WHERE id = %s",
                    (diferencia_cantidad, prod['producto_id'])
                )
            
            # Actualizar venta principal
            execute_update("""
                UPDATE ventas 
                SET total = %s, metodo_pago = %s, descuento = %s, 
                    vendedor = %s, observaciones = %s
                WHERE id = %s
            """, (nuevo_total - nuevo_descuento, nuevo_metodo, nuevo_descuento, 
                  nuevo_vendedor, nuevas_observaciones, orden_id))
            
            st.success("✅ Orden modificada exitosamente")
            
            # Reimprimir si se solicitó
            if submit_reimprimir:
                reimprimir_ticket(orden_id)
            
            # Limpiar selección
            del st.session_state.orden_seleccionada
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al modificar la orden: {str(e)}")

def reimprimir_ticket(orden_id: int):
    """Reimprime el ticket de una orden"""
    try:
        # Obtener datos de la venta
        venta_data = execute_query("SELECT * FROM ventas WHERE id = %s", (orden_id,))
        if not venta_data:
            st.error("No se encontró la orden")
            return
        
        venta = venta_data[0]
        
        # Obtener detalle
        detalle_data = execute_query("""
            SELECT dv.*, p.nombre 
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
        """, (orden_id,))
        
        # Generar ticket
        ticket_gen = TicketGenerator()
        
        # Simular objetos para el generador
        class MockVenta:
            def __init__(self, data):
                self.id = data['id']
                self.total = float(data['total'])
                self.metodo_pago = data['metodo_pago']
                self.fecha = data['fecha']
                self.vendedor = data['vendedor']
                self.observaciones = data['observaciones']
                self.descuento = float(data['descuento'] or 0)
        
        class MockItem:
            def __init__(self, data):
                self.producto = type('obj', (object,), {'nombre': data['nombre']})
                self.cantidad = data['cantidad']
                self.subtotal = float(data['subtotal'])
        
        mock_venta = MockVenta(venta)
        mock_items = [MockItem(item) for item in detalle_data]
        
        # Generar PDF
        pdf_path = ticket_gen.generar_ticket(mock_venta, mock_items)
        
        # Mostrar enlace de descarga
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📄 Descargar Ticket (Reimpresión)",
                data=pdf_file.read(),
                file_name=f"ticket_orden_{orden_id}_reimpresion.pdf",
                mime="application/pdf"
            )
        
        st.success(f"✅ Ticket de la orden #{orden_id} generado para reimpresión")
        
    except Exception as e:
        st.error(f"Error al generar ticket: {str(e)}")

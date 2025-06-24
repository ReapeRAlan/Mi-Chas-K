"""
Punto de Venta Simplificado
Versión 3.1.0 - Con Adaptador Compatible
"""
import streamlit as st
from datetime import datetime
from database.connection_adapter import execute_query, execute_update

def mostrar_punto_venta_simple():
    """Interfaz simplificada del punto de venta"""
    
    # Header
    st.title("🛒 Punto de Venta")
    
    # Botón volver
    if st.button("← Volver al inicio"):
        st.session_state.page = 'main'
        st.rerun()
    
    # Inicializar carrito
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📦 Productos Disponibles")
        
        # Obtener productos
        productos = execute_query("""
            SELECT p.*, p.categoria as categoria_nombre 
            FROM productos p 
            WHERE p.activo = 1
            ORDER BY p.nombre
        """)
        
        if not productos:
            st.warning("No hay productos disponibles")
            return
        
        # Mostrar productos en grid
        cols = st.columns(3)
        for i, producto in enumerate(productos):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                        <h4>{producto['nombre']}</h4>
                        <p>Precio: ${producto['precio']:,.2f}</p>
                        <p>Stock: {producto['stock']}</p>
                        <p>Categoría: {producto['categoria_nombre'] or 'Sin categoría'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    cantidad = st.number_input(
                        "Cantidad", 
                        min_value=0, 
                        max_value=producto['stock'], 
                        value=0,
                        key=f"cant_{producto['id']}"
                    )
                    
                    if st.button(f"Agregar", key=f"add_{producto['id']}", use_container_width=True):
                        if cantidad > 0:
                            agregar_al_carrito(producto, cantidad)
                            st.success(f"✅ Agregado: {cantidad}x {producto['nombre']}")
                            st.rerun()
    
    with col2:
        st.subheader("🛍️ Carrito de Compras")
        
        if not st.session_state.carrito:
            st.info("El carrito está vacío")
        else:
            total = 0
            for i, item in enumerate(st.session_state.carrito):
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 0.5rem; border-radius: 5px; margin: 0.25rem 0;">
                        <strong>{item['nombre']}</strong><br>
                        Cantidad: {item['cantidad']}<br>
                        Precio: ${item['precio']:,.2f}<br>
                        Subtotal: ${item['cantidad'] * item['precio']:,.2f}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🗑️", key=f"remove_{i}", help="Eliminar"):
                        st.session_state.carrito.pop(i)
                        st.rerun()
                
                total += item['cantidad'] * item['precio']
            
            st.markdown("---")
            st.markdown(f"### Total: ${total:,.2f}")
            
            # Formulario de venta
            with st.form("form_venta"):
                st.subheader("💳 Finalizar Venta")
                
                vendedor = st.selectbox("Vendedor", ["Sistema", "Vendedor 1"])
                metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta", "Transferencia"])
                observaciones = st.text_area("Observaciones", "")
                
                submitted = st.form_submit_button("✅ Procesar Venta", type="primary")
                
                if submitted:
                    if procesar_venta_simple(total, vendedor, metodo_pago, observaciones):
                        st.success("🎉 ¡Venta procesada exitosamente!")
                        st.session_state.carrito = []
                        st.rerun()
                    else:
                        st.error("❌ Error procesando la venta")

def agregar_al_carrito(producto, cantidad):
    """Agregar producto al carrito"""
    # Verificar si ya existe en el carrito
    for item in st.session_state.carrito:
        if item['id'] == producto['id']:
            item['cantidad'] += cantidad
            return
    
    # Agregar nuevo item
    st.session_state.carrito.append({
        'id': producto['id'],
        'nombre': producto['nombre'],
        'precio': producto['precio'],
        'cantidad': cantidad
    })

def procesar_venta_simple(total, vendedor, metodo_pago, observaciones):
    """Procesar la venta de manera simple"""
    try:
        # Crear venta
        venta_data = {
            'table': 'ventas',
            'operation': 'INSERT',
            'data': {
                'fecha': datetime.now().isoformat(),
                'total': total,
                'metodo_pago': metodo_pago,
                'vendedor': vendedor,
                'observaciones': observaciones,
                'descuento': 0.0
            }
        }
        
        venta_id = execute_update("""
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones, descuento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now(), total, metodo_pago, vendedor, observaciones, 0.0), venta_data)
        
        if not venta_id:
            return False
        
        # Agregar items de venta
        for item in st.session_state.carrito:
            item_data = {
                'table': 'detalle_ventas',
                'operation': 'INSERT',
                'data': {
                    'venta_id': venta_id,
                    'producto_id': item['id'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio']
                }
            }
            
            execute_update("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (venta_id, item['id'], item['cantidad'], item['precio']), item_data)
            
            # Actualizar stock
            stock_data = {
                'table': 'productos',
                'operation': 'UPDATE',
                'data': {
                    'id': item['id'],
                    'stock': f"stock - {item['cantidad']}"
                }
            }
            
            execute_update("""
                UPDATE productos SET stock = stock - ? WHERE id = ?
            """, (item['cantidad'], item['id']), stock_data)
        
        return True
        
    except Exception as e:
        st.error(f"Error: {e}")
        return False

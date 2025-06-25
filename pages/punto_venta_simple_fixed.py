"""
Punto de Venta Simplificado - Versión Funcional
"""
import streamlit as st
from datetime import datetime

def show_punto_venta(adapter):
    """Interfaz simplificada del punto de venta"""
    
    st.title("🛒 Punto de Venta")
    
    # Inicializar carrito
    if 'carrito' not in st.session_state:
        st.session_state.carrito = []

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📦 Productos Disponibles")
        
        # Obtener productos
        try:
            productos = adapter.execute_query("""
                SELECT * FROM productos WHERE activo = 1 ORDER BY nombre
            """)
            
            if productos:
                for producto in productos:
                    with st.expander(f"📦 {producto['nombre']} - ${producto['precio']:.2f}"):
                        col_info, col_action = st.columns([2, 1])
                        
                        with col_info:
                            st.write(f"**Precio:** ${producto['precio']:.2f}")
                            st.write(f"**Stock:** {producto.get('stock', 0)}")
                            st.write(f"**Categoría:** {producto.get('categoria', 'General')}")
                        
                        with col_action:
                            cantidad = st.number_input(
                                "Cantidad", 
                                min_value=1, 
                                value=1, 
                                key=f"qty_{producto['id']}"
                            )
                            if st.button("🛒 Agregar", key=f"add_{producto['id']}"):
                                agregar_al_carrito(producto, cantidad)
                                st.success(f"✅ {producto['nombre']} agregado!")
                                st.rerun()
            else:
                st.info("No hay productos disponibles")
                
        except Exception as e:
            st.error(f"Error cargando productos: {e}")
    
    with col2:
        st.subheader("🛒 Carrito de Compras")
        
        if st.session_state.carrito:
            total = 0
            for i, item in enumerate(st.session_state.carrito):
                with st.container():
                    st.write(f"**{item['nombre']}**")
                    st.write(f"Cantidad: {item['cantidad']}")
                    st.write(f"Precio: ${item['precio']:.2f}")
                    subtotal = item['cantidad'] * item['precio']
                    st.write(f"Subtotal: ${subtotal:.2f}")
                    
                    if st.button("🗑️ Quitar", key=f"remove_{i}"):
                        st.session_state.carrito.pop(i)
                        st.rerun()
                    
                    st.divider()
                    total += subtotal
            
            st.subheader(f"💰 Total: ${total:.2f}")
            
            # Procesar venta
            with st.form("procesar_venta"):
                vendedor = st.text_input("👤 Vendedor", value="Sistema")
                metodo_pago = st.selectbox(
                    "💳 Método de Pago",
                    ["Efectivo", "Tarjeta", "Transferencia"]
                )
                observaciones = st.text_area("📝 Observaciones", "")
                
                if st.form_submit_button("💰 Procesar Venta", type="primary"):
                    if procesar_venta_simple(adapter, total, vendedor, metodo_pago, observaciones):
                        st.success("✅ Venta procesada exitosamente!")
                        st.session_state.carrito = []
                        st.rerun()
        else:
            st.info("🛒 Carrito vacío")
            st.write("Agrega productos desde la izquierda")

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

def procesar_venta_simple(adapter, total, vendedor, metodo_pago, observaciones):
    """Procesar la venta de manera simple"""
    try:
        # Crear venta
        venta_id = adapter.execute_update("""
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones, descuento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now(), total, metodo_pago, vendedor, observaciones, 0.0))
        
        if not venta_id:
            return False
        
        # Agregar items de venta
        for item in st.session_state.carrito:
            subtotal = item['cantidad'] * item['precio']
            
            adapter.execute_update("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (venta_id, item['id'], item['cantidad'], item['precio'], subtotal))
            
            # Actualizar stock si existe la columna
            try:
                adapter.execute_update("""
                    UPDATE productos SET stock = stock - ? WHERE id = ?
                """, (item['cantidad'], item['id']))
            except:
                pass  # Si no existe columna stock, continuar
        
        # FORZAR SINCRONIZACIÓN INMEDIATA después de venta crítica
        try:
            if hasattr(adapter, 'force_sync_now'):
                adapter.force_sync_now()
                st.success("🔄 Venta sincronizada exitosamente")
            elif hasattr(adapter, 'force_sync'):
                adapter.force_sync()
                st.success("🔄 Sincronización iniciada")
        except Exception as sync_error:
            st.warning(f"⚠️ Venta guardada pero error en sincronización: {sync_error}")
        
        return True
        
    except Exception as e:
        st.error(f"Error: {e}")
        return False

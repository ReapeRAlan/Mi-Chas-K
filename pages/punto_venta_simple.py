"""
Punto de Venta Simplificado - Versión Funcional Corregida
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
            
            # Obtener lista de vendedores
            try:
                vendedores_query = adapter.execute_query("SELECT nombre FROM vendedores WHERE activo = 1")
                vendedores_options = [v['nombre'] for v in vendedores_query] if vendedores_query else ["Sistema", "Vendedor 1"]
            except:
                vendedores_options = ["Sistema", "Vendedor 1"]
            
            # Procesar venta
            with st.form("procesar_venta"):
                vendedor = st.selectbox("👤 Vendedor", vendedores_options)
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
    """Procesar la venta de manera simple y robusta"""
    try:
        # Crear venta principal con datos correctos
        venta_data = {
            'fecha': datetime.now().isoformat(),  # Convertir a string para JSON
            'total': float(total),  # Asegurar que sea float
            'metodo_pago': metodo_pago,
            'vendedor': vendedor,
            'observaciones': observaciones,
            'descuento': 0.0
        }
        
        venta_id = adapter.execute_update("""
            INSERT INTO ventas (fecha, total, metodo_pago, vendedor, observaciones, descuento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now(), float(total), metodo_pago, vendedor, observaciones, 0.0),
        sync_data={'table': 'ventas', 'operation': 'INSERT', 'data': venta_data})
        
        if not venta_id:
            st.error("❌ Error: No se pudo crear la venta")
            return False
        
        # Agregar items de venta (detalles)
        for item in st.session_state.carrito:
            subtotal = float(item['cantidad']) * float(item['precio'])
            
            detalle_data = {
                'venta_id': int(venta_id),
                'producto_id': int(item['id']),
                'cantidad': int(item['cantidad']),  # Asegurar que sea entero
                'precio_unitario': float(item['precio']),
                'subtotal': float(subtotal)
            }
            
            adapter.execute_update("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (int(venta_id), int(item['id']), int(item['cantidad']), 
                  float(item['precio']), float(subtotal)),
            sync_data={'table': 'detalle_ventas', 'operation': 'INSERT', 'data': detalle_data})
            
            # Actualizar stock - CORREGIDO
            try:
                # Datos correctos para la sincronización
                stock_update_data = {
                    'id': int(item['id']),
                    'stock': f"COALESCE(stock, 0) - {int(item['cantidad'])}"  # Descripción del cambio
                }
                
                adapter.execute_update("""
                    UPDATE productos SET stock = COALESCE(stock, 0) - ? WHERE id = ?
                """, (int(item['cantidad']), int(item['id'])),
                sync_data={'table': 'productos', 'operation': 'UPDATE', 'data': stock_update_data})
                
            except Exception as stock_error:
                # Log del error pero continuar
                st.warning(f"⚠️ No se pudo actualizar stock para {item['nombre']}: {stock_error}")
        
        # Forzar sincronización inmediata después de la venta
        try:
            adapter.force_sync()
            st.info("🔄 Venta sincronizada con servidor")
        except:
            st.warning("⚠️ Venta guardada localmente, se sincronizará automáticamente")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error procesando venta: {e}")
        import traceback
        st.error(f"Detalles del error: {traceback.format_exc()}")
        return False

"""
Punto de Venta - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
from datetime import datetime
from decimal import Decimal
from database.connection_optimized import get_db_adapter
import uuid
import json

def show_punto_venta():
    """Mostrar interfaz de punto de venta optimizada para tablets"""
    
    # CSS adicional para punto de venta + impresión
    st.markdown("""
    <style>
        .producto-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 0.5rem;
            cursor: pointer;
        }
        .producto-card:hover {
            background: #f0f8ff;
            border-color: #0066cc;
        }
        .carrito-item {
            background: #f9f9f9;
            padding: 0.8rem;
            border-radius: 6px;
            margin-bottom: 0.3rem;
            border-left: 4px solid #28a745;
        }
        .total-venta {
            background: #28a745;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
        }
        .printer-status {
            background: #17a2b8;
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            text-align: center;
        }
        .printer-disconnected {
            background: #dc3545;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        # Inicializar carrito en session state
        if 'carrito' not in st.session_state:
            st.session_state.carrito = []
        if 'total_venta' not in st.session_state:
            st.session_state.total_venta = 0.0
        if 'auto_print' not in st.session_state:
            st.session_state.auto_print = True
        if 'printer_connected' not in st.session_state:
            st.session_state.printer_connected = False
        
        # Estado de la impresora
        mostrar_estado_impresora()
        
        # Layout principal - optimizado para tablets
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📦 Productos Disponibles")
            
            # Filtros
            col_filtro1, col_filtro2 = st.columns(2)
            
            with col_filtro1:
                categorias = adapter.get_categorias()
                categoria_nombres = ['Todas'] + [cat['nombre'] for cat in categorias]
                categoria_filtro = st.selectbox(
                    "🏷️ Filtrar por categoría:",
                    categoria_nombres,
                    key="categoria_filtro"
                )
            
            with col_filtro2:
                busqueda = st.text_input(
                    "🔍 Buscar producto:",
                    placeholder="Nombre del producto...",
                    key="busqueda_producto"
                )
            
            # Obtener productos
            productos = adapter.get_productos()
            
            # Aplicar filtros
            if categoria_filtro != 'Todas':
                productos = [p for p in productos if p['categoria'] == categoria_filtro]
            
            if busqueda:
                productos = [p for p in productos if busqueda.lower() in p['nombre'].lower()]
            
            # Mostrar productos en grid optimizado para touch
            if productos:
                # Organizar productos en filas de 2 para tablets
                for i in range(0, len(productos), 2):
                    col_prod1, col_prod2 = st.columns(2)
                    
                    # Producto 1
                    with col_prod1:
                        if i < len(productos):
                            producto = productos[i]
                            mostrar_producto_card(producto, adapter)
                    
                    # Producto 2 (si existe)
                    with col_prod2:
                        if i + 1 < len(productos):
                            producto = productos[i + 1]
                            mostrar_producto_card(producto, adapter)
            else:
                st.info("📭 No se encontraron productos")
        
        with col2:
            st.subheader("🛒 Carrito de Compras")
            
            # Controles de impresión
            mostrar_controles_impresion()
            
            # Mostrar carrito
            if st.session_state.carrito:
                for i, item in enumerate(st.session_state.carrito):
                    mostrar_item_carrito(item, i)
                
                # Total
                st.markdown(f"""
                <div class="total-venta">
                    💰 TOTAL: ${st.session_state.total_venta:.2f}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Controles de venta
                col_metodo, col_vendedor = st.columns(2)
                
                with col_metodo:
                    metodo_pago = st.selectbox(
                        "💳 Método de pago:",
                        ["Efectivo", "Tarjeta", "Transferencia"],
                        key="metodo_pago"
                    )
                
                with col_vendedor:
                    vendedores = adapter.execute_query("SELECT nombre FROM vendedores WHERE activo = true")
                    vendedor_nombres = [v['nombre'] for v in vendedores]
                    if vendedor_nombres:
                        vendedor = st.selectbox(
                            "👤 Vendedor:",
                            vendedor_nombres,
                            key="vendedor_seleccionado"
                        )
                    else:
                        vendedor = st.text_input("👤 Vendedor:", value="Vendedor", key="vendedor_manual")
                
                # Observaciones
                observaciones = st.text_area(
                    "📝 Observaciones:",
                    placeholder="Comentarios adicionales...",
                    height=80,
                    key="observaciones_venta"
                )
                
                # Botones de acción - grandes para tablets
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("🗑️ Limpiar Carrito", use_container_width=True, type="secondary", key="btn_limpiar_carrito_main"):
                        limpiar_carrito()
                
                with col_btn2:
                    if st.button("💰 Procesar Venta", use_container_width=True, type="primary", key="btn_procesar_venta_main"):
                        procesar_venta(adapter, metodo_pago, vendedor, observaciones)
            
            else:
                st.info("🛒 Carrito vacío")
                st.markdown("Agregue productos desde la lista de la izquierda")
            
            # Información útil
            st.markdown("---")
            st.markdown("**📱 Atajos de Teclado:**")
            st.markdown("- `Enter`: Buscar productos")
            st.markdown("- `ESC`: Limpiar búsqueda")
            
    except Exception as e:
        st.error(f"❌ Error en punto de venta: {e}")

def mostrar_producto_card(producto, adapter):
    """Mostrar tarjeta de producto optimizada para touch"""
    
    # Determinar disponibilidad
    disponible = producto['stock'] > 0
    color_stock = "🟢" if producto['stock'] > 10 else "🟡" if producto['stock'] > 0 else "🔴"
    
    # Card HTML personalizada
    card_html = f"""
    <div class="producto-card" style="{'opacity: 0.6;' if not disponible else ''}">
        <h4>{producto['nombre']}</h4>
        <p><strong>💰 ${producto['precio']:.2f}</strong></p>
        <p>{color_stock} Stock: {producto['stock']}</p>
        <p>🏷️ {producto['categoria'] or 'Sin categoría'}</p>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Botón para agregar al carrito
    if disponible:
        col_qty, col_btn = st.columns([1, 2])
        
        with col_qty:
            cantidad = st.number_input(
                "Cant:",
                min_value=1,
                max_value=producto['stock'],
                value=1,
                key=f"qty_producto_{producto['id']}"
            )
        
        with col_btn:
            if st.button(
                "➕ Agregar",
                key=f"add_producto_{producto['id']}",
                use_container_width=True,
                type="primary" if disponible else "secondary",
                disabled=not disponible
            ):
                agregar_al_carrito(producto, cantidad)
    else:
        st.button("❌ Sin Stock", key=f"sin_stock_{producto['id']}", disabled=True, use_container_width=True)

def mostrar_item_carrito(item, index):
    """Mostrar item del carrito"""
    
    subtotal = item['cantidad'] * item['precio_unitario']
    
    # HTML del item
    item_html = f"""
    <div class="carrito-item">
        <strong>{item['nombre']}</strong><br>
        <small>{item['cantidad']} x ${item['precio_unitario']:.2f} = ${subtotal:.2f}</small>
    </div>
    """
    
    st.markdown(item_html, unsafe_allow_html=True)
    
    # Botones de control en línea
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("➖", key=f"menos_carrito_{index}_{item['producto_id']}", help="Disminuir cantidad"):
            modificar_cantidad_carrito(index, -1)
    
    with col2:
        if st.button("➕", key=f"mas_carrito_{index}_{item['producto_id']}", help="Aumentar cantidad"):
            modificar_cantidad_carrito(index, 1)
    
    with col3:
        if st.button("🗑️", key=f"eliminar_carrito_{index}_{item['producto_id']}", help="Eliminar item"):
            eliminar_del_carrito(index)

def agregar_al_carrito(producto, cantidad):
    """Agregar producto al carrito"""
    
    # Verificar si el producto ya está en el carrito
    for item in st.session_state.carrito:
        if item['producto_id'] == producto['id']:
            item['cantidad'] += cantidad
            calcular_total()
            st.success(f"✅ Actualizado: {producto['nombre']}")
            st.rerun()
            return
    
    # Agregar nuevo item
    nuevo_item = {
        'producto_id': producto['id'],
        'nombre': producto['nombre'],
        'precio_unitario': float(producto['precio']),
        'cantidad': cantidad
    }
    
    st.session_state.carrito.append(nuevo_item)
    calcular_total()
    st.success(f"✅ Agregado: {producto['nombre']} (x{cantidad})")
    st.rerun()

def modificar_cantidad_carrito(index, cambio):
    """Modificar cantidad en el carrito"""
    if 0 <= index < len(st.session_state.carrito):
        st.session_state.carrito[index]['cantidad'] += cambio
        
        if st.session_state.carrito[index]['cantidad'] <= 0:
            st.session_state.carrito.pop(index)
        
        calcular_total()
        st.rerun()

def eliminar_del_carrito(index):
    """Eliminar item del carrito"""
    if 0 <= index < len(st.session_state.carrito):
        nombre = st.session_state.carrito[index]['nombre']
        st.session_state.carrito.pop(index)
        calcular_total()
        st.success(f"🗑️ Eliminado: {nombre}")
        st.rerun()

def calcular_total():
    """Calcular total del carrito"""
    total = sum(item['cantidad'] * item['precio_unitario'] for item in st.session_state.carrito)
    st.session_state.total_venta = total

def limpiar_carrito():
    """Limpiar carrito completo"""
    st.session_state.carrito = []
    st.session_state.total_venta = 0.0
    st.success("🧹 Carrito limpiado")
    st.rerun()

def procesar_venta(adapter, metodo_pago, vendedor, observaciones):
    """Procesar venta completa con impresión automática"""
    try:
        if not st.session_state.carrito:
            st.error("❌ El carrito está vacío")
            return
        
        # Datos de la venta
        venta_data = {
            'total': st.session_state.total_venta,
            'metodo_pago': metodo_pago,
            'descuento': 0.0,
            'impuestos': 0.0,
            'fecha': datetime.now(),
            'vendedor': vendedor,
            'observaciones': observaciones,
            'estado': 'Completada'
        }
        
        # Detalles de la venta
        detalles = []
        for item in st.session_state.carrito:
            detalle = {
                'producto_id': item['producto_id'],
                'cantidad': item['cantidad'],
                'precio_unitario': item['precio_unitario'],
                'subtotal': item['cantidad'] * item['precio_unitario']
            }
            detalles.append(detalle)
        
        # Crear venta en la base de datos
        venta_id = adapter.crear_venta(venta_data, detalles)
        
        if venta_id:
            st.success(f"✅ Venta procesada exitosamente!")
            st.success(f"📄 ID de venta: {venta_id}")
            st.success(f"💰 Total: ${st.session_state.total_venta:.2f}")
            
            # Preparar datos para impresión
            ticket_data = {
                'id': str(venta_id),
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'vendedor': vendedor,
                'metodo_pago': metodo_pago,
                'total': float(st.session_state.total_venta),
                'productos': [
                    {
                        'nombre': item['nombre'],
                        'cantidad': item['cantidad'],
                        'precio_unitario': float(item['precio_unitario']),
                        'subtotal': float(item['cantidad'] * item['precio_unitario'])
                    }
                    for item in st.session_state.carrito
                ],
                'observaciones': observaciones
            }
            
            # Mostrar resumen en modal
            with st.expander("📄 Resumen de Venta", expanded=True):
                st.write(f"**ID:** {venta_id}")
                st.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Vendedor:** {vendedor}")
                st.write(f"**Método:** {metodo_pago}")
                st.write(f"**Total:** ${st.session_state.total_venta:.2f}")
                
                st.write("**Productos:**")
                for item in st.session_state.carrito:
                    st.write(f"- {item['nombre']}: {item['cantidad']} x ${item['precio_unitario']:.2f}")
                
                # Botón manual de impresión
                col_print, col_skip = st.columns(2)
                with col_print:
                    if st.button("🖨️ Imprimir Ticket", key="manual_print_btn", use_container_width=True):
                        enviar_a_impresora(ticket_data)
                
                with col_skip:
                    if st.button("⏭️ Continuar sin Imprimir", key="skip_print_btn", use_container_width=True):
                        limpiar_carrito()
            
            # Impresión automática si está habilitada
            if st.session_state.auto_print and st.session_state.printer_connected:
                enviar_a_impresora(ticket_data)
                st.info("🖨️ Imprimiendo ticket automáticamente...")
                
                # Auto-limpiar carrito después de 3 segundos
                import time
                time.sleep(1)
                limpiar_carrito()
            
        else:
            st.error("❌ Error procesando la venta")
    
    except Exception as e:
        st.error(f"❌ Error procesando venta: {e}")

def mostrar_estado_impresora():
    """Mostrar estado de conexión de la impresora"""
    if st.session_state.printer_connected:
        st.markdown("""
        <div class="printer-status">
            🖨️ Impresora Conectada - Lista para imprimir
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="printer-status printer-disconnected">
            ❌ Impresora Desconectada - Toque para conectar
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔗 Conectar Impresora Bluetooth", use_container_width=True, key="connect_printer_btn"):
            conectar_impresora()

def mostrar_controles_impresion():
    """Mostrar controles de configuración de impresión"""
    st.markdown("#### ⚙️ Configuración de Impresión")
    
    col_auto, col_test = st.columns(2)
    
    with col_auto:
        auto_print = st.checkbox(
            "🖨️ Imprimir automáticamente",
            value=st.session_state.auto_print,
            key="auto_print_checkbox",
            help="Imprimir ticket automáticamente al completar venta"
        )
        st.session_state.auto_print = auto_print
    
    with col_test:
        if st.button("🧪 Imprimir Prueba", key="test_print_btn", help="Imprimir ticket de prueba"):
            imprimir_ticket_prueba()
    
    st.markdown("---")

def conectar_impresora():
    """Conectar a impresora Bluetooth"""
    try:
        # JavaScript para conectar impresora
        js_code = """
        <script>
        async function conectarImpresora() {
            if (window.conectarImpresora) {
                const conectado = await window.conectarImpresora();
                if (conectado) {
                    // Actualizar estado en Streamlit
                    window.parent.postMessage({
                        type: 'printer_connected',
                        connected: true
                    }, '*');
                }
            } else {
                alert('Función de impresora no disponible. Asegúrese de estar usando la app Android.');
            }
        }
        conectarImpresora();
        </script>
        """
        st.components.v1.html(js_code, height=0)
        st.session_state.printer_connected = True
        st.success("🖨️ Intentando conectar impresora...")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error conectando impresora: {e}")

def imprimir_ticket_prueba():
    """Imprimir ticket de prueba"""
    ticket_prueba = {
        'id': 'PRUEBA-001',
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'vendedor': 'Sistema',
        'metodo_pago': 'Prueba',
        'total': 100.00,
        'productos': [
            {
                'nombre': 'Producto de Prueba',
                'cantidad': 1,
                'precio_unitario': 100.00,
                'subtotal': 100.00
            }
        ]
    }
    
    enviar_a_impresora(ticket_prueba)

def enviar_a_impresora(venta_data):
    """Enviar datos a la impresora"""
    try:
        # Convertir datos a JSON para JavaScript
        venta_json = json.dumps(venta_data, default=str)
        
        # JavaScript para imprimir
        js_code = f"""
        <script>
        async function imprimirTicket() {{
            const ventaData = {venta_json};
            
            if (window.imprimirTicket) {{
                try {{
                    const impreso = await window.imprimirTicket(ventaData);
                    if (impreso) {{
                        window.parent.postMessage({{
                            type: 'print_success',
                            message: 'Ticket impreso correctamente'
                        }}, '*');
                    }} else {{
                        window.parent.postMessage({{
                            type: 'print_error',
                            message: 'Error al imprimir ticket'
                        }}, '*');
                    }}
                }} catch (error) {{
                    window.parent.postMessage({{
                        type: 'print_error',
                        message: 'Error: ' + error.message
                    }}, '*');
                }}
            }} else {{
                window.parent.postMessage({{
                    type: 'print_error',
                    message: 'Función de impresión no disponible'
                }}, '*');
            }}
        }}
        
        // Ejecutar inmediatamente
        imprimirTicket();
        </script>
        """
        
        # Ejecutar JavaScript
        st.components.v1.html(js_code, height=0)
        
        # Mostrar mensaje temporal
        st.info("🖨️ Enviando a impresora...")
        
    except Exception as e:
        st.error(f"❌ Error preparando impresión: {e}")

if __name__ == "__main__":
    show_punto_venta()

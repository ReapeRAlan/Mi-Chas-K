"""
Inventario - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection_optimized import get_db_adapter

def show_inventario():
    """Mostrar gestión de inventario optimizada para tablets"""
    
    # CSS adicional para inventario
    st.markdown("""
    <style>
        .producto-row {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 0.5rem;
        }
        .stock-bajo {
            border-left: 4px solid #ffc107;
        }
        .sin-stock {
            border-left: 4px solid #dc3545;
        }
        .stock-ok {
            border-left: 4px solid #28a745;
        }
        .form-container {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        st.subheader("📦 Gestión de Inventario")
        
        # Tabs principales
        tab1, tab2, tab3 = st.tabs(["📋 Ver Inventario", "➕ Agregar Producto", "🔄 Actualizar Stock"])
        
        with tab1:
            mostrar_lista_productos(adapter)
        
        with tab2:
            agregar_producto(adapter)
        
        with tab3:
            actualizar_stock(adapter)
    
    except Exception as e:
        st.error(f"❌ Error en inventario: {e}")

def mostrar_lista_productos(adapter):
    """Mostrar lista de productos con filtros"""
    
    # Controles y filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        categorias = adapter.get_categorias()
        categoria_nombres = ['Todas'] + [cat['nombre'] for cat in categorias]
        categoria_filtro = st.selectbox(
            "🏷️ Filtrar por categoría:",
            categoria_nombres,
            key="inventario_categoria_filtro"
        )
    
    with col_filtro2:
        estado_filtro = st.selectbox(
            "📊 Filtrar por stock:",
            ["Todos", "Stock OK", "Stock Bajo", "Sin Stock"],
            key="inventario_estado_filtro"
        )
    
    with col_filtro3:
        busqueda = st.text_input(
            "🔍 Buscar:",
            placeholder="Nombre del producto...",
            key="inventario_busqueda"
        )
    
    # Obtener productos
    productos = adapter.get_productos(activo_only=False)
    
    # Aplicar filtros
    if categoria_filtro != 'Todas':
        productos = [p for p in productos if p['categoria'] == categoria_filtro]
    
    if busqueda:
        productos = [p for p in productos if busqueda.lower() in p['nombre'].lower()]
    
    # Filtrar por estado de stock
    if estado_filtro == "Stock OK":
        productos = [p for p in productos if p['stock'] > 5]
    elif estado_filtro == "Stock Bajo":
        productos = [p for p in productos if 1 <= p['stock'] <= 5]
    elif estado_filtro == "Sin Stock":
        productos = [p for p in productos if p['stock'] == 0]
    
    # Mostrar resumen
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    
    with col_res1:
        st.metric("📦 Total", len(productos))
    
    with col_res2:
        stock_ok = len([p for p in productos if p['stock'] > 5])
        st.metric("✅ Stock OK", stock_ok)
    
    with col_res3:
        stock_bajo = len([p for p in productos if 1 <= p['stock'] <= 5])
        st.metric("⚠️ Stock Bajo", stock_bajo)
    
    with col_res4:
        sin_stock = len([p for p in productos if p['stock'] == 0])
        st.metric("🔴 Sin Stock", sin_stock)
    
    st.markdown("---")
    
    # Mostrar productos
    if productos:
        for producto in productos:
            mostrar_producto_inventario(producto, adapter)
    else:
        st.info("📭 No se encontraron productos")

def mostrar_producto_inventario(producto, adapter):
    """Mostrar producto individual en inventario"""
    
    # Determinar clase CSS según stock
    if producto['stock'] > 5:
        css_class = "stock-ok"
        icono_stock = "✅"
    elif producto['stock'] > 0:
        css_class = "stock-bajo"
        icono_stock = "⚠️"
    else:
        css_class = "sin-stock"
        icono_stock = "🔴"
    
    # Container del producto
    with st.container():
        st.markdown(f'<div class="producto-row {css_class}">', unsafe_allow_html=True)
        
        col_info, col_acciones = st.columns([3, 1])
        
        with col_info:
            st.markdown(f"**{producto['nombre']}**")
            col_det1, col_det2, col_det3, col_det4 = st.columns(4)
            
            with col_det1:
                st.write(f"💰 ${producto['precio']:.2f}")
            
            with col_det2:
                st.write(f"{icono_stock} Stock: {producto['stock']}")
            
            with col_det3:
                st.write(f"🏷️ {producto['categoria'] or 'Sin categoría'}")
            
            with col_det4:
                estado = "✅ Activo" if producto['activo'] else "❌ Inactivo"
                st.write(estado)
            
            if producto['descripcion']:
                st.write(f"📝 {producto['descripcion']}")
        
        with col_acciones:
            # Botón de edición rápida de stock
            with st.popover("✏️ Editar"):
                nuevo_stock = st.number_input(
                    "Nuevo stock:",
                    min_value=0,
                    value=producto['stock'],
                    key=f"edit_stock_{producto['id']}"
                )
                
                nuevo_precio = st.number_input(
                    "Nuevo precio:",
                    min_value=0.0,
                    value=float(producto['precio']),
                    step=0.50,
                    key=f"edit_precio_{producto['id']}"
                )
                
                if st.button("💾 Guardar", key=f"save_{producto['id']}", use_container_width=True):
                    actualizar_producto_rapido(adapter, producto['id'], nuevo_stock, nuevo_precio)
                    st.rerun()
                
                # Toggle activo/inactivo
                nuevo_activo = not producto['activo']
                texto_toggle = "✅ Activar" if not producto['activo'] else "❌ Desactivar"
                
                if st.button(texto_toggle, key=f"toggle_{producto['id']}", use_container_width=True):
                    adapter.execute_update(
                        'productos',
                        {'activo': nuevo_activo},
                        'id = %s',
                        (producto['id'],)
                    )
                    st.success(f"Producto {'activado' if nuevo_activo else 'desactivado'}")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def agregar_producto(adapter):
    """Formulario para agregar nuevo producto"""
    
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    with st.form("agregar_producto_form"):
        st.subheader("➕ Nuevo Producto")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "📝 Nombre del producto *:",
                placeholder="Ej: Chasca Especial"
            )
            
            categorias = adapter.get_categorias()
            categoria_nombres = [cat['nombre'] for cat in categorias]
            
            # Opción para nueva categoría
            categoria_opciones = categoria_nombres + ["+ Nueva categoría"]
            categoria_seleccionada = st.selectbox(
                "🏷️ Categoría:",
                categoria_opciones
            )
            
            if categoria_seleccionada == "+ Nueva categoría":
                nueva_categoria = st.text_input("Nueva categoría:")
                categoria_final = nueva_categoria
            else:
                categoria_final = categoria_seleccionada
            
            precio = st.number_input(
                "💰 Precio *:",
                min_value=0.0,
                value=0.0,
                step=0.50,
                format="%.2f"
            )
        
        with col2:
            stock = st.number_input(
                "📦 Stock inicial:",
                min_value=0,
                value=0
            )
            
            descripcion = st.text_area(
                "📝 Descripción:",
                placeholder="Descripción opcional del producto",
                height=100
            )
            
            codigo_barras = st.text_input(
                "🔢 Código de barras:",
                placeholder="Opcional"
            )
            
            activo = st.checkbox("✅ Producto activo", value=True)
        
        submitted = st.form_submit_button("➕ Agregar Producto", use_container_width=True, type="primary")
        
        if submitted:
            if not nombre or not categoria_final or precio <= 0:
                st.error("❌ Complete los campos obligatorios (nombre, categoría, precio)")
            else:
                # Si es nueva categoría, crearla primero
                if categoria_seleccionada == "+ Nueva categoría" and nueva_categoria:
                    categoria_data = {
                        'nombre': nueva_categoria,
                        'descripcion': f'Categoría creada automáticamente',
                        'activo': True,
                        'fecha_creacion': datetime.now()
                    }
                    adapter.execute_insert('categorias', categoria_data)
                
                # Crear producto
                producto_data = {
                    'nombre': nombre,
                    'categoria': categoria_final,
                    'precio': precio,
                    'descripcion': descripcion if descripcion else None,
                    'stock': stock,
                    'codigo_barras': codigo_barras if codigo_barras else None,
                    'activo': activo,
                    'fecha_creacion': datetime.now(),
                    'fecha_modificacion': datetime.now()
                }
                
                producto_id = adapter.execute_insert('productos', producto_data)
                
                if producto_id:
                    st.success(f"✅ Producto creado exitosamente! ID: {producto_id}")
                    st.rerun()
                else:
                    st.error("❌ Error creando el producto")
    
    st.markdown('</div>', unsafe_allow_html=True)

def actualizar_stock(adapter):
    """Herramientas para actualización masiva de stock"""
    
    st.subheader("🔄 Actualizar Stock")
    
    # Selección de producto
    productos = adapter.get_productos(activo_only=False)
    
    if not productos:
        st.info("📭 No hay productos disponibles")
        return
    
    # Crear diccionario para selección
    productos_dict = {f"{p['nombre']} (Stock: {p['stock']})": p for p in productos}
    
    producto_seleccionado = st.selectbox(
        "📦 Seleccionar producto:",
        list(productos_dict.keys()),
        key="stock_producto_seleccionado"
    )
    
    if producto_seleccionado:
        producto = productos_dict[producto_seleccionado]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Estado Actual:**")
            st.write(f"**Nombre:** {producto['nombre']}")
            st.write(f"**Stock actual:** {producto['stock']}")
            st.write(f"**Precio:** ${producto['precio']:.2f}")
            st.write(f"**Categoría:** {producto['categoria']}")
        
        with col2:
            st.markdown("**🔄 Actualizar:**")
            
            operacion = st.radio(
                "Tipo de operación:",
                ["Establecer nuevo stock", "Agregar al stock", "Quitar del stock"],
                key="tipo_operacion_stock"
            )
            
            cantidad = st.number_input(
                "Cantidad:",
                min_value=0 if operacion == "Establecer nuevo stock" else 1,
                value=0,
                key="cantidad_stock"
            )
            
            motivo = st.text_input(
                "Motivo (opcional):",
                placeholder="Ej: Compra, venta, ajuste...",
                key="motivo_stock"
            )
            
            if st.button("🔄 Actualizar Stock", use_container_width=True, type="primary"):
                actualizar_stock_producto(adapter, producto, operacion, cantidad, motivo)

def actualizar_stock_producto(adapter, producto, operacion, cantidad, motivo):
    """Actualizar stock de un producto específico"""
    try:
        if operacion == "Establecer nuevo stock":
            nuevo_stock = cantidad
        elif operacion == "Agregar al stock":
            nuevo_stock = producto['stock'] + cantidad
        else:  # Quitar del stock
            nuevo_stock = max(0, producto['stock'] - cantidad)
        
        # Actualizar en base de datos
        filas_actualizadas = adapter.execute_update(
            'productos',
            {
                'stock': nuevo_stock,
                'fecha_modificacion': datetime.now()
            },
            'id = %s',
            (producto['id'],)
        )
        
        if filas_actualizadas > 0:
            st.success(f"✅ Stock actualizado: {producto['stock']} → {nuevo_stock}")
            
            # Log de la operación (opcional)
            if motivo:
                st.info(f"📝 Motivo: {motivo}")
            
            st.rerun()
        else:
            st.error("❌ Error actualizando el stock")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")

def actualizar_producto_rapido(adapter, producto_id, nuevo_stock, nuevo_precio):
    """Actualización rápida de producto"""
    try:
        filas_actualizadas = adapter.execute_update(
            'productos',
            {
                'stock': nuevo_stock,
                'precio': nuevo_precio,
                'fecha_modificacion': datetime.now()
            },
            'id = %s',
            (producto_id,)
        )
        
        if filas_actualizadas > 0:
            st.success("✅ Producto actualizado")
        else:
            st.error("❌ Error actualizando producto")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")

if __name__ == "__main__":
    show_inventario()

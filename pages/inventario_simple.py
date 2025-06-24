"""
Inventario Simplificado
Versión 3.1.0 - Con Adaptador Compatible
"""
import streamlit as st
from database.connection_adapter import execute_query, execute_update

def mostrar_inventario_simple():
    """Interfaz simplificada de inventario"""
    
    st.title("📦 Gestión de Inventario")
    
    # Botón volver
    if st.button("← Volver al inicio"):
        st.session_state.page = 'main'
        st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📋 Productos", "➕ Agregar Producto", "🏷️ Categorías"])
    
    with tab1:
        st.subheader("Lista de Productos")
        
        # Obtener productos
        productos = execute_query("""
            SELECT p.*, p.categoria as categoria_nombre 
            FROM productos p 
            ORDER BY p.nombre
        """)
        
        if productos:
            for producto in productos:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 2])
                
                with col1:
                    st.write(f"**{producto['nombre']}**")
                    st.write(f"Categoría: {producto['categoria_nombre'] or 'Sin categoría'}")
                
                with col2:
                    st.write(f"Precio: ${producto['precio']:,.2f}")
                    
                with col3:
                    nuevo_stock = st.number_input(
                        "Stock",
                        value=producto['stock'],
                        min_value=0,
                        key=f"stock_{producto['id']}"
                    )
                
                with col4:
                    if st.button(f"💾 Actualizar", key=f"update_{producto['id']}"):
                        actualizar_stock(producto['id'], nuevo_stock)
                        st.success("Stock actualizado")
                        st.rerun()
                    
                    activo = "✅ Activo" if producto['activo'] else "❌ Inactivo"
                    st.write(activo)
                
                st.markdown("---")
        else:
            st.info("No hay productos registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Producto")
        
        with st.form("form_producto"):
            nombre = st.text_input("Nombre del Producto*")
            precio = st.number_input("Precio*", min_value=0.01, step=0.01)
            stock = st.number_input("Stock Inicial", min_value=0, value=0)
            
            # Obtener categorías
            categorias = execute_query("SELECT * FROM categorias WHERE activo = 1")
            cat_options = {cat['nombre']: cat['nombre'] for cat in categorias}
            categoria_nombre = st.selectbox("Categoría", options=list(cat_options.keys()))
            
            descripcion = st.text_area("Descripción")
            
            submitted = st.form_submit_button("✅ Agregar Producto", type="primary")
            
            if submitted:
                if nombre and precio > 0:
                    categoria_seleccionada = cat_options.get(categoria_nombre)
                    if agregar_producto(nombre, precio, stock, categoria_seleccionada, descripcion):
                        st.success("✅ Producto agregado exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al agregar producto")
                else:
                    st.error("Por favor completa los campos obligatorios")
    
    with tab3:
        st.subheader("Gestión de Categorías")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Categorías Existentes**")
            categorias = execute_query("SELECT * FROM categorias")
            
            for cat in categorias:
                st.write(f"• {cat['nombre']} {'✅' if cat['activo'] else '❌'}")
        
        with col2:
            st.write("**Agregar Nueva Categoría**")
            with st.form("form_categoria"):
                nombre_cat = st.text_input("Nombre de Categoría")
                desc_cat = st.text_area("Descripción")
                
                if st.form_submit_button("➕ Agregar Categoría"):
                    if nombre_cat:
                        if agregar_categoria(nombre_cat, desc_cat):
                            st.success("✅ Categoría agregada")
                            st.rerun()
                    else:
                        st.error("El nombre es obligatorio")

def actualizar_stock(producto_id, nuevo_stock):
    """Actualizar stock de producto"""
    stock_data = {
        'table': 'productos',
        'operation': 'UPDATE',
        'data': {
            'id': producto_id,
            'stock': nuevo_stock
        }
    }
    
    return execute_update("""
        UPDATE productos SET stock = ? WHERE id = ?
    """, (nuevo_stock, producto_id), stock_data)

def agregar_producto(nombre, precio, stock, categoria, descripcion):
    """Agregar nuevo producto"""
    producto_data = {
        'table': 'productos',
        'operation': 'INSERT',
        'data': {
            'nombre': nombre,
            'precio': precio,
            'stock': stock,
            'categoria': categoria,
            'descripcion': descripcion,
            'activo': True
        }
    }
    
    return execute_update("""
        INSERT INTO productos (nombre, precio, stock, categoria, descripcion, activo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, precio, stock, categoria, descripcion, True), producto_data)

def agregar_categoria(nombre, descripcion):
    """Agregar nueva categoría"""
    categoria_data = {
        'table': 'categorias',
        'operation': 'INSERT',
        'data': {
            'nombre': nombre,
            'descripcion': descripcion,
            'activo': True
        }
    }
    
    return execute_update("""
        INSERT INTO categorias (nombre, descripcion, activo)
        VALUES (?, ?, ?)
    """, (nombre, descripcion, True), categoria_data)

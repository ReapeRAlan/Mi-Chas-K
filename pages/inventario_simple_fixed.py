"""
Inventario Simplificado - Versión Funcional
"""
import streamlit as st

def show_inventario(adapter):
    """Interfaz simplificada de inventario"""
    
    st.title("📦 Gestión de Inventario")
    
    tab1, tab2, tab3 = st.tabs(["📋 Productos", "➕ Agregar Producto", "🏷️ Categorías"])
    
    with tab1:
        st.subheader("📦 Lista de Productos")
        
        try:
            productos = adapter.execute_query("""
                SELECT * FROM productos WHERE activo = 1 ORDER BY nombre
            """)
            
            if productos:
                for producto in productos:
                    with st.expander(f"📦 {producto['nombre']} - ${producto['precio']:.2f}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**ID:** {producto['id']}")
                            st.write(f"**Precio:** ${producto['precio']:.2f}")
                            st.write(f"**Stock:** {producto.get('stock', 'N/A')}")
                            st.write(f"**Categoría:** {producto.get('categoria', 'General')}")
                            if producto.get('descripcion'):
                                st.write(f"**Descripción:** {producto['descripcion']}")
                        
                        with col2:
                            if producto.get('stock') is not None:
                                nuevo_stock = st.number_input(
                                    "Actualizar Stock",
                                    min_value=0,
                                    value=int(producto['stock']),
                                    key=f"stock_{producto['id']}"
                                )
                                if st.button("💾 Actualizar", key=f"update_{producto['id']}"):
                                    try:
                                        adapter.execute_update(
                                            "UPDATE productos SET stock = ? WHERE id = ?",
                                            (nuevo_stock, producto['id'])
                                        )
                                        st.success("✅ Stock actualizado")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
            else:
                st.info("No hay productos registrados")
                
        except Exception as e:
            st.error(f"Error cargando productos: {e}")
    
    with tab2:
        st.subheader("➕ Agregar Nuevo Producto")
        
        try:
            # Obtener categorías
            categorias = adapter.execute_query("SELECT nombre FROM categorias WHERE activo = 1")
            categoria_options = [cat['nombre'] for cat in categorias] if categorias else ['General']
            
            with st.form("agregar_producto"):
                nombre = st.text_input("📦 Nombre del Producto *")
                precio = st.number_input("💰 Precio *", min_value=0.01, step=0.01)
                stock = st.number_input("📊 Stock Inicial", min_value=0, value=0)
                categoria_seleccionada = st.selectbox("🏷️ Categoría", categoria_options)
                descripcion = st.text_area("📝 Descripción")
                
                if st.form_submit_button("💾 Agregar Producto", type="primary"):
                    if nombre and precio > 0:
                        try:
                            adapter.execute_update("""
                                INSERT INTO productos (nombre, precio, stock, categoria, descripcion, activo)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (nombre, precio, stock, categoria_seleccionada, descripcion, True))
                            
                            st.success("✅ Producto agregado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error agregando producto: {e}")
                    else:
                        st.error("❌ El nombre y precio son obligatorios")
        
        except Exception as e:
            st.error(f"Error en formulario: {e}")
    
    with tab3:
        st.subheader("🏷️ Gestión de Categorías")
        
        # Mostrar categorías existentes
        try:
            categorias = adapter.execute_query("SELECT * FROM categorias ORDER BY nombre")
            
            if categorias:
                st.write("**Categorías existentes:**")
                for categoria in categorias:
                    estado = "✅ Activa" if categoria.get('activo', True) else "❌ Inactiva"
                    st.write(f"- {categoria['nombre']}: {categoria.get('descripcion', 'Sin descripción')} ({estado})")
            else:
                st.info("No hay categorías registradas")
        
        except Exception as e:
            st.error(f"Error cargando categorías: {e}")
        
        # Agregar nueva categoría
        st.subheader("➕ Agregar Nueva Categoría")
        
        with st.form("agregar_categoria"):
            nombre_cat = st.text_input("🏷️ Nombre de la Categoría *")
            desc_cat = st.text_area("📝 Descripción")
            
            if st.form_submit_button("💾 Agregar Categoría", type="primary"):
                if nombre_cat:
                    try:
                        adapter.execute_update("""
                            INSERT INTO categorias (nombre, descripcion, activo)
                            VALUES (?, ?, ?)
                        """, (nombre_cat, desc_cat, True))
                        
                        st.success("✅ Categoría agregada")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error agregando categoría: {e}")
                else:
                    st.error("❌ El nombre es obligatorio")

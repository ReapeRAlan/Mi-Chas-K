"""
Página de gestión de inventario
"""
import streamlit as st
import pandas as pd
from database.models import Producto, Categoria
from utils.helpers import (
    validate_positive_number, validate_positive_integer,
    show_success_message, show_error_message, format_currency
)

def mostrar_inventario():
    """Página principal de gestión de inventario"""
    st.title("📦 Gestión de Inventario")
    
    # Pestañas para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["🔍 Ver Productos", "➕ Agregar Producto", "🏷️ Categorías"])
    
    with tab1:
        mostrar_lista_productos()
    
    with tab2:
        mostrar_formulario_producto()
    
    with tab3:
        mostrar_gestion_categorias()

def mostrar_lista_productos():
    """Muestra la lista de productos con opciones de edición"""
    st.subheader("📋 Lista de Productos")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        categorias = Categoria.get_all()
        categoria_names = ["Todas"] + [cat.nombre for cat in categorias]
        categoria_filtro = st.selectbox("Filtrar por categoría:", categoria_names)
    
    with col2:
        mostrar_inactivos = st.checkbox("Mostrar productos inactivos")
    
    # Obtener productos
    if categoria_filtro == "Todas":
        productos = Producto.get_all(activos_solamente=not mostrar_inactivos)
    else:
        productos = Producto.get_by_categoria(categoria_filtro)
        if not mostrar_inactivos:
            productos = [p for p in productos if p.activo]
    
    if not productos:
        st.info("No hay productos que mostrar con los filtros seleccionados")
        return
    
    # Convertir a DataFrame para tabla
    data = []
    for producto in productos:
        data.append({
            "ID": producto.id,
            "Nombre": producto.nombre,
            "Precio": f"{producto.precio:.2f}",
            "Stock": producto.stock,
            "Categoría": producto.categoria,
            "Estado": "Activo" if producto.activo else "Inactivo"
        })
    
    df = pd.DataFrame(data)
    
    # Mostrar tabla
    st.dataframe(df, use_container_width=True)
    
    # Selección de producto para editar
    st.subheader("✏️ Editar Producto")
    
    producto_ids = [p.id for p in productos]
    producto_seleccionado_id = st.selectbox(
        "Seleccionar producto para editar:",
        options=[None] + producto_ids,
        format_func=lambda x: "Seleccionar..." if x is None else f"ID {x} - {next(p.nombre for p in productos if p.id == x)}"
    )
    
    if producto_seleccionado_id:
        mostrar_formulario_edicion(producto_seleccionado_id)

def mostrar_formulario_edicion(producto_id: int):
    """Muestra el formulario de edición de un producto específico"""
    producto = Producto.get_by_id(producto_id)
    
    if not producto:
        show_error_message("Producto no encontrado")
        return
    
    with st.form(f"editar_producto_{producto_id}"):
        st.write(f"**Editando:** {producto.nombre}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_nombre = st.text_input("Nombre:", value=producto.nombre)
            nuevo_precio = st.number_input("Precio:", value=float(producto.precio), min_value=0.01, step=0.01)
            nuevo_stock = st.number_input("Stock:", value=producto.stock, min_value=0, step=1)
        
        with col2:
            categorias = Categoria.get_all()
            categoria_names = [cat.nombre for cat in categorias]
            categoria_actual_idx = categoria_names.index(producto.categoria) if producto.categoria in categoria_names else 0
            
            nueva_categoria = st.selectbox("Categoría:", categoria_names, index=categoria_actual_idx)
            nuevo_codigo = st.text_input("Código de barras:", value=producto.codigo_barras or "")
            producto_activo = st.checkbox("Producto activo", value=producto.activo)
        
        nueva_descripcion = st.text_area("Descripción:", value=producto.descripcion or "")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("💾 Guardar Cambios", type="primary"):
                try:
                    producto.nombre = nuevo_nombre
                    producto.precio = nuevo_precio
                    producto.stock = nuevo_stock
                    producto.categoria = nueva_categoria
                    producto.codigo_barras = nuevo_codigo if nuevo_codigo else None
                    producto.descripcion = nueva_descripcion
                    producto.activo = producto_activo
                    
                    producto.save()
                    show_success_message("Producto actualizado exitosamente!")
                    st.rerun()
                    
                except Exception as e:
                    show_error_message(f"Error al actualizar producto: {str(e)}")
        
        with col2:
            if st.form_submit_button("🗑️ Desactivar"):
                try:
                    producto.activo = False
                    producto.save()
                    show_success_message("Producto desactivado")
                    st.rerun()
                except Exception as e:
                    show_error_message(f"Error al desactivar producto: {str(e)}")
        
        with col3:
            if st.form_submit_button("❌ Cancelar"):
                st.rerun()

def mostrar_formulario_producto():
    """Muestra el formulario para agregar un nuevo producto"""
    st.subheader("➕ Agregar Nuevo Producto")
    
    with st.form("nuevo_producto"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre del producto *")
            precio = st.number_input("Precio *", min_value=0.01, step=0.01)
            stock = st.number_input("Stock inicial", min_value=0, value=0, step=1)
        
        with col2:
            categorias = Categoria.get_all()
            categoria_names = [cat.nombre for cat in categorias]
            categoria = st.selectbox("Categoría", categoria_names)
            codigo_barras = st.text_input("Código de barras (opcional)")
        
        descripcion = st.text_area("Descripción (opcional)")
        
        if st.form_submit_button("➕ Agregar Producto", type="primary"):
            # Validaciones
            if not nombre.strip():
                show_error_message("El nombre del producto es obligatorio")
                return
            
            if precio <= 0:
                show_error_message("El precio debe ser mayor a 0")
                return
            
            try:
                # Crear nuevo producto
                nuevo_producto = Producto(
                    nombre=nombre.strip(),
                    precio=precio,
                    stock=stock,
                    categoria=categoria,
                    codigo_barras=codigo_barras.strip() if codigo_barras.strip() else None,
                    descripcion=descripcion.strip()
                )
                
                producto_id = nuevo_producto.save()
                show_success_message(f"Producto '{nombre}' agregado con ID #{producto_id}")
                
                # Limpiar formulario
                st.rerun()
                
            except Exception as e:
                show_error_message(f"Error al agregar producto: {str(e)}")

def mostrar_gestion_categorias():
    """Muestra la gestión de categorías"""
    st.subheader("🏷️ Gestión de Categorías")
    
    # Mostrar categorías existentes
    categorias = Categoria.get_all(activas_solamente=False)
    
    if categorias:
        st.write("**Categorías existentes:**")
        for categoria in categorias:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                estado = "✅" if categoria.activo else "❌"
                st.write(f"{estado} **{categoria.nombre}** - {categoria.descripcion}")
            
            with col2:
                if categoria.activo:
                    if st.button(f"Desactivar", key=f"deactivate_{categoria.id}"):
                        try:
                            from database.connection import execute_update
                            execute_update("UPDATE categorias SET activo = 0 WHERE id = ?", (categoria.id,))
                            show_success_message(f"Categoría '{categoria.nombre}' desactivada")
                            st.rerun()
                        except Exception as e:
                            show_error_message(f"Error: {str(e)}")
                else:
                    if st.button(f"Activar", key=f"activate_{categoria.id}"):
                        try:
                            from database.connection import execute_update
                            execute_update("UPDATE categorias SET activo = 1 WHERE id = ?", (categoria.id,))
                            show_success_message(f"Categoría '{categoria.nombre}' activada")
                            st.rerun()
                        except Exception as e:
                            show_error_message(f"Error: {str(e)}")
    
    st.divider()
    
    # Formulario para nueva categoría
    st.write("**Agregar nueva categoría:**")
    
    with st.form("nueva_categoria"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_categoria = st.text_input("Nombre de la categoría *")
        
        with col2:
            descripcion_categoria = st.text_input("Descripción")
        
        if st.form_submit_button("➕ Agregar Categoría"):
            if not nombre_categoria.strip():
                show_error_message("El nombre de la categoría es obligatorio")
                return
            
            try:
                from database.connection import execute_update
                execute_update(
                    "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)",
                    (nombre_categoria.strip(), descripcion_categoria.strip())
                )
                show_success_message(f"Categoría '{nombre_categoria}' agregada exitosamente")
                st.rerun()
                
            except Exception as e:
                show_error_message(f"Error al agregar categoría: {str(e)}")

# Función principal para ejecutar la página
def main():
    mostrar_inventario()

"""
Configuración - Optimizado para Tablets
Sistema MiChaska - PostgreSQL Directo
"""
import streamlit as st
from datetime import datetime
from database.connection_optimized import get_db_adapter

def show_configuracion():
    """Mostrar configuración del sistema optimizada para tablets"""
    
    # CSS adicional para configuración
    st.markdown("""
    <style>
        .config-section {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #ddd;
            margin-bottom: 1rem;
        }
        .config-item {
            padding: 0.8rem;
            border-bottom: 1px solid #eee;
        }
        .config-item:last-child {
            border-bottom: none;
        }
        .status-ok {
            color: #28a745;
            font-weight: bold;
        }
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .status-error {
            color: #dc3545;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        st.subheader("⚙️ Configuración del Sistema")
        
        # Tabs principales
        tab1, tab2, tab3, tab4 = st.tabs(["🏢 Negocio", "👥 Vendedores", "🏷️ Categorías", "🔧 Sistema"])
        
        with tab1:
            configuracion_negocio(adapter)
        
        with tab2:
            gestion_vendedores(adapter)
        
        with tab3:
            gestion_categorias(adapter)
        
        with tab4:
            informacion_sistema(adapter)
    
    except Exception as e:
        st.error(f"❌ Error en configuración: {e}")

def configuracion_negocio(adapter):
    """Configuración de información del negocio"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.markdown("**🏢 Información del Negocio**")
    
    # Obtener configuración actual
    try:
        config_items = adapter.execute_query("SELECT clave, valor, descripcion FROM configuracion ORDER BY clave")
        config_dict = {item['clave']: item['valor'] for item in config_items}
    except:
        config_dict = {}
    
    with st.form("config_negocio_form"):
        nombre_negocio = st.text_input(
            "🏪 Nombre del negocio:",
            value=config_dict.get('nombre_negocio', 'MiChaska'),
            key="config_nombre_negocio"
        )
        
        direccion = st.text_area(
            "📍 Dirección:",
            value=config_dict.get('direccion', ''),
            height=80,
            key="config_direccion"
        )
        
        telefono = st.text_input(
            "📞 Teléfono:",
            value=config_dict.get('telefono', ''),
            key="config_telefono"
        )
        
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            email = st.text_input(
                "📧 Email:",
                value=config_dict.get('email', ''),
                key="config_email"
            )
        
        with col_config2:
            rfc = st.text_input(
                "🆔 RFC:",
                value=config_dict.get('rfc', ''),
                key="config_rfc"
            )
        
        mensaje_ticket = st.text_area(
            "📄 Mensaje en tickets:",
            value=config_dict.get('mensaje_ticket', '¡Gracias por su compra!'),
            height=100,
            key="config_mensaje_ticket"
        )
        
        if st.form_submit_button("💾 Guardar Configuración", use_container_width=True, type="primary"):
            actualizar_configuracion_negocio(adapter, {
                'nombre_negocio': nombre_negocio,
                'direccion': direccion,
                'telefono': telefono,
                'email': email,
                'rfc': rfc,
                'mensaje_ticket': mensaje_ticket
            })
    
    st.markdown('</div>', unsafe_allow_html=True)

def actualizar_configuracion_negocio(adapter, config_data):
    """Actualizar configuración del negocio"""
    try:
        for clave, valor in config_data.items():
            # Verificar si la configuración existe
            existing = adapter.execute_query("SELECT id FROM configuracion WHERE clave = %s", (clave,))
            
            if existing:
                # Actualizar
                adapter.execute_update(
                    'configuracion',
                    {'valor': valor, 'fecha_modificacion': datetime.now()},
                    'clave = %s',
                    (clave,)
                )
            else:
                # Insertar nuevo
                adapter.execute_insert('configuracion', {
                    'clave': clave,
                    'valor': valor,
                    'descripcion': f'Configuración de {clave}',
                    'fecha_modificacion': datetime.now()
                })
        
        st.success("✅ Configuración actualizada exitosamente")
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error actualizando configuración: {e}")

def gestion_vendedores(adapter):
    """Gestión de vendedores"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.markdown("**👥 Gestión de Vendedores**")
    
    # Obtener vendedores actuales
    vendedores = adapter.execute_query("SELECT * FROM vendedores ORDER BY nombre")
    
    # Mostrar vendedores existentes
    if vendedores:
        st.markdown("**Vendedores Actuales:**")
        
        for vendedor in vendedores:
            col_vend1, col_vend2, col_vend3 = st.columns([2, 1, 1])
            
            with col_vend1:
                estado_icon = "✅" if vendedor['activo'] else "❌"
                st.write(f"{estado_icon} **{vendedor['nombre']}**")
            
            with col_vend2:
                if vendedor['fecha_registro']:
                    fecha_registro = vendedor['fecha_registro'].strftime('%Y-%m-%d')
                    st.write(f"📅 {fecha_registro}")
            
            with col_vend3:
                # Toggle activo/inactivo
                nuevo_estado = not vendedor['activo']
                texto_boton = "✅ Activar" if not vendedor['activo'] else "❌ Desactivar"
                
                if st.button(texto_boton, key=f"toggle_vendedor_{vendedor['id']}"):
                    adapter.execute_update(
                        'vendedores',
                        {'activo': nuevo_estado},
                        'id = %s',
                        (vendedor['id'],)
                    )
                    st.success(f"Vendedor {'activado' if nuevo_estado else 'desactivado'}")
                    st.rerun()
    
    st.markdown("---")
    
    # Formulario para agregar vendedor
    st.markdown("**➕ Agregar Nuevo Vendedor:**")
    
    with st.form("agregar_vendedor_form"):
        nuevo_vendedor_nombre = st.text_input(
            "👤 Nombre del vendedor:",
            placeholder="Nombre completo",
            key="nuevo_vendedor_nombre"
        )
        
        nuevo_vendedor_activo = st.checkbox("✅ Activo desde el inicio", value=True)
        
        if st.form_submit_button("➕ Agregar Vendedor", use_container_width=True, type="primary"):
            if nuevo_vendedor_nombre.strip():
                # Verificar que no exista
                existe = adapter.execute_query(
                    "SELECT id FROM vendedores WHERE LOWER(nombre) = LOWER(%s)",
                    (nuevo_vendedor_nombre.strip(),)
                )
                
                if existe:
                    st.error("❌ Ya existe un vendedor con ese nombre")
                else:
                    vendedor_id = adapter.execute_insert('vendedores', {
                        'nombre': nuevo_vendedor_nombre.strip(),
                        'activo': nuevo_vendedor_activo,
                        'fecha_registro': datetime.now()
                    })
                    
                    if vendedor_id:
                        st.success(f"✅ Vendedor agregado exitosamente! ID: {vendedor_id}")
                        st.rerun()
                    else:
                        st.error("❌ Error agregando vendedor")
            else:
                st.error("❌ El nombre del vendedor es requerido")
    
    st.markdown('</div>', unsafe_allow_html=True)

def gestion_categorias(adapter):
    """Gestión de categorías"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.markdown("**🏷️ Gestión de Categorías**")
    
    # Obtener categorías actuales
    categorias = adapter.execute_query("SELECT * FROM categorias ORDER BY nombre")
    
    # Mostrar categorías existentes
    if categorias:
        st.markdown("**Categorías Actuales:**")
        
        for categoria in categorias:
            col_cat1, col_cat2, col_cat3, col_cat4 = st.columns([2, 2, 1, 1])
            
            with col_cat1:
                estado_icon = "✅" if categoria['activo'] else "❌"
                st.write(f"{estado_icon} **{categoria['nombre']}**")
            
            with col_cat2:
                if categoria['descripcion']:
                    st.write(f"📝 {categoria['descripcion']}")
                else:
                    st.write("📝 Sin descripción")
            
            with col_cat3:
                # Contar productos en esta categoría
                productos_count = adapter.execute_query(
                    "SELECT COUNT(*) as count FROM productos WHERE categoria = %s",
                    (categoria['nombre'],)
                )
                count = productos_count[0]['count'] if productos_count else 0
                st.write(f"📦 {count}")
            
            with col_cat4:
                # Toggle activo/inactivo
                nuevo_estado = not categoria['activo']
                texto_boton = "✅" if not categoria['activo'] else "❌"
                
                if st.button(texto_boton, key=f"toggle_categoria_{categoria['id']}"):
                    adapter.execute_update(
                        'categorias',
                        {'activo': nuevo_estado},
                        'id = %s',
                        (categoria['id'],)
                    )
                    st.success(f"Categoría {'activada' if nuevo_estado else 'desactivada'}")
                    st.rerun()
    
    st.markdown("---")
    
    # Formulario para agregar categoría
    st.markdown("**➕ Agregar Nueva Categoría:**")
    
    with st.form("agregar_categoria_form"):
        col_cat_form1, col_cat_form2 = st.columns(2)
        
        with col_cat_form1:
            nueva_categoria_nombre = st.text_input(
                "🏷️ Nombre de la categoría:",
                placeholder="Ej: Bebidas, Comidas, etc.",
                key="nueva_categoria_nombre"
            )
        
        with col_cat_form2:
            nueva_categoria_activa = st.checkbox("✅ Activa desde el inicio", value=True)
        
        nueva_categoria_descripcion = st.text_area(
            "📝 Descripción:",
            placeholder="Descripción opcional de la categoría",
            height=80,
            key="nueva_categoria_descripcion"
        )
        
        if st.form_submit_button("➕ Agregar Categoría", use_container_width=True, type="primary"):
            if nueva_categoria_nombre.strip():
                # Verificar que no exista
                existe = adapter.execute_query(
                    "SELECT id FROM categorias WHERE LOWER(nombre) = LOWER(%s)",
                    (nueva_categoria_nombre.strip(),)
                )
                
                if existe:
                    st.error("❌ Ya existe una categoría con ese nombre")
                else:
                    categoria_id = adapter.execute_insert('categorias', {
                        'nombre': nueva_categoria_nombre.strip(),
                        'descripcion': nueva_categoria_descripcion.strip() if nueva_categoria_descripcion else None,
                        'activo': nueva_categoria_activa,
                        'fecha_creacion': datetime.now()
                    })
                    
                    if categoria_id:
                        st.success(f"✅ Categoría agregada exitosamente! ID: {categoria_id}")
                        st.rerun()
                    else:
                        st.error("❌ Error agregando categoría")
            else:
                st.error("❌ El nombre de la categoría es requerido")
    
    st.markdown('</div>', unsafe_allow_html=True)

def informacion_sistema(adapter):
    """Información del sistema y diagnósticos"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    
    st.markdown("**🔧 Información del Sistema**")
    
    # Estado de la base de datos
    col_sys1, col_sys2 = st.columns(2)
    
    with col_sys1:
        st.markdown("**📊 Estado de la Base de Datos:**")
        
        try:
            # Contar registros en tablas principales
            productos_count = len(adapter.get_productos(activo_only=False))
            categorias_count = len(adapter.get_categorias())
            ventas_count = adapter.execute_query("SELECT COUNT(*) as count FROM ventas")[0]['count']
            vendedores_count = adapter.execute_query("SELECT COUNT(*) as count FROM vendedores")[0]['count']
            
            st.markdown(f'<div class="config-item">📦 Productos: <span class="status-ok">{productos_count}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">🏷️ Categorías: <span class="status-ok">{categorias_count}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">💰 Ventas: <span class="status-ok">{ventas_count}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">👥 Vendedores: <span class="status-ok">{vendedores_count}</span></div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f'<div class="config-item">❌ Error: <span class="status-error">{e}</span></div>', unsafe_allow_html=True)
    
    with col_sys2:
        st.markdown("**🔗 Información de Conexión:**")
        
        # Información de conexión (sin datos sensibles)
        try:
            import os
            st.markdown(f'<div class="config-item">🌐 Host: <span class="status-ok">{os.getenv("DB_HOST", "N/A")}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">🗄️ Base: <span class="status-ok">{os.getenv("DB_NAME", "N/A")}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">👤 Usuario: <span class="status-ok">{os.getenv("DB_USER", "N/A")}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="config-item">🔌 Puerto: <span class="status-ok">{os.getenv("DB_PORT", "5432")}</span></div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f'<div class="config-item">❌ Error: <span class="status-error">{e}</span></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Herramientas de mantenimiento
    st.markdown("**🔧 Herramientas de Mantenimiento:**")
    
    col_mant1, col_mant2, col_mant3 = st.columns(3)
    
    with col_mant1:
        if st.button("🔄 Probar Conexión", use_container_width=True):
            try:
                result = adapter.execute_query("SELECT NOW() as timestamp")
                if result:
                    st.success(f"✅ Conexión OK: {result[0]['timestamp']}")
                else:
                    st.error("❌ Error en consulta de prueba")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")
    
    with col_mant2:
        if st.button("📊 Estadísticas", use_container_width=True):
            try:
                # Últimas ventas
                ultima_venta = adapter.execute_query("SELECT MAX(fecha) as ultima FROM ventas")
                if ultima_venta and ultima_venta[0]['ultima']:
                    st.info(f"📅 Última venta: {ultima_venta[0]['ultima']}")
                else:
                    st.info("📅 No hay ventas registradas")
                
                # Producto más vendido
                top_producto = adapter.execute_query("""
                    SELECT p.nombre, SUM(dv.cantidad) as total
                    FROM detalle_ventas dv
                    JOIN productos p ON dv.producto_id = p.id
                    GROUP BY p.id, p.nombre
                    ORDER BY total DESC
                    LIMIT 1
                """)
                
                if top_producto:
                    st.info(f"⭐ Top producto: {top_producto[0]['nombre']} ({top_producto[0]['total']} vendidos)")
                
            except Exception as e:
                st.error(f"❌ Error obteniendo estadísticas: {e}")
    
    with col_mant3:
        if st.button("📱 Info Tablet", use_container_width=True):
            st.info("💯 Sistema optimizado para tablets")
            st.info("🔗 PostgreSQL directo")
            st.info("⚡ Sin sincronización híbrida")
            st.info("🎯 Interfaz touch-friendly")
    
    # Información de versión
    st.markdown("---")
    st.markdown("**📱 Información del Sistema:**")
    st.markdown("- **Versión:** MiChaska v3.0 - Tablet Edition")
    st.markdown("- **Base de datos:** PostgreSQL (Directo)")
    st.markdown("- **Optimización:** Tablets y dispositivos touch")
    st.markdown("- **Última actualización:** 2025-06-26")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_configuracion()

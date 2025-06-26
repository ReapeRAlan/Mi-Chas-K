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
        .status-ok { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        adapter = get_db_adapter()
        
        st.subheader("⚙️ Configuración del Sistema")
        
        # Pestañas principales
        tab1, tab2, tab3, tab4 = st.tabs(["🏢 Negocio", "👥 Vendedores", "🏷️ Categorías", "🔧 Sistema"])
        
        with tab1:
            mostrar_config_negocio(adapter)
        
        with tab2:
            mostrar_config_vendedores(adapter)
        
        with tab3:
            mostrar_config_categorias(adapter)
        
        with tab4:
            mostrar_config_sistema(adapter)
    
    except Exception as e:
        st.error(f"❌ Error en configuración: {e}")

def mostrar_config_negocio(adapter):
    """Mostrar configuración del negocio"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("**🏢 Información del Negocio**")
    
    # Obtener configuración actual
    try:
        config_actual = {}
        configs = adapter.execute_query("SELECT clave, valor FROM configuracion")
        for config in configs:
            config_actual[config['clave']] = config['valor']
    except:
        config_actual = {}
    
    with st.form("config_negocio"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_negocio = st.text_input(
                "🏪 Nombre del negocio:",
                value=config_actual.get('nombre_negocio', 'MiChaska'),
                placeholder="Ej: MiChaska"
            )
            
            telefono = st.text_input(
                "📞 Teléfono:",
                value=config_actual.get('telefono', ''),
                placeholder="Ej: +52 55 1234 5678"
            )
            
            email = st.text_input(
                "📧 Email:",
                value=config_actual.get('email', ''),
                placeholder="Ej: contacto@michaska.com"
            )
        
        with col2:
            direccion = st.text_area(
                "📍 Dirección:",
                value=config_actual.get('direccion', ''),
                placeholder="Dirección completa del negocio",
                height=100
            )
            
            rfc = st.text_input(
                "🆔 RFC:",
                value=config_actual.get('rfc', ''),
                placeholder="RFC del negocio"
            )
            
            moneda = st.selectbox(
                "💰 Moneda:",
                ["MXN", "USD", "EUR"],
                index=0 if config_actual.get('moneda', 'MXN') == 'MXN' else 1 if config_actual.get('moneda') == 'USD' else 2
            )
        
        if st.form_submit_button("💾 Guardar Configuración", use_container_width=True, type="primary"):
            guardar_configuracion_negocio(adapter, {
                'nombre_negocio': nombre_negocio,
                'telefono': telefono,
                'email': email,
                'direccion': direccion,
                'rfc': rfc,
                'moneda': moneda
            })
    
    st.markdown('</div>', unsafe_allow_html=True)

def mostrar_config_vendedores(adapter):
    """Mostrar configuración de vendedores"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("**👥 Gestión de Vendedores**")
    
    # Lista de vendedores actuales
    vendedores = adapter.execute_query("SELECT * FROM vendedores ORDER BY nombre")
    
    if vendedores:
        st.markdown("**📋 Vendedores Actuales:**")
        
        for vendedor in vendedores:
            col_nombre, col_estado, col_acciones = st.columns([2, 1, 1])
            
            with col_nombre:
                st.write(f"👤 **{vendedor['nombre']}**")
                fecha_registro = vendedor.get('fecha_registro')
                if fecha_registro:
                    st.write(f"📅 Registrado: {fecha_registro.strftime('%Y-%m-%d')}")
            
            with col_estado:
                estado = "✅ Activo" if vendedor['activo'] else "❌ Inactivo"
                estado_class = "status-ok" if vendedor['activo'] else "status-error"
                st.markdown(f'<span class="{estado_class}">{estado}</span>', unsafe_allow_html=True)
            
            with col_acciones:
                nuevo_estado = not vendedor['activo']
                btn_texto = "❌ Desactivar" if vendedor['activo'] else "✅ Activar"
                
                if st.button(btn_texto, key=f"toggle_vendedor_{vendedor['id']}", use_container_width=True):
                    toggle_vendedor_estado(adapter, vendedor['id'], nuevo_estado)
            
            st.markdown("---")
    
    # Agregar nuevo vendedor
    st.markdown("**➕ Agregar Nuevo Vendedor**")
    
    with st.form("nuevo_vendedor"):
        nombre_vendedor = st.text_input("👤 Nombre completo:", placeholder="Ej: Juan Pérez")
        
        if st.form_submit_button("➕ Agregar Vendedor", use_container_width=True, type="primary"):
            if nombre_vendedor:
                agregar_vendedor(adapter, nombre_vendedor)
            else:
                st.error("❌ El nombre es obligatorio")
    
    st.markdown('</div>', unsafe_allow_html=True)

def mostrar_config_categorias(adapter):
    """Mostrar configuración de categorías"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("**🏷️ Gestión de Categorías**")
    
    # Lista de categorías actuales
    categorias = adapter.execute_query("SELECT * FROM categorias ORDER BY nombre")
    
    if categorias:
        st.markdown("**📋 Categorías Actuales:**")
        
        for categoria in categorias:
            col_nombre, col_estado, col_acciones = st.columns([2, 1, 1])
            
            with col_nombre:
                st.write(f"🏷️ **{categoria['nombre']}**")
                if categoria.get('descripcion'):
                    st.write(f"📝 {categoria['descripcion']}")
            
            with col_estado:
                estado = "✅ Activa" if categoria['activo'] else "❌ Inactiva"
                estado_class = "status-ok" if categoria['activo'] else "status-error"
                st.markdown(f'<span class="{estado_class}">{estado}</span>', unsafe_allow_html=True)
            
            with col_acciones:
                nuevo_estado = not categoria['activo']
                btn_texto = "❌ Desactivar" if categoria['activo'] else "✅ Activar"
                
                if st.button(btn_texto, key=f"toggle_categoria_{categoria['id']}", use_container_width=True):
                    toggle_categoria_estado(adapter, categoria['id'], nuevo_estado)
            
            st.markdown("---")
    
    # Agregar nueva categoría
    st.markdown("**➕ Agregar Nueva Categoría**")
    
    with st.form("nueva_categoria"):
        col_cat1, col_cat2 = st.columns(2)
        
        with col_cat1:
            nombre_categoria = st.text_input("🏷️ Nombre:", placeholder="Ej: Bebidas")
        
        with col_cat2:
            descripcion_categoria = st.text_input("📝 Descripción:", placeholder="Descripción opcional")
        
        if st.form_submit_button("➕ Agregar Categoría", use_container_width=True, type="primary"):
            if nombre_categoria:
                agregar_categoria(adapter, nombre_categoria, descripcion_categoria)
            else:
                st.error("❌ El nombre es obligatorio")
    
    st.markdown('</div>', unsafe_allow_html=True)

def mostrar_config_sistema(adapter):
    """Mostrar configuración del sistema"""
    
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("**🔧 Estado del Sistema**")
    
    # Verificar estado de la base de datos
    try:
        # Probar conexión
        test_result = adapter.execute_query("SELECT 1 as test")
        db_status = "✅ Conectado" if test_result else "❌ Error"
        db_class = "status-ok" if test_result else "status-error"
        
        # Obtener estadísticas
        productos_count = len(adapter.get_productos(activo_only=False))
        categorias_count = len(adapter.get_categorias())
        
        ventas_hoy = adapter.execute_query(
            "SELECT COUNT(*) as count FROM ventas WHERE DATE(fecha) = CURRENT_DATE"
        )
        ventas_hoy_count = ventas_hoy[0]['count'] if ventas_hoy else 0
        
    except Exception as e:
        db_status = f"❌ Error: {str(e)[:50]}..."
        db_class = "status-error"
        productos_count = 0
        categorias_count = 0
        ventas_hoy_count = 0
    
    # Mostrar estado
    col_est1, col_est2, col_est3 = st.columns(3)
    
    with col_est1:
        st.markdown("**🔌 Base de Datos:**")
        st.markdown(f'<span class="{db_class}">{db_status}</span>', unsafe_allow_html=True)
        st.markdown("**📊 Estadísticas:**")
        st.write(f"📦 Productos: {productos_count}")
        st.write(f"🏷️ Categorías: {categorias_count}")
    
    with col_est2:
        st.markdown("**📈 Actividad Hoy:**")
        st.write(f"🛒 Ventas: {ventas_hoy_count}")
        
        try:
            ingresos_hoy = adapter.execute_query(
                "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE DATE(fecha) = CURRENT_DATE"
            )
            ingresos_hoy_total = ingresos_hoy[0]['total'] if ingresos_hoy else 0
            st.write(f"💰 Ingresos: ${ingresos_hoy_total:.2f}")
        except:
            st.write("💰 Ingresos: $0.00")
    
    with col_est3:
        st.markdown("**🚀 Información del Sistema:**")
        st.write("📱 Optimizado para tablets")
        st.write("🔗 PostgreSQL directo")
        st.write("⚡ Sin sincronización híbrida")
        st.write(f"🕐 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    
    # Botones de mantenimiento
    st.markdown("---")
    st.markdown("**🛠️ Herramientas de Mantenimiento:**")
    
    col_mant1, col_mant2, col_mant3 = st.columns(3)
    
    with col_mant1:
        if st.button("🔄 Actualizar Estado", use_container_width=True, key="actualizar_estado"):
            st.rerun()
    
    with col_mant2:
        if st.button("📊 Ver Logs", use_container_width=True, key="ver_logs"):
            st.info("📋 Función de logs disponible en versión administrativa")
    
    with col_mant3:
        if st.button("⚙️ Optimizar BD", use_container_width=True, key="optimizar_bd"):
            try:
                adapter.execute_query("VACUUM ANALYZE")
                st.success("✅ Base de datos optimizada")
            except Exception as e:
                st.error(f"❌ Error optimizando: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def guardar_configuracion_negocio(adapter, config_data):
    """Guardar configuración del negocio"""
    try:
        for clave, valor in config_data.items():
            # Verificar si ya existe
            existing = adapter.execute_query(
                "SELECT id FROM configuracion WHERE clave = %s",
                (clave,)
            )
            
            if existing:
                # Actualizar
                adapter.execute_update(
                    'configuracion',
                    {'valor': valor, 'fecha_modificacion': datetime.now()},
                    'clave = %s',
                    (clave,)
                )
            else:
                # Insertar
                adapter.execute_insert('configuracion', {
                    'clave': clave,
                    'valor': valor,
                    'descripcion': f'Configuración de {clave}',
                    'fecha_modificacion': datetime.now()
                })
        
        st.success("✅ Configuración guardada exitosamente")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error guardando configuración: {e}")

def toggle_vendedor_estado(adapter, vendedor_id, nuevo_estado):
    """Cambiar estado de vendedor"""
    try:
        rows_updated = adapter.execute_update(
            'vendedores',
            {'activo': nuevo_estado},
            'id = %s',
            (vendedor_id,)
        )
        
        if rows_updated > 0:
            estado_texto = "activado" if nuevo_estado else "desactivado"
            st.success(f"✅ Vendedor {estado_texto} exitosamente")
            st.rerun()
        else:
            st.error("❌ Error actualizando vendedor")
    except Exception as e:
        st.error(f"❌ Error: {e}")

def agregar_vendedor(adapter, nombre):
    """Agregar nuevo vendedor"""
    try:
        vendedor_id = adapter.execute_insert('vendedores', {
            'nombre': nombre,
            'activo': True,
            'fecha_registro': datetime.now()
        })
        
        if vendedor_id:
            st.success(f"✅ Vendedor agregado exitosamente! ID: {vendedor_id}")
            st.rerun()
        else:
            st.error("❌ Error agregando vendedor")
    except Exception as e:
        st.error(f"❌ Error: {e}")

def toggle_categoria_estado(adapter, categoria_id, nuevo_estado):
    """Cambiar estado de categoría"""
    try:
        rows_updated = adapter.execute_update(
            'categorias',
            {'activo': nuevo_estado},
            'id = %s',
            (categoria_id,)
        )
        
        if rows_updated > 0:
            estado_texto = "activada" if nuevo_estado else "desactivada"
            st.success(f"✅ Categoría {estado_texto} exitosamente")
            st.rerun()
        else:
            st.error("❌ Error actualizando categoría")
    except Exception as e:
        st.error(f"❌ Error: {e}")

def agregar_categoria(adapter, nombre, descripcion):
    """Agregar nueva categoría"""
    try:
        categoria_id = adapter.execute_insert('categorias', {
            'nombre': nombre,
            'descripcion': descripcion,
            'activo': True,
            'fecha_creacion': datetime.now()
        })
        
        if categoria_id:
            st.success(f"✅ Categoría agregada exitosamente! ID: {categoria_id}")
            st.rerun()
        else:
            st.error("❌ Error agregando categoría")
    except Exception as e:
        st.error(f"❌ Error: {e}")

if __name__ == "__main__":
    show_configuracion()

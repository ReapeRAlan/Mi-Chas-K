"""
Configuración Simplificada
Versión 3.1.0 - Con Adaptador Compatible
"""
import streamlit as st
import os
from database.connection_adapter import db_adapter, execute_query

def mostrar_configuracion_simple():
    """Configuración simplificada del sistema"""
    
    st.title("⚙️ Configuración del Sistema")
    
    # Botón volver
    if st.button("← Volver al inicio"):
        st.session_state.page = 'main'
        st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["🔄 Sincronización", "👥 Vendedores", "🗃️ Base de Datos"])
    
    with tab1:
        st.subheader("🔄 Estado de Sincronización")
        
        # Obtener estado actual
        sync_status = db_adapter.get_sync_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Estado Actual")
            
            if sync_status['database_available']:
                st.success("🌐 **Conectado** a base de datos remota")
            else:
                st.warning("💾 **Modo Local** - Sin conexión remota")
            
            st.info(f"📊 **Estadísticas de Sincronización:**")
            st.write(f"• Pendientes: {sync_status['pending']}")
            st.write(f"• Completadas: {sync_status['completed']}")
            st.write(f"• Fallidas: {sync_status['failed']}")
        
        with col2:
            st.markdown("### Acciones")
            
            if st.button("🔄 Sincronizar Ahora", type="primary"):
                with st.spinner("Sincronizando..."):
                    if db_adapter.force_sync():
                        st.success("✅ Sincronización exitosa")
                    else:
                        st.error("❌ Error en sincronización")
                st.rerun()
            
            if st.button("🔍 Verificar Conexión"):
                if db_adapter.check_database_connection():
                    st.success("✅ Conexión disponible")
                else:
                    st.warning("⚠️ Sin conexión remota")
            
            if st.button("📊 Ver Cola de Sincronización"):
                mostrar_cola_sincronizacion()
    
    with tab2:
        st.subheader("👥 Gestión de Vendedores")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Vendedores Activos")
            
            vendedores = execute_query("SELECT * FROM vendedores WHERE activo = 1")
            
            for vendedor in vendedores:
                st.write(f"• {vendedor['nombre']}")
        
        with col2:
            st.markdown("### Agregar Vendedor")
            
            with st.form("form_vendedor"):
                nombre_vendedor = st.text_input("Nombre del Vendedor")
                
                if st.form_submit_button("➕ Agregar Vendedor"):
                    if nombre_vendedor:
                        if agregar_vendedor(nombre_vendedor):
                            st.success("✅ Vendedor agregado")
                            st.rerun()
                    else:
                        st.error("El nombre es obligatorio")
    
    with tab3:
        st.subheader("🗃️ Información de Base de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Base de Datos Local")
            st.write(f"📍 **Ubicación:** `{db_adapter.local_db_path}`")
            
            # Verificar si existe
            if os.path.exists(db_adapter.local_db_path):
                size = os.path.getsize(db_adapter.local_db_path)
                st.write(f"📏 **Tamaño:** {size:,} bytes")
                st.success("✅ Base de datos local disponible")
            else:
                st.error("❌ Base de datos local no encontrada")
        
        with col2:
            st.markdown("### Base de Datos Remota")
            
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                # Ocultar contraseña en la URL
                url_safe = database_url.split('@')[1] if '@' in database_url else 'No configurada'
                st.write(f"🌐 **Servidor:** {url_safe}")
                
                if db_adapter.check_database_connection():
                    st.success("✅ Conexión disponible")
                else:
                    st.warning("⚠️ No se puede conectar")
            else:
                st.warning("⚠️ URL de base de datos remota no configurada")
        
        # Estadísticas de tablas
        st.markdown("### 📊 Estadísticas de Datos")
        
        try:
            stats = {}
            tables = ['productos', 'categorias', 'vendedores', 'ventas', 'items_venta']
            
            for table in tables:
                result = execute_query(f"SELECT COUNT(*) as count FROM {table}")
                stats[table] = result[0]['count'] if result else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Productos", stats.get('productos', 0))
                st.metric("Categorías", stats.get('categorias', 0))
            
            with col2:
                st.metric("Vendedores", stats.get('vendedores', 0))
                st.metric("Ventas", stats.get('ventas', 0))
            
            with col3:
                st.metric("Items de Venta", stats.get('items_venta', 0))
        
        except Exception as e:
            st.error(f"Error obteniendo estadísticas: {e}")
        
        # Opciones de mantenimiento
        st.markdown("---")
        st.markdown("### 🔧 Mantenimiento")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Limpiar Cola Completada"):
                limpiar_cola_completada()
                st.success("✅ Cola limpiada")
        
        with col2:
            if st.button("🔄 Reinicializar BD Local"):
                st.warning("Esta acción recreará la base de datos local")
        
        with col3:
            if st.button("📊 Verificar Integridad"):
                verificar_integridad()

def mostrar_cola_sincronizacion():
    """Mostrar elementos en cola de sincronización"""
    st.subheader("📋 Cola de Sincronización")
    
    try:
        cola = execute_query("""
            SELECT table_name, operation, timestamp, attempts, status
            FROM sync_queue 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        
        if cola:
            for item in cola:
                status_icon = "⏳" if item['status'] == 'pending' else "✅"
                st.write(f"{status_icon} {item['table_name']} - {item['operation']} - {item['timestamp'][:19]} (intentos: {item['attempts']})")
        else:
            st.info("No hay elementos en la cola")
    
    except Exception as e:
        st.error(f"Error mostrando cola: {e}")

def agregar_vendedor(nombre):
    """Agregar nuevo vendedor"""
    from database.connection_adapter import execute_update
    
    vendedor_data = {
        'table': 'vendedores',
        'operation': 'INSERT',
        'data': {
            'nombre': nombre,
            'activo': True
        }
    }
    
    return execute_update("""
        INSERT INTO vendedores (nombre, activo)
        VALUES (?, ?)
    """, (nombre, True), vendedor_data)

def limpiar_cola_completada():
    """Limpiar elementos completados de la cola"""
    from database.connection_adapter import execute_update
    
    execute_update("DELETE FROM sync_queue WHERE status = 'completed'")

def verificar_integridad():
    """Verificar integridad de la base de datos"""
    try:
        # Verificaciones básicas
        result = execute_query("PRAGMA integrity_check")
        if result and result[0].get('integrity_check') == 'ok':
            st.success("✅ Integridad de base de datos OK")
        else:
            st.warning("⚠️ Problemas de integridad detectados")
    
    except Exception as e:
        st.error(f"Error verificando integridad: {e}")

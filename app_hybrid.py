"""
Aplicación Principal del Sistema Mi Chas-K
Versión 3.0.0 - Modo Híbrido Local/Remoto
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Configurar paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar página
st.set_page_config(
    page_title="Mi Chas-K - Sistema POS",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .status-offline {
        border-left-color: #FF9800;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }
    
    .action-button {
        background: #4CAF50;
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        margin: 0.25rem;
        font-weight: bold;
    }
    
    .sync-info {
        background: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_system():
    """Inicializar el sistema y verificar estado"""
    try:
        from database.connection_adapter import db_adapter
        
        # Verificar estado de conexión
        sync_status = db_adapter.get_sync_status()
        
        return {
            'status': 'ok',
            'sync_status': sync_status,
            'db_adapter': db_adapter
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def show_main_page():
    """Página principal del sistema"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Mi Chas-K - Sistema POS</h1>
        <p>Sistema de Punto de Venta Híbrido - Versión 3.0.0</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar sistema
    system_info = initialize_system()
    
    if system_info['status'] == 'error':
        st.error(f"❌ Error inicializando sistema: {system_info['error']}")
        return
    
    # Mostrar estado de conexión
    sync_status = system_info['sync_status']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if sync_status['database_available']:
            st.markdown("""
            <div class="status-card">
                <h4>🌐 Estado: ONLINE</h4>
                <p>Conectado a base de datos remota</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card status-offline">
                <h4>💾 Estado: OFFLINE</h4>
                <p>Usando base de datos local</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="status-card">
            <h4>🔄 Sincronización</h4>
            <p>Pendientes: {sync_status['pending']}</p>
            <p>Completadas: {sync_status['completed']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Sincronizar Ahora", type="primary"):
            if system_info['db_adapter'].force_sync():
                st.success("✅ Sincronización completada")
                st.rerun()
            else:
                st.warning("⚠️ No se pudo sincronizar. Revisa tu conexión.")
    
    st.markdown("---")
    
    # Menú principal
    st.subheader("📋 Menú Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🛒 **Punto de Venta**", use_container_width=True):
            st.session_state.page = 'punto_venta'
            st.rerun()
    
    with col2:
        if st.button("📦 **Inventario**", use_container_width=True):
            st.session_state.page = 'inventario'
            st.rerun()
    
    with col3:
        if st.button("📊 **Dashboard**", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
    
    with col4:
        if st.button("⚙️ **Configuración**", use_container_width=True):
            st.session_state.page = 'configuracion'
            st.rerun()
    
    # Información del sistema
    if sync_status['pending'] > 0:
        st.markdown(f"""
        <div class="sync-info">
            <h4>🔄 Información de Sincronización</h4>
            <p>Hay <strong>{sync_status['pending']} elementos pendientes</strong> de sincronizar.</p>
            <p>Se sincronizarán automáticamente cuando haya conexión a internet.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Métricas rápidas
    st.markdown("---")
    st.subheader("📈 Resumen Rápido")
    
    try:
        from database.connection_adapter import execute_query
        
        # Obtener métricas básicas
        ventas_hoy = execute_query("""
            SELECT COUNT(*) as total, COALESCE(SUM(total), 0) as monto
            FROM ventas 
            WHERE DATE(fecha) = CURRENT_DATE
        """)
        
        productos_count = execute_query("SELECT COUNT(*) as total FROM productos WHERE activo = 1")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ventas Hoy", ventas_hoy[0]['total'] if ventas_hoy else 0)
        
        with col2:
            monto = ventas_hoy[0]['monto'] if ventas_hoy else 0
            st.metric("Total Hoy", f"${monto:,.2f}")
        
        with col3:
            st.metric("Productos Activos", productos_count[0]['total'] if productos_count else 0)
        
        with col4:
            st.metric("Estado BD", "🟢 Online" if sync_status['database_available'] else "🟡 Local")
    
    except Exception as e:
        st.warning(f"No se pudieron cargar las métricas: {e}")

def show_punto_venta():
    """Página del punto de venta"""
    try:
        from pages.punto_venta_simple import mostrar_punto_venta_simple
        mostrar_punto_venta_simple()
    except ImportError:
        st.error("❌ Módulo de punto de venta no encontrado")
        if st.button("← Volver al inicio"):
            st.session_state.page = 'main'
            st.rerun()

def show_inventario():
    """Página de inventario"""
    try:
        from pages.inventario_simple import mostrar_inventario_simple
        mostrar_inventario_simple()
    except ImportError:
        st.error("❌ Módulo de inventario no encontrado")
        if st.button("← Volver al inicio"):
            st.session_state.page = 'main'
            st.rerun()

def show_dashboard():
    """Página de dashboard"""
    try:
        from pages.dashboard_simple import mostrar_dashboard_simple
        mostrar_dashboard_simple()
    except ImportError:
        st.error("❌ Módulo de dashboard no encontrado")
        if st.button("← Volver al inicio"):
            st.session_state.page = 'main'
            st.rerun()

def show_configuracion():
    """Página de configuración"""
    try:
        from pages.configuracion_simple import mostrar_configuracion_simple
        mostrar_configuracion_simple()
    except ImportError:
        st.error("❌ Módulo de configuración no encontrado")
        if st.button("← Volver al inicio"):
            st.session_state.page = 'main'
            st.rerun()

def main():
    """Función principal"""
    
    # Inicializar estado de sesión
    if 'page' not in st.session_state:
        st.session_state.page = 'main'
    
    # Navegación
    if st.session_state.page == 'main':
        show_main_page()
    elif st.session_state.page == 'punto_venta':
        show_punto_venta()
    elif st.session_state.page == 'inventario':
        show_inventario()
    elif st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'configuracion':
        show_configuracion()
    else:
        st.session_state.page = 'main'
        st.rerun()

if __name__ == "__main__":
    main()

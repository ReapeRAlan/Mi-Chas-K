"""
Aplicación Principal Mi Chas-K - Sistema Híbrido Bidireccional
Versión 4.0.0 - Sincronización Completa y Robusta
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Configurar el path para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Mi Chas-K - Sistema de Ventas Híbrido v4.0",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar colapsado por defecto
)

# Importar adaptador de base de datos
try:
    from database.connection_adapter import DatabaseAdapter
except ImportError as e:
    st.error(f"❌ Error importando adaptador de base de datos: {e}")
    st.stop()

# Inicializar adaptador global
@st.cache_resource
def init_database_adapter():
    """Inicializar adaptador de base de datos (cached)"""
    return DatabaseAdapter()

# CSS personalizado mejorado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .status-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #28a745;
        transition: transform 0.2s ease;
    }
    
    .status-card:hover {
        transform: translateY(-2px);
    }
    
    .status-card.warning {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    }
    
    .status-card.error {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #f8d7da 0%, #fab1a0 100%);
    }
    
    .status-card.info {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, #d1ecf1 0%, #74b9ff 100%);
    }
    
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-top: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    }
    
    /* Navegación horizontal mejorada */
    .nav-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Mejorar botones de navegación */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        min-height: 3rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: #a0aec0;
        transform: none;
        box-shadow: none;
        cursor: not-allowed;
    }
    
    /* Barra de estado del sistema */
    .system-status {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    /* Esconder sidebar completamente */
    .css-1d391kg {
        display: none;
    }
    
    /* Ajustar contenido principal */
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    .nav-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border: none;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        width: 100%;
    }
    
    .nav-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .sync-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #2196f3;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-top: 3px solid #28a745;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    .sidebar .stSelectbox {
        margin: 1rem 0;
    }
    
    .sidebar .stButton {
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def show_system_status():
    """Mostrar estado completo del sistema híbrido"""
    try:
        adapter = init_database_adapter()
        status = adapter.get_system_status()
        sync_status = adapter.get_sync_status()
        
        # Header principal
        st.markdown("""
        <div class="main-header">
            <h1>🛒 Mi Chas-K v4.0</h1>
            <p>Sistema de Punto de Venta con Sincronización Bidireccional</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Estado del sistema en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            local_available = status.get('local_db', {}).get('available', False)
            local_size = status.get('local_db', {}).get('size_mb', 0)
            
            if local_available:
                st.markdown(f"""
                <div class="status-card">
                    <h4>💾 Base de Datos Local</h4>
                    <p><strong>✅ Disponible</strong></p>
                    <small>Tamaño: {local_size:.1f} MB</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-card error">
                    <h4>💾 Base de Datos Local</h4>
                    <p><strong>❌ Error</strong></p>
                    <small>No se puede acceder</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            remote_available = status.get('remote_db', {}).get('available', False)
            
            if remote_available:
                st.markdown("""
                <div class="status-card">
                    <h4>🌐 Base de Datos Remota</h4>
                    <p><strong>✅ Conectada</strong></p>
                    <small>PostgreSQL en Render</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-card warning">
                    <h4>🌐 Base de Datos Remota</h4>
                    <p><strong>⚠️ Desconectada</strong></p>
                    <small>Trabajando en modo offline</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            internet_available = status.get('internet', False)
            
            if internet_available:
                st.markdown("""
                <div class="status-card">
                    <h4>📶 Conectividad</h4>
                    <p><strong>✅ Internet OK</strong></p>
                    <small>Sincronización habilitada</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-card warning">
                    <h4>📶 Conectividad</h4>
                    <p><strong>⚠️ Sin Internet</strong></p>
                    <small>Modo offline solamente</small>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            pending = sync_status.get('pending', 0)
            failed = sync_status.get('failed', 0)
            
            if pending == 0 and failed == 0:
                st.markdown("""
                <div class="status-card">
                    <h4>🔄 Sincronización</h4>
                    <p><strong>✅ Al día</strong></p>
                    <small>Todo sincronizado</small>
                </div>
                """, unsafe_allow_html=True)
            elif pending > 0:
                st.markdown(f"""
                <div class="status-card warning">
                    <h4>🔄 Sincronización</h4>
                    <p><strong>⏳ {pending} pendientes</strong></p>
                    <small>{'❌ ' + str(failed) + ' fallidos' if failed > 0 else 'En proceso'}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card error">
                    <h4>🔄 Sincronización</h4>
                    <p><strong>❌ {failed} fallidos</strong></p>
                    <small>Requiere atención</small>
                </div>
                """, unsafe_allow_html=True)
        
        return adapter, status, sync_status
        
    except Exception as e:
        st.error(f"❌ Error obteniendo estado del sistema: {e}")
        return None, {}, {}

def show_data_statistics(adapter, status):
    """Mostrar estadísticas de datos"""
    try:
        st.subheader("📊 Estadísticas de Datos")
        
        # Obtener datos de tablas locales
        local_tables = status.get('local_db', {}).get('tables', {})
        
        if local_tables:
            cols = st.columns(5)
            table_icons = {
                'productos': '📦',
                'categorias': '🏷️',
                'vendedores': '👤',
                'ventas': '💰',
                'detalle_ventas': '📋'
            }
            
            for idx, (table, count) in enumerate(local_tables.items()):
                with cols[idx % 5]:
                    icon = table_icons.get(table, '📊')
                    st.metric(
                        label=f"{icon} {table.replace('_', ' ').title()}",
                        value=f"{count:,}"
                    )
        
        # Métricas de ventas del día
        st.subheader("📈 Resumen del Día")
        
        today_stats = adapter.execute_query("""
            SELECT 
                COUNT(*) as ventas_count,
                COALESCE(SUM(total), 0) as ventas_total,
                COALESCE(AVG(total), 0) as venta_promedio
            FROM ventas 
            WHERE DATE(fecha) = DATE('now')
        """)
        
        if today_stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🛒 Ventas Hoy", today_stats[0]['ventas_count'])
            
            with col2:
                st.metric("💵 Total Vendido", f"${today_stats[0]['ventas_total']:,.2f}")
            
            with col3:
                st.metric("📊 Venta Promedio", f"${today_stats[0]['venta_promedio']:,.2f}")
        
    except Exception as e:
        st.warning(f"No se pudieron cargar las estadísticas: {e}")

def show_sync_controls(adapter, sync_status):
    """Mostrar controles de sincronización"""
    st.subheader("🔄 Control de Sincronización")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Sincronización Completa", type="primary", use_container_width=True):
            with st.spinner("Ejecutando sincronización bidireccional..."):
                if adapter.force_sync():
                    st.success("✅ Sincronización bidireccional completada exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error en la sincronización. Verifica tu conexión.")
    
    with col2:
        if st.button("📤 Solo Local → Remoto", use_container_width=True):
            with st.spinner("Sincronizando cambios locales..."):
                try:
                    adapter._process_sync_queue()
                    st.success("✅ Cambios locales enviados al servidor")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col3:
        if st.button("📥 Solo Remoto → Local", use_container_width=True):
            with st.spinner("Descargando cambios remotos..."):
                try:
                    adapter._sync_remote_to_local()
                    st.success("✅ Cambios remotos descargados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    # Mostrar información de sincronización si hay elementos pendientes
    if sync_status.get('pending', 0) > 0:
        st.markdown(f"""
        <div class="sync-info">
            <h4>🔄 Información de Sincronización</h4>
            <p>Hay <strong>{sync_status['pending']} operaciones pendientes</strong> de sincronizar con el servidor.</p>
            <p>Se sincronizarán automáticamente cuando haya conexión estable a internet.</p>
            {f"<p><strong>⚠️ {sync_status.get('failed', 0)} operaciones han fallado</strong> y requieren atención.</p>" if sync_status.get('failed', 0) > 0 else ""}
        </div>
        """, unsafe_allow_html=True)

def main():
    """Aplicación principal con navegación mejorada"""
    
    # Mostrar estado del sistema
    adapter, status, sync_status = show_system_status()
    
    if not adapter:
        st.stop()
    
    # Inicializar página actual en session_state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Inicio"
    
    # Navegación horizontal con botones
    st.markdown("---")
    
    # Crear botones de navegación en columnas
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    pages = [
        ("� Inicio", col1),
        ("🛒 Punto de Venta", col2),
        ("📦 Inventario", col3),
        ("📊 Dashboard", col4),
        ("⚙️ Configuración", col5),
        ("� Admin. Sync", col6)
    ]
    
    # Crear botones de navegación
    for page_name, col in pages:
        with col:
            # Determinar si es la página actual
            is_current = st.session_state.current_page == page_name
            
            # Botón con estado visual diferente si es la página actual
            if is_current:
                # Botón activo con color diferente
                button_type = "primary"
                disabled = True
            else:
                button_type = "secondary"
                disabled = False
            
            if st.button(
                page_name, 
                key=f"nav_{page_name}",
                type=button_type,
                disabled=disabled,
                use_container_width=True
            ):
                st.session_state.current_page = page_name
                st.rerun()
    
    st.markdown("---")
    
    # Mostrar información compacta del sistema
    if status.get('remote_db', {}).get('available'):
        sync_info = f"🌐 **Modo Híbrido** | "
    else:
        sync_info = f"💾 **Modo Local** | "
    
    if sync_status.get('pending', 0) > 0:
        sync_info += f"⏳ {sync_status['pending']} ops. pendientes | "
    
    if sync_status.get('failed', 0) > 0:
        sync_info += f"❌ {sync_status['failed']} ops. fallidas | "
    
    sync_info += f"🔄 Estado: {'Activo' if adapter else 'Inactivo'}"
    
    st.markdown(f"<div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 20px;'>{sync_info}</div>", unsafe_allow_html=True)
    
    # Renderizar páginas basado en session_state
    current_page = st.session_state.current_page
    
    try:
        if current_page == "🏠 Inicio":
            show_home_page(adapter, status, sync_status)
            
        elif current_page == "🛒 Punto de Venta":
            from pages.punto_venta_simple import show_punto_venta
            show_punto_venta(adapter)
            
        elif current_page == "📦 Inventario":
            from pages.inventario_simple import show_inventario
            show_inventario(adapter)
            
        elif current_page == "📊 Dashboard":
            from pages.dashboard_simple import show_dashboard
            show_dashboard(adapter)
            
        elif current_page == "⚙️ Configuración":
            from pages.configuracion_simple import show_configuracion
            show_configuracion(adapter)
            
        elif current_page == "🔧 Admin. Sync":
            show_sync_admin_page(adapter, sync_status)
    
    except Exception as e:
        st.error(f"❌ Error cargando página '{current_page}': {str(e)}")
        st.exception(e)

def show_home_page(adapter, status, sync_status):
    """Página de inicio mejorada"""
    
    # Mostrar estadísticas de datos
    show_data_statistics(adapter, status)
    
    st.markdown("---")
    
    # Controles de sincronización
    show_sync_controls(adapter, sync_status)
    
    st.markdown("---")
    
    # Características principales
    st.subheader("✨ Características del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🛒 Punto de Venta Inteligente</h4>
            <ul>
                <li>✅ Interfaz rápida e intuitiva</li>
                <li>✅ Búsqueda de productos avanzada</li>
                <li>✅ Múltiples métodos de pago</li>
                <li>✅ Generación automática de tickets</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Dashboard Analítico</h4>
            <ul>
                <li>✅ Reportes de ventas en tiempo real</li>
                <li>✅ Gráficos interactivos</li>
                <li>✅ Análisis de productos top</li>
                <li>✅ Tendencias de ventas</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🔄 Sincronización Bidireccional</h4>
            <ul>
                <li>✅ Funciona online y offline</li>
                <li>✅ Sincronización automática</li>
                <li>✅ Resolución inteligente de conflictos</li>
                <li>✅ Backup en la nube seguro</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>📦 Gestión de Inventario</h4>
            <ul>
                <li>✅ Control de stock en tiempo real</li>
                <li>✅ Alertas de stock bajo</li>
                <li>✅ Categorización avanzada</li>
                <li>✅ Histórico de movimientos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Accesos rápidos
    st.markdown("---")
    st.subheader("🚀 Accesos Rápidos")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🛒 **Nueva Venta**", use_container_width=True):
            st.session_state.current_page = "🛒 Punto de Venta"
            st.rerun()
    
    with col2:
        if st.button("📦 **Agregar Producto**", use_container_width=True):
            st.session_state.current_page = "📦 Inventario"
            st.rerun()
    
    with col3:
        if st.button("📊 **Ver Reportes**", use_container_width=True):
            st.session_state.current_page = "📊 Dashboard"
            st.rerun()
    
    with col4:
        if st.button("⚙️ **Configurar**", use_container_width=True):
            st.session_state.current_page = "⚙️ Configuración"
            st.rerun()

def show_sync_admin_page(adapter, sync_status):
    """Página de administración de sincronización"""
    st.subheader("🔧 Administrador de Sincronización")
    
    # Información avanzada
    st.info("💡 Para administración completa, ejecuta en terminal: `python sync_admin.py`")
    
    # Métricas de sincronización
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏳ Pendientes", sync_status.get('pending', 0))
    with col2:
        st.metric("✅ Completados", sync_status.get('completed', 0))
    with col3:
        st.metric("❌ Fallidos", sync_status.get('failed', 0))
    with col4:
        online_status = "🟢 Online" if sync_status.get('remote_available') else "🟡 Offline"
        st.metric("🌐 Estado", online_status)
    
    # Controles avanzados
    st.subheader("🛠️ Herramientas de Administración")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Limpiar Cola (Fallidos)", use_container_width=True):
            try:
                cleaned = adapter.execute_update("DELETE FROM sync_queue WHERE status = 'failed'")
                st.success(f"✅ {cleaned or 0} elementos fallidos eliminados")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        if st.button("🔄 Reiniciar Sincronización", use_container_width=True):
            try:
                # Reiniciar elementos con muchos intentos
                reset = adapter.execute_update("""
                    UPDATE sync_queue 
                    SET attempts = 0, status = 'pending' 
                    WHERE attempts >= 3
                """)
                st.success(f"✅ {reset or 0} elementos reiniciados")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("📊 Generar Reporte", use_container_width=True):
            try:
                report_data = {
                    'timestamp': datetime.now().isoformat(),
                    'system_status': adapter.get_system_status(),
                    'sync_status': sync_status
                }
                
                st.download_button(
                    label="💾 Descargar Reporte JSON",
                    data=str(report_data),
                    file_name=f"sync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"❌ Error generando reporte: {e}")
        
        if st.button("🔍 Inspeccionar BD", use_container_width=True):
            st.info("💡 Usa `python system_status.py` para inspección detallada")
    
    # Mostrar elementos pendientes recientes
    if sync_status.get('recent_pending'):
        st.subheader("📋 Operaciones Pendientes Recientes")
        
        for item in sync_status['recent_pending'][:10]:  # Mostrar máximo 10
            with st.expander(f"🔄 {item.get('operation', 'N/A')} en {item.get('table', 'N/A')}"):
                st.write(f"**Timestamp:** {item.get('timestamp', 'N/A')}")
                st.write(f"**Tabla:** {item.get('table', 'N/A')}")
                st.write(f"**Operación:** {item.get('operation', 'N/A')}")

if __name__ == "__main__":
    main()

"""
App principal optimizada para tablets
Sistema MiChaska - PostgreSQL directo
"""
import streamlit as st
import os
from dotenv import load_dotenv
from database.connection_optimized import get_db_adapter, test_database_connection

# Cargar variables de entorno
load_dotenv()

# Configuración de página optimizada para tablets
st.set_page_config(
    page_title="MiChaska - POS",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Sistema MiChaska - Optimizado para Tablets"
    }
)

# CSS personalizado para tablets
st.markdown("""
<style>
    /* Optimización para tablets */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Botones más grandes para touch */
    .stButton > button {
        height: 3rem;
        font-size: 1.2rem;
        width: 100%;
        border-radius: 8px;
    }
    
    /* Input más grandes */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        height: 3rem;
        font-size: 1.1rem;
    }
    
    /* Sidebar optimizada */
    .css-1d391kg {
        width: 280px;
    }
    
    /* Tablas responsive */
    .dataframe {
        font-size: 1rem;
    }
    
    /* Métricas más grandes */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Alertas más visibles */
    .stAlert {
        font-size: 1.1rem;
    }
    
    /* Ocultar elementos innecesarios en tablets */
    .css-10trblm {
        display: none;
    }
    
    /* Espaciado optimizado */
    .stMarkdown h1 {
        margin-bottom: 1rem;
        font-size: 2rem;
    }
    
    .stMarkdown h2 {
        margin-bottom: 0.8rem;
        font-size: 1.5rem;
    }
    
    .stMarkdown h3 {
        margin-bottom: 0.6rem;
        font-size: 1.3rem;
    }
</style>
""", unsafe_allow_html=True)

def check_database_connection():
    """Verificar conexión a base de datos"""
    try:
        if test_database_connection():
            st.sidebar.success("🟢 PostgreSQL Conectado")
            return True
        else:
            st.sidebar.error("🔴 Error de Conexión")
            st.error("❌ No se puede conectar a la base de datos PostgreSQL")
            st.stop()
    except Exception as e:
        st.sidebar.error("🔴 Error de Conexión")
        st.error(f"❌ Error de base de datos: {e}")
        st.stop()

def load_page(page_name):
    """Cargar página específica"""
    try:
        if page_name == "Punto de Venta":
            from pages.punto_venta import show_punto_venta
            show_punto_venta()
        elif page_name == "Dashboard":
            from pages.dashboard import show_dashboard
            show_dashboard()
        elif page_name == "Inventario":
            from pages.inventario import show_inventario
            show_inventario()
        elif page_name == "Órdenes":
            from pages.ordenes_new import show_ordenes
            show_ordenes()
        elif page_name == "Configuración":
            from pages.configuracion_new import show_configuracion
            show_configuracion()
    except Exception as e:
        st.error(f"❌ Error cargando {page_name}: {e}")
        st.error("Verifique que todos los módulos estén instalados correctamente")

def main():
    """Función principal"""
    
    # Verificar conexión de base de datos
    check_database_connection()
    
    # Título principal
    st.title("🛒 MiChaska - Sistema POS")
    
    # Sidebar para navegación
    st.sidebar.title("📱 Navegación")
    
    # Información del sistema
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 Sistema:**")
    st.sidebar.markdown("PostgreSQL Directo")
    st.sidebar.markdown("Optimizado para Tablets")
    
    # Menú de navegación optimizado para tablets
    pages = {
        "🛒 Punto de Venta": "Punto de Venta",
        "📊 Dashboard": "Dashboard", 
        "📦 Inventario": "Inventario",
        "📋 Órdenes": "Órdenes",
        "⚙️ Configuración": "Configuración"
    }
    
    # Selector de página con iconos grandes
    selected_page = st.sidebar.selectbox(
        "Seleccionar página:",
        list(pages.keys()),
        format_func=lambda x: x,
        key="page_selector"
    )
    
    # Información adicional en sidebar
    st.sidebar.markdown("---")
    
    # Estado de la conexión con más detalles
    try:
        adapter = get_db_adapter()
        productos_count = len(adapter.get_productos())
        categorias_count = len(adapter.get_categorias())
        
        st.sidebar.markdown("**📈 Estado:**")
        st.sidebar.markdown(f"- Productos: {productos_count}")
        st.sidebar.markdown(f"- Categorías: {categorias_count}")
        
    except Exception as e:
        st.sidebar.error(f"Error obteniendo estadísticas: {e}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📱 Para tablets:**")
    st.sidebar.markdown("- Botones grandes optimizados")
    st.sidebar.markdown("- Interfaz responsive")
    st.sidebar.markdown("- PostgreSQL directo")
    
    # Cargar página seleccionada
    page_name = pages[selected_page]
    
    # Agregar indicador de página actual
    st.markdown(f"### {selected_page}")
    
    # Cargar contenido de la página
    load_page(page_name)
    
    # Footer optimizado para tablets
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🛒 MiChaska POS**")
    
    with col2:
        st.markdown("**📱 Optimizado para Tablets**")
    
    with col3:
        st.markdown("**🔧 PostgreSQL Directo**")

if __name__ == "__main__":
    main()

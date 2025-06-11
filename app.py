"""
Aplicación principal del Sistema de Facturación MiChaska
Desarrollado con Streamlit - Adaptado para Render con PostgreSQL
"""
import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar la página
st.set_page_config(
    page_title="MiChaska - Sistema de Facturación",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ReapeRAlan/Mi-Chas-K',
        'Report a bug': 'https://github.com/ReapeRAlan/Mi-Chas-K/issues',
        'About': """
        # MiChaska - Sistema de Facturación
        
        Sistema de punto de venta desarrollado en Python con Streamlit.
        
        **Características:**
        - Punto de venta intuitivo
        - Gestión de inventario
        - Dashboard de ventas
        - Generación de tickets PDF
        - Base de datos PostgreSQL en la nube
        
        Versión: 2.0.0 - Render Edition
        """
    }
)

# Inicializar la base de datos
def init_app():
    """Inicializa la aplicación y la base de datos"""
    try:
        from database.connection import init_database
        init_database()
        st.success("✅ Conectado a PostgreSQL exitosamente", icon="🗄️")
    except Exception as e:
        st.error(f"❌ Error al conectar con la base de datos: {str(e)}")
        st.info("🔧 Verifica que las variables de entorno estén configuradas correctamente")
        st.stop()

def main():
    """Función principal de la aplicación"""
    # Inicializar aplicación
    init_app()
    
    # CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    
    .product-button {
        background: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .product-button:hover {
        border-color: #1f77b4;
        background: #e3f2fd;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(45deg, #1f77b4, #ff7f0e);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar para navegación
    with st.sidebar:
        # Logo/Header del sidebar
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🛒 MiChaska</h2>
            <p>Sistema de Facturación</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navegación principal
        st.markdown("### 📋 Navegación")
        
        # Opciones de navegación
        paginas = {
            "🛒 Punto de Venta": "punto_venta",
            "📦 Inventario": "inventario", 
            "📊 Dashboard": "dashboard",
            "⚙️ Configuración": "configuracion"
        }
        
        # Selector de página
        pagina_seleccionada = st.selectbox(
            "Seleccionar página:",
            list(paginas.keys()),
            key="navegacion_principal"
        )
        
        st.divider()
        
        # Información rápida
        mostrar_info_rapida()
        
        st.divider()
        
        # Footer del sidebar
        st.markdown("""
        <small>
        💡 **Tip:** Usa los botones grandes en el punto de venta para agregar productos rápidamente al carrito.
        
        📞 **Soporte:** Contacta al administrador para ayuda técnica.
        </small>
        """, unsafe_allow_html=True)
    
    # Contenido principal basado en la página seleccionada
    pagina_codigo = paginas[pagina_seleccionada]
    
    if pagina_codigo == "punto_venta":
        from pages.punto_venta import mostrar_punto_venta
        mostrar_punto_venta()
        
    elif pagina_codigo == "inventario":
        from pages.inventario import mostrar_inventario
        mostrar_inventario()
        
    elif pagina_codigo == "dashboard":
        from pages.dashboard import mostrar_dashboard
        mostrar_dashboard()
        
    elif pagina_codigo == "configuracion":
        from pages.configuracion import mostrar_configuracion
        mostrar_configuracion()

def mostrar_info_rapida():
    """Muestra información rápida en el sidebar"""
    st.markdown("### 📊 Info Rápida")
    
    try:
        from database.models import Producto, Venta
        from database.connection import execute_query
        
        # Productos con stock bajo
        productos_stock_bajo = len([p for p in Producto.get_all() if p.stock <= 5])
        
        # Ventas de hoy
        ventas_hoy = Venta.get_ventas_hoy()
        total_hoy = sum(venta.total for venta in ventas_hoy)
        
        # Mostrar métricas
        st.metric("Stock Bajo", productos_stock_bajo)
        st.metric("Ventas Hoy", len(ventas_hoy))
        st.metric("Ingresos Hoy", f"{total_hoy:.2f} MXN")
        
        # Estado del carrito
        if 'carrito' in st.session_state:
            items_carrito = st.session_state.carrito.cantidad_items
            if items_carrito > 0:
                st.success(f"🛒 {items_carrito} items en carrito")
        
    except Exception as e:
        st.error("Error al cargar info rápida")

def mostrar_bienvenida():
    """Muestra la página de bienvenida"""
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Bienvenido a MiChaska</h1>
        <p>Sistema de Facturación y Punto de Venta</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tarjetas de características principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🛒 Punto de Venta</h3>
            <p>Interfaz intuitiva con botones grandes para agregar productos al carrito de forma rápida.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📦 Inventario</h3>
            <p>Gestión completa de productos, stock, precios y categorías.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Dashboard</h3>
            <p>Estadísticas de ventas, gráficos y reportes detallados.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>🧾 Tickets</h3>
            <p>Generación automática de tickets en PDF listos para imprimir.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Instrucciones rápidas
    st.markdown("### 🚀 Inicio Rápido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Para hacer una venta:**
        1. Ve a 🛒 **Punto de Venta**
        2. Haz clic en los productos para agregarlos al carrito
        3. Ajusta cantidades si es necesario
        4. Haz clic en **Procesar Venta**
        5. Completa la información y confirma
        6. Genera e imprime el ticket
        """)
    
    with col2:
        st.markdown("""
        **Para gestionar productos:**
        1. Ve a 📦 **Inventario**
        2. Usa la pestaña **Agregar Producto** para nuevos items
        3. Edita productos existentes desde **Ver Productos**
        4. Gestiona categorías en la pestaña **Categorías**
        """)

if __name__ == "__main__":
    main()

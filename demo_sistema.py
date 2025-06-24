#!/usr/bin/env python3
"""
Demo del Sistema Mi Chas-K v3.0.0 - Híbrido
"""

import streamlit as st
import os
import sys
import sqlite3
from pathlib import Path

# Configurar página
st.set_page_config(
    page_title="Mi Chas-K v3.0.0 Demo",
    page_icon="🛒",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .demo-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
        border: 2px solid #e9ecef;
    }
    
    .success-box {
        background: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_demo_database():
    """Crear base de datos demo con datos de ejemplo"""
    os.makedirs('data', exist_ok=True)
    db_path = 'data/demo_database.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Crear tablas
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                activo INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                categoria_id INTEGER,
                activo INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                vendedor TEXT DEFAULT 'Sistema'
            );
            
            DELETE FROM categorias;
            DELETE FROM productos;
            DELETE FROM ventas;
            
            INSERT INTO categorias (nombre) VALUES 
                ('Bebidas'), ('Comida'), ('Snacks');
            
            INSERT INTO productos (nombre, precio, stock, categoria_id) VALUES 
                ('Coca Cola', 2.50, 50, 1),
                ('Agua', 1.00, 100, 1),
                ('Hamburguesa', 8.50, 20, 2),
                ('Pizza', 12.00, 15, 2),
                ('Papas', 3.00, 30, 3),
                ('Galletas', 2.00, 40, 3);
            
            INSERT INTO ventas (total, vendedor) VALUES 
                (15.50, 'Juan'),
                (8.50, 'Maria'),
                (25.00, 'Pedro'),
                (6.00, 'Ana');
        """)
        
        conn.commit()
    
    return db_path

def get_demo_stats(db_path):
    """Obtener estadísticas de demo"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM productos")
        productos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        ventas = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total) FROM ventas")
        total_ventas = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT nombre, precio, stock FROM productos LIMIT 3")
        productos_sample = cursor.fetchall()
    
    return {
        'productos': productos,
        'ventas': ventas,
        'total_ventas': total_ventas,
        'productos_sample': productos_sample
    }

def main():
    # Header principal
    st.markdown("""
    <div class="demo-header">
        <h1>🛒 Mi Chas-K v3.0.0</h1>
        <h2>Sistema de Punto de Venta Híbrido</h2>
        <p><strong>DEMO - Funcionamiento Local/Remoto</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Crear base de datos demo
    db_path = create_demo_database()
    stats = get_demo_stats(db_path)
    
    # Estado del sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="status-card">
            <h3>🟢 Sistema ONLINE</h3>
            <p>Modo híbrido activado</p>
            <p>Base de datos local funcionando</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="status-card">
            <h3>📊 Datos Demo</h3>
            <p>6 productos de ejemplo</p>
            <p>4 ventas simuladas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="status-card">
            <h3>🔄 Sincronización</h3>
            <p>0 elementos pendientes</p>
            <p>Sistema listo</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Métricas principales
    st.markdown("---")
    st.subheader("📈 Dashboard Demo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Productos", stats['productos'])
    
    with col2:
        st.metric("Ventas", stats['ventas'])
    
    with col3:
        st.metric("Total Vendido", f"${stats['total_ventas']:.2f}")
    
    with col4:
        st.metric("Estado", "🟢 Activo")
    
    # Características principales
    st.markdown("---")
    st.subheader("🚀 Características Principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3>🛒 Punto de Venta</h3>
            <p>• Interfaz intuitiva</p>
            <p>• Carrito de compras</p>
            <p>• Múltiples métodos de pago</p>
            <p>• Actualización automática de stock</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3>📦 Inventario</h3>
            <p>• Gestión de productos</p>
            <p>• Control de categorías</p>
            <p>• Actualización de stock</p>
            <p>• Productos activos/inactivos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h3>📊 Reportes</h3>
            <p>• Dashboard en tiempo real</p>
            <p>• Ventas por período</p>
            <p>• Productos más vendidos</p>
            <p>• Exportación de datos</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Modo híbrido
    st.markdown("---")
    st.subheader("🔄 Sistema Híbrido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="success-box">
            <h4>💾 Modo Local (OFFLINE)</h4>
            <p><strong>✅ Funciona sin internet</strong></p>
            <p>• Base de datos SQLite local</p>
            <p>• Todas las funciones disponibles</p>
            <p>• Datos guardados localmente</p>
            <p>• Cola de sincronización automática</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-box">
            <h4>🌐 Modo Remoto (ONLINE)</h4>
            <p><strong>✅ Sincronización automática</strong></p>
            <p>• Conexión a PostgreSQL en la nube</p>
            <p>• Sincronización en tiempo real</p>
            <p>• Backup automático</p>
            <p>• Acceso multi-dispositivo</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Instalación para Windows
    st.markdown("---")
    st.subheader("🖥️ Instalación en Windows")
    
    st.markdown("""
    <div class="success-box">
        <h4>⚡ Instalación Automática</h4>
        <p><strong>1 archivo instala todo el sistema:</strong></p>
        <ol>
            <li>Descargar <code>install_windows.bat</code></li>
            <li>Ejecutar como administrador</li>
            <li>El script instala Python + dependencias automáticamente</li>
            <li>Configurar base de datos en archivo .env</li>
            <li>Ejecutar <code>menu.bat</code> para iniciar</li>
        </ol>
        <p><strong>¡Sistema listo en 5 minutos!</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Productos demo
    st.markdown("---")
    st.subheader("📦 Productos Demo")
    
    st.write("**Productos disponibles en la demo:**")
    for producto in stats['productos_sample']:
        nombre, precio, stock = producto
        st.write(f"• **{nombre}** - ${precio:.2f} (Stock: {stock})")
    
    # Acciones
    st.markdown("---")
    st.subheader("🎯 Próximos Pasos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛒 **Ir al Punto de Venta**", use_container_width=True):
            st.info("En la versión completa, esto abriría el punto de venta")
    
    with col2:
        if st.button("📦 **Gestionar Inventario**", use_container_width=True):
            st.info("En la versión completa, esto abriría el inventario")
    
    with col3:
        if st.button("📊 **Ver Dashboard**", use_container_width=True):
            st.info("En la versión completa, esto abriría el dashboard")
    
    # Información técnica
    st.markdown("---")
    st.subheader("🔧 Información Técnica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Tecnologías:**")
        st.write("• Python 3.9+")
        st.write("• Streamlit (UI)")
        st.write("• SQLite (Local)")
        st.write("• PostgreSQL (Remoto)")
        st.write("• Threading (Sincronización)")
    
    with col2:
        st.write("**Archivos del sistema:**")
        st.write(f"• Base de datos: `{db_path}`")
        st.write("• Configuración: `.env`")
        st.write("• Aplicación: `app_hybrid.py`")
        st.write("• Instalador: `install_windows.bat`")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 10px;">
        <h3>🎉 Mi Chas-K v3.0.0 - Sistema Híbrido</h3>
        <p><strong>El sistema de punto de venta que funciona online y offline</strong></p>
        <p>Desarrollado para pequeños negocios que necesitan confiabilidad</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

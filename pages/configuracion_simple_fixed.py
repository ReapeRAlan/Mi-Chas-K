"""
Configuración Simplificada - Versión Funcional
"""
import streamlit as st
import sqlite3
import os

def show_configuracion(adapter):
    """Configuración simplificada"""
    
    st.title("⚙️ Configuración del Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🔧 General", "🔄 Sincronización", "💾 Base de Datos"])
    
    with tab1:
        st.subheader("🔧 Configuración General")
        
        st.info("💡 Configuración básica del sistema")
        
        # Información del sistema
        with st.expander("📊 Información del Sistema"):
            try:
                # Conteos básicos
                productos = adapter.execute_query("SELECT COUNT(*) as count FROM productos")
                ventas = adapter.execute_query("SELECT COUNT(*) as count FROM ventas")
                categorias = adapter.execute_query("SELECT COUNT(*) as count FROM categorias")
                
                st.metric("📦 Total Productos", productos[0]['count'] if productos else 0)
                st.metric("💰 Total Ventas", ventas[0]['count'] if ventas else 0)
                st.metric("🏷️ Total Categorías", categorias[0]['count'] if categorias else 0)
                
            except Exception as e:
                st.error(f"Error obteniendo información: {e}")
        
        # Configuración de vendedores
        with st.expander("👤 Gestión de Vendedores"):
            try:
                vendedores = adapter.execute_query("SELECT * FROM vendedores ORDER BY nombre")
                
                if vendedores:
                    st.write("**Vendedores registrados:**")
                    for vendedor in vendedores:
                        estado = "✅ Activo" if vendedor.get('activo', True) else "❌ Inactivo"
                        st.write(f"- {vendedor['nombre']} ({estado})")
                else:
                    st.info("No hay vendedores registrados")
                
                # Agregar vendedor
                with st.form("agregar_vendedor"):
                    nombre_vendedor = st.text_input("👤 Nombre del Vendedor")
                    
                    if st.form_submit_button("➕ Agregar Vendedor"):
                        if nombre_vendedor:
                            try:
                                adapter.execute_update("""
                                    INSERT INTO vendedores (nombre, activo)
                                    VALUES (?, ?)
                                """, (nombre_vendedor, True))
                                st.success("✅ Vendedor agregado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        else:
                            st.error("❌ El nombre es obligatorio")
                            
            except Exception as e:
                st.error(f"Error en vendedores: {e}")
    
    with tab2:
        st.subheader("🔄 Estado de Sincronización")
        
        try:
            # Estado de la cola
            cola_stats = adapter.execute_query("""
                SELECT status, COUNT(*) as count
                FROM sync_queue
                GROUP BY status
            """)
            
            if cola_stats:
                st.write("**Estado de la cola de sincronización:**")
                for stat in cola_stats:
                    icon = {'pending': '⏳', 'completed': '✅', 'failed': '❌'}.get(stat['status'], '📋')
                    st.write(f"{icon} {stat['status']}: {stat['count']} elementos")
            else:
                st.info("✅ Cola de sincronización vacía")
            
            # Controles de sincronización
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🧹 Limpiar Cola Completados", use_container_width=True):
                    try:
                        adapter.execute_update("DELETE FROM sync_queue WHERE status = 'completed'")
                        st.success("✅ Cola limpiada")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with col2:
                if st.button("🔄 Forzar Sincronización", use_container_width=True):
                    try:
                        if hasattr(adapter, 'force_sync'):
                            if adapter.force_sync():
                                st.success("✅ Sincronización completada")
                            else:
                                st.warning("⚠️ No se pudo sincronizar")
                        else:
                            st.info("💡 Función de sincronización no disponible")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        except Exception as e:
            st.error(f"Error en sincronización: {e}")
    
    with tab3:
        st.subheader("💾 Mantenimiento de Base de Datos")
        
        # Información de la base de datos
        try:
            db_path = os.path.join('data', 'local_database.db')
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
                st.metric("📊 Tamaño de BD Local", f"{db_size:.1f} MB")
            else:
                st.warning("⚠️ Base de datos local no encontrada")
        except Exception as e:
            st.error(f"Error verificando BD: {e}")
        
        # Herramientas de mantenimiento
        st.write("**Herramientas de mantenimiento:**")
        
        if st.button("🔍 Verificar Integridad", use_container_width=True):
            try:
                # Verificación simple
                tablas = ['productos', 'categorias', 'ventas', 'detalle_ventas', 'vendedores']
                for tabla in tablas:
                    try:
                        result = adapter.execute_query(f"SELECT COUNT(*) as count FROM {tabla}")
                        st.write(f"✅ {tabla}: {result[0]['count']} registros")
                    except Exception as e:
                        st.write(f"❌ {tabla}: Error - {e}")
                
                st.success("✅ Verificación completada")
                
            except Exception as e:
                st.error(f"Error en verificación: {e}")
        
        # Información del sistema híbrido
        with st.expander("🌐 Estado del Sistema Híbrido"):
            try:
                if hasattr(adapter, 'remote_available'):
                    if adapter.remote_available:
                        st.success("🌐 Conectado a la base de datos remota")
                    else:
                        st.warning("💾 Trabajando solo con base de datos local")
                
                if hasattr(adapter, 'check_internet_connection'):
                    if adapter.check_internet_connection():
                        st.success("📶 Conexión a internet disponible")
                    else:
                        st.warning("📶 Sin conexión a internet")
                
            except Exception as e:
                st.error(f"Error verificando estado híbrido: {e}")

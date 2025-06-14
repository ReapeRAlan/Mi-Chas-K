"""
Página de configuración del sistema
"""
import streamlit as st
from database.connection import execute_query, execute_update
from utils.helpers import show_success_message, show_error_message
from utils.timezone_utils import get_mexico_datetime

def mostrar_configuracion():
    """Página principal de configuración"""
    st.title("⚙️ Configuración del Sistema")
    
    # Pestañas para organizar configuraciones
    tab1, tab2, tab3 = st.tabs(["🏪 Negocio", "💰 Facturación", "🔧 Sistema"])
    
    with tab1:
        mostrar_config_negocio()
    
    with tab2:
        mostrar_config_facturacion()
    
    with tab3:
        mostrar_config_sistema()

def mostrar_config_negocio():
    """Configuración de datos del negocio"""
    st.subheader("🏪 Información del Negocio")
    
    # Obtener configuración actual
    config_actual = obtener_configuracion_actual()
    
    with st.form("config_negocio"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_negocio = st.text_input(
                "Nombre del negocio:",
                value=config_actual.get('nombre_negocio', 'MiChaska')
            )
            
            direccion = st.text_input(
                "Dirección:",
                value=config_actual.get('direccion', '')
            )
        
        with col2:
            telefono = st.text_input(
                "Teléfono:",
                value=config_actual.get('telefono', '')
            )
            
            email = st.text_input(
                "Email:",
                value=config_actual.get('email', '')
            )
        
        mensaje_ticket = st.text_area(
            "Mensaje en el ticket:",
            value=config_actual.get('mensaje_ticket', 'Gracias por su compra'),
            help="Este mensaje aparecerá al final de cada ticket"
        )
        
        if st.form_submit_button("💾 Guardar Configuración", type="primary"):
            try:
                # Actualizar cada configuración
                configuraciones = {
                    'nombre_negocio': nombre_negocio,
                    'direccion': direccion,
                    'telefono': telefono,
                    'email': email,
                    'mensaje_ticket': mensaje_ticket
                }
                
                for clave, valor in configuraciones.items():
                    execute_update(
                        "UPDATE configuracion SET valor = %s WHERE clave = %s",
                        (valor, clave)
                    )
                
                show_success_message("Configuración del negocio actualizada correctamente")
                
            except Exception as e:
                show_error_message(f"Error al actualizar configuración: {str(e)}")

def mostrar_config_facturacion():
    """Configuración de facturación"""
    st.subheader("💰 Configuración de Facturación")
    
    config_actual = obtener_configuracion_actual()
    
    with st.form("config_facturacion"):
        col1, col2 = st.columns(2)
        
        with col1:
            moneda = st.selectbox(
                "Moneda:",
                ["BOB", "USD", "EUR", "PEN", "COP", "MXN"],
                index=0 if config_actual.get('moneda', 'BOB') == 'BOB' else 0
            )
            
            impuesto_porcentaje = st.number_input(
                "Porcentaje de impuesto (%):",
                min_value=0.0,
                max_value=50.0,
                value=float(config_actual.get('impuesto_porcentaje', 0)),
                step=0.1
            )
        
        with col2:
            # Configuraciones adicionales de facturación
            numeracion_automatica = st.checkbox(
                "Numeración automática de tickets",
                value=True,
                help="Los tickets se numerarán automáticamente"
            )
            
            mostrar_stock_ticket = st.checkbox(
                "Mostrar stock en tickets",
                value=False,
                help="Incluir información de stock en los tickets"
            )
        
        st.write("**Formato de ticket:**")
        ancho_ticket = st.selectbox(
            "Ancho de ticket:",
            ["80mm", "58mm", "A4"],
            index=0,
            help="Ancho del papel para impresión de tickets"
        )
        
        if st.form_submit_button("💾 Guardar Configuración", type="primary"):
            try:
                configuraciones = {
                    'moneda': moneda,
                    'impuesto_porcentaje': str(impuesto_porcentaje),
                    'numeracion_automatica': str(numeracion_automatica),
                    'mostrar_stock_ticket': str(mostrar_stock_ticket),
                    'ancho_ticket': ancho_ticket
                }
                
                for clave, valor in configuraciones.items():
                    # Insertar o actualizar usando UPSERT de PostgreSQL
                    execute_update(
                        """INSERT INTO configuracion (clave, valor) VALUES (%s, %s) 
                           ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor""",
                        (clave, valor)
                    )
                
                show_success_message("Configuración de facturación actualizada correctamente")
                
            except Exception as e:
                show_error_message(f"Error al actualizar configuración: {str(e)}")

def mostrar_config_sistema():
    """Configuración del sistema"""
    st.subheader("🔧 Configuración del Sistema")
    
    # Información de la base de datos
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Información de la Base de Datos:**")
        
        # Contar registros
        try:
            productos_count = execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = TRUE")[0]['count']
            ventas_count = execute_query("SELECT COUNT(*) as count FROM ventas")[0]['count']
            categorias_count = execute_query("SELECT COUNT(*) as count FROM categorias WHERE activo = TRUE")[0]['count']
            
            st.metric("Productos activos", productos_count)
            st.metric("Total de ventas", ventas_count)
            st.metric("Categorías activas", categorias_count)
            
        except Exception as e:
            st.error(f"Error al obtener estadísticas: {str(e)}")
    
    with col2:
        st.write("**Acciones de Mantenimiento:**")
        
        if st.button("🗃️ Respaldar Base de Datos"):
            realizar_respaldo()
        
        # Sección de limpieza de ventas integrada
        st.write("**Limpiar Ventas Antiguas:**")
        
        with st.form("limpiar_ventas_form"):
            dias_antiguedad = st.number_input(
                "Eliminar ventas anteriores a (días):",
                min_value=30,
                max_value=3650,
                value=365
            )
            
            st.warning(f"⚠️ Esto eliminará permanentemente todas las ventas anteriores a {dias_antiguedad} días")
            
            confirmacion = st.checkbox("Confirmo que quiero eliminar estos datos")
            
            if st.form_submit_button("🗑️ Eliminar Ventas Antiguas") and confirmacion:
                try:
                    from datetime import datetime, timedelta
                    
                    # Calcular fecha límite
                    fecha_limite = get_mexico_datetime() - timedelta(days=dias_antiguedad)
                    fecha_str = fecha_limite.strftime('%Y-%m-%d')
                    
                    # Contar ventas que se van a eliminar
                    ventas_a_eliminar = execute_query(
                        "SELECT COUNT(*) as count FROM ventas WHERE DATE(fecha) < %s",
                        (fecha_str,)
                    )[0]['count']
                    
                    if ventas_a_eliminar == 0:
                        st.info("No hay ventas antiguas para eliminar")
                    else:
                        # Primero eliminar detalles de venta
                        execute_update(
                            "DELETE FROM detalle_ventas WHERE venta_id IN (SELECT id FROM ventas WHERE DATE(fecha) < %s)",
                            (fecha_str,)
                        )
                        
                        # Luego eliminar ventas
                        execute_update(
                            "DELETE FROM ventas WHERE DATE(fecha) < %s",
                            (fecha_str,)
                        )
                        
                        show_success_message(f"✅ {ventas_a_eliminar} ventas antiguas eliminadas correctamente")
                        st.rerun()
                        
                except Exception as e:
                    show_error_message(f"❌ Error al eliminar ventas: {str(e)}")
        
        if st.button("📊 Optimizar Base de Datos"):
            optimizar_base_datos()
    
    # Configuraciones avanzadas
    st.write("**Configuraciones Avanzadas:**")
    
    with st.form("config_avanzada"):
        dias_mantener_ventas = st.number_input(
            "Días para mantener ventas (0 = mantener todas):",
            min_value=0,
            max_value=3650,
            value=365,
            help="Ventas más antiguas que este número de días pueden ser archivadas"
        )
        
        activar_logs = st.checkbox(
            "Activar logs del sistema",
            value=False,
            help="Registrar actividades del sistema en archivos de log"
        )
        
        if st.form_submit_button("💾 Guardar Configuración Avanzada"):
            try:
                configuraciones = {
                    'dias_mantener_ventas': str(dias_mantener_ventas),
                    'activar_logs': str(activar_logs)
                }
                
                for clave, valor in configuraciones.items():
                    execute_update(
                        """INSERT INTO configuracion (clave, valor) VALUES (%s, %s) 
                           ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor""",
                        (clave, valor)
                    )
                
                show_success_message("Configuración avanzada actualizada correctamente")
                
            except Exception as e:
                show_error_message(f"Error al actualizar configuración: {str(e)}")

def obtener_configuracion_actual():
    """Obtiene toda la configuración actual del sistema"""
    try:
        rows = execute_query("SELECT clave, valor FROM configuracion")
        return {row['clave']: row['valor'] for row in rows}
    except Exception:
        return {}

def realizar_respaldo():
    """Realiza un respaldo de la base de datos"""
    try:
        import shutil
        from datetime import datetime
        import os
        
        # Crear directorio de respaldos si no existe
        os.makedirs("respaldos", exist_ok=True)
        
        # Nombre del archivo de respaldo
        timestamp = get_mexico_datetime().strftime("%Y%m%d_%H%M%S")
        archivo_respaldo = f"respaldos/michaska_backup_{timestamp}.db"
        
        # Copiar la base de datos
        shutil.copy2("michaska.db", archivo_respaldo)
        
        show_success_message(f"Respaldo creado exitosamente: {archivo_respaldo}")
        
        # Ofrecer descarga del respaldo
        with open(archivo_respaldo, "rb") as file:
            st.download_button(
                label="📥 Descargar Respaldo",
                data=file,
                file_name=f"michaska_backup_{timestamp}.db",
                mime="application/octet-stream"
            )
            
    except Exception as e:
        show_error_message(f"Error al crear respaldo: {str(e)}")

def mostrar_dialogo_limpieza():
    """Muestra opciones para limpiar datos antiguos"""
    st.write("**Limpiar Ventas Antiguas:**")
    
    with st.form("limpiar_ventas"):
        dias_antiguedad = st.number_input(
            "Eliminar ventas anteriores a (días):",
            min_value=30,
            max_value=3650,
            value=365
        )
        
        st.warning(f"⚠️ Esto eliminará permanentemente todas las ventas anteriores a {dias_antiguedad} días")
        
        confirmacion = st.checkbox("Confirmo que quiero eliminar estos datos")
        
        if st.form_submit_button("🗑️ Eliminar Ventas Antiguas") and confirmacion:
            try:
                from datetime import datetime, timedelta
                fecha_limite = get_mexico_datetime() - timedelta(days=dias_antiguedad)
                
                # Primero eliminar detalles de venta
                execute_update(
                    "DELETE FROM detalle_ventas WHERE venta_id IN (SELECT id FROM ventas WHERE fecha < %s)",
                    (fecha_limite.isoformat(),)
                )
                
                # Luego eliminar ventas
                resultado = execute_update(
                    "DELETE FROM ventas WHERE fecha < %s",
                    (fecha_limite.isoformat(),)
                )
                
                show_success_message(f"Ventas antiguas eliminadas correctamente")
                
            except Exception as e:
                show_error_message(f"Error al eliminar ventas: {str(e)}")

def optimizar_base_datos():
    """Optimiza la base de datos"""
    try:
        execute_update("VACUUM")
        execute_update("ANALYZE")
        show_success_message("Base de datos optimizada correctamente")
        
    except Exception as e:
        show_error_message(f"Error al optimizar base de datos: {str(e)}")

# Función principal para ejecutar la página
def main():
    mostrar_configuracion()

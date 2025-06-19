"""
Página del dashboard con estadísticas, reportes y gestión de gastos
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.models import Venta, Producto, GastoDiario, CorteCaja, Vendedor
from database.connection import execute_query
from utils.helpers import format_currency, get_date_range_options, show_success_message, show_error_message
from utils.timezone_utils import get_mexico_date_str, get_mexico_datetime
import io
import numpy as np

def mostrar_dashboard():
    """Página principal del dashboard"""
    st.title("📊 Dashboard Mi Chas-K")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Análisis de Ventas", 
        "💰 Gestión de Gastos", 
        "📋 Corte de Caja",
        "📊 Resumen Financiero"
    ])
    
    with tab1:
        mostrar_analisis_ventas()
    
    with tab2:
        mostrar_gestion_gastos()
    
    with tab3:
        mostrar_corte_caja()
    
    with tab4:
        mostrar_resumen_financiero()

def mostrar_analisis_ventas():
    """Análisis de ventas con gráficos y métricas"""
    st.subheader("📈 Análisis de Ventas")
    
    # Selector de período
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        opciones_fecha = get_date_range_options()
        periodo_seleccionado = st.selectbox(
            "Período a analizar:",
            list(opciones_fecha.keys())
        )
        fecha_inicio, fecha_fin = opciones_fecha[periodo_seleccionado]
    
    with col2:
        fecha_inicio_custom = st.date_input("Desde:", value=fecha_inicio, key="dashboard_fecha_inicio")
    
    with col3:
        fecha_fin_custom = st.date_input("Hasta:", value=fecha_fin, key="dashboard_fecha_fin")
    
    # Usar fechas personalizadas si son diferentes
    if fecha_inicio_custom != fecha_inicio or fecha_fin_custom != fecha_fin:
        fecha_inicio, fecha_fin = fecha_inicio_custom, fecha_fin_custom
    
    # Obtener datos del período
    ventas = Venta.get_by_fecha(str(fecha_inicio), str(fecha_fin))
    
    if not ventas:
        st.warning(f"No hay ventas registradas en el período del {fecha_inicio} al {fecha_fin}")
        return
    
    # Métricas principales
    mostrar_metricas_ventas(ventas)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        mostrar_grafico_ventas_diarias(ventas)
        mostrar_grafico_metodos_pago(ventas)
    
    with col2:
        mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin)
        mostrar_grafico_vendedores(ventas)

def mostrar_gestion_gastos():
    """Gestión de gastos diarios"""
    st.subheader("💰 Gestión de Gastos")
    
    # Selector de fecha
    fecha_seleccionada = st.date_input(
        "Fecha:",
        value=get_mexico_datetime().date(),
        key="fecha_gastos"
    )
    fecha_str = str(fecha_seleccionada)
    
    # Pestañas para gastos
    tab1, tab2 = st.tabs(["➕ Agregar Gasto", "📋 Ver Gastos"])
    
    with tab1:
        agregar_gasto(fecha_str)
    
    with tab2:
        ver_gastos(fecha_str)

def agregar_gasto(fecha: str):
    """Formulario para agregar gastos"""
    st.write("### ➕ Registrar Nuevo Gasto")
    
    with st.form("agregar_gasto"):
        col1, col2 = st.columns(2)
        
        with col1:
            concepto = st.text_input("Concepto del gasto*:", placeholder="Ej: Compra de ingredientes")
            monto = st.number_input("Monto*:", min_value=0.01, step=0.01)
            
            categorias_gasto = ["Operación", "Compras", "Servicios", "Mantenimiento", "Otros"]
            categoria = st.selectbox("Categoría*:", categorias_gasto)
        
        with col2:
            vendedores = Vendedor.get_nombres_activos()
            vendedor = st.selectbox("Quien realizó el gasto:", vendedores if vendedores else ["Sin especificar"])
            
            comprobante = st.text_input("Número de comprobante:", placeholder="Factura/Ticket #")
            descripcion = st.text_area("Descripción adicional:")
        
        submitted = st.form_submit_button("💾 Registrar Gasto", type="primary")
        
        if submitted:
            if concepto and monto > 0:
                try:
                    gasto = GastoDiario(
                        fecha=fecha,
                        concepto=concepto,
                        monto=monto,
                        categoria=categoria,
                        descripcion=descripcion,
                        comprobante=comprobante,
                        vendedor=vendedor
                    )
                    gasto.save()
                    st.success("✅ Gasto registrado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar gasto: {str(e)}")
            else:
                st.error("Por favor completa los campos obligatorios (concepto y monto)")

def ver_gastos(fecha: str):
    """Mostrar gastos del día con opciones de editar y eliminar"""
    st.write(f"### 📋 Gastos del {fecha}")
    
    gastos = GastoDiario.get_by_fecha(fecha)
    
    if not gastos:
        st.info("No hay gastos registrados para esta fecha")
        return
    
    # Métricas de gastos
    total_gastos = sum(g.monto for g in gastos)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    with col2:
        categorias_gastos = {}
        for g in gastos:
            categorias_gastos[g.categoria] = categorias_gastos.get(g.categoria, 0) + g.monto
        categoria_mayor = max(categorias_gastos.keys(), key=lambda k: categorias_gastos[k]) if categorias_gastos else "N/A"
        st.metric("Categoría Principal", categoria_mayor)
    
    with col3:
        promedio_gasto = total_gastos / len(gastos) if gastos else 0
        st.metric("Promedio por Gasto", f"${promedio_gasto:,.2f}")
    
    # Gráfico de gastos por categoría
    if gastos:
        df_chart = pd.DataFrame([{'Categoría': k, 'Monto': v} for k, v in categorias_gastos.items()])
        fig_gastos = px.pie(
            df_chart, 
            values='Monto', 
            names='Categoría',
            title="Distribución de Gastos por Categoría"
        )
        st.plotly_chart(fig_gastos, use_container_width=True)
    
    # Lista de gastos con opciones de editar/eliminar
    st.subheader("💰 Lista de Gastos")
    
    for i, gasto in enumerate(gastos):
        with st.expander(f"💸 {gasto.concepto} - ${gasto.monto:,.2f}", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Categoría:** {gasto.categoria}")
                st.write(f"**Vendedor:** {gasto.vendedor}")
                st.write(f"**Comprobante:** {gasto.comprobante or 'Sin comprobante'}")
                if gasto.descripcion:
                    st.write(f"**Descripción:** {gasto.descripcion}")
            
            with col2:
                if st.button("✏️ Editar", key=f"edit_{gasto.id}_{i}"):
                    st.session_state[f'editing_gasto_{gasto.id}'] = True
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Eliminar", key=f"delete_{gasto.id}_{i}", type="secondary"):
                    if st.session_state.get(f'confirm_delete_{gasto.id}', False):
                        # Eliminar el gasto
                        if gasto.delete():
                            show_success_message(f"Gasto '{gasto.concepto}' eliminado exitosamente")
                            # Limpiar el estado de confirmación
                            if f'confirm_delete_{gasto.id}' in st.session_state:
                                del st.session_state[f'confirm_delete_{gasto.id}']
                            st.rerun()
                        else:
                            show_error_message("Error al eliminar el gasto")
                    else:
                        st.session_state[f'confirm_delete_{gasto.id}'] = True
                        st.rerun()
            
            # Mostrar confirmación de eliminación
            if st.session_state.get(f'confirm_delete_{gasto.id}', False):
                st.warning("⚠️ ¿Estás seguro de que deseas eliminar este gasto? Esta acción no se puede deshacer.")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ Confirmar", key=f"confirm_yes_{gasto.id}_{i}"):
                        if gasto.delete():
                            show_success_message(f"Gasto '{gasto.concepto}' eliminado exitosamente")
                            if f'confirm_delete_{gasto.id}' in st.session_state:
                                del st.session_state[f'confirm_delete_{gasto.id}']
                            st.rerun()
                        else:
                            show_error_message("Error al eliminar el gasto")
                with col_cancel:
                    if st.button("❌ Cancelar", key=f"confirm_no_{gasto.id}_{i}"):
                        if f'confirm_delete_{gasto.id}' in st.session_state:
                            del st.session_state[f'confirm_delete_{gasto.id}']
                        st.rerun()
            
            # Formulario de edición
            if st.session_state.get(f'editing_gasto_{gasto.id}', False):
                st.write("---")
                st.write("**✏️ Editando gasto:**")
                
                with st.form(f"edit_gasto_{gasto.id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nuevo_concepto = st.text_input("Concepto:", value=gasto.concepto)
                        nuevo_monto = st.number_input("Monto:", value=float(gasto.monto), min_value=0.01, step=0.01)
                        nueva_categoria = st.selectbox("Categoría:", 
                                                     ["Operación", "Compras", "Servicios", "Marketing", "Mantenimiento", "Otros"],
                                                     index=["Operación", "Compras", "Servicios", "Marketing", "Mantenimiento", "Otros"].index(gasto.categoria) if gasto.categoria in ["Operación", "Compras", "Servicios", "Marketing", "Mantenimiento", "Otros"] else 0)
                    
                    with col2:
                        nuevo_vendedor = st.text_input("Vendedor:", value=gasto.vendedor)
                        nuevo_comprobante = st.text_input("Comprobante:", value=gasto.comprobante or "")
                        nueva_descripcion = st.text_area("Descripción:", value=gasto.descripcion or "")
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("💾 Guardar cambios"):
                            if not nuevo_concepto.strip():
                                show_error_message("El concepto es obligatorio")
                            elif nuevo_monto <= 0:
                                show_error_message("El monto debe ser mayor a 0")
                            else:
                                # Actualizar el gasto
                                gasto.concepto = nuevo_concepto.strip()
                                gasto.monto = nuevo_monto
                                gasto.categoria = nueva_categoria
                                gasto.vendedor = nuevo_vendedor.strip()
                                gasto.comprobante = nuevo_comprobante.strip()
                                gasto.descripcion = nueva_descripcion.strip()
                                
                                if gasto.save():
                                    show_success_message(f"Gasto actualizado exitosamente")
                                    del st.session_state[f'editing_gasto_{gasto.id}']
                                    st.rerun()
                                else:
                                    show_error_message("Error al actualizar el gasto")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar"):
                            del st.session_state[f'editing_gasto_{gasto.id}']
                            st.rerun()

def mostrar_corte_caja():
    """Página de corte de caja mejorada con comparación detallada"""
    st.subheader("📋 Corte de Caja")
    
    # Selector de fecha
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fecha_hoy = get_mexico_datetime().date()
        fecha_seleccionada = st.date_input("Fecha del corte:", value=fecha_hoy, key="corte_fecha")
        fecha_str = str(fecha_seleccionada)
    
    with col2:
        st.markdown("### 📊 Acciones")
        if st.button("📄 Generar Reporte del Día", key="btn_reporte_dia"):
            generar_reporte_diario(fecha_str)
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3 = st.tabs([
        "💰 Nuevo Corte", 
        "📊 Comparación Detallada",
        "📋 Historial de Cortes"
    ])
    
    with tab1:
        realizar_corte_caja(fecha_str)
    
    with tab2:
        mostrar_comparacion_detallada(fecha_str)
    
    with tab3:
        mostrar_historial_cortes()

def mostrar_comparacion_detallada(fecha: str):
    """Comparación detallada con lógica contable correcta"""
    st.write("### 🔍 Análisis Contable: Sistema vs Caja Física")
    st.info("💡 **Comparación contable**: Se compara lo que debería haber según el sistema vs lo que realmente hay en la caja")
    
    # Obtener datos del día
    ventas = Venta.get_by_fecha(fecha, fecha)
    gastos = GastoDiario.get_by_fecha(fecha)
    corte = CorteCaja.get_by_fecha(fecha)
    
    if not ventas and not gastos and not corte:
        st.info("📊 No hay datos registrados para esta fecha")
        return

    # =================================================================
    # CÁLCULOS PRINCIPALES CON LÓGICA CORRECTA
    # =================================================================
    total_ventas_sistema = sum(v.total for v in ventas)
    total_gastos_sistema = sum(g.monto for g in gastos)
    
    if corte:
        dinero_inicial = corte.dinero_inicial
        dinero_final = corte.dinero_final
        
        # LÓGICA CONTABLE CORRECTA
        # Sistema: Ingresos - Gastos (lo que debería quedar)
        resultado_sistema = total_ventas_sistema - total_gastos_sistema
        
        # Caja: (Final - Inicial) - Gastos (lo que realmente pasó)
        incremento_caja = dinero_final - dinero_inicial
        resultado_caja = incremento_caja - total_gastos_sistema
        
        # Diferencia: Sistema - Caja
        diferencia_correcta = resultado_sistema - resultado_caja
        diferencia_registrada = corte.diferencia or 0.0
        
        # =================================================================
        # PRESENTACIÓN VISUAL CLARA
        # =================================================================
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 LADO SISTEMA")
            st.markdown("*Lo que debería haber según las operaciones*")
            
            st.metric("💰 Ingresos Totales", f"${total_ventas_sistema:,.2f}")
            st.metric("💸 Gastos Totales", f"${total_gastos_sistema:,.2f}")
            st.metric("📈 Resultado Sistema", f"${resultado_sistema:,.2f}", 
                     help="Ingresos - Gastos")
        
        with col2:
            st.markdown("#### 💵 LADO CAJA FÍSICA")
            st.markdown("*Lo que realmente pasó con el dinero*")
            
            st.metric("🌅 Dinero Inicial", f"${dinero_inicial:,.2f}")
            st.metric("🌇 Dinero Final", f"${dinero_final:,.2f}")
            st.metric("📉 Resultado Caja", f"${resultado_caja:,.2f}", 
                     help="(Final - Inicial) - Gastos")
        
        # =================================================================
        # ANÁLISIS DE LA DIFERENCIA
        # =================================================================
        st.markdown("---")
        st.markdown("#### ⚖️ ANÁLISIS DE LA DIFERENCIA")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            color = "normal" if abs(diferencia_correcta) < 1 else "inverse"
            st.metric("🧮 Diferencia Calculada", f"${diferencia_correcta:,.2f}",
                     help="Sistema - Caja")
        
        with col4:
            st.metric("📝 Diferencia Registrada", f"${diferencia_registrada:,.2f}",
                     help="La que está guardada en el corte")
        
        with col5:
            discrepancia = abs(diferencia_correcta - diferencia_registrada)
            color_disc = "normal" if discrepancia < 0.01 else "inverse"
            st.metric("⚠️ Discrepancia", f"${discrepancia:,.2f}",
                     help="Diferencia entre calculada y registrada")
        
        # Interpretación de la diferencia
        if abs(diferencia_correcta) < 0.01:
            st.success("✅ **CAJA PERFECTA**: El dinero físico coincide exactamente con lo esperado según el sistema")
        elif diferencia_correcta > 0:
            st.warning(f"⚠️ **FALTA DINERO**: Según el sistema debería haber ${abs(diferencia_correcta):,.2f} más en la caja")
        else:
            st.info(f"💰 **SOBRA DINERO**: Hay ${abs(diferencia_correcta):,.2f} más de lo esperado en la caja")
        
        # Verificar exactitud del registro
        if discrepancia < 0.01:
            st.success("✅ **REGISTRO CORRECTO**: La diferencia registrada coincide con el cálculo")
        else:
            st.error(f"""
            ❌ **ERROR EN EL REGISTRO**: 
            - Diferencia que debería estar registrada: ${diferencia_correcta:,.2f}
            - Diferencia actualmente registrada: ${diferencia_registrada:,.2f}
            - Error de: ${discrepancia:,.2f}
            """)
    
    else:
        st.warning("⚠️ No hay corte de caja registrado para esta fecha")
        if ventas or gastos:
            st.info(f"""
            📊 **Datos disponibles:**
            - Ventas del sistema: ${total_ventas_sistema:,.2f}
            - Gastos del sistema: ${total_gastos_sistema:,.2f}
            - Resultado teórico: ${total_ventas_sistema - total_gastos_sistema:,.2f}
            """)
    
    # =================================================================
    # INFORMACIÓN TÉCNICA ADICIONAL (COLAPSABLE)
    # =================================================================
    # =================================================================
    # INFORMACIÓN TÉCNICA ADICIONAL (COLAPSABLE)
    # =================================================================
    if corte:
        with st.expander("🔧 Información Técnica Detallada", expanded=False):
            st.markdown("#### 📊 Desglose por Método de Pago")
            
            # Calcular ventas por método desde el sistema
            ventas_efectivo_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'efectivo')
            ventas_tarjeta_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'tarjeta')
            ventas_transferencia_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'transferencia')
            
            col_tec1, col_tec2 = st.columns(2)
            
            with col_tec1:
                st.markdown("**💻 Datos del Sistema:**")
                st.code(f"""
Efectivo:      ${ventas_efectivo_sistema:,.2f}
Tarjeta:       ${ventas_tarjeta_sistema:,.2f}
Transferencia: ${ventas_transferencia_sistema:,.2f}
Total:         ${total_ventas_sistema:,.2f}
                """)
            
            with col_tec2:
                st.markdown("**💰 Datos del Corte:**")
                st.code(f"""
Efectivo:      ${corte.ventas_efectivo:,.2f}
Tarjeta/Transf: ${corte.ventas_tarjeta:,.2f}
Total:         ${corte.ventas_efectivo + corte.ventas_tarjeta:,.2f}
                """)
            
            # Mostrar la fórmula usada
            st.markdown("#### 🧮 Fórmula de Cálculo")
            st.code(f"""
LADO SISTEMA:
Resultado = Ingresos - Gastos
         = ${total_ventas_sistema:,.2f} - ${total_gastos_sistema:,.2f}
         = ${resultado_sistema:,.2f}

LADO CAJA:
Incremento = Dinero Final - Dinero Inicial
          = ${dinero_final:,.2f} - ${dinero_inicial:,.2f}
          = ${incremento_caja:,.2f}

Resultado = Incremento - Gastos
         = ${incremento_caja:,.2f} - ${total_gastos_sistema:,.2f}
         = ${resultado_caja:,.2f}

DIFERENCIA:
Diferencia = Sistema - Caja
          = ${resultado_sistema:,.2f} - ${resultado_caja:,.2f}
          = ${diferencia_correcta:,.2f}
            """)
            
            # Comparación con método anterior (si existe)
            diff_registrada = float(diferencia_registrada) if diferencia_registrada is not None else 0.0
            diff_correcta = float(diferencia_correcta) if diferencia_correcta is not None else 0.0
            
            if abs(diff_registrada - diff_correcta) >= 0.01:
                st.markdown("#### ⚠️ Comparación con Registro Actual")
                st.warning(f"""
                **Diferencia en el cálculo detectada:**
                - Método correcto (nuevo): ${diff_correcta:,.2f}
                - Registro actual (anterior): ${diff_registrada:,.2f}
                - Discrepancia: ${abs(diff_correcta - diff_registrada):,.2f}
                
                **Recomendación**: Actualizar el registro para usar la fórmula correcta.
                """)
            
            # Detalle de transacciones
            st.markdown("#### 📋 Resumen de Transacciones")
            
            if ventas:
                st.markdown("**Ventas del día:**")
                ventas_df = []
                for v in ventas[:10]:  # Mostrar solo las primeras 10
                    ventas_df.append({
                        'Hora': v.fecha.strftime('%H:%M') if v.fecha else 'N/A',
                        'Total': f"${v.total:.2f}",
                        'Método': v.metodo_pago or 'N/A',
                        'Vendedor': v.vendedor or 'N/A'
                    })
                
                if ventas_df:
                    st.dataframe(pd.DataFrame(ventas_df), use_container_width=True)
                    if len(ventas) > 10:
                        st.info(f"Se muestran las primeras 10 de {len(ventas)} ventas totales")
            
            if gastos:
                st.markdown("**Gastos del día:**")
                gastos_df = []
                for g in gastos:
                    gastos_df.append({
                        'Concepto': g.concepto or 'N/A',
                        'Monto': f"${g.monto:.2f}",
                        'Categoría': g.categoria or 'N/A',
                        'Descripción': g.descripcion or 'N/A'
                    })
                
                if gastos_df:
                    st.dataframe(pd.DataFrame(gastos_df), use_container_width=True)


def generar_reporte_diario(fecha: str):
    """Genera y descarga el reporte diario completo"""
    try:
        from utils.pdf_generator import ReporteGenerator
        
        generator = ReporteGenerator()
        pdf_bytes = generator.generar_reporte_diario(fecha)
        
        st.download_button(
            label="📄 Descargar Reporte Completo",
            data=pdf_bytes,
            file_name=f"reporte_diario_{fecha}.pdf",
            mime="application/pdf",
            key="download_reporte"
        )
        
        st.success(f"✅ Reporte del {fecha} generado exitosamente")
        
    except Exception as e:
        st.error(f"❌ Error al generar reporte: {str(e)}")

def mostrar_historial_cortes():
    """Mostrar historial de cortes de caja"""
    st.write("### 📋 Historial de Cortes")
    
    # Obtener cortes recientes
    query = """
        SELECT * FROM cortes_caja 
        ORDER BY fecha DESC 
        LIMIT 30
    """
    cortes = execute_query(query)
    
    if cortes:
        try:
            df_cortes = pd.DataFrame(cortes)
            
            # Asegurar que las columnas numéricas sean float
            numeric_cols = ['dinero_inicial', 'dinero_final', 'ventas_efectivo', 'total_gastos']
            for col in numeric_cols:
                if col in df_cortes.columns:
                    df_cortes[col] = pd.to_numeric(df_cortes[col], errors='coerce').fillna(0)
            
            # Calcular diferencias para cada corte con manejo seguro
            df_cortes['dinero_esperado'] = df_cortes['dinero_inicial'] + df_cortes['ventas_efectivo'] - df_cortes['total_gastos']
            df_cortes['diferencia'] = df_cortes['dinero_final'] - df_cortes['dinero_esperado']
            
            # Calcular exactitud con manejo de división por cero
            df_cortes['exactitud'] = df_cortes.apply(
                lambda row: 100 - (abs(row['diferencia']) / row['dinero_esperado'] * 100) 
                if row['dinero_esperado'] > 0 else 0, 
                axis=1
            )
            
            # Formatear para mostrar
            display_cols = ['fecha', 'vendedor', 'dinero_inicial', 'dinero_final', 'diferencia', 'exactitud']
            df_display = df_cortes[display_cols].copy()
            
            # Redondear exactitud de forma segura
            df_display['exactitud'] = df_display['exactitud'].apply(
                lambda x: round(float(x), 1) if pd.notnull(x) and not np.isinf(x) else 0.0
            )
            
            # Formatear números para mejor visualización
            df_display['dinero_inicial'] = df_display['dinero_inicial'].apply(lambda x: f"${x:,.2f}")
            df_display['dinero_final'] = df_display['dinero_final'].apply(lambda x: f"${x:,.2f}")
            df_display['diferencia'] = df_display['diferencia'].apply(lambda x: f"${x:,.2f}")
            df_display['exactitud'] = df_display['exactitud'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(df_display, use_container_width=True)
            
            # Estadísticas del historial con manejo seguro
            col1, col2, col3 = st.columns(3)
            
            with col1:
                promedio_diferencia = df_cortes['diferencia'].mean()
                if pd.notnull(promedio_diferencia):
                    st.metric("Diferencia Promedio", f"${promedio_diferencia:,.2f}")
                else:
                    st.metric("Diferencia Promedio", "$0.00")
            
            with col2:
                exactitud_promedio = df_cortes['exactitud'].mean()
                if pd.notnull(exactitud_promedio) and not np.isinf(exactitud_promedio):
                    st.metric("Exactitud Promedio", f"{exactitud_promedio:.1f}%")
                else:
                    st.metric("Exactitud Promedio", "0.0%")
            
            with col3:
                cortes_perfectos = len(df_cortes[abs(df_cortes['diferencia']) < 1])
                st.metric("Cortes Perfectos", f"{cortes_perfectos}/{len(df_cortes)}")
                
        except Exception as e:
            st.error(f"❌ Error al mostrar historial: {str(e)}")
            st.info("📊 No se pudieron cargar las estadísticas del historial")
    
    else:
        st.info("📊 No hay cortes de caja registrados")

def mostrar_corte_existente(corte: CorteCaja):
    """Muestra un corte de caja existente"""
    st.write("### 📋 Corte Existente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Dinero Inicial", f"${corte.dinero_inicial:,.2f}")
        st.metric("Ventas Efectivo", f"${corte.ventas_efectivo:,.2f}")
        st.metric("Total Gastos", f"${corte.total_gastos:,.2f}")
    
    with col2:
        st.metric("Dinero Final", f"${corte.dinero_final:,.2f}")
        st.metric("Ventas Tarjeta", f"${corte.ventas_tarjeta:,.2f}")
        color = "normal" if abs(corte.diferencia) < 1 else "inverse"
        st.metric("Diferencia", f"${corte.diferencia:,.2f}")
    
    if corte.observaciones:
        st.write(f"**Observaciones:** {corte.observaciones}")
    
    st.write(f"**Realizado por:** {corte.vendedor}")

def mostrar_resumen_financiero():
    """Resumen financiero con inversiones y ganancias"""
    st.subheader("📊 Resumen Financiero")
    
    # Selector de período
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde:", value=get_mexico_datetime().date() - timedelta(days=30), key="resumen_fecha_inicio")
    
    with col2:
        fecha_fin = st.date_input("Hasta:", value=get_mexico_datetime().date(), key="resumen_fecha_fin")
    
    # Obtener datos del período
    fecha_inicio_str = str(fecha_inicio)
    fecha_fin_str = str(fecha_fin)
    
    ventas = Venta.get_by_fecha(fecha_inicio_str, fecha_fin_str)
    total_ventas = sum(v.total for v in ventas)
    
    # Gastos por categoría
    query_gastos = """
        SELECT categoria, SUM(monto) as total
        FROM gastos_diarios 
        WHERE fecha BETWEEN %s AND %s 
        GROUP BY categoria
    """
    gastos_categoria = execute_query(query_gastos, (fecha_inicio_str, fecha_fin_str))
    total_gastos = sum(float(g['total']) for g in gastos_categoria)
    
    # Métricas principales
    ganancia_bruta = total_ventas - total_gastos
    margen = (ganancia_bruta / total_ventas * 100) if total_ventas > 0 else 0
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ventas", f"${total_ventas:,.2f}")
    
    with col2:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    with col3:
        st.metric("Ganancia Bruta", f"${ganancia_bruta:,.2f}", delta=ganancia_bruta)
    
    with col4:
        st.metric("Margen (%)", f"{margen:.1f}%")
    
    # Gráficos comparativos
    if gastos_categoria:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de gastos por categoría
            df_gastos_cat = pd.DataFrame(gastos_categoria)
            fig_gastos = px.pie(
                df_gastos_cat,
                values='total',
                names='categoria',
                title="Distribución de Gastos por Categoría"
            )
            st.plotly_chart(fig_gastos, use_container_width=True)
        
        with col2:
            # Gráfico de ingresos vs gastos
            datos_comparativo = pd.DataFrame({
                'Concepto': ['Ingresos', 'Gastos', 'Ganancia'],
                'Monto': [total_ventas, total_gastos, ganancia_bruta],
                'Color': ['green', 'red', 'blue']
            })
            
            fig_comp = px.bar(
                datos_comparativo,
                x='Concepto',
                y='Monto',
                color='Color',
                title="Comparativo Financiero"
            )
            st.plotly_chart(fig_comp, use_container_width=True)

# Funciones auxiliares para gráficos (existentes)
def mostrar_metricas_ventas(ventas):
    """Muestra las métricas principales de ventas"""
    total_ventas = len(ventas)
    total_ingresos = sum(venta.total for venta in ventas)
    promedio_venta = total_ingresos / total_ventas if total_ventas > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ventas", total_ventas)
    
    with col2:
        st.metric("Ingresos Totales", format_currency(total_ingresos))
    
    with col3:
        st.metric("Promedio por Venta", format_currency(promedio_venta))
    
    with col4:
        # Ventas de hoy
        ventas_hoy = len([v for v in ventas if v.fecha.date() == get_mexico_datetime().date()])
        st.metric("Ventas Hoy", ventas_hoy)

def mostrar_grafico_ventas_diarias(ventas):
    """Gráfico de ventas por día"""
    if not ventas:
        return
    
    # Agrupar ventas por día
    ventas_por_dia = {}
    for venta in ventas:
        fecha = venta.fecha.date()
        if fecha not in ventas_por_dia:
            ventas_por_dia[fecha] = {'count': 0, 'total': 0}
        ventas_por_dia[fecha]['count'] += 1
        ventas_por_dia[fecha]['total'] += venta.total
    
    # Crear DataFrame
    df = pd.DataFrame([
        {'Fecha': fecha, 'Ventas': data['count'], 'Ingresos': data['total']}
        for fecha, data in ventas_por_dia.items()
    ])
    
    if not df.empty:
        fig = px.line(df, x='Fecha', y='Ingresos', title='Ingresos por Día')
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_metodos_pago(ventas):
    """Gráfico de métodos de pago"""
    if not ventas:
        return
        
    metodos = {}
    for venta in ventas:
        metodo = venta.metodo_pago
        if metodo not in metodos:
            metodos[metodo] = 0
        metodos[metodo] += venta.total
    
    if metodos:
        fig = px.pie(
            values=list(metodos.values()),
            names=list(metodos.keys()),
            title='Distribución por Método de Pago'
        )
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_productos_vendidos(fecha_inicio, fecha_fin):
    """Gráfico de productos más vendidos"""
    query = """
        SELECT p.nombre, SUM(dv.cantidad) as cantidad_vendida, SUM(dv.subtotal) as total_vendido
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE DATE(v.fecha) BETWEEN %s AND %s
        GROUP BY p.id, p.nombre
        ORDER BY cantidad_vendida DESC
        LIMIT 10
    """
    
    resultados = execute_query(query, (str(fecha_inicio), str(fecha_fin)))
    
    if resultados:
        df = pd.DataFrame(resultados)
        fig = px.bar(
            df, 
            x='nombre', 
            y='cantidad_vendida',
            title='Top 10 Productos Más Vendidos'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def mostrar_grafico_vendedores(ventas):
    """Gráfico de ventas por vendedor"""
    if not ventas:
        return
        
    vendedores = {}
    for venta in ventas:
        vendedor = venta.vendedor or "Sin especificar"
        if vendedor not in vendedores:
            vendedores[vendedor] = {'count': 0, 'total': 0}
        vendedores[vendedor]['count'] += 1
        vendedores[vendedor]['total'] += venta.total
    
    if vendedores:
        df = pd.DataFrame([
            {'Vendedor': vendedor, 'Ventas': data['count'], 'Total': data['total']}
            for vendedor, data in vendedores.items()
        ])
        
        fig = px.bar(
            df,
            x='Vendedor',
            y='Total',
            title='Ventas por Vendedor'
        )
        st.plotly_chart(fig, use_container_width=True)

def realizar_corte_caja(fecha: str):
    """Formulario para realizar corte de caja"""
    st.write("### 💰 Realizar Corte de Caja")
    
    # Verificar si ya existe corte para esta fecha
    corte_existente = CorteCaja.get_by_fecha(fecha)
    
    if corte_existente:
        st.warning(f"⚠️ Ya existe un corte de caja para el {fecha}")
        mostrar_corte_existente(corte_existente)
        
        if st.button("🔄 Realizar Nuevo Corte", key="nuevo_corte_btn"):
            st.session_state.realizar_nuevo_corte = True
            st.rerun()
        
        if not st.session_state.get('realizar_nuevo_corte', False):
            return
    
    # Obtener datos automáticos del día
    ventas_dia = Venta.get_by_fecha(fecha, fecha)
    gastos_dia = GastoDiario.get_by_fecha(fecha)
    
    # Calcular totales automáticos por método de pago
    ventas_efectivo = sum(v.total for v in ventas_dia if v.metodo_pago.lower() == "efectivo")
    ventas_tarjeta = sum(v.total for v in ventas_dia if v.metodo_pago.lower() == "tarjeta")
    ventas_transferencia = sum(v.total for v in ventas_dia if v.metodo_pago.lower() == "transferencia")
    total_gastos = sum(g.monto for g in gastos_dia)
    
    # Mostrar resumen del día
    st.markdown("#### 📊 Resumen del Día")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ventas Efectivo", f"${ventas_efectivo:,.2f}")
    with col2:
        st.metric("Ventas Tarjeta", f"${ventas_tarjeta:,.2f}")
    with col3:
        st.metric("Ventas Transferencia", f"${ventas_transferencia:,.2f}")
    with col4:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    # Formulario de corte
    with st.form("corte_caja_form"):
        st.markdown("#### 💰 Datos del Corte")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Dinero en Caja:**")
            dinero_inicial = st.number_input(
                "Dinero inicial:", 
                min_value=0.0, 
                step=0.01,
                help="¿Con cuánto dinero inició el día?"
            )
            
            dinero_final = st.number_input(
                "Dinero final (conteo físico):", 
                min_value=0.0, 
                step=0.01,
                help="¿Cuánto dinero hay físicamente en la caja?"
            )
        
        with col2:
            st.write("**Verificación de Ventas:**")
            ventas_efectivo_real = st.number_input(
                "Ventas efectivo (real):", 
                value=float(ventas_efectivo),
                step=0.01,
                help="Ajustar si hay diferencias con el sistema"
            )
            
            ventas_tarjeta_real = st.number_input(
                "Ventas tarjeta (real):", 
                value=float(ventas_tarjeta),
                step=0.01,
                help="Ajustar si hay diferencias con el sistema"
            )
            
            ventas_transferencia_real = st.number_input(
                "Ventas transferencia (real):", 
                value=float(ventas_transferencia),
                step=0.01,
                help="Ajustar si hay diferencias con el sistema"
            )
            
            gastos_real = st.number_input(
                "Gastos (real):", 
                value=float(total_gastos),
                step=0.01,
                help="Ajustar si hay gastos no registrados"
            )
        
        # Información adicional
        col3, col4 = st.columns(2)
        
        with col3:
            vendedores = Vendedor.get_nombres_activos()
            vendedor = st.selectbox(
                "Quien realiza el corte:", 
                vendedores if vendedores else ["Sin especificar"]
            )
        
        with col4:
            observaciones = st.text_area(
                "Observaciones:", 
                placeholder="Notas adicionales sobre el corte...",
                height=100
            )
        
        # Cálculo previo
        if dinero_inicial >= 0 and dinero_final >= 0:
            dinero_esperado = dinero_inicial + ventas_efectivo_real - gastos_real
            diferencia = dinero_final - dinero_esperado
            
            st.markdown("#### 📊 Cálculo Preliminar")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Dinero Esperado", f"${dinero_esperado:,.2f}")
            
            with col2:
                st.metric("Dinero Real", f"${dinero_final:,.2f}")
            
            with col3:
                st.metric("Diferencia", f"${diferencia:,.2f}", delta=diferencia if diferencia != 0 else None)
            
            with col4:
                if abs(diferencia) < 1:
                    st.success("✅ Perfecto")
                elif abs(diferencia) < 10:
                    st.warning("⚠️ Diferencia menor")
                else:
                    st.error("❌ Revisar")
        
        submitted = st.form_submit_button("💾 Guardar Corte de Caja", type="primary")
        
        if submitted:
            if dinero_inicial >= 0 and dinero_final >= 0:
                try:
                    # Si existe corte, eliminarlo primero
                    if corte_existente:
                        # Aquí podrías agregar lógica para actualizar en lugar de crear nuevo
                        pass
                    
                    corte = CorteCaja(
                        fecha=fecha,
                        dinero_inicial=dinero_inicial,
                        dinero_final=dinero_final,
                        ventas_efectivo=ventas_efectivo_real,
                        ventas_tarjeta=ventas_tarjeta_real,
                        total_gastos=gastos_real,
                        observaciones=observaciones,
                        vendedor=vendedor
                    )
                    corte.save()
                    
                    st.success("✅ Corte de caja guardado exitosamente")
                    st.session_state.realizar_nuevo_corte = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error al guardar corte: {str(e)}")
            else:
                st.error("⚠️ Por favor completa todos los campos requeridos")



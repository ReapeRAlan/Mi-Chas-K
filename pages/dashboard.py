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
from utils.helpers import format_currency, get_date_range_options
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
    """Mostrar gastos del día"""
    st.write(f"### 📋 Gastos del {fecha}")
    
    gastos = GastoDiario.get_by_fecha(fecha)
    
    if not gastos:
        st.info("No hay gastos registrados para esta fecha")
        return
    
    # Resumen por categorías
    df_gastos = pd.DataFrame([{
        'ID': g.id,
        'Concepto': g.concepto,
        'Monto': g.monto,
        'Categoría': g.categoria,
        'Vendedor': g.vendedor,
        'Comprobante': g.comprobante or '',
        'Descripción': g.descripcion[:50] + '...' if g.descripcion and len(g.descripcion) > 50 else g.descripcion or ''
    } for g in gastos])
    
    # Métricas de gastos
    total_gastos = sum(g.monto for g in gastos)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Gastos", f"${total_gastos:,.2f}")
    
    with col2:
        gastos_por_categoria = df_gastos.groupby('Categoría')['Monto'].sum()
        categoria_mayor = gastos_por_categoria.idxmax() if not gastos_por_categoria.empty else "N/A"
        st.metric("Categoría Principal", categoria_mayor)
    
    with col3:
        promedio_gasto = total_gastos / len(gastos) if gastos else 0
        st.metric("Promedio por Gasto", f"${promedio_gasto:,.2f}")
    
    # Gráfico de gastos por categoría
    if not df_gastos.empty:
        fig_gastos = px.pie(
            df_gastos, 
            values='Monto', 
            names='Categoría',
            title="Distribución de Gastos por Categoría"
        )
        st.plotly_chart(fig_gastos, use_container_width=True)
    
    # Tabla de gastos
    st.dataframe(df_gastos, use_container_width=True)

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
    """Comparación detallada entre CAJA FÍSICA vs SISTEMA/APP por separado"""
    st.write("### 🔍 Análisis Detallado: Caja Física vs Sistema de Ventas")
    st.info("💡 **Comparación separada**: Lado izquierdo muestra datos del sistema, lado derecho muestra dinero físico real")
    
    # Obtener datos del día
    ventas = Venta.get_by_fecha(fecha, fecha)
    gastos = GastoDiario.get_by_fecha(fecha)
    corte = CorteCaja.get_by_fecha(fecha)
    
    # DEBUG: Mostrar información del corte
    if corte:
        with st.expander("🔍 DEBUG: Datos del Corte"):
            st.write(f"**Dinero inicial:** ${corte.dinero_inicial}")
            st.write(f"**Ventas efectivo:** ${corte.ventas_efectivo}")
            st.write(f"**Ventas tarjeta:** ${corte.ventas_tarjeta}")
            st.write(f"**Ventas transferencia:** ${getattr(corte, 'ventas_transferencia', 'NO EXISTE')}")
            st.write(f"**Total gastos:** ${corte.total_gastos}")
            st.write(f"**Dinero final:** ${corte.dinero_final}")
    
    # DEBUG: Mostrar información de ventas del sistema
    with st.expander("🔍 DEBUG: Ventas del Sistema"):
        for i, venta in enumerate(ventas[:5]):  # Solo primeras 5
            st.write(f"**Venta {i+1}:** ${venta.total} - {venta.metodo_pago}")
        if len(ventas) > 5:
            st.write(f"... y {len(ventas) - 5} ventas más")
    
    if not ventas and not gastos and not corte:
        st.info("📊 No hay datos registrados para esta fecha")
        return
    
    # =================================================================
    # CÁLCULOS DEL SISTEMA/APP (LADO A)
    # =================================================================
    total_ventas_sistema = sum(v.total for v in ventas)
    ventas_efectivo_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'efectivo')
    ventas_tarjeta_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'tarjeta')
    ventas_transferencia_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'transferencia')
    total_gastos_sistema = sum(g.monto for g in gastos)
    ganancia_sistema = total_ventas_sistema - total_gastos_sistema
    
    # =================================================================
    # CÁLCULOS DE CAJA FÍSICA (LADO B)
    # =================================================================
    if corte:
        dinero_inicial_caja = corte.dinero_inicial
        ingresos_efectivo_caja = corte.ventas_efectivo  # Lo que realmente ingresó en efectivo
        ingresos_tarjeta_caja = corte.ventas_tarjeta    # Lo que realmente se cobró en tarjeta
        ingresos_transferencia_caja = getattr(corte, 'ventas_transferencia', 0)
        gastos_caja = corte.total_gastos                # Lo que realmente se gastó
        dinero_final_caja = corte.dinero_final          # Lo que quedó físicamente
        
        # CORRECCIÓN: Si ventas_transferencia no existe en el corte, calcularlo
        # como la diferencia entre el total y efectivo + tarjeta
        if not hasattr(corte, 'ventas_transferencia') or ingresos_transferencia_caja == 0:
            # Si el campo no existe, asumir que las transferencias van como "tarjeta" en el corte
            # y redistribuir correctamente
            total_sistema_sin_efectivo = total_ventas_sistema - ventas_efectivo_sistema
            if total_sistema_sin_efectivo > 0 and ventas_transferencia_sistema > 0:
                # Redistribuir: lo que está en corte.ventas_tarjeta puede incluir transferencias
                ingresos_transferencia_caja = ventas_transferencia_sistema  # Usar el del sistema
                ingresos_tarjeta_caja = corte.ventas_tarjeta - ventas_transferencia_sistema
                if ingresos_tarjeta_caja < 0:
                    ingresos_tarjeta_caja = 0
        
        # Cálculo de la caja: Inicial + Ingresos - Gastos = Final esperado
        total_ingresos_caja = ingresos_efectivo_caja + ingresos_tarjeta_caja + ingresos_transferencia_caja
        dinero_final_calculado = dinero_inicial_caja + ingresos_efectivo_caja - gastos_caja
        diferencia_caja_interna = dinero_final_caja - dinero_final_calculado
        ganancia_caja = total_ingresos_caja - gastos_caja
    else:
        dinero_inicial_caja = 0
        ingresos_efectivo_caja = 0
        ingresos_tarjeta_caja = 0
        ingresos_transferencia_caja = 0
        gastos_caja = 0
        dinero_final_caja = 0
        total_ingresos_caja = 0
        dinero_final_calculado = 0
        diferencia_caja_interna = 0
        ganancia_caja = 0
    
    # =================================================================
    # LAYOUT EN DOS COLUMNAS SEPARADAS
    # =================================================================
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🖥️ **SISTEMA/APP**")
        st.markdown("*📊 Datos registrados en la aplicación*")
        st.markdown("---")
        
        # Ventas del sistema
        st.metric("💰 Total Ventas Registradas", f"${total_ventas_sistema:,.2f}")
        
        col1_1, col1_2 = st.columns(2)
        with col1_1:
            st.metric("Efectivo", f"${ventas_efectivo_sistema:,.2f}")
            st.metric("Transferencia", f"${ventas_transferencia_sistema:,.2f}")
        with col1_2:
            st.metric("Tarjeta", f"${ventas_tarjeta_sistema:,.2f}")
            st.metric("Gastos", f"${total_gastos_sistema:,.2f}")
        
        # Ganancia del sistema
        delta_ganancia_sistema = ganancia_sistema if ganancia_sistema != 0 else None
        color_ganancia_sistema = "normal" if ganancia_sistema >= 0 else "inverse"
        st.metric("🎯 Ganancia Teórica", f"${ganancia_sistema:,.2f}", 
                 delta=delta_ganancia_sistema, help="Ventas - Gastos registrados")
        
        # Resumen del sistema
        st.markdown("**📊 Flujo del Sistema:**")
        st.text(f"Ventas:  +${total_ventas_sistema:,.2f}")
        st.text(f"Gastos:  -${total_gastos_sistema:,.2f}")
        st.text(f"= Ganancia: ${ganancia_sistema:,.2f}")
    
    with col2:
        st.markdown("#### 💰 **CAJA FÍSICA**")
        st.markdown("*💵 Dinero real contado y verificado*")
        st.markdown("---")
        
        if corte:
            # Ingresos de la caja
            st.metric("💵 Total Ingresos Reales", f"${total_ingresos_caja:,.2f}")
            
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Efectivo", f"${ingresos_efectivo_caja:,.2f}")
                st.metric("Transferencia", f"${ingresos_transferencia_caja:,.2f}")
            with col2_2:
                st.metric("Tarjeta", f"${ingresos_tarjeta_caja:,.2f}")
                st.metric("Gastos", f"${gastos_caja:,.2f}")
            
            # Ganancia de la caja
            delta_ganancia_caja = ganancia_caja if ganancia_caja != 0 else None
            st.metric("🎯 Ganancia Real", f"${ganancia_caja:,.2f}", 
                     delta=delta_ganancia_caja, help="Ingresos - Gastos reales")
            
            # Estado de la caja física
            st.markdown("**💰 Estado de Caja:**")
            st.text(f"Inicial:   ${dinero_inicial_caja:,.2f}")
            st.text(f"Efectivo: +${ingresos_efectivo_caja:,.2f}")
            st.text(f"Gastos:   -${gastos_caja:,.2f}")
            st.text(f"Final:     ${dinero_final_caja:,.2f}")
            
            # Verificación interna de caja
            if abs(diferencia_caja_interna) > 0.5:
                st.warning(f"⚠️ Diferencia interna: ${diferencia_caja_interna:,.2f}")
            else:
                st.success("✅ Caja cuadrada internamente")
        else:
            st.warning("⚠️ No se ha realizado corte de caja")
            st.info("Realiza el corte en 'Nuevo Corte' para ver los datos reales")
    
    # =================================================================
    # COMPARACIÓN ENTRE AMBOS LADOS
    # =================================================================
    if corte:
        st.markdown("---")
        st.markdown("### ⚖️ **COMPARACIÓN DETALLADA: SISTEMA vs CAJA**")
        st.markdown("*🔍 Análisis de diferencias entre lo registrado y lo físico*")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            st.markdown("#### 💰 Por Método de Pago")
            
            # Diferencias por método
            diff_efectivo = ingresos_efectivo_caja - ventas_efectivo_sistema
            diff_tarjeta = ingresos_tarjeta_caja - ventas_tarjeta_sistema
            diff_transferencia = ingresos_transferencia_caja - ventas_transferencia_sistema
            
            st.metric("Efectivo", f"${diff_efectivo:,.2f}", 
                     delta=diff_efectivo if diff_efectivo != 0 else None,
                     help="Caja - Sistema")
            st.metric("Tarjeta", f"${diff_tarjeta:,.2f}", 
                     delta=diff_tarjeta if diff_tarjeta != 0 else None,
                     help="Caja - Sistema")
            st.metric("Transferencia", f"${diff_transferencia:,.2f}", 
                     delta=diff_transferencia if diff_transferencia != 0 else None,
                     help="Caja - Sistema")
        
        with col4:
            st.markdown("#### 📊 Totales Generales")
            
            # Diferencias en totales
            diff_ingresos = total_ingresos_caja - total_ventas_sistema
            diff_gastos = gastos_caja - total_gastos_sistema
            diff_ganancia = ganancia_caja - ganancia_sistema
            
            st.metric("Total Ingresos", f"${diff_ingresos:,.2f}", 
                     delta=diff_ingresos if diff_ingresos != 0 else None,
                     help="Ingresos Caja - Ventas Sistema")
            st.metric("Total Gastos", f"${diff_gastos:,.2f}", 
                     delta=diff_gastos if diff_gastos != 0 else None,
                     help="Gastos Caja - Gastos Sistema")
            st.metric("Ganancia", f"${diff_ganancia:,.2f}", 
                     delta=diff_ganancia if diff_ganancia != 0 else None,
                     help="Ganancia Caja - Ganancia Sistema")
        
        with col5:
            st.markdown("#### 🎯 Análisis Final")
            
            # Análisis de exactitud
            if abs(diff_ingresos) < 1 and abs(diff_gastos) < 1:
                st.success("🎉 **PERFECTO**")
                st.write("Sistema y caja coinciden")
            elif abs(diff_ingresos) < 10 and abs(diff_gastos) < 10:
                st.warning("⚠️ **DIFERENCIA MENOR**")
                st.write("Revisar pequeñas diferencias")
            else:
                st.error("❌ **DIFERENCIA SIGNIFICATIVA**")
                st.write("Requiere investigación")
            
            # Porcentaje de exactitud general
            if total_ventas_sistema > 0:
                exactitud_ingresos = 100 - (abs(diff_ingresos) / total_ventas_sistema * 100)
                st.metric("Exactitud Ingresos", f"{max(0, exactitud_ingresos):.1f}%")
            
            if total_gastos_sistema > 0:
                exactitud_gastos = 100 - (abs(diff_gastos) / total_gastos_sistema * 100)
                st.metric("Exactitud Gastos", f"{max(0, exactitud_gastos):.1f}%")
        
        # =================================================================
        # TABLA RESUMEN COMPARATIVA
        # =================================================================
        st.markdown("#### 📋 Tabla Resumen Comparativa")
        
        datos_comparacion = {
            "Concepto": [
                "💰 Efectivo", 
                "💳 Tarjeta", 
                "📱 Transferencia", 
                "💸 Gastos",
                "📊 TOTAL INGRESOS", 
                "🎯 GANANCIA"
            ],
            "Sistema/App": [
                f"${ventas_efectivo_sistema:,.2f}",
                f"${ventas_tarjeta_sistema:,.2f}",
                f"${ventas_transferencia_sistema:,.2f}",
                f"${total_gastos_sistema:,.2f}",
                f"${total_ventas_sistema:,.2f}",
                f"${ganancia_sistema:,.2f}"
            ],
            "Caja Física": [
                f"${ingresos_efectivo_caja:,.2f}",
                f"${ingresos_tarjeta_caja:,.2f}",
                f"${ingresos_transferencia_caja:,.2f}",
                f"${gastos_caja:,.2f}",
                f"${total_ingresos_caja:,.2f}",
                f"${ganancia_caja:,.2f}"
            ],
            "Diferencia": [
                f"${diff_efectivo:,.2f}",
                f"${diff_tarjeta:,.2f}",
                f"${diff_transferencia:,.2f}",
                f"${diff_gastos:,.2f}",
                f"${diff_ingresos:,.2f}",
                f"${diff_ganancia:,.2f}"
            ]
        }
        
        df_comparacion = pd.DataFrame(datos_comparacion)
        st.dataframe(df_comparacion, use_container_width=True)
        
        # =================================================================
        # CASOS Y RECOMENDACIONES ESPECÍFICAS
        # =================================================================
        st.markdown("### 💡 **ANÁLISIS Y RECOMENDACIONES**")
        
        # Análisis por casos específicos
        if abs(diff_ingresos) < 1 and abs(diff_gastos) < 1:
            st.success("""
            ✅ **EXCELENTE CONTROL FINANCIERO**
            - El sistema y la caja física coinciden perfectamente
            - Los procesos de registro están funcionando correctamente
            - No se requieren acciones adicionales
            """)
        
        elif diff_ingresos > 10:
            st.info(f"""
            💰 **INGRESOS EXTRAS EN CAJA**: +${diff_ingresos:,.2f}
            **Posibles causas:**
            - Ventas no registradas en el sistema
            - Ingresos de días anteriores
            - Errores en el conteo de la caja
            
            **Acciones recomendadas:**
            - Verificar si hay ventas sin registrar
            - Revisar el conteo físico del dinero
            - Registrar las ventas faltantes si es el caso
            """)
        
        elif diff_ingresos < -10:
            st.warning(f"""
            💸 **FALTANTE EN INGRESOS**: ${abs(diff_ingresos):,.2f}
            **Posibles causas:**
            - Ventas registradas pero dinero no depositado en caja
            - Uso del dinero para gastos no registrados
            - Errores en el registro del sistema
            
            **Acciones recomendadas:**
            - Verificar que todo el dinero esté en la caja
            - Revisar si hay gastos no registrados
            - Confirmar que las ventas fueron reales
            """)
        
        if abs(diff_gastos) > 5:
            st.warning(f"""
            📊 **DIFERENCIA EN GASTOS**: ${diff_gastos:,.2f}
            **Recomendación:**
            - Revisar que todos los gastos estén registrados correctamente
            - Verificar comprobantes y facturas
            - Actualizar registros faltantes
            """)
        
        # Resumen de estado
        if abs(diferencia_caja_interna) > 1:
            st.error(f"""
            🚨 **PROBLEMA EN CAJA FÍSICA**
            - La caja no cuadra internamente
            - Diferencia: ${diferencia_caja_interna:,.2f}
            - Revisar el conteo físico del dinero
            """)

# ...existing code...

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

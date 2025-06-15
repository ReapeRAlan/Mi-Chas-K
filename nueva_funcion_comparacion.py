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
        diferencia_registrada = corte.diferencia
        
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
            if abs(diferencia_registrada - diferencia_correcta) >= 0.01:
                st.markdown("#### ⚠️ Comparación con Registro Actual")
                st.warning(f"""
                **Diferencia en el cálculo detectada:**
                - Método correcto (nuevo): ${diferencia_correcta:,.2f}
                - Registro actual (anterior): ${diferencia_registrada:,.2f}
                - Discrepancia: ${abs(diferencia_correcta - diferencia_registrada):,.2f}
                
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

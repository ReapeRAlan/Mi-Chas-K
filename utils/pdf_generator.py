"""
Generador de tickets en PDF usando ReportLab
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
from utils.timezone_utils import get_mexico_datetime, format_mexico_datetime
import os
import io
from database.models import Venta, DetalleVenta, Producto
from database.connection import execute_query

class TicketGenerator:
    def __init__(self):
        self.width = 80 * mm  # Ancho de ticket térmico estándar
        self.height = 200 * mm  # Alto flexible
        
    def get_configuracion(self, clave: str, default: str = "") -> str:
        """Obtiene un valor de configuración"""
        rows = execute_query("SELECT valor FROM configuracion WHERE clave = %s", (clave,))
        return rows[0]['valor'] if rows else default
    
    def generar_ticket_memoria(self, venta: Venta) -> bytes:
        """Genera un ticket PDF en memoria y devuelve los bytes"""
        # Crear buffer en memoria
        buffer = io.BytesIO()
        
        # Crear documento en memoria
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(self.width, self.height),
            leftMargin=5*mm,
            rightMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Contenido del ticket
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        
        style_titulo = ParagraphStyle(
            'TituloTicket',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=3*mm,
            textColor=colors.black
        )
        
        style_subtitulo = ParagraphStyle(
            'SubtituloTicket',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=2*mm
        )
        
        style_normal = ParagraphStyle(
            'NormalTicket',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=1*mm
        )
        
        style_total = ParagraphStyle(
            'TotalTicket',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=3*mm,
            textColor=colors.black
        )
        
        # Encabezado
        nombre_negocio = self.get_configuracion('nombre_negocio', 'MiChaska')
        story.append(Paragraph(nombre_negocio, style_titulo))
        
        direccion = self.get_configuracion('direccion', '')
        if direccion:
            story.append(Paragraph(direccion, style_subtitulo))
        
        telefono = self.get_configuracion('telefono', '')
        if telefono:
            story.append(Paragraph(f"Tel: {telefono}", style_subtitulo))
        
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("=" * 30, style_normal))
        story.append(Spacer(1, 2*mm))
        
        # Información de la venta
        story.append(Paragraph(f"<b>Ticket #{venta.id}</b>", style_normal))
        if venta.fecha:
            story.append(Paragraph(f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}", style_normal))
        else:
            story.append(Paragraph(f"Fecha: {format_mexico_datetime(get_mexico_datetime())}", style_normal))
        story.append(Paragraph(f"Método: {venta.metodo_pago}", style_normal))
        
        if venta.vendedor:
            story.append(Paragraph(f"Vendedor: {venta.vendedor}", style_normal))
        
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("-" * 30, style_normal))
        
        # Detalles de la venta
        if venta.id:
            detalles = DetalleVenta.get_by_venta(venta.id)
        else:
            detalles = []
        
        # Crear tabla de productos
        data = [['Producto', 'Cant', 'Precio', 'Total']]
        
        for detalle in detalles:
            producto = Producto.get_by_id(detalle.producto_id)
            if producto:
                data.append([
                    producto.nombre[:15] + "..." if len(producto.nombre) > 15 else producto.nombre,
                    str(detalle.cantidad),
                    f"${detalle.precio_unitario:.2f}",
                    f"${detalle.subtotal:.2f}"
                ])
        
        # Crear tabla con estilo compacto
        table = Table(data, colWidths=[25*mm, 10*mm, 15*mm, 15*mm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("-" * 30, style_normal))
        
        # Totales
        subtotal = venta.total + venta.descuento
        
        if venta.descuento > 0:
            story.append(Paragraph(f"Subtotal: ${subtotal:.2f}", style_normal))
            story.append(Paragraph(f"Descuento: -${venta.descuento:.2f}", style_normal))
        
        story.append(Paragraph(f"<b>TOTAL: ${venta.total:.2f}</b>", style_total))
        
        if venta.observaciones:
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph(f"Nota: {venta.observaciones}", style_normal))
        
        # Pie de página
        mensaje_ticket = self.get_configuracion('mensaje_ticket', 'Gracias por su compra')
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("=" * 30, style_normal))
        story.append(Paragraph(mensaje_ticket, style_subtitulo))
        story.append(Paragraph(f"Generado: {format_mexico_datetime(get_mexico_datetime())}", style_subtitulo))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener bytes del buffer
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def generar_ticket(self, venta: Venta, ruta_salida: str = "") -> str:
        """Genera un ticket PDF para la venta (método legacy)"""
        if not ruta_salida:
            os.makedirs("tickets", exist_ok=True)
            ruta_salida = f"tickets/ticket_{venta.id}_{get_mexico_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Generar en memoria y guardar a archivo
        pdf_bytes = self.generar_ticket_memoria(venta)
        
        with open(ruta_salida, 'wb') as f:
            f.write(pdf_bytes)
        
        return ruta_salida


def generar_reporte_ventas(fecha_inicio: str, fecha_fin: str, ruta_salida: str = "") -> str:
    """Genera un reporte de ventas en PDF"""
    if ruta_salida == "":
        os.makedirs("reportes", exist_ok=True)
        ruta_salida = f"reportes/reporte_ventas_{get_mexico_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    doc = SimpleDocTemplate(ruta_salida, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    titulo = Paragraph(f"<b>Reporte de Ventas</b><br/>{fecha_inicio} - {fecha_fin}", 
                      styles['Title'])
    story.append(titulo)
    story.append(Spacer(1, 12))
    
    # Obtener ventas del período
    from database.models import Venta
    ventas = Venta.get_by_fecha(fecha_inicio, fecha_fin)
    
    if not ventas:
        story.append(Paragraph("No hay ventas en el período seleccionado", styles['Normal']))
    else:
        # Crear tabla de ventas
        data = [['ID', 'Fecha', 'Total', 'Método Pago', 'Vendedor']]
        
        total_periodo = 0
        for venta in ventas:
            if isinstance(venta.fecha, str):
                fecha_venta = datetime.fromisoformat(venta.fecha)
            elif venta.fecha is not None:
                fecha_venta = venta.fecha
            else:
                fecha_venta = get_mexico_datetime()
                
            data.append([
                str(venta.id),
                fecha_venta.strftime('%d/%m/%Y %H:%M'),
                f"{venta.total:.2f}",
                venta.metodo_pago,
                venta.vendedor or '-'
            ])
            total_periodo += venta.total
        
        # Añadir fila de total
        data.append(['', '', '', 'TOTAL:', f"{total_periodo:.2f}"])
        
        # Crear tabla
        tabla = Table(data)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla)
        
        # Estadísticas
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Resumen del Período:</b>", styles['Heading2']))
        story.append(Paragraph(f"Total de ventas: {len(ventas)}", styles['Normal']))
        story.append(Paragraph(f"Total facturado: {total_periodo:.2f} MXN", styles['Normal']))
        story.append(Paragraph(f"Promedio por venta: {total_periodo/len(ventas):.2f} MXN", styles['Normal']))
    
    doc.build(story)
    return ruta_salida

class ReporteGenerator:
    def __init__(self):
        self.page_size = A4
        
    def _crear_estilos_personalizados(self):
        """Crear estilos personalizados para el reporte"""
        styles = getSampleStyleSheet()
        
        # Estilo para títulos de sección
        styles.add(ParagraphStyle(
            name='SeccionTitulo',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10,
            spaceBefore=15,
            leftIndent=0
        ))
        
        # Estilo para subtítulos
        styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para métricas importantes
        styles.add(ParagraphStyle(
            name='Metrica',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        # Estilo para fórmulas
        styles.add(ParagraphStyle(
            name='Formula',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Courier',
            backColor=colors.lightgrey,
            leftIndent=20,
            rightIndent=20,
            spaceBefore=5,
            spaceAfter=5
        ))
        
        return styles
    
    def _crear_tabla_metrica(self, datos, titulo="", colores_fondo=None):
        """Crear una tabla estilizada para métricas"""
        if colores_fondo is None:
            colores_fondo = [colors.lightblue, colors.lightcoral]
        
        tabla = Table(datos, colWidths=[80*mm, 60*mm])
        
        estilo = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colores_fondo[0]),
            ('BACKGROUND', (1, 0), (1, -1), colores_fondo[1])
        ]
        
        tabla.setStyle(TableStyle(estilo))
        return tabla
    
    def generar_reporte_diario(self, fecha: str) -> bytes:
        """Genera un reporte completo del día en PDF con el mismo nivel de detalle que el dashboard"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        styles = self._crear_estilos_personalizados()
        
        # ===============================================================
        # ENCABEZADO PRINCIPAL
        # ===============================================================
        titulo_principal = f"<b>📊 REPORTE CONTABLE DIARIO</b><br/>Mi Chas-K - {fecha}"
        story.append(Paragraph(titulo_principal, styles['Title']))
        story.append(Spacer(1, 15))
        
        # Fecha de generación
        fecha_generacion = get_mexico_datetime().strftime("%d/%m/%Y %H:%M:%S")
        story.append(Paragraph(f"<i>Generado el: {fecha_generacion}</i>", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # ===============================================================
        # OBTENER DATOS DEL DÍA
        # ===============================================================
        from database.models import Venta, GastoDiario, CorteCaja
        
        ventas = Venta.get_by_fecha(fecha, fecha)
        gastos = GastoDiario.get_by_fecha(fecha)
        corte = CorteCaja.get_by_fecha(fecha)
        
        # ===============================================================
        # SECCIÓN 1: ANÁLISIS CONTABLE PRINCIPAL
        # ===============================================================
        story.append(Paragraph("🧮 ANÁLISIS CONTABLE PRINCIPAL", styles['SeccionTitulo']))
        
        # Cálculos principales
        total_ventas_sistema = sum(v.total for v in ventas)
        total_gastos_sistema = sum(g.monto for g in gastos)
        
        if corte:
            # Aplicar la misma lógica corregida del dashboard
            dinero_inicial = corte.dinero_inicial
            dinero_final = corte.dinero_final
            
            # LÓGICA CONTABLE CORRECTA
            resultado_sistema = total_ventas_sistema - total_gastos_sistema
            incremento_caja = dinero_final - dinero_inicial
            resultado_caja = incremento_caja - total_gastos_sistema
            diferencia_correcta = resultado_sistema - resultado_caja
            diferencia_registrada = corte.diferencia
            discrepancia = abs(diferencia_correcta - diferencia_registrada)
            
            # Tabla de comparación lado a lado (como en el dashboard)
            datos_comparacion = [
                ['📊 LADO SISTEMA', '💵 LADO CAJA FÍSICA'],
                ['Lo que debería haber según las operaciones', 'Lo que realmente pasó con el dinero'],
                ['', ''],
                [f'💰 Ingresos Totales: ${total_ventas_sistema:,.2f}', f'🌅 Dinero Inicial: ${dinero_inicial:,.2f}'],
                [f'💸 Gastos Totales: ${total_gastos_sistema:,.2f}', f'🌇 Dinero Final: ${dinero_final:,.2f}'],
                [f'📈 Resultado Sistema: ${resultado_sistema:,.2f}', f'📉 Resultado Caja: ${resultado_caja:,.2f}'],
            ]
            
            tabla_comparacion = Table(datos_comparacion, colWidths=[90*mm, 90*mm])
            tabla_comparacion.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 1), 12),
                ('FONTSIZE', (0, 2), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('BACKGROUND', (1, 0), (1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 3), (-1, -1), colors.beige)
            ]))
            
            story.append(tabla_comparacion)
            story.append(Spacer(1, 15))
            
            # ===============================================================
            # ANÁLISIS DE LA DIFERENCIA
            # ===============================================================
            story.append(Paragraph("⚖️ ANÁLISIS DE LA DIFERENCIA", styles['SeccionTitulo']))
            
            datos_diferencia = [
                ['🧮 Diferencia Calculada', f'${diferencia_correcta:,.2f}'],
                ['📝 Diferencia Registrada', f'${diferencia_registrada:,.2f}'],
                ['⚠️ Discrepancia', f'${discrepancia:,.2f}']
            ]
            
            if abs(diferencia_correcta) < 0.01:
                interpretacion = "✅ CAJA PERFECTA: El dinero físico coincide exactamente con lo esperado"
                color_interpretacion = colors.green
            elif diferencia_correcta > 0:
                interpretacion = f"⚠️ FALTA DINERO: Según el sistema debería haber ${abs(diferencia_correcta):,.2f} más en la caja"
                color_interpretacion = colors.orange
            else:
                interpretacion = f"💰 SOBRA DINERO: Hay ${abs(diferencia_correcta):,.2f} más de lo esperado en la caja"
                color_interpretacion = colors.lightblue
            
            datos_diferencia.append(['📊 Interpretación', interpretacion])
            
            if discrepancia >= 0.01:
                estado_registro = f"❌ ERROR EN EL REGISTRO: Discrepancia de ${discrepancia:,.2f}"
                color_registro = colors.red
            else:
                estado_registro = "✅ REGISTRO CORRECTO: La diferencia registrada coincide con el cálculo"
                color_registro = colors.green
            
            datos_diferencia.append(['📋 Estado del Registro', estado_registro])
            
            tabla_diferencia = self._crear_tabla_metrica(datos_diferencia)
            story.append(tabla_diferencia)
            story.append(Spacer(1, 15))
            
            # ===============================================================
            # FÓRMULAS DE CÁLCULO (como en el dashboard)
            # ===============================================================
            story.append(Paragraph("🧮 FÓRMULAS DE CÁLCULO", styles['SeccionTitulo']))
            
            formula_texto = f"""
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
            """
            
            story.append(Paragraph(formula_texto, styles['Formula']))
            story.append(Spacer(1, 20))
        
        else:
            story.append(Paragraph("⚠️ No hay corte de caja registrado para esta fecha", styles['Normal']))
            story.append(Spacer(1, 15))
        
        # ===============================================================
        # SECCIÓN 2: DESGLOSE POR MÉTODO DE PAGO
        # ===============================================================
        story.append(Paragraph("💳 DESGLOSE POR MÉTODO DE PAGO", styles['SeccionTitulo']))
        
        # Calcular ventas por método desde el sistema
        ventas_efectivo_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'efectivo')
        ventas_tarjeta_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'tarjeta')
        ventas_transferencia_sistema = sum(v.total for v in ventas if v.metodo_pago.lower() == 'transferencia')
        
        datos_metodos = [
            ['MÉTODO DE PAGO', 'SISTEMA', 'CORTE', 'DIFERENCIA'],
            ['💵 Efectivo', f'${ventas_efectivo_sistema:,.2f}', 
             f'${corte.ventas_efectivo:,.2f}' if corte else 'N/A',
             f'${(corte.ventas_efectivo - ventas_efectivo_sistema):,.2f}' if corte else 'N/A'],
            ['💳 Tarjeta', f'${ventas_tarjeta_sistema:,.2f}',
             f'${corte.ventas_tarjeta * (ventas_tarjeta_sistema / (ventas_tarjeta_sistema + ventas_transferencia_sistema)) if (ventas_tarjeta_sistema + ventas_transferencia_sistema) > 0 else corte.ventas_tarjeta:,.2f}' if corte else 'N/A',
             'Ver análisis técnico'],
            ['📱 Transferencia', f'${ventas_transferencia_sistema:,.2f}',
             'Incluido en Tarjeta/Transf',
             'Ver análisis técnico'],
            ['📊 TOTAL', f'${total_ventas_sistema:,.2f}',
             f'${(corte.ventas_efectivo + corte.ventas_tarjeta):,.2f}' if corte else 'N/A',
             f'${((corte.ventas_efectivo + corte.ventas_tarjeta) - total_ventas_sistema):,.2f}' if corte else 'N/A']
        ]
        
        tabla_metodos = Table(datos_metodos, colWidths=[45*mm, 35*mm, 35*mm, 35*mm])
        tabla_metodos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_metodos)
        story.append(Spacer(1, 20))
        
        # ===============================================================
        # SECCIÓN 3: RESUMEN DE TRANSACCIONES
        # ===============================================================
        story.append(Paragraph("📋 RESUMEN DE TRANSACCIONES", styles['SeccionTitulo']))
        
        # Ventas del día
        if ventas:
            story.append(Paragraph("💰 VENTAS DEL DÍA", styles['Subtitulo']))
            
            datos_ventas = [['#', 'Hora', 'Método Pago', 'Vendedor', 'Total']]
            for i, v in enumerate(ventas[:15], 1):  # Mostrar máximo 15 ventas
                hora = v.fecha.strftime('%H:%M') if v.fecha else 'N/A'
                datos_ventas.append([
                    str(i),
                    hora,
                    v.metodo_pago or 'N/A',
                    v.vendedor or 'N/A',
                    f'${v.total:.2f}'
                ])
            
            if len(ventas) > 15:
                datos_ventas.append(['...', '...', '...', '...', f'... y {len(ventas) - 15} más'])
            
            tabla_ventas = Table(datos_ventas, colWidths=[15*mm, 25*mm, 30*mm, 40*mm, 25*mm])
            tabla_ventas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tabla_ventas)
            story.append(Spacer(1, 15))
        
        # Gastos del día
        if gastos:
            story.append(Paragraph("💸 GASTOS DEL DÍA", styles['Subtitulo']))
            
            datos_gastos = [['Concepto', 'Categoría', 'Monto', 'Vendedor']]
            for g in gastos:
                concepto = g.concepto[:25] + "..." if len(g.concepto) > 25 else g.concepto
                datos_gastos.append([
                    concepto,
                    g.categoria or 'N/A',
                    f'${g.monto:.2f}',
                    g.vendedor or 'N/A'
                ])
            
            tabla_gastos = Table(datos_gastos, colWidths=[50*mm, 30*mm, 25*mm, 30*mm])
            tabla_gastos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tabla_gastos)
            story.append(Spacer(1, 20))
        
        # ===============================================================
        # SECCIÓN 4: MÉTRICAS DE CALIDAD
        # ===============================================================
        if corte:
            story.append(Paragraph("📊 MÉTRICAS DE CALIDAD", styles['SeccionTitulo']))
            
            # Calcular métricas como en el dashboard
            efectivo_esperado = dinero_inicial + corte.ventas_efectivo - total_gastos_sistema
            diferencia_efectivo_real = dinero_final - efectivo_esperado
            
            exactitud_efectivo = 100 - (abs(diferencia_efectivo_real) / efectivo_esperado * 100) if efectivo_esperado > 0 else 0
            exactitud_total = 100 - (abs((corte.ventas_efectivo + corte.ventas_tarjeta) - total_ventas_sistema) / total_ventas_sistema * 100) if total_ventas_sistema > 0 else 0
            
            diferencias_criticas = sum(1 for d in [abs(diferencia_correcta), abs(discrepancia)] if d > 10)
            estado_general = "🟢 EXCELENTE" if diferencias_criticas == 0 else "🟡 REVISAR" if diferencias_criticas <= 1 else "🔴 CRÍTICO"
            
            datos_metricas = [
                ['🎯 Exactitud Efectivo', f'{max(0, exactitud_efectivo):.1f}%'],
                ['📊 Exactitud Total', f'{max(0, exactitud_total):.1f}%'],
                ['⚖️ Estado General', estado_general],
                ['🔍 Diferencias Críticas', f'{diferencias_criticas} detectadas'],
                ['💰 Control Financiero', 'EXCELENTE' if abs(diferencia_correcta) <= 1 else 'REVISAR' if abs(diferencia_correcta) <= 10 else 'CRÍTICO']
            ]
            
            tabla_metricas = self._crear_tabla_metrica(datos_metricas, colores_fondo=[colors.lightblue, colors.lightgreen])
            story.append(tabla_metricas)
            story.append(Spacer(1, 20))
        
        # ===============================================================
        # PIE DE PÁGINA
        # ===============================================================
        story.append(Spacer(1, 30))
        story.append(Paragraph("━" * 80, styles['Normal']))
        story.append(Paragraph("<b>Sistema de Punto de Venta Mi Chas-K</b>", styles['Normal']))
        story.append(Paragraph(f"Reporte generado automáticamente el {fecha_generacion}", styles['Normal']))
        story.append(Paragraph("Este reporte utiliza la lógica contable corregida para máxima precisión", styles['Normal']))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener bytes del buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

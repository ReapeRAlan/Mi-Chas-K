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
        
    def generar_reporte_diario(self, fecha: str) -> bytes:
        """Genera un reporte completo del día en PDF"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Título del reporte
        titulo = f"REPORTE DIARIO - {fecha}"
        story.append(Paragraph(titulo, styles['Title']))
        story.append(Spacer(1, 20))
        
        # Información general
        from database.models import Venta, GastoDiario, CorteCaja
        
        # Obtener datos del día
        ventas = Venta.get_by_fecha(fecha, fecha)
        gastos = GastoDiario.get_by_fecha(fecha)
        corte = CorteCaja.get_by_fecha(fecha)
        
        # Resumen ejecutivo
        story.append(Paragraph("📊 RESUMEN EJECUTIVO", styles['Heading2']))
        
        total_ventas = sum(v.total for v in ventas)
        total_gastos = sum(g.monto for g in gastos)
        ganancia = total_ventas - total_gastos
        
        datos_resumen = [
            ['Concepto', 'Cantidad', 'Monto'],
            ['Ventas del día', f"{len(ventas)} ventas", f"${total_ventas:,.2f}"],
            ['Gastos del día', f"{len(gastos)} gastos", f"${total_gastos:,.2f}"],
            ['Ganancia bruta', '', f"${ganancia:,.2f}"],
        ]
        
        tabla_resumen = Table(datos_resumen, colWidths=[60*mm, 40*mm, 40*mm])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_resumen)
        story.append(Spacer(1, 20))
        
        # Análisis de caja vs ventas
        story.append(Paragraph("💰 ANÁLISIS CAJA VS VENTAS", styles['Heading2']))
        
        if corte:
            ventas_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'efectivo')
            ventas_tarjeta = sum(v.total for v in ventas if v.metodo_pago == 'tarjeta')
            
            datos_analisis = [
                ['Concepto', 'Registrado', 'Real', 'Diferencia'],
                ['Dinero inicial', '', f"${corte.dinero_inicial:,.2f}", ''],
                ['Ventas efectivo', f"${ventas_efectivo:,.2f}", f"${corte.ventas_efectivo:,.2f}", f"${corte.ventas_efectivo - ventas_efectivo:,.2f}"],
                ['Ventas tarjeta', f"${ventas_tarjeta:,.2f}", f"${corte.ventas_tarjeta:,.2f}", f"${corte.ventas_tarjeta - ventas_tarjeta:,.2f}"],
                ['Gastos', f"${total_gastos:,.2f}", f"${corte.total_gastos:,.2f}", f"${corte.total_gastos - total_gastos:,.2f}"],
                ['Dinero final', '', f"${corte.dinero_final:,.2f}", ''],
            ]
            
            # Calcular diferencia total
            esperado = corte.dinero_inicial + corte.ventas_efectivo - corte.total_gastos
            diferencia_total = corte.dinero_final - esperado
            datos_analisis.append(['DIFERENCIA TOTAL', '', '', f"${diferencia_total:,.2f}"])
            
            tabla_analisis = Table(datos_analisis, colWidths=[50*mm, 35*mm, 35*mm, 35*mm])
            tabla_analisis.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tabla_analisis)
        else:
            story.append(Paragraph("⚠️ No se encontró corte de caja para este día", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Detalle de ventas
        if ventas:
            story.append(Paragraph("🛒 DETALLE DE VENTAS", styles['Heading2']))
            
            datos_ventas = [['#', 'Hora', 'Vendedor', 'Método', 'Total']]
            for i, venta in enumerate(ventas, 1):
                hora = venta.fecha.strftime("%H:%M")
                datos_ventas.append([
                    str(i),
                    hora,
                    venta.vendedor or "N/A",
                    venta.metodo_pago.upper(),
                    f"${venta.total:,.2f}"
                ])
            
            tabla_ventas = Table(datos_ventas, colWidths=[15*mm, 25*mm, 40*mm, 30*mm, 30*mm])
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
            story.append(Spacer(1, 20))
        
        # Detalle de gastos
        if gastos:
            story.append(Paragraph("💸 DETALLE DE GASTOS", styles['Heading2']))
            
            datos_gastos = [['Concepto', 'Categoría', 'Monto', 'Vendedor']]
            for gasto in gastos:
                datos_gastos.append([
                    gasto.concepto[:30] + "..." if len(gasto.concepto) > 30 else gasto.concepto,
                    gasto.categoria,
                    f"${gasto.monto:,.2f}",
                    gasto.vendedor or "N/A"
                ])
            
            tabla_gastos = Table(datos_gastos, colWidths=[50*mm, 30*mm, 30*mm, 30*mm])
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
        
        # Construir PDF
        doc.build(story)
        
        # Obtener bytes del buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

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
            story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_normal))
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
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", style_subtitulo))
        
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
            ruta_salida = f"tickets/ticket_{venta.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Generar en memoria y guardar a archivo
        pdf_bytes = self.generar_ticket_memoria(venta)
        
        with open(ruta_salida, 'wb') as f:
            f.write(pdf_bytes)
        
        return ruta_salida


def generar_reporte_ventas(fecha_inicio: str, fecha_fin: str, ruta_salida: str = "") -> str:
    """Genera un reporte de ventas en PDF"""
    if ruta_salida == "":
        os.makedirs("reportes", exist_ok=True)
        ruta_salida = f"reportes/reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
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
                fecha_venta = datetime.now()
                
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

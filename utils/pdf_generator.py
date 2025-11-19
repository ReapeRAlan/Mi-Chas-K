"""
Generador de tickets en PDF usando ReportLab - Optimizado para impresoras térmicas
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from datetime import datetime
from utils.timezone_utils import format_mexico_datetime, get_mexico_datetime
import io
from database.connection_dual import execute_query

class TicketGenerator:
    def __init__(self):
        self.width = 80 * mm  # Ancho de ticket térmico estándar (80mm)
        self.height = 280 * mm  # Alto flexible
        
    def get_configuracion(self, clave: str, default: str = "") -> str:
        """Obtiene un valor de configuración"""
        try:
            rows = execute_query("SELECT valor FROM configuracion WHERE clave = %s", (clave,))
            return rows[0]['valor'] if rows else default
        except:
            return default
    
    def generar_ticket_memoria(self, venta_data: dict, detalle_rows: list) -> bytes:
        """Genera un ticket PDF en memoria optimizado para impresoras térmicas genéricas"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(self.width, self.height),
            leftMargin=3*mm,
            rightMargin=3*mm,
            topMargin=3*mm,
            bottomMargin=3*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos optimizados para ticket térmico
        style_titulo = ParagraphStyle(
            'TituloTicket',
            parent=styles['Heading1'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=2*mm,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        style_subtitulo = ParagraphStyle(
            'SubtituloTicket',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=1*mm
        )
        
        style_normal = ParagraphStyle(
            'NormalTicket',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            spaceAfter=0.5*mm
        )
        
        style_total = ParagraphStyle(
            'TotalTicket',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=2*mm,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Encabezado
        nombre_negocio = self.get_configuracion('nombre_negocio', 'Mi Chas-K')
        story.append(Paragraph(f"<b>{nombre_negocio}</b>", style_titulo))
        
        direccion = self.get_configuracion('direccion', 'Aguascalientes, Ags.')
        story.append(Paragraph(direccion, style_subtitulo))
        
        telefono = self.get_configuracion('telefono', '')
        if telefono:
            story.append(Paragraph(f"Tel: {telefono}", style_subtitulo))
        
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("=" * 40, style_normal))
        story.append(Spacer(1, 2*mm))
        
        # Información de la venta
        venta_id = venta_data.get('id', 0)
        story.append(Paragraph(f"<b>TICKET #{venta_id}</b>", style_normal))
        
        # Formatear fecha
        fecha_venta = venta_data.get('fecha')
        if isinstance(fecha_venta, str):
            try:
                fecha_obj = datetime.fromisoformat(fecha_venta.replace('Z', '+00:00'))
                fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except:
                fecha_str = fecha_venta[:16] if len(fecha_venta) >= 16 else fecha_venta
        else:
            fecha_str = format_mexico_datetime(get_mexico_datetime())
        
        story.append(Paragraph(f"Fecha: {fecha_str}", style_normal))
        
        metodo_pago = venta_data.get('metodo_pago', 'Efectivo')
        story.append(Paragraph(f"Pago: {metodo_pago}", style_normal))
        
        # Extraer info del vendedor de notas si existe
        notas = venta_data.get('notas', '')
        if notas and 'Vendedor:' in notas:
            vendedor_parte = notas.split('|')[0].replace('Vendedor:', '').strip()
            story.append(Paragraph(f"Atiende: {vendedor_parte}", style_normal))
        
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("-" * 40, style_normal))
        story.append(Spacer(1, 1*mm))
        
        # Tabla de productos
        data = [['Producto', 'Cant', 'P.U.', 'Total']]
        
        total_general = 0
        for detalle in detalle_rows:
            producto_nombre = detalle.get('producto_nombre', 'Producto')
            cantidad = detalle.get('cantidad', 1)
            precio_unit = float(detalle.get('precio_unitario', 0))
            subtotal = float(detalle.get('subtotal', 0))
            total_general += subtotal
            
            # Truncar nombre si es muy largo
            if len(producto_nombre) > 18:
                producto_nombre = producto_nombre[:15] + "..."
            
            data.append([
                producto_nombre,
                str(cantidad),
                f"${precio_unit:.0f}",
                f"${subtotal:.0f}"
            ])
        
        # Crear tabla compacta
        table = Table(data, colWidths=[36*mm, 10*mm, 12*mm, 14*mm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("=" * 40, style_normal))
        story.append(Spacer(1, 2*mm))
        
        # Total
        total_venta = float(venta_data.get('total', total_general))
        story.append(Paragraph(f"<b>TOTAL: ${total_venta:.2f}</b>", style_total))
        
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("-" * 40, style_normal))
        
        # Mensaje de agradecimiento
        mensaje = self.get_configuracion('mensaje_ticket', '¡Gracias por tu compra!')
        story.append(Paragraph(f"<b>{mensaje}</b>", style_subtitulo))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener bytes del PDF
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

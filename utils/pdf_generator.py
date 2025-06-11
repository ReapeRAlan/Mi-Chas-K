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
from database.models import Venta, DetalleVenta, Producto
from database.connection import execute_query

class TicketGenerator:
    def __init__(self):
        self.width = 80 * mm  # Ancho de ticket térmico estándar
        self.height = 200 * mm  # Alto flexible
        
    def get_configuracion(self, clave: str, default: str = "") -> str:
        """Obtiene un valor de configuración"""
        rows = execute_query("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        return rows[0]['valor'] if rows else default
    
    def generar_ticket(self, venta: Venta, ruta_salida: str = None) -> str:
        """Genera un ticket PDF para la venta"""
        if ruta_salida is None:
            os.makedirs("tickets", exist_ok=True)
            ruta_salida = f"tickets/ticket_{venta.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Crear documento
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=(self.width, self.height),
            leftMargin=5*mm,
            rightMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
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
        
        style_info = ParagraphStyle(
            'InfoTicket',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=2*mm
        )
        
        style_detalle = ParagraphStyle(
            'DetalleTicket',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            spaceAfter=1*mm
        )
        
        style_total = ParagraphStyle(
            'TotalTicket',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=2*mm,
            textColor=colors.black
        )
        
        # Contenido del ticket
        story = []
        
        # Encabezado
        nombre_negocio = self.get_configuracion('nombre_negocio', 'MiChaska')
        direccion = self.get_configuracion('direccion', '')
        telefono = self.get_configuracion('telefono', '')
        
        story.append(Paragraph(f"<b>{nombre_negocio}</b>", style_titulo))
        
        if direccion:
            story.append(Paragraph(direccion, style_info))
        if telefono:
            story.append(Paragraph(f"Tel: {telefono}", style_info))
        
        # Línea separadora
        story.append(Paragraph("=" * 40, style_info))
        
        # Información de la venta
        if isinstance(venta.fecha, str):
            fecha_venta = datetime.fromisoformat(venta.fecha)
        elif venta.fecha is not None:
            fecha_venta = venta.fecha
        else:
            fecha_venta = datetime.now()  # Usar fecha actual si no hay fecha
            
        story.append(Paragraph(f"<b>TICKET #{venta.id}</b>", style_info))
        story.append(Paragraph(f"Fecha: {fecha_venta.strftime('%d/%m/%Y %H:%M')}", style_info))
        story.append(Paragraph(f"Método: {venta.metodo_pago}", style_info))
        
        if venta.vendedor:
            story.append(Paragraph(f"Vendedor: {venta.vendedor}", style_info))
        
        story.append(Paragraph("-" * 40, style_info))
        
        # Detalle de productos
        detalles = DetalleVenta.get_by_venta(venta.id or 0)
        
        for detalle in detalles:
            # Obtener información del producto
            producto = Producto.get_by_id(detalle.producto_id)
            nombre_producto = producto.nombre if producto else "Producto no encontrado"
            
            # Línea del producto
            story.append(Paragraph(f"<b>{nombre_producto}</b>", style_detalle))
            
            # Cantidad, precio unitario y subtotal
            linea_detalle = f"{detalle.cantidad} x {detalle.precio_unitario:.2f} = {detalle.subtotal:.2f}"
            story.append(Paragraph(linea_detalle, style_detalle))
            
            story.append(Spacer(1, 1*mm))
        
        # Línea separadora
        story.append(Paragraph("-" * 40, style_info))
        
        # Totales
        moneda = self.get_configuracion('moneda', 'MXN')
        
        if venta.descuento > 0:
            subtotal = venta.total + venta.descuento
            story.append(Paragraph(f"Subtotal: {subtotal:.2f} {moneda}", style_total))
            story.append(Paragraph(f"Descuento: -{venta.descuento:.2f} {moneda}", style_total))
        
        if venta.impuestos > 0:
            story.append(Paragraph(f"Impuestos: {venta.impuestos:.2f} {moneda}", style_total))
        
        story.append(Paragraph(f"<b>TOTAL: {venta.total:.2f} {moneda}</b>", style_total))
        
        # Mensaje final
        mensaje = self.get_configuracion('mensaje_ticket', 'Gracias por su compra')
        if mensaje:
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph("=" * 40, style_info))
            story.append(Paragraph(mensaje, style_info))
        
        # Información adicional
        if venta.observaciones:
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(f"Obs: {venta.observaciones}", style_info))
        
        # Generar PDF
        doc.build(story)
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

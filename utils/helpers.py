"""
Funciones auxiliares para el sistema de facturación
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Union
from decimal import Decimal

def format_currency(amount: Union[float, Decimal, str], currency: str = "MXN") -> str:
    """Formatea un monto como moneda"""
    safe_amount = safe_float_conversion(amount)
    return f"${safe_amount:.2f} {currency}"

def format_datetime(dt: Union[datetime, str, None], format_str: str = "%d/%m/%Y %H:%M") -> str:
    """Formatea una fecha y hora"""
    if dt is None:
        return ""
    
    if isinstance(dt, str):
        try:
            # Si es string, intentar convertir a datetime usando métodos de string
            dt_clean = dt
            if 'Z' in dt_clean:
                dt_clean = dt_clean.replace('Z', '+00:00')
            dt_obj = datetime.fromisoformat(dt_clean)
            return dt_obj.strftime(format_str)
        except (ValueError, AttributeError):
            return str(dt)
    
    try:
        return dt.strftime(format_str)
    except AttributeError:
        return str(dt)

def get_date_range_options():
    """Retorna opciones comunes de rangos de fecha"""
    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    semana_pasada = hoy - timedelta(days=7)
    mes_pasado = hoy - timedelta(days=30)
    
    return {
        "Hoy": (hoy, hoy),
        "Ayer": (ayer, ayer),
        "Últimos 7 días": (semana_pasada, hoy),
        "Últimos 30 días": (mes_pasado, hoy),
        "Este mes": (hoy.replace(day=1), hoy)
    }

def validate_positive_number(value: str, field_name: str = "campo") -> Optional[float]:
    """Valida que un valor sea un número positivo"""
    try:
        num = float(value)
        if num < 0:
            st.error(f"{field_name} debe ser un número positivo")
            return None
        return num
    except ValueError:
        st.error(f"{field_name} debe ser un número válido")
        return None

def validate_positive_integer(value: str, field_name: str = "campo") -> Optional[int]:
    """Valida que un valor sea un entero positivo"""
    try:
        num = int(value)
        if num < 0:
            st.error(f"{field_name} debe ser un número entero positivo")
            return None
        return num
    except ValueError:
        st.error(f"{field_name} debe ser un número entero válido")
        return None

def show_success_message(message: str):
    """Muestra un mensaje de éxito"""
    st.success(f"✅ {message}")

def show_error_message(message: str):
    """Muestra un mensaje de error"""
    st.error(f"❌ {message}")

def show_warning_message(message: str):
    """Muestra un mensaje de advertencia"""
    st.warning(f"⚠️ {message}")

def show_info_message(message: str):
    """Muestra un mensaje informativo"""
    st.info(f"ℹ️ {message}")

def create_download_button(file_path: str, file_name: str, button_text: str = "Descargar"):
    """Crea un botón de descarga para un archivo"""
    try:
        with open(file_path, "rb") as file:
            st.download_button(
                label=button_text,
                data=file,
                file_name=file_name,
                mime="application/pdf"
            )
    except FileNotFoundError:
        st.error("Archivo no encontrado")

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """División segura que evita división por cero"""
    return numerator / denominator if denominator != 0 else default

def truncate_text(text: str, max_length: int = 50) -> str:
    """Trunca un texto si es muy largo"""
    return text if len(text) <= max_length else text[:max_length-3] + "..."

def get_color_for_status(status: str) -> str:
    """Retorna un color basado en el estado"""
    colors = {
        "success": "#28a745",
        "warning": "#ffc107", 
        "error": "#dc3545",
        "info": "#17a2b8",
        "active": "#28a745",
        "inactive": "#6c757d"
    }
    return colors.get(status.lower(), "#17a2b8")

def initialize_session_state():
    """Inicializa variables de sesión necesarias"""
    if 'carrito' not in st.session_state:
        from database.models import Carrito
        st.session_state.carrito = Carrito()
    
    if 'venta_procesada' not in st.session_state:
        st.session_state.venta_procesada = None
    
    if 'show_ticket' not in st.session_state:
        st.session_state.show_ticket = False
        
    if 'show_form_venta' not in st.session_state:
        st.session_state.show_form_venta = False
    
    if 'ticket_generado' not in st.session_state:
        st.session_state.ticket_generado = False
        
    if 'ruta_ticket' not in st.session_state:
        st.session_state.ruta_ticket = None

def reset_venta_state():
    """Resetea el estado relacionado con ventas"""
    keys_to_reset = ['venta_procesada', 'show_ticket', 'show_form_venta', 'ticket_generado', 'ruta_ticket']
    
    for key in keys_to_reset:
        if key in st.session_state:
            if key in ['venta_procesada', 'ruta_ticket']:
                st.session_state[key] = None
            else:
                st.session_state[key] = False

def format_product_display(nombre: str, precio: float, stock: Optional[int] = None) -> str:
    """Formatea la información de un producto para mostrar"""
    display = f"{nombre}\n{format_currency(precio)}"
    if stock is not None:
        display += f"\nStock: {stock}"
    return display

def calculate_tax(subtotal: float, tax_rate: float) -> float:
    """Calcula el impuesto sobre un subtotal"""
    return subtotal * (tax_rate / 100)

def apply_discount(total: float, discount_percentage: float) -> tuple[float, float]:
    """Aplica un descuento y retorna (nuevo_total, descuento_aplicado)"""
    discount_amount = total * (discount_percentage / 100)
    new_total = total - discount_amount
    return new_total, discount_amount

def safe_float_conversion(value) -> float:
    """Conversión segura de cualquier tipo numérico a float"""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return 0.0
    return float(value) if value is not None else 0.0

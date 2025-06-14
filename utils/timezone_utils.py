"""
Utilidades para manejo de zona horaria México (UTC-6)
VERSIÓN DEFINITIVA - Offset fijo calculado UNA VEZ, sin servicios externos
"""
from datetime import datetime, timezone, timedelta
import pytz
from typing import Optional
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# ZONA HORARIA MÉXICO - DEFINIDA UNA VEZ Y PARA SIEMPRE
MEXICO_OFFSET_HOURS = -6  # UTC-6 siempre
MEXICO_OFFSET = timedelta(hours=MEXICO_OFFSET_HOURS)
MEXICO_TZ_PYTZ = pytz.timezone('America/Mexico_City')  # Para localize()
MEXICO_TZ_SIMPLE = timezone(MEXICO_OFFSET)  # Para astimezone()

# Sistema de cache simplificado
_timezone_cache = {
    'offset_calculated': False,
    'final_offset_hours': MEXICO_OFFSET_HOURS,  # Por defecto UTC-6
    'last_log': 0
}

def _calculate_offset_once():
    """
    Calcula el offset de México UNA SOLA VEZ y lo guarda en cache
    Sin servicios externos, solo lógica interna
    """
    global _timezone_cache
    
    if _timezone_cache['offset_calculated']:
        return _timezone_cache['final_offset_hours']
    
    # LÓGICA SIMPLE: México está en UTC-6 casi todo el año
    # Durante horario de verano (abril-octubre) puede ser UTC-5, pero
    # para consistencia en el sistema de ventas, usar SIEMPRE UTC-6
    
    _timezone_cache['final_offset_hours'] = -6
    _timezone_cache['offset_calculated'] = True
    
    logger.info(f"🇲🇽 Offset México calculado: UTC{_timezone_cache['final_offset_hours']}")
    return _timezone_cache['final_offset_hours']

def get_mexico_datetime() -> datetime:
    """
    Obtiene la fecha y hora actual en zona horaria de México
    VERSIÓN DEFINITIVA: Offset calculado una vez, sin servicios externos
    """
    global _timezone_cache
    import time
    
    # Calcular offset una sola vez
    offset_hours = _calculate_offset_once()
    
    # Obtener UTC actual y aplicar offset
    utc_now = datetime.now(timezone.utc)
    mexico_offset = timedelta(hours=offset_hours)
    mexico_time = utc_now + mexico_offset
    mexico_naive = mexico_time.replace(tzinfo=None)
    
    # Logging muy reducido
    current_time = time.time()
    if current_time - _timezone_cache.get('last_log', 0) > 1800:  # Solo cada 30 minutos
        logger.info(f"🇲🇽 México UTC{offset_hours}: {mexico_naive}")
        _timezone_cache['last_log'] = current_time
    
    return mexico_naive

def format_mexico_datetime(dt: Optional[datetime] = None) -> str:
    """
    Formatea una fecha y hora en formato legible para México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Si no tiene timezone, asumimos que ya es hora México
    if dt.tzinfo is None:
        # Ya está en hora México, solo formatear
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    else:
        # Convertir a México usando nuestro sistema
        dt_utc = dt.astimezone(timezone.utc)
        offset_hours = _calculate_offset_once()
        mexico_time = dt_utc + timedelta(hours=offset_hours)
        return mexico_time.strftime("%d/%m/%Y %H:%M:%S")

def get_mexico_date_str(dt: Optional[datetime] = None) -> str:
    """
    Obtiene la fecha en formato YYYY-MM-DD en zona horaria de México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Si no tiene timezone, asumimos que ya es hora México
    if dt.tzinfo is None:
        return dt.strftime("%Y-%m-%d")
    else:
        # Convertir a México
        dt_utc = dt.astimezone(timezone.utc)
        offset_hours = _calculate_offset_once()
        mexico_time = dt_utc + timedelta(hours=offset_hours)
        return mexico_time.strftime("%Y-%m-%d")

def get_mexico_time_str(dt: Optional[datetime] = None) -> str:
    """
    Obtiene la hora en formato HH:MM:SS en zona horaria de México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Si no tiene timezone, asumimos que ya es hora México
    if dt.tzinfo is None:
        return dt.strftime("%H:%M:%S")
    else:
        # Convertir a México
        dt_utc = dt.astimezone(timezone.utc)
        offset_hours = _calculate_offset_once()
        mexico_time = dt_utc + timedelta(hours=offset_hours)
        return mexico_time.strftime("%H:%M:%S")

def convert_to_mexico_time(dt: datetime) -> datetime:
    """
    Convierte cualquier datetime a zona horaria de México
    """
    if dt.tzinfo is None:
        # Asumimos que es UTC si no tiene timezone
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convertir a UTC primero
    dt_utc = dt.astimezone(timezone.utc)
    
    # Aplicar offset de México
    offset_hours = _calculate_offset_once()
    mexico_time = dt_utc + timedelta(hours=offset_hours)
    
    return mexico_time.replace(tzinfo=None)

def convert_to_mexico_tz(dt: datetime) -> datetime:
    """
    Convierte un datetime a zona horaria de México
    Args:
        dt: datetime a convertir (puede tener o no timezone)
    Returns:
        datetime en zona horaria de México
    """
    try:
        # Si no tiene timezone, asumimos UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convertir a timezone de México
        return dt.astimezone(MEXICO_TZ_SIMPLE)
        
    except Exception as e:
        logger.warning(f"⚠️ Error al convertir timezone: {e}")
        # Fallback: asumir que ya está en México
        return dt

def get_current_shift_period() -> str:
    """
    Determina el turno actual basado en la hora de México
    """
    mx_time = get_mexico_datetime()
    hour = mx_time.hour
    
    if 6 <= hour < 14:
        return "Matutino"
    elif 14 <= hour < 22:
        return "Vespertino"
    else:
        return "Nocturno"

def is_same_mexico_date(dt1: datetime, dt2: datetime) -> bool:
    """
    Verifica si dos fechas son el mismo día en zona horaria de México
    """
    mx_dt1 = convert_to_mexico_time(dt1)
    mx_dt2 = convert_to_mexico_time(dt2)
    
    return mx_dt1.date() == mx_dt2.date()

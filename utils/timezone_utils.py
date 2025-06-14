"""
Utilidades para manejo de zona horaria México (UTC-6)
OPTIMIZADO - con cache para reducir llamadas externas
"""
from datetime import datetime, timezone, timedelta
import pytz
from typing import Optional
import requests
import logging
import time

# Configurar logging
logger = logging.getLogger(__name__)

# Zona horaria de México
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Cache para tiempo sincronizado
_time_cache = {
    'last_sync': 0,
    'time_offset': None,
    'cache_duration': 300  # 5 minutos
}

def get_mexico_datetime() -> datetime:
    """
    Obtiene la fecha y hora actual en zona horaria de México (UTC-6)
    Usa cache para reducir llamadas externas
    """
    current_time = time.time()
    
    # Si no hay cache o ha expirado, intentar sincronizar
    if (_time_cache['time_offset'] is None or 
        current_time - _time_cache['last_sync'] > _time_cache['cache_duration']):
        
        try:
            # Solo intentar sincronización cada 5 minutos
            response = requests.get(
                'http://worldtimeapi.org/api/timezone/America/Mexico_City',
                timeout=2  # Timeout más corto
            )
            
            if response.status_code == 200:
                data = response.json()
                datetime_str = data['datetime']
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                
                # Calcular offset con tiempo local
                local_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
                _time_cache['time_offset'] = dt - local_utc
                _time_cache['last_sync'] = current_time
                
                logger.info(f"Tiempo sincronizado con servidor mexicano: {dt}")
                return dt
                
        except Exception as e:
            # No loggear cada error para reducir spam
            if current_time - _time_cache['last_sync'] > 60:  # Solo cada minuto
                logger.warning(f"No se pudo sincronizar con servidor de tiempo: {e}")
    
    # Usar cache si está disponible
    if _time_cache['time_offset'] is not None:
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return utc_now + _time_cache['time_offset']
    
    # Fallback: usar tiempo local convertido a México (sin log frecuente)
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    mexico_time = utc_now.astimezone(MEXICO_TZ)
    return mexico_time

def format_mexico_datetime(dt: Optional[datetime] = None) -> str:
    """
    Formatea una fecha y hora en formato legible para México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Asegurar que el datetime tenga timezone
    if dt.tzinfo is None:
        dt = MEXICO_TZ.localize(dt)
    elif dt.tzinfo != MEXICO_TZ:
        dt = dt.astimezone(MEXICO_TZ)
    
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def get_mexico_date_str(dt: Optional[datetime] = None) -> str:
    """
    Obtiene la fecha en formato YYYY-MM-DD en zona horaria de México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Asegurar que el datetime tenga timezone
    if dt.tzinfo is None:
        dt = MEXICO_TZ.localize(dt)
    elif dt.tzinfo != MEXICO_TZ:
        dt = dt.astimezone(MEXICO_TZ)
    
    return dt.strftime("%Y-%m-%d")

def get_mexico_time_str(dt: Optional[datetime] = None) -> str:
    """
    Obtiene la hora en formato HH:MM:SS en zona horaria de México
    """
    if dt is None:
        dt = get_mexico_datetime()
    
    # Asegurar que el datetime tenga timezone
    if dt.tzinfo is None:
        dt = MEXICO_TZ.localize(dt)
    elif dt.tzinfo != MEXICO_TZ:
        dt = dt.astimezone(MEXICO_TZ)
    
    return dt.strftime("%H:%M:%S")

def convert_to_mexico_time(dt: datetime) -> datetime:
    """
    Convierte cualquier datetime a zona horaria de México
    """
    if dt.tzinfo is None:
        # Si no tiene timezone, asumimos que es UTC
        dt = pytz.UTC.localize(dt)
    
    return dt.astimezone(MEXICO_TZ)

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

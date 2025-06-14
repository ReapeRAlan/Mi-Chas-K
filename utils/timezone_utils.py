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

"""
Utilidades para manejo de zona horaria México (UTC-6)
VERSIÓN ROBUSTA - con offset fijo confiable
"""
from datetime import datetime, timezone, timedelta
import pytz
from typing import Optional
import requests
import logging
import time

# Configurar logging
logger = logging.getLogger(__name__)

# Zona horaria de México (UTC-6) - SIEMPRE
MEXICO_OFFSET = timedelta(hours=-6)
MEXICO_TZ = timezone(MEXICO_OFFSET)

# Cache para tiempo sincronizado - reiniciar cache
_time_cache = {
    'last_sync': 0,
    'server_offset_validated': False,
    'cache_duration': 3600,  # 1 hora
    'last_log': 0  # Para logging controlado
}

def get_mexico_datetime() -> datetime:
    """
    Obtiene la fecha y hora actual en zona horaria de México (UTC-6)
    VERSIÓN ROBUSTA: Siempre usa UTC-6, validado contra servidor
    """
    current_time = time.time()
    
    # Obtener UTC actual
    utc_now = datetime.now(timezone.utc)
    
    # Si no hemos validado el offset recientemente, intentar sincronizar UNA VEZ
    if (not _time_cache['server_offset_validated'] or 
        current_time - _time_cache['last_sync'] > _time_cache['cache_duration']):
        
        try:
            # Intentar validar con servidor mexicano
            response = requests.get(
                'http://worldtimeapi.org/api/timezone/America/Mexico_City',
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                datetime_str = data['datetime']
                server_mexico = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                
                # Calcular qué offset usa el servidor
                server_utc = server_mexico.astimezone(timezone.utc)
                calculated_offset = server_mexico - server_utc
                
                # Verificar que el servidor confirma UTC-6
                if abs(calculated_offset.total_seconds() + 6*3600) < 3600:  # Dentro de 1 hora de diferencia
                    _time_cache['server_offset_validated'] = True
                    _time_cache['last_sync'] = current_time
                    logger.info(f"✅ Offset México validado con servidor: UTC-6")
                else:
                    logger.warning(f"⚠️ Servidor reporta offset diferente: {calculated_offset}")
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo validar con servidor, usando UTC-6 fijo: {e}")
    
    # SIEMPRE usar UTC-6 (independiente de la sincronización)
    mexico_time = utc_now.astimezone(MEXICO_TZ)
    mexico_naive = mexico_time.replace(tzinfo=None)
    
    # Logging solo cuando hay cambios significativos
    if current_time - _time_cache.get('last_log', 0) > 300:  # Solo cada 5 minutos
        logger.info(f"🇲🇽 Hora México (UTC-6): {mexico_naive}")
        _time_cache['last_log'] = current_time
    
    return mexico_naive

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

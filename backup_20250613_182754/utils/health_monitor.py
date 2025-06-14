"""
Sistema de monitoreo y health checks para MiChaska
"""
import streamlit as st
import time
import os
from datetime import datetime
from database.connection import get_db_connection
from utils.logging_config import log_database_operation
import logging

logger = logging.getLogger('michaska.health')

def check_database_health() -> dict:
    """Verifica el estado de la base de datos"""
    start_time = time.time()
    result = {
        'status': 'error',
        'message': '',
        'response_time': 0,
        'timestamp': datetime.now()
    }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        
        result['status'] = 'healthy'
        result['message'] = 'Database connection successful'
        result['response_time'] = round((time.time() - start_time) * 1000, 2)
        
        log_database_operation("Health Check", True, f"Response time: {result['response_time']}ms")
        
    except Exception as e:
        result['message'] = f"Database error: {str(e)}"
        result['response_time'] = round((time.time() - start_time) * 1000, 2)
        
        log_database_operation("Health Check", False, result['message'])
    
    return result

def show_system_status():
    """Muestra el estado del sistema en la sidebar"""
    with st.sidebar:
        if st.button("🔍 Check System Status"):
            with st.spinner("Checking system health..."):
                db_health = check_database_health()
                
                if db_health['status'] == 'healthy':
                    st.success(f"✅ Database: OK ({db_health['response_time']}ms)")
                else:
                    st.error(f"❌ Database: {db_health['message']}")
                
                # Mostrar información del entorno
                env_info = {
                    'Environment': 'Production' if os.getenv('DATABASE_URL') else 'Development',
                    'Timestamp': db_health['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with st.expander("Environment Info"):
                    for key, value in env_info.items():
                        st.text(f"{key}: {value}")

def monitor_performance():
    """Monitorea el rendimiento de la aplicación"""
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {
            'page_loads': 0,
            'database_queries': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    # Incrementar contador de carga de página
    st.session_state.performance_metrics['page_loads'] += 1

def show_performance_metrics():
    """Muestra métricas de rendimiento"""
    if 'performance_metrics' in st.session_state:
        metrics = st.session_state.performance_metrics
        uptime = time.time() - metrics['start_time']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Page Loads", metrics['page_loads'])
        
        with col2:
            st.metric("DB Queries", metrics['database_queries'])
        
        with col3:
            st.metric("Errors", metrics['errors'])
        
        with col4:
            st.metric("Uptime", f"{uptime/60:.1f}m")

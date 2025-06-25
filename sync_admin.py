#!/usr/bin/env python3
"""
Administrador de Sincronización Bidireccional
Sistema Mi Chas-K - Panel de Control Híbrido
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_adapter import DatabaseAdapter

class SyncManager:
    """Administrador de sincronización con panel de control"""
    
    def __init__(self):
        self.adapter = DatabaseAdapter()
        
    def get_sync_dashboard(self) -> Dict[str, Any]:
        """Obtener dashboard completo de sincronización"""
        try:
            # Estado del sistema
            system_status = self.adapter.get_system_status()
            
            # Estadísticas de cola de sincronización
            queue_stats = self._get_queue_statistics()
            
            # Último estado de sincronización
            last_sync = self._get_last_sync_info()
            
            # Diferencias entre local y remoto
            data_differences = self._analyze_data_differences()
            
            # Estado de salud del sistema
            health_status = self._get_health_status()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'queue_stats': queue_stats,
                'last_sync': last_sync,
                'data_differences': data_differences,
                'health_status': health_status,
                'recommendations': self._get_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard: {e}")
            return {'error': str(e)}
    
    def _get_queue_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas detalladas de la cola"""
        try:
            # Estadísticas por estado
            status_stats = self.adapter.execute_query("""
                SELECT status, COUNT(*) as count
                FROM sync_queue
                GROUP BY status
            """)
            
            # Estadísticas por tabla
            table_stats = self.adapter.execute_query("""
                SELECT table_name, COUNT(*) as count
                FROM sync_queue
                WHERE status = 'pending'
                GROUP BY table_name
            """)
            
            # Elementos con más intentos
            high_attempts = self.adapter.execute_query("""
                SELECT id, table_name, operation, attempts, data
                FROM sync_queue
                WHERE attempts >= 3 AND status = 'pending'
                ORDER BY attempts DESC, timestamp ASC
                LIMIT 10
            """)
            
            # Elementos más antiguos pendientes
            oldest_pending = self.adapter.execute_query("""
                SELECT id, table_name, operation, timestamp, attempts
                FROM sync_queue
                WHERE status = 'pending'
                ORDER BY timestamp ASC
                LIMIT 5
            """)
            
            return {
                'by_status': {row['status']: row['count'] for row in status_stats},
                'by_table': {row['table_name']: row['count'] for row in table_stats},
                'high_attempts': [dict(row) for row in high_attempts],
                'oldest_pending': [dict(row) for row in oldest_pending]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de cola: {e}")
            return {}
    
    def _get_last_sync_info(self) -> Dict[str, Any]:
        """Obtener información del último proceso de sincronización"""
        try:
            # Última sincronización exitosa
            last_completed = self.adapter.execute_query("""
                SELECT MAX(timestamp) as last_completed
                FROM sync_queue
                WHERE status = 'completed'
            """)
            
            # Última sincronización fallida
            last_failed = self.adapter.execute_query("""
                SELECT MAX(timestamp) as last_failed
                FROM sync_queue
                WHERE status = 'failed'
            """)
            
            # Total de operaciones hoy
            today_ops = self.adapter.execute_query("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM sync_queue
                WHERE DATE(timestamp) = DATE('now')
            """)
            
            return {
                'last_completed': last_completed[0]['last_completed'] if last_completed and last_completed[0]['last_completed'] else None,
                'last_failed': last_failed[0]['last_failed'] if last_failed and last_failed[0]['last_failed'] else None,
                'today_operations': dict(today_ops[0]) if today_ops else {},
                'last_attempt': getattr(self.adapter, 'last_sync_attempt', None)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo info de última sincronización: {e}")
            return {}
    
    def _analyze_data_differences(self) -> Dict[str, Any]:
        """Analizar diferencias entre datos locales y remotos"""
        differences = {}
        
        if not self.adapter.remote_available:
            return {'note': 'Conexión remota no disponible para comparación'}
        
        try:
            tables = ['productos', 'categorias', 'vendedores', 'ventas', 'detalle_ventas']
            
            for table in tables:
                # Contar registros locales
                local_count = self.adapter.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}", prefer_remote=False
                )
                
                # Contar registros remotos
                remote_count = self.adapter.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}", prefer_remote=True
                )
                
                local_num = local_count[0]['count'] if local_count else 0
                remote_num = remote_count[0]['count'] if remote_count else 0
                
                differences[table] = {
                    'local': local_num,
                    'remote': remote_num,
                    'difference': remote_num - local_num,
                    'sync_needed': abs(remote_num - local_num) > 0
                }
                
        except Exception as e:
            logger.error(f"Error analizando diferencias: {e}")
            differences['error'] = str(e)
        
        return differences
    
    def _get_health_status(self) -> Dict[str, Any]:
        """Evaluar estado de salud del sistema de sincronización"""
        health = {
            'overall': 'healthy',
            'issues': [],
            'warnings': [],
            'score': 100
        }
        
        try:
            # Verificar conexiones
            if not self.adapter.remote_available:
                health['warnings'].append('Conexión remota no disponible')
                health['score'] -= 20
            
            # Verificar cola de sincronización
            pending_count = self.adapter.execute_query("""
                SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'
            """)
            
            if pending_count and pending_count[0]['count'] > 50:
                health['issues'].append(f"Cola de sincronización alta: {pending_count[0]['count']} elementos pendientes")
                health['score'] -= 15
            elif pending_count and pending_count[0]['count'] > 20:
                health['warnings'].append(f"Cola de sincronización moderada: {pending_count[0]['count']} elementos pendientes")
                health['score'] -= 5
            
            # Verificar elementos con muchos intentos fallidos
            failed_attempts = self.adapter.execute_query("""
                SELECT COUNT(*) as count FROM sync_queue WHERE attempts >= 3 AND status = 'pending'
            """)
            
            if failed_attempts and failed_attempts[0]['count'] > 0:
                health['issues'].append(f"{failed_attempts[0]['count']} elementos con múltiples intentos fallidos")
                health['score'] -= 10
            
            # Verificar elementos muy antiguos
            old_pending = self.adapter.execute_query("""
                SELECT COUNT(*) as count 
                FROM sync_queue 
                WHERE status = 'pending' 
                AND timestamp < datetime('now', '-1 hour')
            """)
            
            if old_pending and old_pending[0]['count'] > 0:
                health['warnings'].append(f"{old_pending[0]['count']} elementos pendientes por más de 1 hora")
                health['score'] -= 5
            
            # Determinar estado general
            if health['score'] >= 90:
                health['overall'] = 'excellent'
            elif health['score'] >= 75:
                health['overall'] = 'good'
            elif health['score'] >= 50:
                health['overall'] = 'fair'
            else:
                health['overall'] = 'poor'
                
        except Exception as e:
            health['issues'].append(f"Error evaluando salud del sistema: {e}")
            health['overall'] = 'unknown'
        
        return health
    
    def _get_recommendations(self) -> List[str]:
        """Obtener recomendaciones basadas en el estado del sistema"""
        recommendations = []
        
        try:
            # Verificar cola pendiente
            pending = self.adapter.execute_query("""
                SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'
            """)
            
            if pending and pending[0]['count'] > 20:
                recommendations.append("Ejecutar sincronización manual para reducir cola pendiente")
            
            # Verificar elementos fallidos
            failed = self.adapter.execute_query("""
                SELECT COUNT(*) as count FROM sync_queue WHERE status = 'failed'
            """)
            
            if failed and failed[0]['count'] > 10:
                recommendations.append("Limpiar elementos fallidos de la cola de sincronización")
            
            # Verificar conexión remota
            if not self.adapter.remote_available:
                recommendations.append("Verificar configuración de conexión remota")
                recommendations.append("Considerar trabajar en modo offline hasta restaurar conexión")
            
            # Recomendaciones generales
            if not recommendations:
                recommendations.append("Sistema funcionando correctamente")
                recommendations.append("Mantener monitoreo regular del estado de sincronización")
                
        except Exception as e:
            recommendations.append(f"Error generando recomendaciones: {e}")
        
        return recommendations
    
    def force_full_sync(self, direction: str = 'bidirectional') -> Dict[str, Any]:
        """Forzar sincronización completa"""
        result = {
            'started_at': datetime.now().isoformat(),
            'direction': direction,
            'success': False,
            'details': {}
        }
        
        try:
            if direction in ['bidirectional', 'local_to_remote']:
                logger.info("🔄 Sincronizando cambios locales a remoto...")
                self.adapter._process_sync_queue()
                result['details']['local_to_remote'] = 'completed'
            
            if direction in ['bidirectional', 'remote_to_local']:
                logger.info("🔄 Sincronizando cambios remotos a local...")
                self.adapter._sync_remote_to_local()
                result['details']['remote_to_local'] = 'completed'
            
            result['success'] = True
            result['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error en sincronización forzada: {e}")
        
        return result
    
    def clean_sync_queue(self, clean_type: str = 'failed') -> Dict[str, Any]:
        """Limpiar cola de sincronización"""
        result = {
            'started_at': datetime.now().isoformat(),
            'clean_type': clean_type,
            'cleaned_count': 0
        }
        
        try:
            if clean_type == 'failed':
                # Limpiar elementos fallidos
                cleaned = self.adapter.execute_update("""
                    DELETE FROM sync_queue WHERE status = 'failed'
                """)
                
            elif clean_type == 'completed':
                # Limpiar elementos completados (mantener últimos 100)
                cleaned = self.adapter.execute_update("""
                    DELETE FROM sync_queue 
                    WHERE status = 'completed' 
                    AND id NOT IN (
                        SELECT id FROM sync_queue 
                        WHERE status = 'completed' 
                        ORDER BY timestamp DESC 
                        LIMIT 100
                    )
                """)
                
            elif clean_type == 'old':
                # Limpiar elementos antiguos (más de 7 días)
                cleaned = self.adapter.execute_update("""
                    DELETE FROM sync_queue 
                    WHERE timestamp < datetime('now', '-7 days')
                    AND status IN ('completed', 'failed')
                """)
                
            elif clean_type == 'all':
                # Limpiar toda la cola (PELIGROSO)
                cleaned = self.adapter.execute_update("DELETE FROM sync_queue")
            
            result['cleaned_count'] = cleaned or 0
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error limpiando cola: {e}")
        
        return result

def print_dashboard():
    """Imprimir dashboard de sincronización"""
    manager = SyncManager()
    dashboard = manager.get_sync_dashboard()
    
    if 'error' in dashboard:
        print(f"❌ Error obteniendo dashboard: {dashboard['error']}")
        return
    
    print("🎛️  PANEL DE CONTROL - SINCRONIZACIÓN BIDIRECCIONAL")
    print("=" * 60)
    
    # Estado del sistema
    system = dashboard.get('system_status', {})
    print("🖥️  ESTADO DEL SISTEMA:")
    print(f"   🌐 Remoto: {'✅ Disponible' if system.get('remote_available') else '❌ No disponible'}")
    print(f"   💾 Local: {'✅ OK' if system.get('local_available') else '❌ Error'}")
    print(f"   📶 Internet: {'✅ Conectado' if system.get('internet_connection') else '❌ Sin conexión'}")
    
    # Estado de salud
    health = dashboard.get('health_status', {})
    health_icon = {
        'excellent': '🟢',
        'good': '🟡', 
        'fair': '🟠',
        'poor': '🔴',
        'unknown': '⚪'
    }.get(health.get('overall'), '⚪')
    
    print(f"\n💚 ESTADO DE SALUD: {health_icon} {health.get('overall', 'unknown').upper()} (Score: {health.get('score', 0)})")
    
    if health.get('issues'):
        print("   🚨 Problemas:")
        for issue in health['issues']:
            print(f"     - {issue}")
    
    if health.get('warnings'):
        print("   ⚠️  Advertencias:")
        for warning in health['warnings']:
            print(f"     - {warning}")
    
    # Cola de sincronización
    queue = dashboard.get('queue_stats', {})
    print(f"\n📝 COLA DE SINCRONIZACIÓN:")
    by_status = queue.get('by_status', {})
    total_queue = sum(by_status.values())
    print(f"   📊 Total: {total_queue} elementos")
    for status, count in by_status.items():
        status_icon = {'pending': '⏳', 'completed': '✅', 'failed': '❌'}.get(status, '📋')
        print(f"   {status_icon} {status}: {count}")
    
    if queue.get('by_table'):
        print("   📋 Por tabla:")
        for table, count in queue['by_table'].items():
            print(f"     - {table}: {count} pendientes")
    
    # Diferencias de datos
    differences = dashboard.get('data_differences', {})
    if differences and 'note' not in differences:
        print(f"\n📊 DIFERENCIAS DE DATOS:")
        for table, diff in differences.items():
            if isinstance(diff, dict):
                local_count = diff.get('local', 0)
                remote_count = diff.get('remote', 0)
                difference = diff.get('difference', 0)
                sync_icon = '🔄' if diff.get('sync_needed') else '✅'
                print(f"   {sync_icon} {table}: Local({local_count}) | Remoto({remote_count}) | Diff({difference:+d})")
    
    # Recomendaciones
    recommendations = dashboard.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMENDACIONES:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    print(f"\n🕐 Actualizado: {dashboard.get('timestamp', 'N/A')}")

def interactive_menu():
    """Menú interactivo para administrar sincronización"""
    manager = SyncManager()
    
    while True:
        print("\n" + "=" * 60)
        print("🎛️  ADMINISTRADOR DE SINCRONIZACIÓN - Mi Chas-K")
        print("=" * 60)
        print("1. 📊 Ver Dashboard")
        print("2. 🔄 Sincronización Forzada (Bidireccional)")
        print("3. ⬆️  Sincronizar Local → Remoto")
        print("4. ⬇️  Sincronizar Remoto → Local")
        print("5. 🧹 Limpiar Cola (Elementos Fallidos)")
        print("6. 🧹 Limpiar Cola (Elementos Completados)")
        print("7. 🧹 Limpiar Cola (Elementos Antiguos)")
        print("8. 🧪 Ejecutar Pruebas")
        print("9. 🔧 Test Correcciones de Errores")
        print("0. ❌ Salir")
        
        choice = input("\n👉 Selecciona una opción: ").strip()
        
        if choice == '1':
            print_dashboard()
            
        elif choice == '2':
            print("\n🔄 Ejecutando sincronización bidireccional...")
            result = manager.force_full_sync('bidirectional')
            if result['success']:
                print("✅ Sincronización completada exitosamente")
            else:
                print(f"❌ Error en sincronización: {result.get('error')}")
                
        elif choice == '3':
            print("\n⬆️ Sincronizando local a remoto...")
            result = manager.force_full_sync('local_to_remote')
            if result['success']:
                print("✅ Sincronización local→remoto completada")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif choice == '4':
            print("\n⬇️ Sincronizando remoto a local...")
            result = manager.force_full_sync('remote_to_local')
            if result['success']:
                print("✅ Sincronización remoto→local completada")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif choice == '5':
            print("\n🧹 Limpiando elementos fallidos...")
            result = manager.clean_sync_queue('failed')
            if result.get('success'):
                print(f"✅ {result['cleaned_count']} elementos fallidos eliminados")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif choice == '6':
            print("\n🧹 Limpiando elementos completados antiguos...")
            result = manager.clean_sync_queue('completed')
            if result.get('success'):
                print(f"✅ {result['cleaned_count']} elementos completados eliminados")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif choice == '7':
            print("\n🧹 Limpiando elementos antiguos (>7 días)...")
            result = manager.clean_sync_queue('old')
            if result.get('success'):
                print(f"✅ {result['cleaned_count']} elementos antiguos eliminados")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif choice == '8':
            print("\n🧪 Ejecutando pruebas de sincronización...")
            os.system("python test_bidirectional_sync.py")
            
        elif choice == '9':
            print("\n🔧 Ejecutando tests de correcciones de errores...")
            os.system("python test_sync_errors.py")
            
        elif choice == '0':
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción no válida")
        
        input("\n📎 Presiona Enter para continuar...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--dashboard':
        print_dashboard()
    else:
        interactive_menu()

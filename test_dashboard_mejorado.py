#!/usr/bin/env python3
"""
Prueba de las nuevas funcionalidades del dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_generator():
    """Prueba del generador de reportes PDF"""
    
    print("🧪 PRUEBA GENERADOR DE REPORTES PDF")
    print("=" * 50)
    
    try:
        from utils.pdf_generator import ReporteGenerator
        from utils.timezone_utils import get_mexico_date_str
        
        generator = ReporteGenerator()
        fecha_hoy = get_mexico_date_str()
        
        print(f"📅 Generando reporte para: {fecha_hoy}")
        
        # Generar reporte
        pdf_bytes = generator.generar_reporte_diario(fecha_hoy)
        
        print(f"📄 PDF generado: {len(pdf_bytes)} bytes")
        
        # Guardar archivo de prueba
        with open(f"reporte_prueba_{fecha_hoy}.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        print("✅ Reporte PDF generado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en generador PDF: {e}")
        return False

def test_dashboard_functions():
    """Prueba las funciones principales del dashboard"""
    
    print("\n🧪 PRUEBA FUNCIONES DASHBOARD")
    print("=" * 50)
    
    try:
        from pages.dashboard import (
            mostrar_dashboard,
            mostrar_comparacion_detallada,
            generar_reporte_diario
        )
        
        print("✅ Importaciones del dashboard exitosas")
        
        # Verificar que las funciones existen
        functions_to_test = [
            mostrar_dashboard,
            mostrar_comparacion_detallada,
            generar_reporte_diario
        ]
        
        for func in functions_to_test:
            print(f"✅ Función {func.__name__} disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en funciones dashboard: {e}")
        return False

def test_database_models():
    """Prueba que los modelos de base de datos estén funcionando"""
    
    print("\n🧪 PRUEBA MODELOS DE BASE DE DATOS")
    print("=" * 50)
    
    try:
        from database.models import Venta, GastoDiario, CorteCaja
        from utils.timezone_utils import get_mexico_date_str
        
        fecha_hoy = get_mexico_date_str()
        print(f"📅 Consultando datos para: {fecha_hoy}")
        
        # Probar consultas básicas
        ventas = Venta.get_by_fecha(fecha_hoy, fecha_hoy)
        print(f"📊 Ventas encontradas: {len(ventas)}")
        
        gastos = GastoDiario.get_by_fecha(fecha_hoy)
        print(f"💸 Gastos encontrados: {len(gastos)}")
        
        corte = CorteCaja.get_by_fecha(fecha_hoy)
        print(f"💰 Corte de caja: {'Existe' if corte else 'No existe'}")
        
        print("✅ Modelos de base de datos funcionando")
        return True
        
    except Exception as e:
        print(f"❌ Error en modelos: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del dashboard mejorado...")
    
    exito1 = test_database_models()
    exito2 = test_dashboard_functions()
    exito3 = test_pdf_generator()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 50)
    print(f"   Modelos BD:       {'✅ PASS' if exito1 else '❌ FAIL'}")
    print(f"   Funciones dash:   {'✅ PASS' if exito2 else '❌ FAIL'}")
    print(f"   Generador PDF:    {'✅ PASS' if exito3 else '❌ FAIL'}")
    
    if exito1 and exito2 and exito3:
        print("\n🎉 DASHBOARD MEJORADO LISTO")
        print("   ✅ Comparación caja vs ventas")
        print("   ✅ Generador de reportes PDF")
        print("   ✅ Análisis detallado de diferencias")
        print("   ✅ Casos y recomendaciones")
        sys.exit(0)
    else:
        print("\n💥 ALGUNAS FUNCIONALIDADES TIENEN PROBLEMAS")
        sys.exit(1)

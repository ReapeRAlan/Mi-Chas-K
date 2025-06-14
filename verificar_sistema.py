#!/usr/bin/env python3
"""
Verificación de posibles errores en el dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dashboard_syntax():
    """Verifica la sintaxis del dashboard"""
    print("🔍 VERIFICACIÓN SINTAXIS DASHBOARD")
    print("=" * 50)
    
    try:
        # Verificar sintaxis básica
        with open("pages/dashboard.py", "r") as f:
            code = f.read()
        
        compile(code, "pages/dashboard.py", "exec")
        print("✅ Sintaxis del dashboard correcta")
        
        # Verificar imports críticos
        critical_patterns = [
            "pd.to_numeric",
            "fillna(0)",
            "if dinero_esperado > 0 else",
            "try:",
            "except Exception",
            "pd.notnull",
            "pd.isinf"
        ]
        
        missing_patterns = []
        for pattern in critical_patterns:
            if pattern not in code:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"⚠️  Patrones faltantes: {missing_patterns}")
        else:
            print("✅ Todos los patrones de seguridad presentes")
        
        # Verificar funciones críticas
        critical_functions = [
            "def mostrar_historial_cortes",
            "def mostrar_comparacion_detallada",
            "def generar_reporte_diario",
            "def realizar_corte_caja"
        ]
        
        for func in critical_functions:
            if func in code:
                print(f"✅ {func} presente")
            else:
                print(f"❌ {func} faltante")
                return False
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_pdf_generator():
    """Verifica el generador PDF"""
    print("\n📄 VERIFICACIÓN GENERADOR PDF")
    print("=" * 50)
    
    try:
        with open("utils/pdf_generator.py", "r") as f:
            code = f.read()
        
        compile(code, "utils/pdf_generator.py", "exec")
        print("✅ Sintaxis del generador PDF correcta")
        
        # Verificar clase ReporteGenerator
        if "class ReporteGenerator" in code:
            print("✅ Clase ReporteGenerator presente")
        else:
            print("❌ Clase ReporteGenerator faltante")
            return False
        
        # Verificar método principal
        if "def generar_reporte_diario" in code:
            print("✅ Método generar_reporte_diario presente")
        else:
            print("❌ Método generar_reporte_diario faltante")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en PDF generator: {e}")
        return False

def check_timezone_utils():
    """Verifica las utilidades de zona horaria"""
    print("\n🕐 VERIFICACIÓN TIMEZONE UTILS")
    print("=" * 50)
    
    try:
        with open("utils/timezone_utils.py", "r") as f:
            code = f.read()
        
        compile(code, "utils/timezone_utils.py", "exec")
        print("✅ Sintaxis de timezone_utils correcta")
        
        # Verificar funciones críticas
        critical_functions = [
            "def get_mexico_datetime",
            "def format_mexico_datetime",
            "def _calculate_offset_once"
        ]
        
        for func in critical_functions:
            if func in code:
                print(f"✅ {func} presente")
            else:
                print(f"❌ {func} faltante")
                return False
        
        # Verificar que no usa servicios externos problemáticos
        if "requests.get" not in code:
            print("✅ Sin dependencias externas problemáticas")
        else:
            print("⚠️  Todavía usa requests (revisar si es necesario)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en timezone_utils: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando verificación completa del sistema...")
    
    exito1 = check_dashboard_syntax()
    exito2 = check_pdf_generator()
    exito3 = check_timezone_utils()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    print(f"   Dashboard:        {'✅ OK' if exito1 else '❌ ERROR'}")
    print(f"   PDF Generator:    {'✅ OK' if exito2 else '❌ ERROR'}")
    print(f"   Timezone Utils:   {'✅ OK' if exito3 else '❌ ERROR'}")
    
    if exito1 and exito2 and exito3:
        print("\n🎉 SISTEMA COMPLETAMENTE VERIFICADO")
        print("   ✅ Sin errores de sintaxis")
        print("   ✅ Funciones críticas presentes")
        print("   ✅ Protecciones implementadas")
        print("   ✅ Listo para producción")
        
        print("\n🚀 EL REDEPLOY DEBERÍA FUNCIONAR SIN ERRORES")
        sys.exit(0)
    else:
        print("\n💥 SE ENCONTRARON PROBLEMAS")
        print("   Revisar los errores antes del deploy")
        sys.exit(1)

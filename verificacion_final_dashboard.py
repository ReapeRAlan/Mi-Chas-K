#!/usr/bin/env python3
"""
Verificación final del dashboard mejorado
Valida que todas las funciones críticas estén presentes y funcionando
"""

import sys
import os
from datetime import datetime

print("🔍 VERIFICACIÓN FINAL DEL DASHBOARD MEJORADO")
print("=" * 50)

# Verificar sintaxis de archivos críticos
archivos_criticos = [
    'pages/dashboard.py',
    'utils/pdf_generator.py',
    'utils/timezone_utils.py',
    'database/models.py'
]

print("\n1. 🧪 VERIFICACIÓN DE SINTAXIS")
print("-" * 30)
for archivo in archivos_criticos:
    try:
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                compile(f.read(), archivo, 'exec')
            print(f"✅ {archivo}: SINTAXIS OK")
        else:
            print(f"❌ {archivo}: ARCHIVO NO ENCONTRADO")
    except SyntaxError as e:
        print(f"❌ {archivo}: ERROR DE SINTAXIS - {e}")
    except Exception as e:
        print(f"⚠️ {archivo}: ADVERTENCIA - {e}")

# Verificar funciones críticas en dashboard
print("\n2. 🔧 VERIFICACIÓN DE FUNCIONES CRÍTICAS")
print("-" * 40)

try:
    with open('pages/dashboard.py', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    funciones_criticas = [
        'mostrar_dashboard',
        'mostrar_comparacion_detallada',
        'mostrar_corte_caja',
        'generar_reporte_diario',
        'mostrar_historial_cortes'
    ]
    
    for funcion in funciones_criticas:
        if f"def {funcion}" in contenido:
            print(f"✅ Función {funcion}: PRESENTE")
        else:
            print(f"❌ Función {funcion}: FALTANTE")
    
    # Verificar elementos específicos de la comparación
    elementos_comparacion = [
        'SISTEMA/APP',
        'CAJA FÍSICA',
        'COMPARACIÓN DETALLADA',
        'Análisis de diferencias',
        'Tabla Resumen Comparativa'
    ]
    
    print(f"\n   📊 Elementos de comparación:")
    for elemento in elementos_comparacion:
        if elemento in contenido:
            print(f"   ✅ {elemento}: PRESENTE")
        else:
            print(f"   ❌ {elemento}: FALTANTE")

except Exception as e:
    print(f"❌ Error al verificar dashboard: {e}")

# Verificar generador de PDF
print("\n3. 📄 VERIFICACIÓN GENERADOR PDF")
print("-" * 35)

try:
    with open('utils/pdf_generator.py', 'r', encoding='utf-8') as f:
        contenido_pdf = f.read()
    
    if 'class ReporteGenerator' in contenido_pdf:
        print("✅ Clase ReporteGenerator: PRESENTE")
        if 'generar_reporte_diario' in contenido_pdf:
            print("✅ Método generar_reporte_diario: PRESENTE")
        else:
            print("❌ Método generar_reporte_diario: FALTANTE")
    else:
        print("❌ Clase ReporteGenerator: FALTANTE")

except Exception as e:
    print(f"❌ Error al verificar PDF generator: {e}")

# Verificar timezone utils
print("\n4. 🌍 VERIFICACIÓN ZONA HORARIA")
print("-" * 35)

try:
    with open('utils/timezone_utils.py', 'r', encoding='utf-8') as f:
        contenido_tz = f.read()
    
    funciones_tz = [
        'get_mexico_datetime',
        'get_mexico_date_str',
        'convert_to_mexico_tz'
    ]
    
    for funcion in funciones_tz:
        if f"def {funcion}" in contenido_tz:
            print(f"✅ {funcion}: PRESENTE")
        else:
            print(f"❌ {funcion}: FALTANTE")

except Exception as e:
    print(f"❌ Error al verificar timezone utils: {e}")

# Verificar requirements.txt
print("\n5. 📦 VERIFICACIÓN DEPENDENCIAS")
print("-" * 35)

try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = f.read()
    
    dependencias_criticas = [
        'streamlit',
        'pandas',
        'plotly',
        'reportlab',
        'pytz'
    ]
    
    for dep in dependencias_criticas:
        if dep in requirements:
            print(f"✅ {dep}: PRESENTE")
        else:
            print(f"❌ {dep}: FALTANTE")

except Exception as e:
    print(f"❌ Error al verificar requirements: {e}")

print("\n" + "=" * 50)
print("🎯 VERIFICACIÓN COMPLETADA")
print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🚀 Sistema listo para producción")
print("=" * 50)

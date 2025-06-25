#!/usr/bin/env python3
"""
Script para corregir todas las páginas del sistema
"""
import os
import re

def fix_page_file(filepath, old_function_name, new_function_name):
    """Corregir archivo de página individual"""
    print(f"🔧 Corrigiendo {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Corregir importaciones
        content = re.sub(
            r'from database\.connection_adapter import execute_query, execute_update',
            '',
            content
        )
        
        # 2. Corregir definición de función
        content = re.sub(
            rf'def {old_function_name}\(\):',
            f'def {new_function_name}(adapter):',
            content
        )
        
        # 3. Corregir llamadas a execute_query
        content = re.sub(
            r'execute_query\(',
            'adapter.execute_query(',
            content
        )
        
        # 4. Corregir llamadas a execute_update
        content = re.sub(
            r'execute_update\(',
            'adapter.execute_update(',
            content
        )
        
        # 5. Remover botones de "volver al inicio" (ya no necesarios)
        content = re.sub(
            r'\s*# Botón volver\s*if st\.button\("← Volver al inicio"\):\s*st\.session_state\.page = \'main\'\s*st\.rerun\(\)',
            '',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # 6. Limpiar importaciones vacías
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Escribir archivo corregido
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Corregido exitosamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 CORRIGIENDO TODAS LAS PÁGINAS DEL SISTEMA")
    print("=" * 50)
    
    pages_to_fix = [
        ('pages/inventario_simple.py', 'mostrar_inventario_simple', 'show_inventario'),
        ('pages/dashboard_simple.py', 'mostrar_dashboard_simple', 'show_dashboard'),
        ('pages/configuracion_simple.py', 'mostrar_configuracion_simple', 'show_configuracion'),
    ]
    
    success_count = 0
    
    for filepath, old_name, new_name in pages_to_fix:
        if os.path.exists(filepath):
            if fix_page_file(filepath, old_name, new_name):
                success_count += 1
        else:
            print(f"⚠️ Archivo no encontrado: {filepath}")
    
    print(f"\n📊 RESUMEN:")
    print(f"   ✅ Archivos corregidos: {success_count}")
    print(f"   📋 Total archivos: {len(pages_to_fix)}")
    
    if success_count == len(pages_to_fix):
        print("\n🎉 Todas las páginas corregidas exitosamente!")
    else:
        print(f"\n⚠️ Algunos archivos necesitan corrección manual")

if __name__ == "__main__":
    main()

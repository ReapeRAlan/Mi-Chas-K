#!/usr/bin/env python3
"""
Script para investigar la estructura real de la base de datos en Render
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
from dotenv import load_dotenv

load_dotenv()

def investigar_base_datos():
    """Investigar estructura completa de la base de datos"""
    print("🔍 INVESTIGANDO ESTRUCTURA DE BASE DE DATOS EN RENDER")
    print("=" * 60)
    
    try:
        # Conectar a la base de datos
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL no encontrada")
            return
        
        print(f"🌐 Conectando a: {database_url.split('@')[1]}")
        
        with psycopg2.connect(database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                # 1. Listar todas las tablas
                print("\n📋 TABLAS EXISTENTES:")
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tablas = cursor.fetchall()
                
                for tabla in tablas:
                    print(f"  📄 {tabla['table_name']}")
                
                # 2. Estructura de cada tabla
                for tabla in tablas:
                    nombre_tabla = tabla['table_name']
                    print(f"\n🏗️ ESTRUCTURA DE TABLA: {nombre_tabla}")
                    
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (nombre_tabla,))
                    
                    columnas = cursor.fetchall()
                    
                    for col in columnas:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"    {col['column_name']}: {col['data_type']} {nullable}{default}")
                    
                    # Contar registros
                    try:
                        cursor.execute(f"SELECT COUNT(*) as total FROM {nombre_tabla}")
                        count = cursor.fetchone()['total']
                        print(f"    📊 Total registros: {count}")
                    except Exception as e:
                        print(f"    ❌ Error contando: {e}")
                
                # 3. Datos de muestra de cada tabla
                print(f"\n📊 DATOS DE MUESTRA:")
                for tabla in tablas:
                    nombre_tabla = tabla['table_name']
                    try:
                        cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT 3")
                        datos = cursor.fetchall()
                        
                        if datos:
                            print(f"\n  🔍 Muestra de {nombre_tabla}:")
                            for i, row in enumerate(datos, 1):
                                print(f"    {i}. {dict(row)}")
                        else:
                            print(f"\n  📝 {nombre_tabla}: Sin datos")
                    except Exception as e:
                        print(f"\n  ❌ Error en {nombre_tabla}: {e}")
                
                # 4. Verificar tipos específicos problemáticos
                print(f"\n🔧 VERIFICACIONES ESPECÍFICAS:")
                
                # Verificar campo activo en productos
                if any(t['table_name'] == 'productos' for t in tablas):
                    try:
                        cursor.execute("""
                            SELECT column_name, data_type 
                            FROM information_schema.columns
                            WHERE table_name = 'productos' AND column_name LIKE '%activ%'
                        """)
                        activo_cols = cursor.fetchall()
                        print(f"  🔍 Columnas 'activo' en productos:")
                        for col in activo_cols:
                            print(f"    {col['column_name']}: {col['data_type']}")
                    except Exception as e:
                        print(f"  ❌ Error verificando 'activo': {e}")
                
                # Verificar relaciones categoria
                try:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns
                        WHERE table_name = 'productos' AND column_name LIKE '%categoria%'
                    """)
                    cat_cols = cursor.fetchall()
                    print(f"  🔍 Columnas categoria en productos:")
                    for col in cat_cols:
                        print(f"    {col['column_name']}: {col['data_type']}")
                except Exception as e:
                    print(f"  ❌ Error verificando categoria: {e}")
                
                print(f"\n✅ INVESTIGACIÓN COMPLETADA")
                
    except Exception as e:
        print(f"❌ ERROR CONECTANDO A BASE DE DATOS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigar_base_datos()

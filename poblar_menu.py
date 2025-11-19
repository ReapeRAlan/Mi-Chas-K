#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con el menú completo de Mi Chas-K
"""
import os
import sqlite3
from datetime import datetime

def poblar_menu_michaska():
    """Crea el menú completo de Mi Chas-K"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'michaska_local.db')
    print(f"📂 Base de datos: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Limpiar datos existentes
    print("🧹 Limpiando datos existentes...")
    cursor.execute("DELETE FROM detalle_ventas")
    cursor.execute("DELETE FROM entregas")
    cursor.execute("DELETE FROM ventas")
    cursor.execute("DELETE FROM productos")
    cursor.execute("DELETE FROM categorias")
    cursor.execute("DELETE FROM vendedores")
    conn.commit()
    print("   ✅ Datos limpiados\n")
    
    # Categorías del menú
    print("📦 Insertando categorías...")
    categorias = [
        ('Chascas', 'Chascas clásicas en diferentes tamaños'),
        ('DoriChascas', 'Chascas con diferentes sabores de Doritos'),
        ('Empapelados', 'Empapelados con variedad de ingredientes'),
        ('Elotes', 'Elotes en diferentes presentaciones'),
        ('Especialidades', 'Platillos especiales y combinaciones')
    ]
    
    cursor.executemany(
        "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)",
        categorias
    )
    print(f"   ✅ {len(categorias)} categorías insertadas\n")
    
    # Obtener IDs de categorías
    cursor.execute("SELECT id, nombre FROM categorias")
    cats = {nombre: id for id, nombre in cursor.fetchall()}
    
    # Productos del menú
    print("🍴 Insertando productos del menú...")
    productos = [
        # Chascas (categoría 1)
        ('Chasca Mini', 'Chasca en presentación mini', 20.00, 100, cats['Chascas']),
        ('Chasca Chica', 'Chasca en presentación chica', 25.00, 100, cats['Chascas']),
        ('Chasca Chica Plus', 'Chasca chica con extras', 35.00, 100, cats['Chascas']),
        ('Chasca Mediana', 'Chasca en presentación mediana', 50.00, 100, cats['Chascas']),
        ('Chasca Grande', 'Chasca en presentación grande', 60.00, 100, cats['Chascas']),
        
        # DoriChascas (categoría 2)
        ('DoriChasca Original', 'Chasca con Doritos Nacho', 65.00, 100, cats['DoriChascas']),
        ('TostiChasca', 'Chasca con Tostitos', 65.00, 100, cats['DoriChascas']),
        ('ChetoChasca', 'Chasca con Cheetos', 65.00, 100, cats['DoriChascas']),
        ('RuffleChasca', 'Chasca con Ruffles', 65.00, 100, cats['DoriChascas']),
        ('SabriChasca', 'Chasca con Sabritas', 65.00, 100, cats['DoriChascas']),
        
        # Empapelados (categoría 3)
        ('Empapelado de Champiñones', 'Empapelado con champiñones', 90.00, 50, cats['Empapelados']),
        ('Empapelado de Bisteck', 'Empapelado con bisteck', 95.00, 50, cats['Empapelados']),
        ('Empapelado de Salchicha', 'Empapelado con salchicha', 90.00, 50, cats['Empapelados']),
        ('Empapelado de Tocino', 'Empapelado con tocino', 100.00, 50, cats['Empapelados']),
        ('Empapelado 3 Quesos', 'Empapelado con tres tipos de queso', 95.00, 50, cats['Empapelados']),
        ('Empapelado de Carnes Frías', 'Empapelado con carnes frías', 95.00, 50, cats['Empapelados']),
        ('Empapelado Cubano', 'Empapelado estilo cubano', 110.00, 50, cats['Empapelados']),
        ('Empapelado de Arrachera', 'Empapelado con arrachera', 110.00, 50, cats['Empapelados']),
        ('Empapelado de Camarones', 'Empapelado con camarones', 110.00, 50, cats['Empapelados']),
        
        # Elotes (categoría 4)
        ('Elote Sencillo', 'Elote tradicional', 18.00, 100, cats['Elotes']),
        ('½ Elote', 'Media mazorca de elote', 20.00, 100, cats['Elotes']),
        ('Elote Amarillo', 'Elote con granos amarillos', 25.00, 100, cats['Elotes']),
        ('Elote Asado', 'Elote asado a las brasas', 30.00, 100, cats['Elotes']),
        ('Elote Crunch', 'Elote con topping crujiente', 40.00, 100, cats['Elotes']),
        
        # Especialidades (categoría 5)
        ('Elote Capricho', 'Elote con ingredientes especiales', 50.00, 50, cats['Especialidades']),
        ('Chorriadas Original', 'Chorriadas clásicas', 60.00, 50, cats['Especialidades']),
        ('Chorriadas Supremas', 'Chorriadas con todos los ingredientes', 75.00, 50, cats['Especialidades']),
        ('Maruchasca Clásica', 'Maruchan con chasca', 70.00, 50, cats['Especialidades']),
        ('Maruchasca Especial', 'Maruchan con chasca y extras', 85.00, 50, cats['Especialidades']),
        ('Maruchasca Premium', 'Maruchan con chasca y proteína premium', 100.00, 50, cats['Especialidades']),
        ('Sabrimaruchan', 'Combinación de sabritas con maruchan', 80.00, 50, cats['Especialidades']),
        ('Sabrimaruchan Deluxe', 'Sabrimaruchan con ingredientes premium', 140.00, 50, cats['Especialidades']),
    ]
    
    cursor.executemany(
        "INSERT INTO productos (nombre, descripcion, precio, stock, categoria_id) VALUES (?, ?, ?, ?, ?)",
        productos
    )
    print(f"   ✅ {len(productos)} productos insertados\n")
    
    # Vendedores
    print("👥 Insertando vendedores...")
    vendedores = [
        ('Administrador', 'Sistema', 'admin@michaska.com', '449-000-0000'),
        ('Juan', 'Pérez', 'juan@michaska.com', '449-111-1111'),
        ('María', 'González', 'maria@michaska.com', '449-222-2222'),
        ('Carlos', 'Ramírez', 'carlos@michaska.com', '449-333-3333'),
    ]
    
    cursor.executemany(
        "INSERT INTO vendedores (nombre, apellido, email, telefono) VALUES (?, ?, ?, ?)",
        vendedores
    )
    print(f"   ✅ {len(vendedores)} vendedores insertados\n")
    
    conn.commit()
    
    # Mostrar resumen
    print("=" * 60)
    print("✨ MENÚ MI CHAS-K CARGADO EXITOSAMENTE")
    print("=" * 60)
    
    # Mostrar productos por categoría
    cursor.execute("""
        SELECT c.nombre, COUNT(p.id) as total, 
               MIN(p.precio) as min_precio, MAX(p.precio) as max_precio
        FROM categorias c
        LEFT JOIN productos p ON c.id = p.categoria_id
        GROUP BY c.nombre
        ORDER BY c.id
    """)
    
    print("\n📊 Resumen del menú:\n")
    for cat_nombre, total, min_precio, max_precio in cursor.fetchall():
        if total > 0:
            print(f"   {cat_nombre}:")
            print(f"      • {total} productos")
            print(f"      • Precios: ${min_precio:.2f} - ${max_precio:.2f}\n")
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vendedores")
    total_vendedores = cursor.fetchone()[0]
    
    print(f"📦 Total: {total_productos} productos en {len(categorias)} categorías")
    print(f"👥 Total: {total_vendedores} vendedores\n")
    
    print("📍 Ubicación del negocio:")
    print("   Av. Valle de Los Romeros & Federico Méndez")
    print("   Villas de Ntra. Sra. de la Asunción")
    print("   20126 Aguascalientes, Ags.\n")
    
    cursor.close()
    conn.close()
    
    print("✅ ¡Listo para vender! 🚀")

if __name__ == '__main__':
    poblar_menu_michaska()

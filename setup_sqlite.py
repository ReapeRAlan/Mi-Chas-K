#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear/verificar todas las tablas necesarias en SQLite
"""
import os
import sqlite3
from datetime import datetime

def crear_tablas_completas():
    """Crea todas las tablas necesarias en SQLite"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'michaska_local.db')
    print(f"📂 Base de datos: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabla de categorías
    print("📦 Creando tabla categorías...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de productos
    print("🏷️ Creando tabla productos...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL CHECK(precio >= 0),
            stock INTEGER DEFAULT 0 CHECK(stock >= 0),
            categoria_id INTEGER,
            codigo_barras TEXT UNIQUE,
            imagen_url TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
        )
    """)
    
    # Tabla de vendedores
    print("👤 Creando tabla vendedores...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT,
            email TEXT UNIQUE,
            telefono TEXT,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de ventas
    print("💰 Creando tabla ventas...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL CHECK(total >= 0),
            vendedor_id INTEGER,
            metodo_pago TEXT DEFAULT 'Efectivo',
            notas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id) ON DELETE SET NULL
        )
    """)
    
    # Tabla de detalle de ventas
    print("📋 Creando tabla detalle_ventas...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK(cantidad > 0),
            precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0),
            subtotal REAL NOT NULL CHECK(subtotal >= 0),
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
        )
    """)
    
    # Tabla de entregas
    print("🚚 Creando tabla entregas...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            direccion TEXT NOT NULL,
            latitud REAL,
            longitud REAL,
            distancia_km REAL,
            estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'En Camino', 'Entregado', 'Cancelado')),
            fecha_entrega TIMESTAMP,
            notas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
        )
    """)
    
    # Tabla de carrito
    print("🛒 Creando tabla carrito...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de items del carrito
    print("📦 Creando tabla items_carrito...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items_carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carrito_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK(cantidad > 0),
            FOREIGN KEY (carrito_id) REFERENCES carrito(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
        )
    """)
    
    # Tabla de gastos diarios
    print("💸 Creando tabla gastos_diarios...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_diarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL CHECK(monto >= 0),
            categoria TEXT,
            notas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de cortes de caja
    print("🧮 Creando tabla cortes_caja...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cortes_caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            vendedor_id INTEGER,
            total_ventas REAL NOT NULL DEFAULT 0,
            total_gastos REAL NOT NULL DEFAULT 0,
            efectivo_inicial REAL NOT NULL DEFAULT 0,
            efectivo_final REAL NOT NULL DEFAULT 0,
            diferencia REAL NOT NULL DEFAULT 0,
            notas TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id) ON DELETE SET NULL
        )
    """)
    
    # Crear índices
    print("\n📊 Creando índices...")
    indices = [
        ("idx_productos_categoria", "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id)"),
        ("idx_productos_activo", "CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)"),
        ("idx_ventas_fecha", "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha)"),
        ("idx_ventas_vendedor", "CREATE INDEX IF NOT EXISTS idx_ventas_vendedor ON ventas(vendedor_id)"),
        ("idx_detalle_venta", "CREATE INDEX IF NOT EXISTS idx_detalle_venta ON detalle_ventas(venta_id)"),
        ("idx_detalle_producto", "CREATE INDEX IF NOT EXISTS idx_detalle_producto ON detalle_ventas(producto_id)"),
        ("idx_entregas_venta", "CREATE INDEX IF NOT EXISTS idx_entregas_venta ON entregas(venta_id)"),
        ("idx_entregas_estado", "CREATE INDEX IF NOT EXISTS idx_entregas_estado ON entregas(estado)"),
        ("idx_entregas_fecha", "CREATE INDEX IF NOT EXISTS idx_entregas_fecha ON entregas(fecha_entrega)"),
    ]
    
    for nombre, sql in indices:
        cursor.execute(sql)
        print(f"   ✅ {nombre}")
    
    # Insertar datos por defecto
    print("\n📥 Insertando datos por defecto...")
    
    # Categorías
    categorias = [
        ('Bebidas', 'Bebidas y refrescos'),
        ('Comida', 'Alimentos y comestibles'),
        ('Snacks', 'Botanas y aperitivos'),
        ('Lácteos', 'Productos lácteos'),
        ('Panadería', 'Pan y productos de panadería'),
        ('Abarrotes', 'Productos básicos'),
        ('Limpieza', 'Productos de limpieza'),
        ('Otros', 'Otros productos')
    ]
    
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)",
            categorias
        )
        print(f"   ✅ {len(categorias)} categorías insertadas")
    else:
        print("   ⚠️ Categorías ya existen")
    
    # Vendedor por defecto
    cursor.execute("SELECT COUNT(*) FROM vendedores")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO vendedores (nombre, apellido, email) VALUES (?, ?, ?)",
            ('Admin', 'Sistema', 'admin@michaska.com')
        )
        print("   ✅ Vendedor por defecto creado")
    else:
        print("   ⚠️ Vendedores ya existen")
    
    # Productos de ejemplo
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_ejemplo = [
            ('Coca Cola 600ml', 'Refresco de cola', 15.00, 50, 1),
            ('Agua Ciel 1L', 'Agua purificada', 10.00, 100, 1),
            ('Sabritas Original', 'Papas fritas', 18.00, 30, 3),
            ('Pan Blanco', 'Pan de caja blanco', 35.00, 20, 5),
            ('Leche Lala 1L', 'Leche entera', 22.00, 40, 4),
            ('Arroz 1kg', 'Arroz blanco', 28.00, 25, 6),
            ('Aceite Capullo 1L', 'Aceite vegetal', 45.00, 15, 6),
            ('Fabuloso 1L', 'Limpiador multiusos', 32.00, 20, 7),
        ]
        
        cursor.executemany(
            "INSERT INTO productos (nombre, descripcion, precio, stock, categoria_id) VALUES (?, ?, ?, ?, ?)",
            productos_ejemplo
        )
        print(f"   ✅ {len(productos_ejemplo)} productos de ejemplo insertados")
    else:
        print("   ⚠️ Productos ya existen")
    
    conn.commit()
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("✨ BASE DE DATOS SQLITE LISTA")
    print("="*60)
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = cursor.fetchall()
    
    print(f"\n📊 Tablas creadas ({len(tablas)}):")
    for tabla in tablas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {tabla[0]}: {count} registros")
    
    cursor.close()
    conn.close()
    
    print(f"\n📂 Ubicación: {db_path}")
    print("\n✅ ¡Listo para usar!")

if __name__ == '__main__':
    crear_tablas_completas()

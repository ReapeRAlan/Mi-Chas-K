#!/usr/bin/env python3
"""
Script para limpiar y reinicializar la base de datos con datos correctos
"""
import sqlite3
import os

DATABASE_PATH = "michaska.db"

def reset_database():
    """Limpia completamente la base de datos y la reinicializa"""
    # Eliminar la base de datos si existe
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print("Base de datos anterior eliminada")
    
    # Crear nueva base de datos
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        print("Creando tablas...")
        
        # Tabla de productos
        cursor.execute("""
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                categoria TEXT DEFAULT 'General',
                codigo_barras TEXT UNIQUE,
                descripcion TEXT,
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de ventas
        cursor.execute("""
            CREATE TABLE ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total REAL NOT NULL,
                metodo_pago TEXT DEFAULT 'Efectivo',
                descuento REAL DEFAULT 0,
                impuestos REAL DEFAULT 0,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vendedor TEXT,
                observaciones TEXT
            )
        """)
        
        # Tabla de detalle de ventas
        cursor.execute("""
            CREATE TABLE detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        """)
        
        # Tabla de categorías
        cursor.execute("""
            CREATE TABLE categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                activo BOOLEAN DEFAULT 1
            )
        """)
        
        # Tabla de configuración
        cursor.execute("""
            CREATE TABLE configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT,
                descripcion TEXT
            )
        """)
        
        print("Insertando configuración...")
        
        # Insertar configuración por defecto
        cursor.execute("""
            INSERT INTO configuracion (clave, valor, descripcion) VALUES
            ('nombre_negocio', 'MiChaska', 'Nombre del negocio'),
            ('direccion', '', 'Dirección del negocio'),
            ('telefono', '', 'Teléfono del negocio'),
            ('email', '', 'Email del negocio'),
            ('moneda', 'MXN', 'Moneda utilizada'),
            ('impuesto_porcentaje', '0', 'Porcentaje de impuesto'),
            ('mensaje_ticket', 'Gracias por su compra', 'Mensaje en el ticket')
        """)
        
        print("Insertando categorías...")
        
        # Insertar categorías
        categorias = [
            ('Chascas', 'Chascas en diferentes tamaños'),
            ('DoriChascas', 'Chascas con diferentes tipos de Doritos'),
            ('Empapelados', 'Empapelados con diversos ingredientes'),
            ('Elotes', 'Elotes preparados de diferentes formas'),
            ('Especialidades', 'Especialidades de la casa'),
            ('Extras', 'Porciones extras')
        ]
        
        cursor.executemany("""
            INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)
        """, categorias)
        
        print("Insertando productos del menú MiChaska...")
        
        # Insertar productos del menú MiChaska
        productos = [
            # Chascas
            ('Chasca Mini', 20.0, 100, 'Chascas', 'Chasca tamaño mini'),
            ('Chasca Chica', 25.0, 100, 'Chascas', 'Chasca tamaño chico'),
            ('Chasca Chica Plus', 35.0, 100, 'Chascas', 'Chasca chica con extras'),
            ('Chasca Mediana', 50.0, 100, 'Chascas', 'Chasca tamaño mediano'),
            ('Chasca Grande', 60.0, 100, 'Chascas', 'Chasca tamaño grande'),
            
            # DoriChascas
            ('DoriChasca', 65.0, 50, 'DoriChascas', 'Chasca con Doritos'),
            ('TostiChasca', 65.0, 50, 'DoriChascas', 'Chasca con Tostitos'),
            ('ChetoChasca', 65.0, 50, 'DoriChascas', 'Chasca con Cheetos'),
            ('RuffleChasca', 65.0, 50, 'DoriChascas', 'Chasca con Ruffles'),
            ('SabriChasca', 65.0, 50, 'DoriChascas', 'Chasca con Sabritas'),
            
            # Empapelados
            ('Champiñones', 95.0, 30, 'Empapelados', 'Empapelado de champiñones'),
            ('Bisteck', 110.0, 30, 'Empapelados', 'Empapelado de bisteck'),
            ('Salchicha', 90.0, 30, 'Empapelados', 'Empapelado de salchicha'),
            ('Tocino', 90.0, 30, 'Empapelados', 'Empapelado de tocino'),
            ('3 quesos', 95.0, 30, 'Empapelados', 'Empapelado de tres quesos'),
            ('Carnes Frías', 110.0, 30, 'Empapelados', 'Empapelado de carnes frías'),
            ('Cubano', 110.0, 30, 'Empapelados', 'Empapelado estilo cubano'),
            ('Arrachera', 110.0, 30, 'Empapelados', 'Empapelado de arrachera'),
            ('Camarones', 110.0, 30, 'Empapelados', 'Empapelado de camarones'),
            
            # Elotes
            ('Elote sencillo', 30.0, 50, 'Elotes', 'Elote sencillo'),
            ('½ Elote', 18.0, 50, 'Elotes', 'Media mazorca de elote'),
            ('Elote Amarillo', 38.0, 50, 'Elotes', 'Elote amarillo preparado'),
            ('Elote Asado', 35.0, 50, 'Elotes', 'Elote asado'),
            ('Elote Crunch', 40.0, 50, 'Elotes', 'Elote con extra crunch'),
            
            # Especialidades
            ('Elote Capricho', 50.0, 25, 'Especialidades', 'Elote preparado especial'),
            ('Chorriada Chica', 65.0, 25, 'Especialidades', 'Chorriada tamaño chico'),
            ('Chorriada Mediana', 85.0, 25, 'Especialidades', 'Chorriada tamaño mediano'),
            ('Chorriada Grande', 130.0, 25, 'Especialidades', 'Chorriada tamaño grande'),
            ('Maruchasca', 70.0, 25, 'Especialidades', 'Maruchan especial'),
            ('Maruchasca Enpolvada', 90.0, 25, 'Especialidades', 'Maruchan con polvo especial'),
            ('Maruchasca Especial', 110.0, 25, 'Especialidades', 'Maruchan preparación especial'),
            ('Maruchasca Suprema', 140.0, 25, 'Especialidades', 'Maruchan preparación suprema'),
            ('Sabrimaruchan', 95.0, 25, 'Especialidades', 'Maruchan con sabritas'),
            
            # Extras
            ('Porción extra 30', 30.0, 100, 'Extras', 'Porción extra de 30 pesos'),
            ('Porción extra 15', 15.0, 100, 'Extras', 'Porción extra de 15 pesos'),
            ('Porción extra 10', 10.0, 100, 'Extras', 'Porción extra de 10 pesos')
        ]
        
        cursor.executemany("""
            INSERT INTO productos (nombre, precio, stock, categoria, descripcion) 
            VALUES (?, ?, ?, ?, ?)
        """, productos)
        
        conn.commit()
        
        # Verificar inserción
        cursor.execute("SELECT COUNT(*) FROM productos")
        productos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categorias")
        categorias_count = cursor.fetchone()[0]
        
        print(f"✅ Base de datos reinicializada correctamente:")
        print(f"   - Productos: {productos_count}")
        print(f"   - Categorías: {categorias_count}")
        print(f"   - Configuración: 7 valores")

if __name__ == "__main__":
    reset_database()

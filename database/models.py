"""
Modelos de datos para el sistema de facturación - PostgreSQL
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from database.connection import execute_query, execute_update

def safe_float(value) -> float:
    """Convierte de forma segura cualquier valor numérico a float"""
    if isinstance(value, Decimal):
        return float(value)
    return float(value) if value is not None else 0.0

@dataclass
class Producto:
    id: Optional[int] = None
    nombre: str = ""
    precio: float = 0.0
    stock: int = 0
    categoria: str = "General"
    codigo_barras: Optional[str] = None
    descripcion: str = ""
    activo: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_modificacion: Optional[datetime] = None

    @classmethod
    def get_all(cls, activos_solamente: bool = True) -> List['Producto']:
        """Obtiene todos los productos"""
        query = "SELECT * FROM productos"
        if activos_solamente:
            query += " WHERE activo = TRUE"
        query += " ORDER BY categoria, nombre"
        
        rows = execute_query(query)
        return [cls(**dict(row)) for row in rows]
    
    @classmethod
    def get_by_id(cls, producto_id: int) -> Optional['Producto']:
        """Obtiene un producto por ID"""
        rows = execute_query("SELECT * FROM productos WHERE id = %s", (producto_id,))
        if rows:
            return cls(**dict(rows[0]))
        return None
    
    @classmethod
    def get_by_categoria(cls, categoria: str) -> List['Producto']:
        """Obtiene productos por categoría"""
        rows = execute_query(
            "SELECT * FROM productos WHERE categoria = %s AND activo = TRUE ORDER BY nombre", 
            (categoria,)
        )
        return [cls(**dict(row)) for row in rows]
    
    def save(self) -> int:
        """Guarda o actualiza el producto"""
        if self.id is None:
            # Insertar nuevo producto
            query = """
                INSERT INTO productos (nombre, precio, stock, categoria, codigo_barras, descripcion, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (self.nombre, self.precio, self.stock, self.categoria, 
                     self.codigo_barras, self.descripcion, self.activo)
            self.id = execute_update(query, params)
        else:
            # Actualizar producto existente
            query = """
                UPDATE productos 
                SET nombre = %s, precio = %s, stock = %s, categoria = %s, 
                    codigo_barras = %s, descripcion = %s, activo = %s,
                    fecha_modificacion = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            params = (self.nombre, self.precio, self.stock, self.categoria,
                     self.codigo_barras, self.descripcion, self.activo, self.id)
            execute_update(query, params)
        return self.id or 0
    
    def actualizar_stock(self, nueva_cantidad: int):
        """Actualiza el stock del producto"""
        execute_update("UPDATE productos SET stock = %s WHERE id = %s", (nueva_cantidad, self.id))
        self.stock = nueva_cantidad

@dataclass
class Venta:
    id: Optional[int] = None
    total: float = 0.0
    metodo_pago: str = "Efectivo"
    descuento: float = 0.0
    impuestos: float = 0.0
    fecha: Optional[datetime] = None
    vendedor: str = ""
    observaciones: str = ""

    @classmethod
    def get_all(cls) -> List['Venta']:
        """Obtiene todas las ventas"""
        rows = execute_query("SELECT * FROM ventas ORDER BY fecha DESC")
        return [cls(**dict(row)) for row in rows]
    
    @classmethod
    def get_by_fecha(cls, fecha_inicio: str, fecha_fin: str) -> List['Venta']:
        """Obtiene ventas por rango de fechas"""
        query = "SELECT * FROM ventas WHERE DATE(fecha) BETWEEN %s AND %s ORDER BY fecha DESC"
        rows = execute_query(query, (fecha_inicio, fecha_fin))
        return [cls(**dict(row)) for row in rows]
    
    @classmethod
    def get_ventas_hoy(cls) -> List['Venta']:
        """Obtiene las ventas del día actual"""
        query = "SELECT * FROM ventas WHERE DATE(fecha) = CURRENT_DATE ORDER BY fecha DESC"
        rows = execute_query(query)
        return [cls(**dict(row)) for row in rows]
    
    def save(self) -> int:
        """Guarda la venta"""
        if self.fecha is None:
            self.fecha = datetime.now()
            
        query = """
            INSERT INTO ventas (total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (self.total, self.metodo_pago, self.descuento, 
                 self.impuestos, self.fecha, self.vendedor, self.observaciones)
        self.id = execute_update(query, params)
        return self.id or 0
        return self.id

@dataclass
class DetalleVenta:
    id: Optional[int] = None
    venta_id: int = 0
    producto_id: int = 0
    cantidad: int = 0
    precio_unitario: float = 0.0
    subtotal: float = 0.0

    @classmethod
    def get_by_venta(cls, venta_id: int) -> List['DetalleVenta']:
        """Obtiene el detalle de una venta específica"""
        query = """
            SELECT id, venta_id, producto_id, cantidad, precio_unitario, subtotal
            FROM detalle_ventas 
            WHERE venta_id = %s
        """
        rows = execute_query(query, (venta_id,))
        return [cls(**dict(row)) for row in rows]
    
    def save(self) -> int:
        """Guarda el detalle de venta"""
        query = """
            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (self.venta_id, self.producto_id, self.cantidad, 
                 self.precio_unitario, self.subtotal)
        self.id = execute_update(query, params)
        return self.id or 0

@dataclass
class Categoria:
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    activo: bool = True

    @classmethod
    def get_all(cls, activas_solamente: bool = True) -> List['Categoria']:
        """Obtiene todas las categorías"""
        # Para PostgreSQL, usar categorías distintas de productos
        query = "SELECT DISTINCT categoria as nombre FROM productos WHERE activo = TRUE ORDER BY categoria"
        rows = execute_query(query)
        return [cls(nombre=row['nombre']) for row in rows]

@dataclass  
class ItemCarrito:
    producto: Producto
    cantidad: int = 1
    
    @property
    def subtotal(self) -> float:
        """Calcula el subtotal del item"""
        return safe_float(self.producto.precio) * self.cantidad

class Carrito:
    def __init__(self):
        self.items: List[ItemCarrito] = []
    
    def agregar_producto(self, producto: Producto, cantidad: int = 1):
        """Agrega un producto al carrito"""
        # Buscar si el producto ya está en el carrito
        for item in self.items:
            if item.producto.id == producto.id:
                item.cantidad += cantidad
                return
        
        # Si no está, agregar nuevo item
        self.items.append(ItemCarrito(producto=producto, cantidad=cantidad))
    
    def eliminar_producto(self, producto_id: int):
        """Elimina un producto del carrito"""
        self.items = [item for item in self.items if item.producto.id != producto_id]
    
    def actualizar_cantidad(self, producto_id: int, nueva_cantidad: int):
        """Actualiza la cantidad de un producto en el carrito"""
        for item in self.items:
            if item.producto.id == producto_id:
                if nueva_cantidad <= 0:
                    self.eliminar_producto(producto_id)
                else:
                    item.cantidad = nueva_cantidad
                break
    
    def limpiar(self):
        """Limpia el carrito"""
        self.items = []
    
    @property
    def total(self) -> float:
        """Calcula el total del carrito"""
        return safe_float(sum(item.subtotal for item in self.items))
    
    @property
    def cantidad_items(self) -> int:
        """Retorna la cantidad total de items en el carrito"""
        return sum(item.cantidad for item in self.items)
    
    def procesar_venta(self, metodo_pago: str = "Efectivo", vendedor: str = "", observaciones: str = "") -> Optional[Venta]:
        """Procesa la venta del carrito actual"""
        if not self.items:
            return None
        
        # Crear la venta
        venta = Venta(
            total=self.total,
            metodo_pago=metodo_pago,
            vendedor=vendedor,
            observaciones=observaciones
        )
        venta_id = venta.save()
        venta.id = venta_id
        
        # Guardar detalle de venta y actualizar stock
        for item in self.items:
            detalle = DetalleVenta(
                venta_id=venta_id,
                producto_id=item.producto.id or 0,
                cantidad=item.cantidad,
                precio_unitario=item.producto.precio,
                subtotal=item.subtotal
            )
            detalle.save()
            
            # Actualizar stock del producto
            nuevo_stock = item.producto.stock - item.cantidad
            item.producto.actualizar_stock(nuevo_stock)
        
        # Limpiar carrito después de procesar
        self.limpiar()
        
        return venta

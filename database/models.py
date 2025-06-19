"""
Modelos de datos para el sistema de facturación - PostgreSQL
OPTIMIZADO - imports al inicio para evitar importaciones repetidas
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import logging
from database.connection import execute_query, execute_update
from utils.timezone_utils import get_mexico_datetime  # Import al inicio

# Configurar logging
logger = logging.getLogger(__name__)

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
        productos = []
        for row in rows:
            data = dict(row)
            data['precio'] = safe_float(data.get('precio', 0))
            productos.append(cls(**data))
        return productos
    
    @classmethod
    def get_by_id(cls, producto_id: int) -> Optional['Producto']:
        """Obtiene un producto por ID"""
        rows = execute_query("SELECT * FROM productos WHERE id = %s", (producto_id,))
        if rows:
            data = dict(rows[0])
            data['precio'] = safe_float(data.get('precio', 0))
            return cls(**data)
        return None
    
    @classmethod
    def get_by_categoria(cls, categoria: str) -> List['Producto']:
        """Obtiene productos por categoría"""
        rows = execute_query(
            "SELECT * FROM productos WHERE categoria = %s AND activo = TRUE ORDER BY nombre", 
            (categoria,)
        )
        productos = []
        for row in rows:
            data = dict(row)
            data['precio'] = safe_float(data.get('precio', 0))
            productos.append(cls(**data))
        return productos
    
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
    estado: str = "Completada"

    @classmethod
    def get_all(cls) -> List['Venta']:
        """Obtiene todas las ventas"""
        rows = execute_query("SELECT * FROM ventas ORDER BY fecha DESC")
        ventas = []
        for row in rows:
            data = dict(row)
            data['total'] = safe_float(data.get('total', 0))
            data['descuento'] = safe_float(data.get('descuento', 0))
            data['impuestos'] = safe_float(data.get('impuestos', 0))
            # Manejar campo estado de forma segura
            if 'estado' not in data:
                data['estado'] = 'Completada'
            ventas.append(cls(**data))
        return ventas
    
    @classmethod
    def get_by_fecha(cls, fecha_inicio: str, fecha_fin: str) -> List['Venta']:
        """Obtiene ventas por rango de fechas"""
        query = "SELECT * FROM ventas WHERE DATE(fecha) BETWEEN %s AND %s ORDER BY fecha DESC"
        rows = execute_query(query, (fecha_inicio, fecha_fin))
        ventas = []
        for row in rows:
            data = dict(row)
            data['total'] = safe_float(data.get('total', 0))
            data['descuento'] = safe_float(data.get('descuento', 0))
            data['impuestos'] = safe_float(data.get('impuestos', 0))
            # Manejar campo estado de forma segura
            if 'estado' not in data:
                data['estado'] = 'Completada'
            ventas.append(cls(**data))
        return ventas
    
    @classmethod
    def get_ventas_hoy(cls) -> List['Venta']:
        """Obtiene las ventas del día actual"""
        query = "SELECT * FROM ventas WHERE DATE(fecha) = CURRENT_DATE ORDER BY fecha DESC"
        rows = execute_query(query)
        ventas = []
        for row in rows:
            data = dict(row)
            data['total'] = safe_float(data.get('total', 0))
            data['descuento'] = safe_float(data.get('descuento', 0))
            data['impuestos'] = safe_float(data.get('impuestos', 0))
            # Manejar campo estado de forma segura
            if 'estado' not in data:
                data['estado'] = 'Completada'
            ventas.append(cls(**data))
        return ventas
    
    def save(self) -> int:
        """Guarda la venta - optimizado para evitar múltiples llamadas de timezone"""
        try:
            if self.fecha is None:
                self.fecha = get_mexico_datetime()
                logger.info(f"⚠️ Fecha era None, asignada: {self.fecha}")
            else:
                logger.info(f"✅ Fecha ya establecida: {self.fecha}")
                
            query = """
                INSERT INTO ventas (total, metodo_pago, descuento, impuestos, fecha, vendedor, observaciones, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (self.total, self.metodo_pago, self.descuento, 
                     self.impuestos, self.fecha, self.vendedor, self.observaciones, self.estado)
            
            logger.info(f"💾 Guardando venta con parámetros: Total=${self.total}, Fecha={self.fecha}")
            
            result_id = execute_update(query, params)
            self.id = result_id
            
            logger.info(f"✅ Venta #{result_id} guardada exitosamente - Total: ${self.total} - Fecha: {self.fecha}")
            return result_id or 0
            
        except Exception as e:
            logger.error(f"❌ Error al guardar venta: {e}")
            raise

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
    fecha_creacion: Optional[datetime] = None

    @classmethod
    def get_all(cls, activas_solamente: bool = True) -> List['Categoria']:
        """Obtiene todas las categorías"""
        try:
            if activas_solamente:
                query = "SELECT * FROM categorias WHERE activo = TRUE ORDER BY nombre"
            else:
                query = "SELECT * FROM categorias ORDER BY nombre"
            
            rows = execute_query(query)
            categorias = []
            for row in rows:
                data = dict(row)
                categorias.append(cls(**data))
            return categorias
        except Exception as e:
            logger.error(f"Error al obtener categorías: {e}")
            return []
    
    @classmethod  
    def get_nombres_categoria(cls) -> List[str]:
        """Obtiene solo los nombres de categorías activas para productos"""
        try:
            query = "SELECT nombre FROM categorias WHERE activo = TRUE ORDER BY nombre"
            rows = execute_query(query)
            nombres = [row['nombre'] for row in rows]
            
            # Si no hay categorías en BD, devolver categorías por defecto
            if not nombres:
                nombres = ['Chascas', 'DoriChascas', 'Empapelados', 'Elotes', 'Especialidades', 'Extras']
                logger.warning("No se encontraron categorías en BD, usando categorías por defecto")
            
            return nombres
        except Exception as e:
            logger.error(f"Error al obtener nombres de categorías: {e}")
            # Devolver categorías por defecto en caso de error
            return ['Chascas', 'DoriChascas', 'Empapelados', 'Elotes', 'Especialidades', 'Extras']
    
    @classmethod
    def get_by_nombre(cls, nombre: str) -> Optional['Categoria']:
        """Obtiene una categoría por nombre"""
        try:
            query = "SELECT * FROM categorias WHERE nombre = %s"
            rows = execute_query(query, (nombre,))
            if rows:
                data = dict(rows[0])
                return cls(**data)
            return None
        except Exception as e:
            logger.error(f"Error al obtener categoría por nombre: {e}")
            return None
    
    @classmethod
    def existe_categoria(cls, nombre: str) -> bool:
        """Verifica si existe una categoría con el nombre dado"""
        try:
            query = "SELECT COUNT(*) as count FROM categorias WHERE nombre = %s"
            rows = execute_query(query, (nombre,))
            return rows[0]['count'] > 0 if rows else False
        except Exception as e:
            logger.error(f"Error al verificar existencia de categoría: {e}")
            return False
    
    @classmethod
    def crear_categorias_default(cls):
        """Crea las categorías por defecto si no existen"""
        try:
            categorias_default = [
                ('Chascas', 'Nuestros productos principales: chascas tradicionales'),
                ('DoriChascas', 'Chascas especiales con frituras populares'),
                ('Empapelados', 'Tortillas rellenas y empapeladas al gusto'),
                ('Elotes', 'Elotes preparados en diferentes estilos'),
                ('Especialidades', 'Productos especiales y combinaciones únicas'),
                ('Extras', 'Porciones adicionales y complementos')
            ]
            
            for nombre, descripcion in categorias_default:
                if not cls.existe_categoria(nombre):
                    categoria = cls(nombre=nombre, descripcion=descripcion)
                    categoria.save()
                    logger.info(f"Categoría '{nombre}' creada exitosamente")
        
        except Exception as e:
            logger.error(f"Error al crear categorías por defecto: {e}")
    
    def save(self) -> int:
        """Guarda o actualiza la categoría"""
        try:
            if self.fecha_creacion is None:
                from utils.timezone_utils import get_mexico_datetime
                self.fecha_creacion = get_mexico_datetime()
                
            if self.id is None:
                # Insertar nueva categoría
                query = """
                    INSERT INTO categorias (nombre, descripcion, activo, fecha_creacion)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                params = (self.nombre, self.descripcion, self.activo, self.fecha_creacion)
                self.id = execute_update(query, params)
            else:
                # Actualizar categoría existente
                query = """
                    UPDATE categorias 
                    SET nombre = %s, descripcion = %s, activo = %s
                    WHERE id = %s
                """
                params = (self.nombre, self.descripcion, self.activo, self.id)
                execute_update(query, params)
            return self.id or 0
        except Exception as e:
            logger.error(f"Error al guardar categoría: {e}")
            return 0

    def delete(self) -> bool:
        """Desactiva la categoría (soft delete)"""
        try:
            query = "UPDATE categorias SET activo = FALSE WHERE id = %s"
            execute_update(query, (self.id,))
            self.activo = False
            return True
        except Exception as e:
            logger.error(f"Error al desactivar categoría: {e}")
            return False

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
    
    def procesar_venta(self, metodo_pago: str = "Efectivo", vendedor: str = "", observaciones: str = "", fecha_personalizada=None) -> Optional[Venta]:
        """Procesa la venta del carrito actual con fecha personalizable"""
        if not self.items:
            return None
        
        # Usar fecha personalizada o fecha actual de México
        if fecha_personalizada:
            # Si se proporciona solo una fecha (date), convertir a datetime
            if hasattr(fecha_personalizada, 'date') and not hasattr(fecha_personalizada, 'hour'):
                from datetime import datetime, time
                fecha_venta = datetime.combine(fecha_personalizada, time())
            else:
                fecha_venta = fecha_personalizada
        else:
            fecha_venta = get_mexico_datetime()
        
        logger.info(f"🕐 Fecha para venta: {fecha_venta}")
        
        # Crear la venta CON fecha explícita
        venta = Venta(
            total=self.total,
            metodo_pago=metodo_pago,
            vendedor=vendedor,
            observaciones=observaciones,
            fecha=fecha_venta,  # ✅ Fecha explícita (personalizada o actual)
            estado="Completada"  # ✅ Estado por defecto
        )
        
        logger.info(f"🛒 Venta creada con fecha: {venta.fecha}")
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

@dataclass
class GastoDiario:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD en zona horaria México
    concepto: str = ""
    monto: float = 0.0
    categoria: str = "Operación"  # Operación, Compras, Servicios, Otros
    descripcion: str = ""
    comprobante: str = ""  # Número de comprobante/factura
    vendedor: str = ""  # Quien realizó el gasto
    fecha_registro: Optional[datetime] = None

    @classmethod
    def get_by_fecha(cls, fecha: str) -> List['GastoDiario']:
        """Obtiene todos los gastos de una fecha específica"""
        query = "SELECT * FROM gastos_diarios WHERE fecha = %s ORDER BY fecha_registro DESC"
        rows = execute_query(query, (fecha,))
        gastos = []
        for row in rows:
            data = dict(row)
            data['monto'] = safe_float(data.get('monto', 0))
            gastos.append(cls(**data))
        return gastos

    @classmethod
    def get_total_by_fecha(cls, fecha: str) -> float:
        """Obtiene el total de gastos de una fecha"""
        query = "SELECT COALESCE(SUM(monto), 0) as total FROM gastos_diarios WHERE fecha = %s"
        rows = execute_query(query, (fecha,))
        return safe_float(rows[0]['total']) if rows else 0.0

    @classmethod
    def get_by_categoria(cls, fecha: str, categoria: str) -> List['GastoDiario']:
        """Obtiene gastos por fecha y categoría"""
        query = "SELECT * FROM gastos_diarios WHERE fecha = %s AND categoria = %s ORDER BY fecha_registro DESC"
        rows = execute_query(query, (fecha, categoria))
        gastos = []
        for row in rows:
            data = dict(row)
            data['monto'] = safe_float(data.get('monto', 0))
            gastos.append(cls(**data))
        return gastos

    @classmethod
    def get_by_id(cls, gasto_id: int) -> Optional['GastoDiario']:
        """Obtiene un gasto específico por ID"""
        query = "SELECT * FROM gastos_diarios WHERE id = %s"
        rows = execute_query(query, (gasto_id,))
        if rows:
            data = dict(rows[0])
            data['monto'] = safe_float(data.get('monto', 0))
            return cls(**data)
        return None

    def delete(self) -> bool:
        """Elimina el gasto de la base de datos"""
        if self.id is None:
            return False
        
        try:
            query = "DELETE FROM gastos_diarios WHERE id = %s"
            execute_update(query, (self.id,))
            return True
        except Exception:
            return False

    def save(self) -> int:
        """Guarda el gasto diario"""
        if self.fecha_registro is None:
            from utils.timezone_utils import get_mexico_datetime
            self.fecha_registro = get_mexico_datetime()
            
        if self.id is None:
            query = """
                INSERT INTO gastos_diarios (fecha, concepto, monto, categoria, descripcion, comprobante, vendedor, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (self.fecha, self.concepto, self.monto, self.categoria, 
                     self.descripcion, self.comprobante, self.vendedor, self.fecha_registro)
            self.id = execute_update(query, params)
        else:
            query = """
                UPDATE gastos_diarios 
                SET concepto = %s, monto = %s, categoria = %s, descripcion = %s, 
                    comprobante = %s, vendedor = %s
                WHERE id = %s
            """
            params = (self.concepto, self.monto, self.categoria, self.descripcion,
                     self.comprobante, self.vendedor, self.id)
            execute_update(query, params)
        return self.id or 0

@dataclass
class CorteCaja:
    id: Optional[int] = None
    fecha: str = ""  # YYYY-MM-DD en zona horaria México
    dinero_inicial: float = 0.0  # Dinero con el que se inició el día
    dinero_final: float = 0.0    # Dinero al final del día (por conteo físico)
    ventas_efectivo: float = 0.0 # Total de ventas en efectivo del día
    ventas_tarjeta: float = 0.0  # Total de ventas con tarjeta del día
    total_gastos: float = 0.0    # Total de gastos del día
    diferencia: float = 0.0      # Diferencia entre esperado y real
    observaciones: str = ""
    vendedor: str = ""           # Quien realizó el corte
    fecha_registro: Optional[datetime] = None

    @classmethod
    def get_by_fecha(cls, fecha: str) -> Optional['CorteCaja']:
        """Obtiene el corte de caja de una fecha específica"""
        query = "SELECT * FROM cortes_caja WHERE fecha = %s"
        rows = execute_query(query, (fecha,))
        if rows:
            data = dict(rows[0])
            # Convertir todos los campos monetarios
            for field in ['dinero_inicial', 'dinero_final', 'ventas_efectivo', 
                         'ventas_tarjeta', 'total_gastos', 'diferencia']:
                data[field] = safe_float(data.get(field, 0))
            return cls(**data)
        return None

    @classmethod
    def existe_corte(cls, fecha: str) -> bool:
        """Verifica si ya existe un corte para la fecha dada"""
        query = "SELECT COUNT(*) as count FROM cortes_caja WHERE fecha = %s"
        rows = execute_query(query, (fecha,))
        return rows[0]['count'] > 0 if rows else False

    def calcular_diferencia(self):
        """Calcula la diferencia entre el dinero esperado y el real"""
        dinero_esperado = (self.dinero_inicial + self.ventas_efectivo - self.total_gastos)
        self.diferencia = self.dinero_final - dinero_esperado

    def save(self) -> int:
        """Guarda el corte de caja"""
        if self.fecha_registro is None:
            from utils.timezone_utils import get_mexico_datetime
            self.fecha_registro = get_mexico_datetime()
        
        # Calcular diferencia antes de guardar
        self.calcular_diferencia()
            
        if self.id is None:
            query = """
                INSERT INTO cortes_caja (fecha, dinero_inicial, dinero_final, ventas_efectivo, 
                                       ventas_tarjeta, total_gastos, diferencia, observaciones, 
                                       vendedor, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (self.fecha, self.dinero_inicial, self.dinero_final, self.ventas_efectivo,
                     self.ventas_tarjeta, self.total_gastos, self.diferencia, self.observaciones,
                     self.vendedor, self.fecha_registro)
            self.id = execute_update(query, params)
        else:
            query = """
                UPDATE cortes_caja 
                SET dinero_inicial = %s, dinero_final = %s, ventas_efectivo = %s, 
                    ventas_tarjeta = %s, total_gastos = %s, diferencia = %s, 
                    observaciones = %s, vendedor = %s
                WHERE id = %s
            """
            params = (self.dinero_inicial, self.dinero_final, self.ventas_efectivo,
                     self.ventas_tarjeta, self.total_gastos, self.diferencia,
                     self.observaciones, self.vendedor, self.id)
            execute_update(query, params)
        return self.id or 0

@dataclass
class Vendedor:
    id: Optional[int] = None
    nombre: str = ""
    activo: bool = True
    fecha_registro: Optional[datetime] = None

    @classmethod
    def get_all_activos(cls) -> List['Vendedor']:
        """Obtiene todos los vendedores activos"""
        query = "SELECT * FROM vendedores WHERE activo = TRUE ORDER BY nombre"
        rows = execute_query(query)
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_nombres_activos(cls) -> List[str]:
        """Obtiene solo los nombres de vendedores activos"""
        query = "SELECT nombre FROM vendedores WHERE activo = TRUE ORDER BY nombre"
        rows = execute_query(query)
        return [row['nombre'] for row in rows]

    def save(self) -> int:
        """Guarda el vendedor"""
        if self.fecha_registro is None:
            from utils.timezone_utils import get_mexico_datetime
            self.fecha_registro = get_mexico_datetime()
            
        if self.id is None:
            query = """
                INSERT INTO vendedores (nombre, activo, fecha_registro)
                VALUES (%s, %s, %s)
                RETURNING id
            """
            params = (self.nombre, self.activo, self.fecha_registro)
            self.id = execute_update(query, params)
        else:
            query = """
                UPDATE vendedores 
                SET nombre = %s, activo = %s
                WHERE id = %s
            """
            params = (self.nombre, self.activo, self.id)
            execute_update(query, params)
        return self.id or 0

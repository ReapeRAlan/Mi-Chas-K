from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Categoria(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    emoji = Column(String(10))
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categories.id"))
    activo = Column(Integer, default=1)
    categoria = relationship("Categoria", back_populates="productos")

class Pedido(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, nullable=False)
    cliente = Column(String, default="Cliente")
    items = relationship("ItemPedido", back_populates="pedido")

class ItemPedido(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("orders.id"))
    producto_id = Column(Integer, ForeignKey("products.id"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    pedido = relationship("Pedido", back_populates="items")

import streamlit as st
from database import SessionLocal, engine
from models import Base, Categoria, Producto, Pedido, ItemPedido
from sqlalchemy.orm import Session
from datetime import datetime

# Botón para inicializar la base de datos
if st.sidebar.button("Inicializar Base de Datos"):
    Base.metadata.create_all(bind=engine)

st.sidebar.title("Mi-Chas-K POS")
page = st.sidebar.radio("Ir a", ["Tienda", "Carrito", "Admin"])

if "cart" not in st.session_state:
    st.session_state["cart"] = []

session = SessionLocal()

if page == "Tienda":
    categorias = session.query(Categoria).all()
    for cat in categorias:
        st.header(f"{cat.emoji} {cat.nombre}")
        productos = session.query(Producto).filter_by(categoria_id=cat.id, activo=1).all()
        for prod in productos:
            if st.button(f"Agregar {prod.nombre} - ${prod.precio}", key=f"add_{prod.id}"):
                added = False
                for item in st.session_state["cart"]:
                    if item["id"] == prod.id:
                        item["cantidad"] += 1
                        added = True
                        break
                if not added:
                    st.session_state["cart"].append({
                        "id": prod.id,
                        "nombre": prod.nombre,
                        "precio": prod.precio,
                        "cantidad": 1
                    })
                st.success(f"Agregado {prod.nombre}")

elif page == "Carrito":
    cart = st.session_state["cart"]
    if cart:
        total = 0.0
        for item in cart:
            subtotal = item["precio"] * item["cantidad"]
            total += subtotal
            st.write(f"{item['nombre']} x{item['cantidad']} - ${subtotal}")
        st.write(f"**Total: ${total}**")
        if st.button("Procesar Pedido"):
            pedido = Pedido(fecha=datetime.utcnow(), total=total)
            session.add(pedido)
            session.commit()
            for item in cart:
                order_item = ItemPedido(
                    pedido_id=pedido.id,
                    producto_id=item["id"],
                    cantidad=item["cantidad"],
                    precio_unitario=item["precio"],
                )
                session.add(order_item)
            session.commit()
            st.session_state["cart"] = []
            st.success(f"Pedido #{pedido.id} guardado")
    else:
        st.info("Carrito vacío")

elif page == "Admin":
    st.header("Últimos Pedidos")
    pedidos = session.query(Pedido).order_by(Pedido.fecha.desc()).limit(50).all()
    data = []
    for p in pedidos:
        data.append({
            "ID": p.id,
            "Fecha": p.fecha.strftime("%Y-%m-%d %H:%M"),
            "Cliente": getattr(p, "cliente", ""),  # Ajusta si 'cliente' no existe
            "Total": p.total,
            "Items": len(p.items) if hasattr(p, "items") else 0,
        })
    st.table(data)

session.close()

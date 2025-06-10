from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import Categoria, Producto


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if not session.query(Categoria).first():
        bebidas = Categoria(nombre="Bebidas", emoji="🥤")
        comidas = Categoria(nombre="Comidas", emoji="🍔")
        session.add_all([bebidas, comidas])
        session.commit()
        productos = [
            Producto(nombre="Refresco", precio=1.5, categoria=bebidas),
            Producto(nombre="Hamburguesa", precio=5.0, categoria=comidas),
        ]
        session.add_all(productos)
        session.commit()
    session.close()


if __name__ == "__main__":
    init_db()

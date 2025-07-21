# database.py

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy import DateTime
from datetime import datetime, timedelta
from sqlalchemy import Date
from sqlalchemy import Time

# Ruta de la base de datos
DATABASE_URL = "sqlite:///./data/crm.db"

# Conexión al motor SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base de modelos
Base = declarative_base()

# Modelo de Cliente en BD
class ClienteDB(Base):
    __tablename__ = "clientes"
    telefono = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    compras = Column(Integer, default=0)
    puntos = Column(Integer, default=0)
    feedback_promedio = Column(Float, default=0.0)
    categoria = Column(String, default="NUEVO")
    ultima_compra = Column(DateTime, nullable=True)
    cancelaciones = Column(Integer, default=0)


# Modelo de Producto
class ProductoDB(Base):
    __tablename__ = "productos"
    nombre = Column(String, primary_key=True, index=True)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    caducidad = Column(DateTime, nullable=True)
    costo_unitario = Column(Float, default=0.0)  # ← AGREGA ESTA LÍNEA

# Modelo de Pedido

class PedidoDB(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String, ForeignKey("clientes.telefono"))
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    detalle = Column(JSON)
    total = Column(Float)
    estado = Column(String, default="completo")  # ya existente
    repartidor = Column(String, nullable=True)   # nuevo
    hora_salida = Column(DateTime, nullable=True)  # nuevo
    hora_entrega_estim = Column(DateTime, nullable=True)  # nuevo


class MetricasDB(Base):
    __tablename__ = "metricas"
    fecha = Column(Date, primary_key=True)
    ingresos_totales = Column(Float, default=0)
    margen_bruto_total = Column(Float, default=0)
    pedidos = Column(Integer, default=0)

class CancelacionDB(Base):
    __tablename__ = "cancelaciones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String)
    fecha = Column(DateTime, default=datetime.now)
    motivo = Column(String)

# Crear las tablas (una vez al inicio)
def crear_tablas():
    Base.metadata.create_all(bind=engine)

    # Cargar productos iniciales si no existen
    db = SessionLocal()
    productos_iniciales = [
        {"nombre": "pollo", "precio": 25, "stock": 10, "costo_unitario": 16},
        {"nombre": "gaseosa", "precio": 5, "stock": 15, "costo_unitario": 2},
        {"nombre": "ensalada", "precio": 6, "stock": 8, "costo_unitario": 3},
        {"nombre": "papas", "precio": 4, "stock": 12, "costo_unitario": 2},
    ]
    for p in productos_iniciales:
        existente = db.query(ProductoDB).filter_by(nombre=p["nombre"]).first()
        if not existente:
            nuevo = ProductoDB(**p)
            db.add(nuevo)
    db.commit()
    db.close()

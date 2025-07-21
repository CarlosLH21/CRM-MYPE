# schema.py

from pydantic import BaseModel

class PedidoInput(BaseModel):
    texto: str
    telefono: str

class FeedbackInput(BaseModel):
    telefono: str
    calificacion: int
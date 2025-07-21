# models.py
class Cliente:
    def __init__(self, telefono, nombre=None):
        self.nombre = nombre or f"Cliente-{telefono[-4:]}"
        self.telefono = telefono
        self.compras = 0
        self.puntos = 0
        self.feedbacks = []

    def registrar_compra(self, puntos):
        self.compras += 1
        self.puntos += puntos

    def registrar_feedback(self, calificacion):
        self.feedbacks.append(calificacion)

    def obtener_promedio_feedback(self):
        if not self.feedbacks:
            return 0
        return round(sum(self.feedbacks) / len(self.feedbacks), 2)




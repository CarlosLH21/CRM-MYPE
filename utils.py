# utils.py

import re

def extraer_productos(texto):
    """
    Extrae los productos válidos del texto usando expresiones regulares.
    Devuelve un diccionario con cantidades por producto.
    """
    productos = re.findall(r"(pollo|gaseosa|ensalada|papas)", texto.lower())
    resultado = {}
    for prod in productos:
        resultado[prod] = resultado.get(prod, 0) + 1
    return resultado

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crud import procesar_pedido, registrar_feedback
from schema import PedidoInput, FeedbackInput
from fastapi import Depends
from database import SessionLocal
from reporte_utils import calcular_metricas_diarias, generar_grafico_ingresos, generar_pdf_reporte
import traceback
# Crear la instancia de la aplicación FastAPI
app = FastAPI(title="CRM para Pappy’s Foods - MYPE")

# Endpoint para procesar pedidos
@app.post("/pedido/")
def nuevo_pedido(pedido: PedidoInput):
    try:
        resultado = procesar_pedido(pedido.texto, pedido.telefono)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint para registrar feedback del cliente
@app.post("/feedback/")
def feedback(feedback: FeedbackInput):
    try:
        mensaje = registrar_feedback(feedback.telefono, feedback.calificacion)
        return {"mensaje": mensaje}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from database import crear_tablas
crear_tablas()

@app.get("/reporte/preview", response_model=dict)
def vista_previa_reporte() -> dict:
    db = SessionLocal()
    try:
        return calcular_metricas_diarias(db)
    finally:
        db.close()

@app.get("/reporte/grafico")
def generar_grafico():
    db = SessionLocal()
    try:
        ruta = generar_grafico_ingresos(db)
        if not ruta:
            return {"mensaje": "No hay métricas para graficar."}
        return {"mensaje": f"Gráfico generado en {ruta}"}
    finally:
        db.close()

@app.get("/reporte/diario_pdf")
def reporte_pdf():
    db = SessionLocal()
    try:
        datos = calcular_metricas_diarias(db)
        ruta = generar_pdf_reporte(datos)
        return {"mensaje": f"Reporte PDF generado en {ruta}"}
    finally:
        db.close()


@app.get("/reporte/diario_pdf")
def reporte_pdf():
    db = SessionLocal()
    try:
        datos = calcular_metricas_diarias(db)
        ruta = generar_pdf_reporte(datos)
        return {"mensaje": f"Reporte PDF generado en {ruta}"}
    except Exception as e:
        traceback.print_exc()  # 👈 Esto imprimirá el error completo en consola
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

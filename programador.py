import schedule
import time
from reporte_utils import calcular_metricas_diarias, generar_grafico_ingresos, generar_pdf_reporte
from database import SessionLocal

def tarea_diaria():
    db = SessionLocal()
    try:
        datos = calcular_metricas_diarias(db)
        ruta = generar_pdf_reporte(datos)
        print(f"📄 Reporte generado en: {ruta}")
    finally:
        db.close()

# Programa la ejecución diaria a las 23:00 (ajústalo si estás haciendo pruebas)
schedule.every().day.at("04:15").do(tarea_diaria)

while True:
    schedule.run_pending()
    time.sleep(60)

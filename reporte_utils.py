# reporte_utils.py

from datetime import date, timedelta
from sqlalchemy import func
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
from database import MetricasDB

def calcular_metricas_diarias(db):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    hace_una_semana = hoy - timedelta(days=7)

    metricas_hoy = db.query(MetricasDB).filter(MetricasDB.fecha == hoy).first()
    ingresos_hoy = metricas_hoy.ingresos_totales if metricas_hoy else 0

    metricas_mes = db.query(MetricasDB).filter(MetricasDB.fecha >= primer_dia_mes).all()
    ingresos_mes = sum(m.ingresos_totales for m in metricas_mes)
    dia_actual = hoy.day
    proyeccion_mes = round((ingresos_mes / dia_actual) * 30, 2) if dia_actual > 0 else 0

    metricas_semana_pasada = db.query(MetricasDB).filter(MetricasDB.fecha == hace_una_semana).first()
    ingresos_semana_pasada = metricas_semana_pasada.ingresos_totales if metricas_semana_pasada else 0

    if ingresos_semana_pasada > 0:
        tasa_crecimiento = round((ingresos_hoy / ingresos_semana_pasada - 1) * 100, 2)
    else:
        tasa_crecimiento = None

    return {
        "fecha": hoy,
        "ingresos_hoy": round(ingresos_hoy, 2),
        "ingresos_mes": round(ingresos_mes, 2),
        "proyeccion_mes": proyeccion_mes,
        "tasa_crecimiento": tasa_crecimiento
    }

def generar_grafico_ingresos(db, ruta_archivo="reportes/ingresos_mes.png"):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    metricas = db.query(MetricasDB).filter(MetricasDB.fecha >= primer_dia_mes).order_by(MetricasDB.fecha).all()

    if not metricas:
        return None

    dias = [m.fecha.day for m in metricas]
    ingresos = [m.ingresos_totales for m in metricas]

    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(dias, ingresos, marker='o')
    plt.title("Evolución de ingresos diarios")
    plt.xlabel("Día")
    plt.ylabel("Ingresos (S/.)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(ruta_archivo)
    plt.close()
    return ruta_archivo

def generar_pdf_reporte(metricas=None, grafico_path="reportes/ingresos_mes.png", logo_path="logopappys.png", ruta_destino="reportes/reporte_diario.pdf"):
    pdf = FPDF()
    pdf.add_page()

    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=40)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 40, "REPORTE DIARIO - Pappy's Foods", ln=True, align="C")
    pdf.set_font("Arial", '', 12)

    if metricas:
        for clave, valor in metricas.items():
            pdf.cell(0, 10, f"{clave.replace('_', ' ').capitalize()}: {valor}", ln=True)

    if grafico_path and os.path.exists(grafico_path):
        pdf.image(grafico_path, x=10, w=180)

    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
    pdf.output(ruta_destino)
    return ruta_destino

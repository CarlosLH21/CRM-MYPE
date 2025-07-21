# app.py

import streamlit as st
from crud import procesar_pedido, registrar_feedback, calcular_metricas_diarias, generar_grafico_ingresos
from database import SessionLocal, crear_tablas
import os

# FORZAR creación de tablas
try:
    crear_tablas()
    st.info("✅ Base de datos inicializada correctamente.")
except Exception as e:
    st.warning(f"⚠️ Error al crear tablas: {e}")

st.set_page_config(page_title="CRM Pappy's Foods", layout="wide")
st.title("🍗 CRM para Pollerías - Pappy’s Foods")

menu = st.sidebar.radio("Selecciona una opción:", ["Registrar Pedido", "Registrar Feedback", "Ver Métricas", "Gráfico de Ingresos"])

# --- REGISTRAR PEDIDO ---
if menu == "Registrar Pedido":
    st.header("🛒 Registrar Pedido (WhatsApp o texto)")
    telefono = st.text_input("📞 Teléfono del cliente", max_chars=9)
    texto = st.text_area("✉️ Texto del pedido recibido")

    if st.button("Procesar Pedido"):
        if not telefono or not texto:
            st.warning("Completa todos los campos.")
        else:
            try:
                resultado = procesar_pedido(texto, telefono)
                st.success(resultado["mensaje_postventa"])
                st.write("### Detalles del pedido:")
                st.json(resultado)
            except Exception as e:
                st.error(f"Error al procesar pedido: {e}")

# --- REGISTRAR FEEDBACK ---
elif menu == "Registrar Feedback":
    st.header("⭐ Calificación del Cliente")
    telefono = st.text_input("📞 Teléfono del cliente")
    calificacion = st.slider("Puntaje del servicio", 1, 5, 3)

    if st.button("Enviar Feedback"):
        try:
            mensaje = registrar_feedback(telefono, calificacion)
            st.success(mensaje)
        except Exception as e:
            st.error(f"No se pudo registrar: {e}")

# --- MÉTRICAS DIARIAS ---
elif menu == "Ver Métricas":
    st.header("📊 Métricas del día")
    db = SessionLocal()
    try:
        datos = calcular_metricas_diarias(db)
        st.metric("Ingresos de Hoy", f"S/ {datos['ingresos_hoy']}")
        st.metric("Ingresos del Mes", f"S/ {datos['ingresos_mes']}")
        st.metric("Proyección del Mes", f"S/ {datos['proyeccion_mes']}")
        st.metric("Tasa de Crecimiento (%)", f"{datos['tasa_crecimiento']}%" if datos['tasa_crecimiento'] is not None else "No disponible")
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
    finally:
        db.close()

# --- GRÁFICO DE INGRESOS ---
elif menu == "Gráfico de Ingresos":
    st.header("📈 Ingresos del mes")
    db = SessionLocal()
    try:
        ruta = generar_grafico_ingresos(db)
        if ruta and os.path.exists(ruta):
            st.image(ruta, caption="Ingresos diarios", use_column_width=True)
        else:
            st.warning("No hay datos suficientes para generar el gráfico.")
    except Exception as e:
        st.error(f"Error al generar gráfico: {e}")
    finally:
        db.close()

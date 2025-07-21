from sqlalchemy.orm import Session
from database import SessionLocal, ClienteDB, ProductoDB, PedidoDB
from utils import extraer_productos
from datetime import datetime, timedelta
from sqlalchemy import func
from datetime import date
from database import MetricasDB
import random
from database import CancelacionDB
from json import dumps, loads
from database import MetricasDB
from datetime import date, timedelta
from sqlalchemy import extract
import matplotlib.pyplot as plt
import os


# Obtener cliente desde la base de datos
def get_cliente(db: Session, telefono: str):
    return db.query(ClienteDB).filter(ClienteDB.telefono == telefono).first()

# Obtener producto desde la base de datos
def get_producto(db: Session, nombre: str):
    return db.query(ProductoDB).filter(ProductoDB.nombre == nombre).first()

# Procesar el pedido recibido desde WhatsApp o formulario
def procesar_pedido(texto, telefono):
    productos_solicitados = extraer_productos(texto)
    if not productos_solicitados:
        raise ValueError("No se detectaron productos válidos en el pedido")

    db = SessionLocal()
    try:
        # 1. Buscar o registrar cliente
        cliente = get_cliente(db, telefono)
        if not cliente:
            cliente = ClienteDB(
                telefono=telefono,
                nombre=f"Cliente-{telefono[-4:]}",
                compras=0,
                puntos=0,
                feedback_promedio=0.0,
                categoria="NUEVO",
                ultima_compra=None
            )
            db.add(cliente)
        costo_total = 0
        # 2. Validar inventario y calcular subtotal
        subtotal = 0
        avisos = {}
        vendidos = {}

        for nombre, cantidad in productos_solicitados.items():
            producto = get_producto(db, nombre)
            if not producto:
                avisos[nombre] = "No registrado"
                continue
            if producto.stock < cantidad:
                avisos[nombre] = f"Stock insuficiente (hay {producto.stock})"
                continue

            # # Evaluar si el producto caduca mañana
            descuento_unitario = 0
            urgente = False
            if producto.caducidad:
                dias_para_caducar = (producto.caducidad.date() - date.today()).days
                if dias_para_caducar == 1:
                    descuento_unitario = producto.precio * 0.12
                    urgente = True
            precio_final = producto.precio - descuento_unitario
            # Evaluar si el producto caduca mañana
            descuento_unitario = 0
            urgente = False
            if producto.caducidad:
                dias_para_caducar = (producto.caducidad.date() - datetime.now().date()).days
                if dias_para_caducar == 1:
                    descuento_unitario = producto.precio * 0.12
                    urgente = True
            # Aplicar descuento
            precio_final = producto.precio - descuento_unitario
            subtotal += precio_final * cantidad
            producto.stock -= cantidad
            vendidos[nombre] = cantidad
            # Calcular costo total (para margen)
            if 'costo_total' not in locals():
                costo_total = 0
            costo_total += producto.costo_unitario * cantidad
            # Mensaje urgente
            if urgente:
                avisos[nombre] = "¡Vender urgente! Descuento aplicado 12%"

        if not vendidos:
            cancelacion = CancelacionDB(
                telefono=telefono,
                motivo="Todos los productos solicitados están agotados"
            )
            db.add(cancelacion)
            cancelaciones_hoy = db.query(CancelacionDB).filter(
                CancelacionDB.fecha >= datetime.now().replace(hour=0, minute=0, second=0),
                CancelacionDB.telefono == telefono
            ).count()
            if cancelaciones_hoy >= 3:
                # Puedes notificar al admin (log, mensaje especial, etc.)
                print(f"⚠️ Alerta: {telefono} tiene 3 cancelaciones hoy.")
            db.commit()
            raise ValueError("Pedido cancelado: ningún producto disponible.")
        elif avisos:  # hubo advertencias (agotados, urgentes)
            if cliente.cancelaciones is None:
                cliente.cancelaciones = 0
            cliente.cancelaciones += 1


            cancelacion = CancelacionDB(
                telefono=telefono,
                motivo="Pedido incompleto: uno o más productos agotados o con advertencia"
            )
            db.add(cancelacion)
        
        # 3. Actualizar cliente: puntos, compras, última compra
        puntos = int(subtotal)
        cliente.compras += 1
        cliente.puntos += puntos
        cliente.ultima_compra = datetime.now()
        tiempo_estimado_min = random.randint(20, 45)
        hora_salida = datetime.now()
        hora_entrega = hora_salida + timedelta(minutes=tiempo_estimado_min)
        repartidor = random.choice(["Luis", "Carla", "José"])

        # 4. Clasificar cliente
        pedidos_ultimos_14_dias = db.query(PedidoDB).filter(
            PedidoDB.telefono == telefono,
            PedidoDB.fecha >= datetime.now() - timedelta(days=14)
        ).count()

        total_30_dias = db.query(PedidoDB).filter(
            PedidoDB.telefono == telefono,
            PedidoDB.fecha >= datetime.now() - timedelta(days=30)
        ).with_entities(func.sum(PedidoDB.total)).scalar() or 0

        dias_desde_ultima = (datetime.now() - cliente.ultima_compra).days if cliente.ultima_compra else 999

        if pedidos_ultimos_14_dias >= 4 or total_30_dias >= 150:
            cliente.categoria = "PREMIUM"
        elif dias_desde_ultima > 21:
            cliente.categoria = "INACTIVO"
        elif pedidos_ultimos_14_dias >= 2:
            cliente.categoria = "RECURRENTE"
        else:
            cliente.categoria = "NUEVO"

        # 5. Registrar pedido
        nuevo_pedido = PedidoDB(
            telefono=telefono,
            detalle=vendidos,
            total=subtotal,
            estado="completo",
            repartidor=repartidor,
            hora_salida=hora_salida,
            hora_entrega_estim=hora_entrega
        )

        db.add(nuevo_pedido)

        # 6. Guardar todo
        margen_bruto = subtotal - (costo_total if 'costo_total' in locals() else 0)
        # Actualizar o crear la métrica del día
        hoy = date.today()
        metricas = db.query(MetricasDB).filter_by(fecha=hoy).first()
        if not metricas:
            metricas = MetricasDB(
                fecha=hoy,
                ingresos_totales=subtotal,
                margen_bruto_total=margen_bruto,
                pedidos=1
            )
            db.add(metricas)
            print(f"🟢 Métrica creada para {hoy}")
        else:
            metricas.ingresos_totales += subtotal
            metricas.margen_bruto_total += margen_bruto
            metricas.pedidos += 1
            print(f"🔄 Métrica actualizada para {hoy}")
        # Confirmar cambios   
        db.commit()

        # 6.1 Mensaje post-venta
        mensaje = f"Pedido procesado. Total: S/{round(subtotal, 2)}. Tiempo estimado: {tiempo_estimado_min} min. Puntos +{puntos}. Gracias."
        # 6.2 Cupón si es PREMIUM o INACTIVO
        cupon = None
        if cliente.categoria in ["PREMIUM", "INACTIVO"]:
            cupon = "CUPON10"  # o genera uno dinámicamente
            mensaje += f" 🎁 Cupón especial: {cupon}"
        
        mensaje_promocional = None
        una_semana_atras = datetime.now() - timedelta(days=7)

        # Buscar pedido del cliente hace exactamente 7 días
        pedido_pasado = db.query(PedidoDB).filter(
            PedidoDB.telefono == telefono,
            PedidoDB.fecha >= una_semana_atras.replace(hour=0, minute=0, second=0),
            PedidoDB.fecha < una_semana_atras.replace(hour=23, minute=59, second=59)
        ).first()
        if pedido_pasado:
            productos_antes = pedido_pasado.detalle
            if productos_antes == vendidos:  # exactamente el mismo pedido
                mensaje_promocional = f"¿Repetimos tu pedido del {una_semana_atras.strftime('%A')} pasado? Responde: Sí"
        # 7. Devolver respuesta completa
        return {
            "cliente": cliente.nombre,
            "productos": vendidos,
            "total": subtotal,
            "puntos": puntos,
            "avisos": avisos,
            "compras_totales": cliente.compras,
            "puntos_totales": cliente.puntos,
            "feedback_promedio": cliente.feedback_promedio,
            "categoria": cliente.categoria,
            "ultima_compra": cliente.ultima_compra,
            "cancelaciones": cliente.cancelaciones,
            "margen_bruto_estimado": round(margen_bruto, 2),
            "entrega": {
                "repartidor": repartidor,
                "hora_salida": hora_salida.strftime("%H:%M"),
                "hora_estimada": hora_entrega.strftime("%H:%M"),
                "tiempo_estimado_min": tiempo_estimado_min
            },
            "mensaje_postventa": mensaje,
            "cupon": cupon,# puede ser None si no aplica
            "promocion_sugerida": mensaje_promocional           
        }

    finally:
        db.close()

# Guardar calificación del cliente
def registrar_feedback(telefono, calificacion):
    db = SessionLocal()
    try:
        cliente = get_cliente(db, telefono)
        if not cliente:
            raise ValueError("Cliente no registrado")

        anterior = cliente.feedback_promedio or 0
        total_feedbacks = cliente.compras
        nuevo_promedio = round(((anterior * (total_feedbacks - 1)) + calificacion) / total_feedbacks, 2)

        cliente.feedback_promedio = nuevo_promedio
        db.commit()

        return f"Gracias {cliente.nombre}, tu opinión fue registrada."
    
    finally:
        db.close()


def calcular_metricas_diarias(db: Session):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    hace_una_semana = hoy - timedelta(days=7)

    # Ingresos de hoy
    metricas_hoy = db.query(MetricasDB).filter(MetricasDB.fecha == hoy).first()
    ingresos_hoy = metricas_hoy.ingresos_totales if metricas_hoy else 0

    # Ingresos acumulados del mes
    metricas_mes = db.query(MetricasDB).filter(MetricasDB.fecha >= primer_dia_mes).all()
    ingresos_mes = sum(m.ingresos_totales for m in metricas_mes)

    # Proyección del mes
    dia_actual = hoy.day
    proyeccion_mes = round((ingresos_mes / dia_actual) * 30, 2) if dia_actual > 0 else 0

    # Crecimiento comparado con mismo día de la semana pasada
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


def generar_grafico_ingresos(db: Session, ruta_archivo="reportes/ingresos_mes.png"):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)

    metricas = db.query(MetricasDB).filter(
        MetricasDB.fecha >= primer_dia_mes
    ).order_by(MetricasDB.fecha).all()

    if not metricas:
        return None

    # Fechas completas como etiquetas en eje X
    fechas = [m.fecha.strftime('%Y-%m-%d') for m in metricas]
    ingresos = [m.ingresos_totales for m in metricas]

    import matplotlib.pyplot as plt
    import os

    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(fechas, ingresos, marker='o', linestyle='-', color='skyblue')
    plt.title("Ingresos diarios del mes")
    plt.xlabel("Fecha")
    plt.ylabel("Ingresos (S/.)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(ruta_archivo)
    plt.close()

    return ruta_archivo


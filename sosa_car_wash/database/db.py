"""Acceso a datos y reglas de negocio de Sosa Car Wash (compartido por escritorio y web)."""
import hashlib
import os
from contextlib import contextmanager
from datetime import date

import psycopg2
import psycopg2.errors
import psycopg2.extras
import psycopg2.sql

from config import DB_CONFIG, HORARIOS, PUESTOS_SIMULTANEOS


# =============== Conexión ===============
@contextmanager
def conexion():
    """Abre una conexión; confirma (commit) al salir o revierte (rollback) si hay error."""
    con = psycopg2.connect(**DB_CONFIG)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def consultar(sql, params=None):
    """SELECT -> lista de diccionarios."""
    with conexion() as con, con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def ejecutar(sql, params=None):
    """INSERT/UPDATE/DELETE. Si la consulta tiene RETURNING, devuelve el primer valor."""
    with conexion() as con, con.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0] if cur.description else None


def mensaje_error(e):
    """Texto legible de un error. PostgreSQL en español devuelve tildes en cp1252 y
    psycopg2 puede fallar al leerlas como UTF-8; aquí recuperamos el mensaje real."""
    if isinstance(e, UnicodeDecodeError):
        return e.object.decode("cp1252", errors="replace")
    return str(e)


# =============== Seguridad ===============
def hash_clave(clave, sal=None):
    sal = sal or os.urandom(8).hex()
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal.encode(), 100_000).hex()
    return f"{sal}${h}"


def verificar_clave(clave, guardada):
    sal = guardada.split("$")[0]
    return hash_clave(clave, sal) == guardada


def autenticar(usuario, clave):
    filas = consultar("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
    if filas and verificar_clave(clave, filas[0]["clave"]):
        return filas[0]
    return None


# =============== Inicialización y migración ===============
def asegurar_base():
    """Crea la base de datos configurada si todavía no existe."""
    con = psycopg2.connect(**dict(DB_CONFIG, dbname="postgres"))
    try:
        con.autocommit = True
        with con.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["dbname"],))
            if not cur.fetchone():
                cur.execute(psycopg2.sql.SQL("CREATE DATABASE {}").format(
                    psycopg2.sql.Identifier(DB_CONFIG["dbname"])))
    finally:
        con.close()


def _columna_existe(tabla, columna):
    return bool(consultar("SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' "
                          "AND table_name = %s AND column_name = %s", (tabla, columna)))


def migrar():
    """Actualiza bases creadas con versiones anteriores (sin perder datos)."""
    if not _columna_existe("clientes", "documento"):
        ejecutar("ALTER TABLE clientes ADD COLUMN documento VARCHAR(20)")
    if not _columna_existe("pagos", "subtotal"):
        ejecutar("ALTER TABLE pagos ADD COLUMN subtotal NUMERIC(12,2) NOT NULL DEFAULT 0")
        ejecutar("UPDATE pagos SET subtotal = monto")
    if not _columna_existe("pagos", "descuento"):
        ejecutar("ALTER TABLE pagos ADD COLUMN descuento NUMERIC(12,2) NOT NULL DEFAULT 0")
    # Versión anterior usaba precios en otra moneda (50, 90, 140...): se pasan a guaraníes (x1000)
    if not consultar("SELECT 1 FROM meta WHERE clave = 'moneda_gs'"):
        mx = consultar("SELECT MAX(precio) AS m FROM servicios")[0]["m"]
        if mx is not None and mx < 1000:
            ejecutar("UPDATE servicios SET precio = precio * 1000")
            ejecutar("UPDATE pagos SET monto = monto * 1000, subtotal = subtotal * 1000")
        ejecutar("INSERT INTO meta (clave, valor) VALUES ('moneda_gs', '1')")


def sincronizar_pagos():
    """Garantiza que todo cobro tenga su ingreso en el libro de movimientos."""
    ejecutar("INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen, pago_id) "
             "SELECT p.fecha::date, 'INGRESO', 'Servicios', 'Cobro de cita #' || p.cita_id, p.monto, "
             "'SERVICIO', p.id FROM pagos p "
             "WHERE NOT EXISTS (SELECT 1 FROM movimientos m WHERE m.pago_id = p.id)")


def inicializar():
    """Crea la base, las tablas y los datos iniciales; actualiza bases antiguas."""
    asegurar_base()
    ruta = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(ruta, encoding="utf-8") as f:
        ejecutar(f.read())
    migrar()
    for indice in ("CREATE INDEX idx_citas_fecha ON citas (fecha, hora)",
                   "CREATE INDEX idx_mov_fecha ON movimientos (fecha)"):
        try:
            ejecutar(indice)
        except psycopg2.errors.DuplicateTable:
            pass                                   # el índice ya existía
    if not consultar("SELECT 1 FROM usuarios LIMIT 1"):
        ejecutar("INSERT INTO usuarios (usuario, clave, nombre, rol) VALUES (%s, %s, %s, 'ADMIN')",
                 ("admin", hash_clave("admin123"), "Administrador"))
        ejecutar("INSERT INTO usuarios (usuario, clave, nombre, rol) VALUES (%s, %s, %s, 'OPERADOR')",
                 ("operador", hash_clave("operador123"), "Operador de turno"))
    if not consultar("SELECT 1 FROM servicios LIMIT 1"):
        for datos in [("Lavado básico", "AUTO", 50000, 45), ("Lavado completo", "AUTO", 90000, 90),
                      ("Lavado + encerado", "AUTO", 150000, 120), ("Lavado de moto", "MOTO", 30000, 30),
                      ("Lavado + lubricación de cadena", "MOTO", 50000, 45)]:
            ejecutar("INSERT INTO servicios (nombre, tipo_vehiculo, precio, duracion_min) "
                     "VALUES (%s, %s, %s, %s)", datos)
    if not consultar("SELECT 1 FROM insumos LIMIT 1"):
        for datos in [("Shampoo automotriz", "litro", 20, 5, 30000), ("Cera líquida", "litro", 8, 2, 60000),
                      ("Desengrasante", "litro", 10, 3, 25000), ("Abrillantador de llantas", "litro", 6, 2, 35000),
                      ("Paños de microfibra", "unidad", 30, 10, 8000), ("Lubricante de cadena", "unidad", 10, 3, 20000)]:
            ejecutar("INSERT INTO insumos (nombre, unidad, stock, stock_minimo, costo_unitario) "
                     "VALUES (%s, %s, %s, %s, %s)", datos)
    sincronizar_pagos()


# =============== Agenda ===============
def horarios_disponibles(fecha):
    """Horas con al menos un puesto libre para una fecha 'AAAA-MM-DD'."""
    date.fromisoformat(fecha)  # lanza ValueError si el formato es inválido
    filas = consultar("SELECT hora, COUNT(*) AS n FROM citas "
                      "WHERE fecha = %s AND estado <> 'CANCELADA' GROUP BY hora", (fecha,))
    ocupados = {f["hora"].strftime("%H:%M"): f["n"] for f in filas}
    return [h for h in HORARIOS if ocupados.get(h, 0) < PUESTOS_SIMULTANEOS]


def crear_cita(vehiculo_id, servicio_id, fecha, hora, origen="ESCRITORIO", observacion=""):
    if date.fromisoformat(fecha) < date.today():
        raise ValueError("No se puede agendar en una fecha pasada.")
    if hora not in horarios_disponibles(fecha):
        raise ValueError("Ese horario ya no tiene puestos disponibles.")
    v = consultar("SELECT tipo FROM vehiculos WHERE id = %s", (vehiculo_id,))
    s = consultar("SELECT tipo_vehiculo FROM servicios WHERE id = %s AND activo", (servicio_id,))
    if not v or not s:
        raise ValueError("Vehículo o servicio no válido.")
    if v[0]["tipo"] != s[0]["tipo_vehiculo"]:
        raise ValueError("El servicio elegido no corresponde al tipo de vehículo.")
    return ejecutar("INSERT INTO citas (vehiculo_id, servicio_id, fecha, hora, origen, observacion) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (vehiculo_id, servicio_id, fecha, hora, origen, observacion or None))


def reserva_web(d):
    """Reserva enviada desde la página: crea cliente y vehículo si no existen."""
    for campo in ("nombre", "telefono", "placa", "tipo", "servicio_id", "fecha", "hora"):
        if not str(d.get(campo, "")).strip():
            raise ValueError(f"Falta completar el campo: {campo}.")
    if d["tipo"] not in ("AUTO", "MOTO"):
        raise ValueError("Tipo de vehículo inválido.")
    placa = d["placa"].strip().upper()
    fila = consultar("SELECT id FROM vehiculos WHERE placa = %s", (placa,))
    if fila:
        vehiculo_id = fila[0]["id"]
    else:
        cliente_id = ejecutar("INSERT INTO clientes (nombre, telefono, email) VALUES (%s, %s, %s) "
                              "RETURNING id", (d["nombre"].strip(), d["telefono"].strip(),
                                               d.get("email") or None))
        vehiculo_id = ejecutar("INSERT INTO vehiculos (cliente_id, tipo, placa) VALUES (%s, %s, %s) "
                               "RETURNING id", (cliente_id, d["tipo"], placa))
    return crear_cita(vehiculo_id, int(d["servicio_id"]), d["fecha"], d["hora"], "WEB",
                      d.get("observacion", ""))


def seguimiento(cita_id, placa):
    """Estado de una reserva. Se exige el número de turno Y la placa para proteger la privacidad."""
    def norm(t):
        return "".join(ch for ch in str(t).upper() if ch.isalnum())
    try:
        cita_id = int(cita_id)
    except (TypeError, ValueError):
        return None
    filas = consultar("SELECT c.id, c.fecha, c.hora, c.estado, v.placa, s.nombre AS servicio, s.precio "
                      "FROM citas c JOIN vehiculos v ON v.id = c.vehiculo_id "
                      "JOIN servicios s ON s.id = c.servicio_id WHERE c.id = %s", (cita_id,))
    if not filas or norm(filas[0]["placa"]) != norm(placa):
        return None
    r = filas[0]
    return {"id": r["id"], "fecha": r["fecha"].isoformat(), "hora": r["hora"].strftime("%H:%M"),
            "estado": r["estado"], "placa": r["placa"], "servicio": r["servicio"], "precio": r["precio"]}


# =============== Cobros y comprobantes ===============
def cobrar_cita(cita_id, metodo, descuento_pct=0):
    """Registra el pago (con descuento opcional), el ingreso contable y completa la cita."""
    descuento_pct = float(descuento_pct or 0)
    if not 0 <= descuento_pct <= 100:
        raise ValueError("El descuento debe estar entre 0 y 100 %.")
    with conexion() as con, con.cursor() as cur:
        cur.execute("SELECT s.precio, c.estado FROM citas c JOIN servicios s ON s.id = c.servicio_id "
                    "WHERE c.id = %s", (cita_id,))
        fila = cur.fetchone()
        if not fila:
            raise ValueError("La cita no existe.")
        subtotal, estado = float(fila[0]), fila[1]
        if estado in ("COMPLETADA", "CANCELADA"):
            raise ValueError(f"La cita ya está {estado.lower()}.")
        descuento = round(subtotal * descuento_pct / 100)
        monto = subtotal - descuento
        cur.execute("INSERT INTO pagos (cita_id, subtotal, descuento, monto, metodo) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id", (cita_id, subtotal, descuento, monto, metodo))
        pago_id = cur.fetchone()[0]
        cur.execute("INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen, pago_id) "
                    "VALUES (CURRENT_DATE, 'INGRESO', 'Servicios', %s, %s, 'SERVICIO', %s)",
                    (f"Cobro de cita #{cita_id}", monto, pago_id))
        cur.execute("UPDATE citas SET estado = 'COMPLETADA' WHERE id = %s", (cita_id,))
    return {"pago_id": pago_id, "subtotal": subtotal, "descuento": descuento, "monto": monto}


def pago_de_cita(cita_id):
    fila = consultar("SELECT id FROM pagos WHERE cita_id = %s", (cita_id,))
    return fila[0]["id"] if fila else None


def datos_comprobante(pago_id):
    fila = consultar(
        "SELECT p.id, p.fecha, p.subtotal, p.descuento, p.monto, p.metodo, c.id AS cita_id, "
        "c.fecha AS fecha_cita, c.hora, cl.nombre, cl.documento, cl.telefono, v.placa, v.tipo, "
        "v.marca, v.modelo, s.nombre AS servicio "
        "FROM pagos p JOIN citas c ON c.id = p.cita_id JOIN vehiculos v ON v.id = c.vehiculo_id "
        "JOIN clientes cl ON cl.id = v.cliente_id JOIN servicios s ON s.id = c.servicio_id "
        "WHERE p.id = %s", (pago_id,))
    return fila[0] if fila else None


# =============== Panel de inicio ===============
def resumen_inicio():
    estados = consultar("SELECT estado, COUNT(*) AS n FROM citas WHERE fecha = CURRENT_DATE GROUP BY estado")
    ingresos_hoy = consultar("SELECT COALESCE(SUM(monto), 0) AS t FROM movimientos "
                             "WHERE tipo = 'INGRESO' AND fecha = CURRENT_DATE")[0]["t"]
    mes = {r["tipo"]: r["t"] for r in consultar(
        "SELECT tipo, COALESCE(SUM(monto), 0) AS t FROM movimientos "
        "WHERE fecha >= date_trunc('month', CURRENT_DATE) GROUP BY tipo")}
    return {
        "por_estado": {r["estado"]: r["n"] for r in estados},
        "ingresos_hoy": ingresos_hoy,
        "balance_mes": mes.get("INGRESO", 0) - mes.get("EGRESO", 0),
        "proximas": consultar(
            "SELECT c.hora, cl.nombre, v.placa, s.nombre AS servicio, c.estado FROM citas c "
            "JOIN vehiculos v ON v.id = c.vehiculo_id JOIN clientes cl ON cl.id = v.cliente_id "
            "JOIN servicios s ON s.id = c.servicio_id WHERE c.fecha = CURRENT_DATE "
            "AND c.estado IN ('PENDIENTE', 'EN_PROCESO') ORDER BY c.hora, c.id LIMIT 10"),
        "insumos_bajos": consultar("SELECT id, nombre, unidad, stock, stock_minimo FROM insumos "
                                   "WHERE activo AND stock <= stock_minimo ORDER BY nombre"),
    }


# =============== Insumos ===============
def insumos_listar():
    return consultar("SELECT * FROM insumos ORDER BY activo DESC, nombre")


def insumo_guardar(insumo_id, nombre, unidad, minimo, costo):
    if insumo_id:
        ejecutar("UPDATE insumos SET nombre=%s, unidad=%s, stock_minimo=%s, costo_unitario=%s WHERE id=%s",
                 (nombre, unidad, minimo, costo, insumo_id))
        return insumo_id
    return ejecutar("INSERT INTO insumos (nombre, unidad, stock_minimo, costo_unitario) "
                    "VALUES (%s, %s, %s, %s) RETURNING id", (nombre, unidad, minimo, costo))


def insumo_movimiento(insumo_id, tipo, cantidad, costo_total=0, nota=""):
    """COMPRA: suma stock y registra un egreso. CONSUMO: descuenta stock."""
    cantidad, costo_total = float(cantidad), float(costo_total or 0)
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    if tipo not in ("COMPRA", "CONSUMO"):
        raise ValueError("Tipo de movimiento inválido.")
    with conexion() as con, con.cursor() as cur:
        cur.execute("SELECT nombre, stock FROM insumos WHERE id = %s FOR UPDATE", (insumo_id,))
        fila = cur.fetchone()
        if not fila:
            raise ValueError("El insumo no existe.")
        nombre, stock = fila[0], float(fila[1])
        if tipo == "CONSUMO":
            if cantidad > stock:
                raise ValueError(f"Stock insuficiente: solo hay {stock:g}.")
            cur.execute("UPDATE insumos SET stock = stock - %s WHERE id = %s", (cantidad, insumo_id))
            costo_total = 0
        else:
            cur.execute("UPDATE insumos SET stock = stock + %s WHERE id = %s", (cantidad, insumo_id))
            if costo_total > 0:
                cur.execute("UPDATE insumos SET costo_unitario = %s WHERE id = %s",
                            (round(costo_total / cantidad), insumo_id))
                cur.execute("INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen) "
                            "VALUES (CURRENT_DATE, 'EGRESO', 'Insumos', %s, %s, 'INSUMO')",
                            (f"Compra de {nombre}", costo_total))
        cur.execute("INSERT INTO insumo_movs (insumo_id, tipo, cantidad, costo_total, nota) "
                    "VALUES (%s, %s, %s, %s, %s)", (insumo_id, tipo, cantidad, costo_total, nota or None))


def insumo_historial(insumo_id):
    return consultar("SELECT fecha, tipo, cantidad, costo_total, nota FROM insumo_movs "
                     "WHERE insumo_id = %s ORDER BY fecha DESC, id DESC LIMIT 30", (insumo_id,))


# =============== Ingresos, egresos y balance ===============
def movimiento_agregar(fecha, tipo, categoria, descripcion, monto):
    if tipo not in ("INGRESO", "EGRESO"):
        raise ValueError("Tipo inválido.")
    return ejecutar("INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen) "
                    "VALUES (%s, %s, %s, %s, %s, 'MANUAL') RETURNING id",
                    (fecha, tipo, categoria, descripcion or None, monto))


def movimiento_eliminar(mov_id):
    ejecutar("DELETE FROM movimientos WHERE id = %s AND origen = 'MANUAL'", (mov_id,))


def movimientos_listar(desde, hasta):
    return consultar("SELECT * FROM movimientos WHERE fecha BETWEEN %s AND %s "
                     "ORDER BY fecha DESC, id DESC", (desde, hasta))


def balance(desde, hasta):
    t = {r["tipo"]: r["t"] for r in consultar(
        "SELECT tipo, COALESCE(SUM(monto), 0) AS t FROM movimientos WHERE fecha BETWEEN %s AND %s "
        "GROUP BY tipo", (desde, hasta))}
    return {"ingresos": t.get("INGRESO", 0), "egresos": t.get("EGRESO", 0)}


def balance_por_categoria(desde, hasta, tipo):
    return consultar("SELECT categoria, SUM(monto) AS total FROM movimientos "
                     "WHERE fecha BETWEEN %s AND %s AND tipo = %s GROUP BY categoria ORDER BY total DESC",
                     (desde, hasta, tipo))


def balance_mensual(n=6):
    """Ingresos y egresos de los últimos n meses -> lista [(AAAA-MM, ingresos, egresos)]."""
    hoy = date.today()
    meses = []
    anio, mes = hoy.year, hoy.month
    for _ in range(n):
        meses.append(f"{anio:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            anio, mes = anio - 1, 12
    meses.reverse()
    filas = consultar("SELECT to_char(fecha, 'YYYY-MM') AS mes, tipo, SUM(monto) AS total FROM movimientos "
                      "WHERE fecha >= %s GROUP BY 1, 2", (meses[0] + "-01",))
    datos = {(r["mes"], r["tipo"]): float(r["total"]) for r in filas}
    return [(m, datos.get((m, "INGRESO"), 0.0), datos.get((m, "EGRESO"), 0.0)) for m in meses]


# =============== Reportes ===============
def ingresos_por_dia(desde, hasta):
    return consultar("SELECT fecha::date AS dia, SUM(monto) AS total, COUNT(*) AS cobros, "
                     "SUM(descuento) AS descuentos FROM pagos "
                     "WHERE fecha::date BETWEEN %s AND %s GROUP BY 1 ORDER BY 1", (desde, hasta))


def servicios_top(desde, hasta):
    return consultar("SELECT s.nombre, COUNT(*) AS cantidad FROM citas c "
                     "JOIN servicios s ON s.id = c.servicio_id "
                     "WHERE c.fecha BETWEEN %s AND %s AND c.estado <> 'CANCELADA' "
                     "GROUP BY s.nombre ORDER BY cantidad DESC", (desde, hasta))


def ingresos_por_metodo(desde, hasta):
    return consultar("SELECT metodo, SUM(monto) AS total FROM pagos WHERE fecha::date BETWEEN %s AND %s "
                     "GROUP BY metodo ORDER BY total DESC", (desde, hasta))


def ingresos_por_tipo(desde, hasta):
    return consultar("SELECT v.tipo, SUM(p.monto) AS total FROM pagos p JOIN citas c ON c.id = p.cita_id "
                     "JOIN vehiculos v ON v.id = c.vehiculo_id WHERE p.fecha::date BETWEEN %s AND %s "
                     "GROUP BY v.tipo ORDER BY total DESC", (desde, hasta))


def citas_por_origen(desde, hasta):
    return consultar("SELECT origen, COUNT(*) AS n FROM citas WHERE fecha BETWEEN %s AND %s "
                     "AND estado <> 'CANCELADA' GROUP BY origen ORDER BY n DESC", (desde, hasta))

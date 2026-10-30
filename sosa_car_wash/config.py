"""Configuración central de Sosa Car Wash.
La conexión a PostgreSQL se guarda en config_local.json (lo crea el asistente configurar_bd.py).
También puede definirse con variables de entorno AQUAWASH_DB_*."""
import json
import os

_AQUI = os.path.dirname(os.path.abspath(__file__))

DB_CONFIG = {
    "host": os.getenv("AQUAWASH_DB_HOST", "localhost"),
    "port": int(os.getenv("AQUAWASH_DB_PORT", "5432")),
    "dbname": os.getenv("AQUAWASH_DB_NAME", "aquawash"),   # nombre interno de la base (no cambiar)
    "user": os.getenv("AQUAWASH_DB_USER", "postgres"),
    "password": os.getenv("AQUAWASH_DB_PASSWORD", "sosa13"),
}

_local = os.path.join(_AQUI, "config_local.json")          # lo escribe configurar_bd.py
if os.path.exists(_local):
    with open(_local, encoding="utf-8") as _f:
        DB_CONFIG.update(json.load(_f))

# ---- Datos del negocio (aparecen en el programa, en los comprobantes y en la página web) ----
NEGOCIO = {
    "nombre": "Sosa Car Wash",
    "eslogan": "Lavadero de autos y motos",
    "telefono": "0981 000 000",                  # EDITAR
    "whatsapp": "595981000000",                  # EDITAR: solo números, con código de país
    "email": "contacto@sosacarwash.com",         # EDITAR
    "direccion": "Escriba aquí la dirección del local",   # EDITAR
    "horario": "Lunes a sábado · 08:00 a 18:00",
    "ruc": "80000000-0",                         # EDITAR
}

PUESTOS_SIMULTANEOS = 2                               # vehículos que se lavan a la vez
HORARIOS = [f"{h:02d}:00" for h in range(8, 18)]      # 08:00 a 17:00
MONEDA = "Gs."                                        # guaraníes
WEB_PORT = 8000

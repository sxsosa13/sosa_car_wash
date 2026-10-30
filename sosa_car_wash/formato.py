"""Formato de guaraníes (sin decimales, punto como separador de miles) y fechas en español."""
from config import MONEDA

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def gs(valor, simbolo=True):
    """1250000 -> 'Gs. 1.250.000'"""
    n = int(round(float(valor or 0)))
    texto = f"{abs(n):,}".replace(",", ".")
    if n < 0:
        texto = "-" + texto
    return f"{MONEDA} {texto}" if simbolo else texto


def fecha_larga(d):
    return f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"

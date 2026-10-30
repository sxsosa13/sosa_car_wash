"""Comprobante de pago imprimible (HTML). Se abre en el navegador: Ctrl+P para imprimir o guardar como PDF."""
import html
import os
import webbrowser
from pathlib import Path

from config import NEGOCIO
from database import db
from formato import gs

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comprobantes")

PLANTILLA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Comprobante N° {numero}</title>
<style>
 body {{ font-family: "Segoe UI", Arial, sans-serif; background:#e3f2fd; margin:0; padding:24px; color:#0b2a57; }}
 .ticket {{ max-width:420px; margin:auto; background:#fff; border-radius:14px; overflow:hidden;
           box-shadow:0 6px 24px rgba(21,101,192,.18); }}
 .cab {{ background:linear-gradient(135deg,#0b2a57,#1565c0); color:#fff; padding:20px; text-align:center; }}
 .cab h1 {{ margin:0; font-size:22px; letter-spacing:1px; }}
 .cab p {{ margin:3px 0 0; font-size:12px; color:#b3e5fc; }}
 .cuerpo {{ padding:18px 22px; }}
 .num {{ text-align:center; font-weight:700; color:#1565c0; margin-bottom:12px; }}
 table {{ width:100%; border-collapse:collapse; font-size:14px; }}
 td {{ padding:6px 0; border-bottom:1px dashed #b3e5fc; vertical-align:top; }}
 td:last-child {{ text-align:right; font-weight:600; }}
 .total td {{ font-size:18px; color:#1565c0; border-bottom:0; border-top:2px solid #1565c0; padding-top:10px; }}
 .pie {{ text-align:center; font-size:12px; color:#5b7186; padding:0 22px 20px; }}
 button {{ display:block; margin:18px auto 0; padding:10px 26px; border:0; border-radius:8px; background:#1565c0;
          color:#fff; font-weight:700; cursor:pointer; }}
 @media print {{ body {{ background:#fff; padding:0; }} .ticket {{ box-shadow:none; }} button {{ display:none; }} }}
</style></head><body>
<div class="ticket">
 <div class="cab"><h1>{negocio}</h1><p>{eslogan}</p><p>RUC {ruc} · Tel. {telefono}</p><p>{direccion}</p></div>
 <div class="cuerpo">
  <div class="num">COMPROBANTE N° {numero}</div>
  <table>
   <tr><td>Fecha</td><td>{fecha}</td></tr>
   <tr><td>Cliente</td><td>{cliente}</td></tr>
   {documento}
   <tr><td>Vehículo</td><td>{vehiculo}</td></tr>
   <tr><td>Placa</td><td>{placa}</td></tr>
   <tr><td>Servicio</td><td>{servicio}</td></tr>
   <tr><td>Subtotal</td><td>{subtotal}</td></tr>
   <tr><td>Descuento</td><td>- {descuento}</td></tr>
   <tr><td>Método de pago</td><td>{metodo}</td></tr>
   <tr class="total"><td>TOTAL</td><td>{total}</td></tr>
  </table>
  <button onclick="window.print()">Imprimir</button>
 </div>
 <div class="pie">¡Gracias por su preferencia!<br>Documento interno, no válido como factura.</div>
</div></body></html>"""


def generar(pago_id):
    d = db.datos_comprobante(pago_id)
    if not d:
        raise ValueError("No se encontró el pago.")
    e = html.escape
    vehiculo = " ".join(x for x in (d["marca"], d["modelo"]) if x) or ("Auto" if d["tipo"] == "AUTO" else "Moto")
    documento = f"<tr><td>CI / RUC</td><td>{e(d['documento'])}</td></tr>" if d["documento"] else ""
    numero = f"{d['id']:06d}"
    texto = PLANTILLA.format(
        numero=numero, negocio=e(NEGOCIO["nombre"]), eslogan=e(NEGOCIO["eslogan"]), ruc=e(NEGOCIO["ruc"]),
        telefono=e(NEGOCIO["telefono"]), direccion=e(NEGOCIO["direccion"]),
        fecha=d["fecha"].strftime("%d/%m/%Y %H:%M"), cliente=e(d["nombre"]), documento=documento,
        vehiculo=e(vehiculo), placa=e(d["placa"]), servicio=e(d["servicio"]), subtotal=gs(d["subtotal"]),
        descuento=gs(d["descuento"]), metodo=e(d["metodo"].title()), total=gs(d["monto"]))
    os.makedirs(CARPETA, exist_ok=True)
    ruta = os.path.join(CARPETA, f"comprobante_{numero}.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    return ruta


def abrir(pago_id):
    webbrowser.open(Path(generar(pago_id)).as_uri())


def abrir_carpeta():
    os.makedirs(CARPETA, exist_ok=True)
    if hasattr(os, "startfile"):
        os.startfile(CARPETA)                      # Windows
    else:
        webbrowser.open(Path(CARPETA).as_uri())

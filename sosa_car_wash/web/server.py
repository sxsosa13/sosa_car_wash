"""Servidor web de Sosa Car Wash: sirve la página de reservas y una pequeña API JSON.
Uso independiente:  python web/server.py   (o desde el menú Archivo de la aplicación)
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HORARIOS, NEGOCIO, WEB_PORT, MONEDA   # noqa: E402
from database import db                                   # noqa: E402

RAIZ = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def _responder(self, cuerpo, tipo, codigo=200):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, codigo=200):
        self._responder(json.dumps(datos, default=str).encode(), "application/json; charset=utf-8", codigo)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        try:
            if url.path in ("/", "/index.html"):
                with open(os.path.join(RAIZ, "index.html"), "rb") as f:
                    self._responder(f.read(), "text/html; charset=utf-8")
            elif url.path == "/api/negocio":
                self._json(dict(NEGOCIO, horarios=HORARIOS, moneda=MONEDA))
            elif url.path == "/api/servicios":
                self._json(db.consultar("SELECT id, nombre, tipo_vehiculo, precio, duracion_min "
                                        "FROM servicios WHERE activo ORDER BY tipo_vehiculo, precio"))
            elif url.path == "/api/horarios":
                self._json(db.horarios_disponibles(q.get("fecha", [""])[0]))
            elif url.path == "/api/seguimiento":
                r = db.seguimiento(q.get("cita", [""])[0], q.get("placa", [""])[0])
                if r is None:
                    self._json({"error": "No encontramos una reserva con esos datos."}, 404)
                else:
                    self._json(r)
            else:
                self.send_error(404)
        except ValueError:
            self._json({"error": "Datos inválidos"}, 400)
        except Exception:
            self._json({"error": "Error interno del servidor"}, 500)

    def do_POST(self):
        if self.path != "/api/reservas":
            return self.send_error(404)
        try:
            largo = int(self.headers.get("Content-Length", 0))
            cita = db.reserva_web(json.loads(self.rfile.read(largo)))
            self._json({"ok": True, "cita": cita}, 201)
        except ValueError as e:
            self._json({"ok": False, "error": str(e) or "Datos inválidos"}, 400)
        except Exception:
            self._json({"ok": False, "error": "Error interno del servidor"}, 500)

    def log_message(self, *args):   # consola silenciosa
        pass


def iniciar_en_hilo():
    """Arranca el servidor en segundo plano (lo usa la aplicación de escritorio)."""
    srv = ThreadingHTTPServer(("0.0.0.0", WEB_PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == "__main__":
    print(f"{NEGOCIO['nombre']} · web en http://localhost:{WEB_PORT}  (Ctrl+C para detener)")
    ThreadingHTTPServer(("0.0.0.0", WEB_PORT), Handler).serve_forever()

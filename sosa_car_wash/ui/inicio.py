from datetime import date
from tkinter import ttk

from database import db
from formato import gs, fecha_larga
from ui.utils import tabla, llenar, tarjeta


class InicioTab(ttk.Frame):
    """Panel de inicio: resumen del día."""

    def __init__(self, master, usuario):
        super().__init__(master, padding=14)
        self.admin = usuario["rol"] == "ADMIN"
        ttk.Label(self, text=f"Bienvenido, {usuario['nombre']}", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self, text=fecha_larga(date.today())).pack(anchor="w", pady=(0, 10))

        fila = ttk.Frame(self)
        fila.pack(fill="x")
        titulos = [("citas", "Citas de hoy"), ("estado", "Pendientes / en proceso"),
                   ("ingresos", "Ingresos de hoy"),
                   ("extra", "Balance del mes" if self.admin else "Servicios completados hoy")]
        self.cifras = {}
        for i, (clave, titulo) in enumerate(titulos):
            fila.columnconfigure(i, weight=1, uniform="tarjetas")
            marco, cifra = tarjeta(fila, titulo)
            marco.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            self.cifras[clave] = cifra

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True, pady=14)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(1, weight=1)
        ttk.Label(cuerpo, text="Próximos servicios de hoy", style="Sub.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(cuerpo, text="Insumos con stock bajo", style="Sub.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))
        m1, self.t_prox = tabla(cuerpo, [("hora", "Hora", 60), ("cliente", "Cliente", 150), ("placa", "Placa", 80),
                                         ("servicio", "Servicio", 170), ("estado", "Estado", 90)], alto=10)
        m1.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        m2, self.t_ins = tabla(cuerpo, [("nombre", "Insumo", 170), ("stock", "Stock", 90), ("min", "Mínimo", 70)], alto=10)
        m2.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=(4, 0))
        ttk.Button(self, text="Actualizar", command=self.refrescar).pack(anchor="e")
        self.refrescar()

    def refrescar(self):
        d = db.resumen_inicio()
        e = d["por_estado"]
        self.cifras["citas"].config(text=str(sum(n for est, n in e.items() if est != "CANCELADA")))
        self.cifras["estado"].config(text=f"{e.get('PENDIENTE', 0)} / {e.get('EN_PROCESO', 0)}")
        self.cifras["ingresos"].config(text=gs(d["ingresos_hoy"]))
        self.cifras["extra"].config(text=gs(d["balance_mes"]) if self.admin else str(e.get("COMPLETADA", 0)))
        llenar(self.t_prox, [(i, (r["hora"].strftime("%H:%M"), r["nombre"], r["placa"], r["servicio"], r["estado"]))
                             for i, r in enumerate(d["proximas"])])
        llenar(self.t_ins, [(r["id"], (r["nombre"], f"{float(r['stock']):g} {r['unidad']}",
                                       f"{float(r['stock_minimo']):g}"), "alerta") for r in d["insumos_bajos"]])

import csv
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox, filedialog

from database import db
from formato import gs
from ui import tema
from ui.utils import tabla, llenar, barras


class ReportesTab(ttk.Frame):
    """Ingresos por día, servicios, método de pago, tipo de vehículo y origen de reservas (solo ADMIN)."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        hoy = date.today()
        self.desde = tk.StringVar(value=hoy.replace(day=1).isoformat())
        self.hasta = tk.StringVar(value=hoy.isoformat())
        self.ingresos = []

        f = ttk.Frame(self)
        f.pack(fill="x")
        ttk.Label(f, text="Desde").pack(side="left")
        ttk.Entry(f, textvariable=self.desde, width=12).pack(side="left", padx=4)
        ttk.Label(f, text="Hasta").pack(side="left")
        ttk.Entry(f, textvariable=self.hasta, width=12).pack(side="left", padx=4)
        ttk.Button(f, text="Generar", command=self.generar).pack(side="left", padx=6)
        ttk.Button(f, text="Exportar CSV", style="Secundario.TButton", command=self.exportar).pack(side="left")
        self.lbl = ttk.Label(f, text="", style="Sub.TLabel")
        self.lbl.pack(side="right")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True, pady=10)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)
        izq = ttk.LabelFrame(cuerpo, text="Ingresos por día", padding=6)
        izq.grid(row=0, column=0, sticky="nsew")
        marco, self.tv = tabla(izq, [("dia", "Día", 90), ("cobros", "Cobros", 60, "e"),
                                     ("desc", "Descuentos (Gs.)", 120, "e"), ("total", "Ingresos (Gs.)", 120, "e")],
                               alto=14)
        marco.pack(fill="both", expand=True)

        nb = ttk.Notebook(cuerpo)
        nb.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.canvas = {}
        for clave, titulo in [("serv", "Servicios"), ("met", "Método de pago"), ("tipo", "Auto / Moto"),
                              ("orig", "Origen")]:
            p = ttk.Frame(nb, padding=6)
            nb.add(p, text=f" {titulo} ")
            c = tk.Canvas(p, width=380, height=300, bg=tema.BLANCO, highlightthickness=0)
            c.pack(fill="both", expand=True)
            self.canvas[clave] = c
        self.generar()

    def refrescar(self):
        self.generar()

    def generar(self):
        try:
            d, h = date.fromisoformat(self.desde.get()), date.fromisoformat(self.hasta.get())
        except ValueError:
            return messagebox.showwarning("Fechas inválidas", "Use el formato AAAA-MM-DD.")
        self.ingresos = db.ingresos_por_dia(d, h)
        llenar(self.tv, [(i, (r["dia"].isoformat(), r["cobros"], gs(r["descuentos"], False), gs(r["total"], False)))
                         for i, r in enumerate(self.ingresos)])
        total = sum(r["total"] for r in self.ingresos)
        descuentos = sum(r["descuentos"] for r in self.ingresos)
        self.lbl.config(text=f"Ingresos: {gs(total)}  ·  Descuentos: {gs(descuentos)}")
        barras(self.canvas["serv"], [(r["nombre"], r["cantidad"]) for r in db.servicios_top(d, h)], str)
        barras(self.canvas["met"], [(r["metodo"].title(), r["total"]) for r in db.ingresos_por_metodo(d, h)],
               gs, tema.AZUL)
        barras(self.canvas["tipo"], [("Autos" if r["tipo"] == "AUTO" else "Motos", r["total"])
                                     for r in db.ingresos_por_tipo(d, h)], gs, tema.CELESTE)
        barras(self.canvas["orig"], [("Página web" if r["origen"] == "WEB" else "Escritorio", r["n"])
                                     for r in db.citas_por_origen(d, h)], str, tema.AZUL_OSCURO)

    def exportar(self):
        if not self.ingresos:
            return messagebox.showinfo("Sin datos", "Genere primero un reporte con datos.")
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="ingresos.csv")
        if ruta:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["dia", "cobros", "descuentos", "ingresos"])
                w.writerows([[r["dia"].isoformat(), r["cobros"], int(r["descuentos"]), int(r["total"])]
                             for r in self.ingresos])
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{ruta}")

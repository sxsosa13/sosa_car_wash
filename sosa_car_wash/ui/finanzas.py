import csv
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox, filedialog

from database import db
from formato import gs
from ui import tema
from ui.utils import tabla, llenar, seleccionado, tarjeta, a_entero, barras

CATEGORIAS = {
    "INGRESO": ["Otros ingresos", "Propinas", "Venta de productos"],
    "EGRESO": ["Sueldos", "Alquiler", "Servicios básicos", "Mantenimiento", "Impuestos", "Otros egresos"],
}


class FinanzasTab(ttk.Frame):
    """Ingresos, egresos y balance económico (solo ADMIN)."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        hoy = date.today()
        self.desde = tk.StringVar(value=hoy.replace(day=1).isoformat())
        self.hasta = tk.StringVar(value=hoy.isoformat())
        self.f = {"tipo": tk.StringVar(value="EGRESO"), "fecha": tk.StringVar(value=hoy.isoformat()),
                  "categoria": tk.StringVar(value="Otros egresos"), "descripcion": tk.StringVar(),
                  "monto": tk.StringVar()}
        self.movs = []

        filtros = ttk.Frame(self)
        filtros.pack(fill="x")
        ttk.Label(filtros, text="Desde").pack(side="left")
        ttk.Entry(filtros, textvariable=self.desde, width=12).pack(side="left", padx=4)
        ttk.Label(filtros, text="Hasta").pack(side="left")
        ttk.Entry(filtros, textvariable=self.hasta, width=12).pack(side="left", padx=4)
        ttk.Button(filtros, text="Actualizar", command=self.actualizar).pack(side="left", padx=6)
        ttk.Button(filtros, text="Exportar CSV", style="Secundario.TButton", command=self.exportar).pack(side="left")

        tarjetas = ttk.Frame(self)
        tarjetas.pack(fill="x", pady=10)
        self.cifras = {}
        for i, (clave, titulo) in enumerate([("ing", "Ingresos del período"), ("egr", "Egresos del período"),
                                             ("bal", "Balance (utilidad)")]):
            tarjetas.columnconfigure(i, weight=1, uniform="t")
            marco, cifra = tarjeta(tarjetas, titulo)
            marco.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            self.cifras[clave] = cifra

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)
        cuerpo.rowconfigure(0, weight=1)
        izq, der = ttk.Frame(cuerpo), ttk.Frame(cuerpo)
        izq.grid(row=0, column=0, sticky="nsew")
        der.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # --- formulario + tabla ---
        form = ttk.LabelFrame(izq, text="Registrar ingreso o egreso", padding=8)
        form.pack(fill="x")
        ttk.Label(form, text="Tipo").grid(row=0, column=0, sticky="e")
        cb = ttk.Combobox(form, textvariable=self.f["tipo"], values=["INGRESO", "EGRESO"], width=10, state="readonly")
        cb.grid(row=0, column=1, padx=4, pady=3)
        cb.bind("<<ComboboxSelected>>", self.cambiar_tipo)
        ttk.Label(form, text="Fecha").grid(row=0, column=2, sticky="e")
        ttk.Entry(form, textvariable=self.f["fecha"], width=12).grid(row=0, column=3, padx=4)
        ttk.Label(form, text="Categoría").grid(row=0, column=4, sticky="e")
        self.cb_cat = ttk.Combobox(form, textvariable=self.f["categoria"], values=CATEGORIAS["EGRESO"], width=18)
        self.cb_cat.grid(row=0, column=5, padx=4)
        ttk.Label(form, text="Descripción").grid(row=1, column=0, sticky="e")
        ttk.Entry(form, textvariable=self.f["descripcion"], width=34).grid(row=1, column=1, columnspan=3, padx=4, sticky="w")
        ttk.Label(form, text="Monto (Gs.)").grid(row=1, column=4, sticky="e")
        ttk.Entry(form, textvariable=self.f["monto"], width=14).grid(row=1, column=5, padx=4, sticky="w")
        acciones = ttk.Frame(form)
        acciones.grid(row=2, column=0, columnspan=6, sticky="e", pady=(6, 0))
        ttk.Button(acciones, text="Registrar", command=self.registrar).pack(side="left", padx=4)
        ttk.Button(acciones, text="Eliminar seleccionado", style="Secundario.TButton",
                   command=self.eliminar).pack(side="left")

        marco, self.tv = tabla(izq, [("fecha", "Fecha", 90), ("tipo", "Tipo", 70), ("cat", "Categoría", 130),
                                     ("desc", "Descripción", 200), ("monto", "Monto (Gs.)", 110, "e"),
                                     ("origen", "Origen", 80)], alto=10)
        marco.pack(fill="both", expand=True, pady=(8, 0))
        ttk.Label(izq, text="Los cobros de servicios y las compras de insumos se registran solos. "
                            "Solo se pueden eliminar los movimientos manuales.", style="TLabel").pack(anchor="w", pady=(4, 0))

        # --- gráficos ---
        g1 = ttk.LabelFrame(der, text="Ingresos vs egresos (últimos 6 meses)", padding=6)
        g1.pack(fill="both", expand=True)
        self.cv_mes = tk.Canvas(g1, height=210, bg=tema.BLANCO, highlightthickness=0)
        self.cv_mes.pack(fill="both", expand=True)
        self.cv_mes.bind("<Configure>", lambda _e: self.grafico_mensual())
        g2 = ttk.LabelFrame(der, text="Egresos por categoría (período)", padding=6)
        g2.pack(fill="both", expand=True, pady=(8, 0))
        self.cv_cat = tk.Canvas(g2, height=190, bg=tema.BLANCO, highlightthickness=0)
        self.cv_cat.pack(fill="both", expand=True)
        self._mensual = []
        self.actualizar()

    def refrescar(self):
        self.actualizar()

    def cambiar_tipo(self, _e=None):
        self.cb_cat["values"] = CATEGORIAS[self.f["tipo"].get()]
        self.f["categoria"].set(CATEGORIAS[self.f["tipo"].get()][0])

    def _rango(self):
        try:
            return date.fromisoformat(self.desde.get()), date.fromisoformat(self.hasta.get())
        except ValueError:
            messagebox.showwarning("Fechas inválidas", "Use el formato AAAA-MM-DD.")
            return None

    def actualizar(self):
        rango = self._rango()
        if not rango:
            return
        d, h = rango
        b = db.balance(d, h)
        ing, egr = float(b["ingresos"]), float(b["egresos"])
        self.cifras["ing"].config(text=gs(ing))
        self.cifras["egr"].config(text=gs(egr))
        self.cifras["bal"].config(text=gs(ing - egr))
        self.movs = db.movimientos_listar(d, h)
        llenar(self.tv, [(m["id"], (m["fecha"].strftime("%d/%m/%Y"), m["tipo"].title(), m["categoria"],
                                    m["descripcion"] or "", gs(m["monto"], False), m["origen"].title()),
                          "alerta" if m["tipo"] == "EGRESO" else "") for m in self.movs])
        barras(self.cv_cat, [(r["categoria"], r["total"]) for r in db.balance_por_categoria(d, h, "EGRESO")],
               gs, tema.CELESTE)
        self._mensual = db.balance_mensual(6)
        self.grafico_mensual()

    def grafico_mensual(self):
        c = self.cv_mes
        c.delete("all")
        w, h = max(c.winfo_width(), 380), max(c.winfo_height(), 200)
        maximo = max([v for _, i, e in self._mensual for v in (i, e)] + [1])
        base, tope = h - 32, 26
        grupo = (w - 30) / max(len(self._mensual), 1)
        c.create_text(6, 8, anchor="w", text=f"Máximo: {gs(maximo)}", fill=tema.GRIS, font=(tema.FUENTE, 8))
        c.create_line(24, base, w - 6, base, fill=tema.CELESTE)
        for i, (mes, ing, egr) in enumerate(self._mensual):
            x0 = 24 + i * grupo
            for j, (valor, color) in enumerate([(ing, tema.AZUL), (egr, tema.CELESTE)]):
                alto = (base - tope) * valor / maximo
                xa = x0 + 6 + j * (grupo / 2 - 4)
                c.create_rectangle(xa, base - alto, xa + grupo / 2 - 8, base, fill=color, outline="")
            c.create_text(x0 + grupo / 2, base + 12, text=f"{mes[5:]}/{mes[2:4]}", fill=tema.AZUL_OSCURO,
                          font=(tema.FUENTE, 8))
        c.create_rectangle(w - 150, 6, w - 140, 16, fill=tema.AZUL, outline="")
        c.create_text(w - 136, 11, anchor="w", text="Ingresos", font=(tema.FUENTE, 8), fill=tema.AZUL_OSCURO)
        c.create_rectangle(w - 78, 6, w - 68, 16, fill=tema.CELESTE, outline="")
        c.create_text(w - 64, 11, anchor="w", text="Egresos", font=(tema.FUENTE, 8), fill=tema.AZUL_OSCURO)

    def registrar(self):
        try:
            fecha = date.fromisoformat(self.f["fecha"].get())
        except ValueError:
            return messagebox.showwarning("Fecha inválida", "Use el formato AAAA-MM-DD.")
        try:
            monto = a_entero(self.f["monto"].get())
        except ValueError as e:
            return messagebox.showwarning("Monto inválido", str(e))
        categoria = self.f["categoria"].get().strip()
        if monto <= 0 or not categoria:
            return messagebox.showwarning("Datos incompletos", "Indique una categoría y un monto mayor que cero.")
        db.movimiento_agregar(fecha, self.f["tipo"].get(), categoria, self.f["descripcion"].get().strip(), monto)
        self.f["descripcion"].set("")
        self.f["monto"].set("")
        self.actualizar()

    def eliminar(self):
        mid = seleccionado(self.tv)
        if mid is None:
            return messagebox.showinfo("Seleccione un movimiento", "Elija una fila de la tabla.")
        mov = next((m for m in self.movs if m["id"] == mid), None)
        if mov and mov["origen"] != "MANUAL":
            return messagebox.showinfo("No se puede eliminar", "Los cobros y las compras de insumos no se borran aquí.")
        if messagebox.askyesno("Confirmar", "¿Eliminar este movimiento?"):
            db.movimiento_eliminar(mid)
            self.actualizar()

    def exportar(self):
        if not self.movs:
            return messagebox.showinfo("Sin datos", "No hay movimientos en el período.")
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")],
                                            initialfile="movimientos.csv")
        if ruta:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["fecha", "tipo", "categoria", "descripcion", "monto", "origen"])
                w.writerows([[m["fecha"].isoformat(), m["tipo"], m["categoria"], m["descripcion"] or "",
                              int(m["monto"]), m["origen"]] for m in self.movs])
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{ruta}")

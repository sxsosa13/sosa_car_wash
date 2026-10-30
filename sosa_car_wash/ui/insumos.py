import tkinter as tk
from tkinter import ttk, messagebox

from database import db
from formato import gs
from ui.utils import tabla, llenar, seleccionado, a_entero, a_numero, pedir_datos

UNIDADES = ["unidad", "litro", "kg", "galón", "caja"]


class InsumosTab(ttk.Frame):
    """Inventario de insumos: stock, compras (generan egreso) y consumos."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.iid = None
        self.v = {"nombre": tk.StringVar(), "unidad": tk.StringVar(value="unidad"),
                  "minimo": tk.StringVar(value="0"), "costo": tk.StringVar(value="0")}
        f = ttk.LabelFrame(self, text="Insumo", padding=8)
        f.pack(fill="x")
        ttk.Label(f, text="Nombre").pack(side="left")
        ttk.Entry(f, textvariable=self.v["nombre"], width=26).pack(side="left", padx=4)
        ttk.Label(f, text="Unidad").pack(side="left", padx=(8, 0))
        ttk.Combobox(f, textvariable=self.v["unidad"], values=UNIDADES, width=9).pack(side="left", padx=4)
        ttk.Label(f, text="Stock mínimo").pack(side="left", padx=(8, 0))
        ttk.Entry(f, textvariable=self.v["minimo"], width=7).pack(side="left", padx=4)
        ttk.Label(f, text="Costo unitario (Gs.)").pack(side="left", padx=(8, 0))
        ttk.Entry(f, textvariable=self.v["costo"], width=11).pack(side="left", padx=4)
        ttk.Button(f, text="Guardar", command=self.guardar).pack(side="left", padx=4)
        ttk.Button(f, text="Nuevo", style="Secundario.TButton", command=self.nuevo).pack(side="left")

        acc = ttk.Frame(self)
        acc.pack(fill="x", pady=8)
        ttk.Button(acc, text="Registrar compra (entrada)", command=self.compra).pack(side="left")
        ttk.Button(acc, text="Registrar consumo (salida)", style="Secundario.TButton",
                   command=self.consumo).pack(side="left", padx=6)
        self.lbl = ttk.Label(acc, text="")
        self.lbl.pack(side="right")

        marco, self.tv = tabla(self, [("nombre", "Insumo", 230), ("stock", "Stock", 100, "e"),
                                      ("unidad", "Unidad", 80), ("minimo", "Mínimo", 80, "e"),
                                      ("costo", "Costo unit. (Gs.)", 130, "e"), ("valor", "Valor en stock (Gs.)", 150, "e"),
                                      ("estado", "Estado", 100)], alto=9)
        marco.pack(fill="both", expand=True)
        self.tv.bind("<<TreeviewSelect>>", self.al_seleccionar)

        h = ttk.LabelFrame(self, text="Últimos movimientos del insumo seleccionado", padding=6)
        h.pack(fill="both", expand=True, pady=(8, 0))
        marco2, self.th = tabla(h, [("fecha", "Fecha", 140), ("tipo", "Tipo", 90), ("cantidad", "Cantidad", 90, "e"),
                                    ("costo", "Costo total (Gs.)", 140, "e"), ("nota", "Nota", 300)], alto=5)
        marco2.pack(fill="both", expand=True)
        self.cargar()

    def refrescar(self):
        self.cargar()

    def cargar(self):
        filas = db.insumos_listar()
        llenar(self.tv, [(r["id"], (r["nombre"], f"{float(r['stock']):g}", r["unidad"], f"{float(r['stock_minimo']):g}",
                                    gs(r["costo_unitario"], False), gs(float(r["stock"]) * float(r["costo_unitario"]), False),
                                    "STOCK BAJO" if r["stock"] <= r["stock_minimo"] else "OK"),
                          "alerta" if r["stock"] <= r["stock_minimo"] else "") for r in filas])
        bajos = sum(1 for r in filas if r["stock"] <= r["stock_minimo"])
        valor = sum(float(r["stock"]) * float(r["costo_unitario"]) for r in filas)
        self.lbl.config(text=f"{bajos} con stock bajo · Valor del inventario: {gs(valor)}")
        if self.iid and self.tv.exists(str(self.iid)):
            self.tv.selection_set(str(self.iid))

    def nuevo(self):
        self.iid = None
        for k, val in (("nombre", ""), ("unidad", "unidad"), ("minimo", "0"), ("costo", "0")):
            self.v[k].set(val)
        self.tv.selection_remove(self.tv.selection())
        llenar(self.th, [])

    def al_seleccionar(self, _e=None):
        iid = seleccionado(self.tv)
        if iid is None:
            return
        self.iid = iid
        r = db.consultar("SELECT * FROM insumos WHERE id = %s", (iid,))[0]
        self.v["nombre"].set(r["nombre"])
        self.v["unidad"].set(r["unidad"])
        self.v["minimo"].set(f"{float(r['stock_minimo']):g}")
        self.v["costo"].set(gs(r["costo_unitario"], False))
        llenar(self.th, [(i, (h["fecha"].strftime("%d/%m/%Y %H:%M"), h["tipo"].title(), f"{float(h['cantidad']):g}",
                              gs(h["costo_total"], False), h["nota"] or "")) for i, h in enumerate(db.insumo_historial(iid))])

    def guardar(self):
        try:
            nombre = self.v["nombre"].get().strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio.")
            minimo = a_numero(self.v["minimo"].get())
            costo = a_entero(self.v["costo"].get())
        except ValueError as e:
            return messagebox.showwarning("Datos inválidos", str(e))
        try:
            self.iid = db.insumo_guardar(self.iid, nombre, self.v["unidad"].get().strip() or "unidad", minimo, costo)
        except Exception as e:
            return messagebox.showerror("No se pudo guardar", f"Revise que el nombre no esté repetido.\n{db.mensaje_error(e)}")
        self.cargar()

    def _movimiento(self, tipo, campos, titulo):
        if self.iid is None:
            return messagebox.showinfo("Seleccione un insumo", "Elija un insumo de la lista.")
        datos = pedir_datos(self, titulo, campos)
        if not datos:
            return
        try:
            cantidad = a_numero(datos["cantidad"])
            costo = a_entero(datos["costo"]) if datos.get("costo") else 0
            db.insumo_movimiento(self.iid, tipo, cantidad, costo, datos.get("nota", ""))
        except ValueError as e:
            return messagebox.showwarning("No se pudo registrar", str(e))
        except Exception as e:
            return messagebox.showerror("Error", db.mensaje_error(e))
        self.cargar()
        self.al_seleccionar()

    def compra(self):
        self._movimiento("COMPRA", [("cantidad", "Cantidad comprada", ""), ("costo", "Costo total (Gs.)", ""),
                                    ("nota", "Proveedor / nota", "")], "Registrar compra")

    def consumo(self):
        self._movimiento("CONSUMO", [("cantidad", "Cantidad consumida", ""), ("nota", "Motivo / nota", "")],
                         "Registrar consumo")

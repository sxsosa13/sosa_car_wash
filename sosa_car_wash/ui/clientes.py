import tkinter as tk
from tkinter import ttk, messagebox

import psycopg2
import psycopg2.errors

from database import db
from ui.utils import tabla, llenar, seleccionado


class ClientesTab(ttk.Frame):
    """Clientes (arriba) y sus vehículos (abajo)."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self.cliente_id = None
        self.v = {k: tk.StringVar() for k in ("nombre", "documento", "telefono", "email", "buscar")}
        self.vv = {k: tk.StringVar() for k in ("tipo", "placa", "marca", "modelo", "color")}
        self.vv["tipo"].set("AUTO")
        self._armar()
        self.cargar()

    def refrescar(self):
        self.cargar()

    def _armar(self):
        f = ttk.LabelFrame(self, text="Cliente", padding=8)
        f.pack(fill="x")
        for i, (txt, k, ancho) in enumerate([("Nombre", "nombre", 22), ("CI / RUC", "documento", 14),
                                             ("Teléfono", "telefono", 14), ("Email", "email", 22)]):
            ttk.Label(f, text=txt).grid(row=0, column=i * 2, padx=4)
            ttk.Entry(f, textvariable=self.v[k], width=ancho).grid(row=0, column=i * 2 + 1, padx=4)
        botones = ttk.Frame(f)
        botones.grid(row=1, column=0, columnspan=8, sticky="e", pady=(8, 0))
        ttk.Button(botones, text="Guardar", command=self.guardar).pack(side="left", padx=4)
        ttk.Button(botones, text="Nuevo", style="Secundario.TButton", command=self.nuevo).pack(side="left", padx=4)
        ttk.Button(botones, text="Eliminar", style="Secundario.TButton", command=self.eliminar).pack(side="left", padx=4)

        b = ttk.Frame(self)
        b.pack(fill="x", pady=6)
        ttk.Label(b, text="Buscar:").pack(side="left")
        e = ttk.Entry(b, textvariable=self.v["buscar"], width=30)
        e.pack(side="left", padx=4)
        e.bind("<KeyRelease>", lambda _e: self.cargar())

        marco, self.tv = tabla(self, [("id", "ID", 50), ("nombre", "Nombre", 220), ("documento", "CI / RUC", 110),
                                      ("telefono", "Teléfono", 120), ("email", "Email", 220)], alto=7)
        marco.pack(fill="both", expand=True)
        self.tv.bind("<<TreeviewSelect>>", self.al_seleccionar)

        g = ttk.LabelFrame(self, text="Vehículos del cliente seleccionado", padding=8)
        g.pack(fill="both", expand=True, pady=(8, 0))
        fila = ttk.Frame(g)
        fila.pack(fill="x")
        ttk.Label(fila, text="Tipo").pack(side="left")
        ttk.Combobox(fila, textvariable=self.vv["tipo"], values=["AUTO", "MOTO"], width=7,
                     state="readonly").pack(side="left", padx=4)
        for txt, k in [("Placa", "placa"), ("Marca", "marca"), ("Modelo", "modelo"), ("Color", "color")]:
            ttk.Label(fila, text=txt).pack(side="left", padx=(6, 0))
            ttk.Entry(fila, textvariable=self.vv[k], width=12).pack(side="left", padx=4)
        ttk.Button(fila, text="Agregar", command=self.agregar_vehiculo).pack(side="left", padx=4)
        ttk.Button(fila, text="Quitar", style="Secundario.TButton", command=self.quitar_vehiculo).pack(side="left")
        marco2, self.tvv = tabla(g, [("tipo", "Tipo", 70), ("placa", "Placa", 110), ("marca", "Marca", 150),
                                     ("modelo", "Modelo", 150), ("color", "Color", 110)], alto=5)
        marco2.pack(fill="both", expand=True, pady=(6, 0))

    # ----- clientes -----
    def cargar(self):
        t = f"%{self.v['buscar'].get().strip()}%"
        filas = db.consultar("SELECT * FROM clientes WHERE nombre ILIKE %s OR telefono ILIKE %s "
                             "OR COALESCE(documento, '') ILIKE %s ORDER BY nombre", (t, t, t))
        llenar(self.tv, [(r["id"], (r["id"], r["nombre"], r["documento"] or "", r["telefono"], r["email"] or ""))
                         for r in filas])

    def nuevo(self):
        self.cliente_id = None
        for k in ("nombre", "documento", "telefono", "email"):
            self.v[k].set("")
        self.tv.selection_remove(self.tv.selection())
        llenar(self.tvv, [])

    def al_seleccionar(self, _e=None):
        cid = seleccionado(self.tv)
        if cid is None:
            return
        self.cliente_id = cid
        r = db.consultar("SELECT * FROM clientes WHERE id = %s", (cid,))[0]
        self.v["nombre"].set(r["nombre"])
        self.v["documento"].set(r["documento"] or "")
        self.v["telefono"].set(r["telefono"])
        self.v["email"].set(r["email"] or "")
        self.cargar_vehiculos()

    def guardar(self):
        n, d, t, e = (self.v[k].get().strip() for k in ("nombre", "documento", "telefono", "email"))
        if not n or not t:
            return messagebox.showwarning("Datos incompletos", "Nombre y teléfono son obligatorios.")
        if self.cliente_id:
            db.ejecutar("UPDATE clientes SET nombre=%s, documento=%s, telefono=%s, email=%s WHERE id=%s",
                        (n, d or None, t, e or None, self.cliente_id))
        else:
            self.cliente_id = db.ejecutar("INSERT INTO clientes (nombre, documento, telefono, email) "
                                          "VALUES (%s, %s, %s, %s) RETURNING id", (n, d or None, t, e or None))
        self.cargar()
        if self.tv.exists(str(self.cliente_id)):
            self.tv.selection_set(str(self.cliente_id))

    def eliminar(self):
        if not self.cliente_id:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar el cliente y sus vehículos?"):
            try:
                db.ejecutar("DELETE FROM clientes WHERE id = %s", (self.cliente_id,))
            except psycopg2.IntegrityError:
                return messagebox.showerror("No se puede eliminar", "El cliente tiene citas registradas.")
            self.nuevo()
            self.cargar()

    # ----- vehículos -----
    def cargar_vehiculos(self):
        filas = db.consultar("SELECT * FROM vehiculos WHERE cliente_id = %s ORDER BY placa", (self.cliente_id,))
        llenar(self.tvv, [(r["id"], (r["tipo"], r["placa"], r["marca"] or "", r["modelo"] or "",
                                     r["color"] or "")) for r in filas])

    def agregar_vehiculo(self):
        if not self.cliente_id:
            return messagebox.showinfo("Seleccione un cliente", "Primero guarde o seleccione un cliente.")
        placa = self.vv["placa"].get().strip().upper()
        if not placa:
            return messagebox.showwarning("Datos incompletos", "La placa es obligatoria.")
        try:
            db.ejecutar("INSERT INTO vehiculos (cliente_id, tipo, placa, marca, modelo, color) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (self.cliente_id, self.vv["tipo"].get(), placa, self.vv["marca"].get() or None,
                         self.vv["modelo"].get() or None, self.vv["color"].get() or None))
        except psycopg2.errors.UniqueViolation:
            return messagebox.showerror("Placa duplicada", "Ya existe un vehículo con esa placa.")
        for k in ("placa", "marca", "modelo", "color"):
            self.vv[k].set("")
        self.cargar_vehiculos()

    def quitar_vehiculo(self):
        vid = seleccionado(self.tvv)
        if vid is None:
            return
        try:
            db.ejecutar("DELETE FROM vehiculos WHERE id = %s", (vid,))
        except psycopg2.IntegrityError:
            return messagebox.showerror("No se puede quitar", "El vehículo tiene citas registradas.")
        self.cargar_vehiculos()

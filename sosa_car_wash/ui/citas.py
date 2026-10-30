import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk, messagebox

from database import db
from formato import gs
from ui import comprobante, tema
from ui.utils import tabla, llenar, seleccionado

ETIQUETAS = {"EN_PROCESO": "proceso", "COMPLETADA": "completada", "CANCELADA": "cancelada"}


class CitasTab(ttk.Frame):
    """Agendamiento, agenda del día, estados, cobro con descuento y comprobante."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        hoy = date.today().isoformat()
        self.fecha_ver = tk.StringVar(value=hoy)
        self.veh, self.srv, self.hora, self.obs = (tk.StringVar() for _ in range(4))
        self.fecha = tk.StringVar(value=hoy)
        self.mapa_veh, self.mapa_srv = {}, {}
        self._armar()
        self.refrescar()

    def _armar(self):
        f = ttk.LabelFrame(self, text="Agendar servicio", padding=8)
        f.pack(fill="x")
        ttk.Label(f, text="Vehículo").grid(row=0, column=0, sticky="e")
        self.cb_veh = ttk.Combobox(f, textvariable=self.veh, width=42, state="readonly")
        self.cb_veh.grid(row=0, column=1, padx=4, pady=3)
        self.cb_veh.bind("<<ComboboxSelected>>", self.filtrar_servicios)
        ttk.Label(f, text="Servicio").grid(row=0, column=2, sticky="e")
        self.cb_srv = ttk.Combobox(f, textvariable=self.srv, width=40, state="readonly")
        self.cb_srv.grid(row=0, column=3, padx=4)

        ttk.Label(f, text="Fecha (AAAA-MM-DD)").grid(row=1, column=0, sticky="e")
        e = ttk.Entry(f, textvariable=self.fecha, width=14)
        e.grid(row=1, column=1, sticky="w", padx=4)
        e.bind("<FocusOut>", self.actualizar_horas)
        e.bind("<Return>", self.actualizar_horas)
        ttk.Label(f, text="Hora").grid(row=1, column=2, sticky="e")
        self.cb_hora = ttk.Combobox(f, textvariable=self.hora, width=10, state="readonly")
        self.cb_hora.grid(row=1, column=3, sticky="w", padx=4)
        ttk.Label(f, text="Observación").grid(row=2, column=0, sticky="e")
        ttk.Entry(f, textvariable=self.obs, width=45).grid(row=2, column=1, padx=4, pady=3, sticky="w")
        ttk.Button(f, text="Agendar", command=self.agendar).grid(row=2, column=3, sticky="e", padx=4)

        b = ttk.Frame(self)
        b.pack(fill="x", pady=8)
        ttk.Label(b, text="Agenda del día:", style="Sub.TLabel").pack(side="left")
        ttk.Button(b, text="◀", width=3, command=lambda: self.mover(-1)).pack(side="left", padx=(8, 2))
        ttk.Entry(b, textvariable=self.fecha_ver, width=12).pack(side="left")
        ttk.Button(b, text="▶", width=3, command=lambda: self.mover(1)).pack(side="left", padx=2)
        ttk.Button(b, text="Ver", command=self.cargar).pack(side="left", padx=4)
        ttk.Button(b, text="Hoy", style="Secundario.TButton", command=self.hoy).pack(side="left")
        self.lbl = ttk.Label(b, text="")
        self.lbl.pack(side="right")

        marco, self.tv = tabla(self, [("hora", "Hora", 65), ("cliente", "Cliente", 180), ("placa", "Placa", 90),
                                      ("servicio", "Servicio", 220), ("precio", "Precio (Gs.)", 100, "e"),
                                      ("estado", "Estado", 100), ("origen", "Origen", 90)], alto=10)
        marco.pack(fill="both", expand=True)
        a = ttk.Frame(self)
        a.pack(fill="x", pady=8)
        ttk.Button(a, text="Iniciar lavado", command=lambda: self.cambiar_estado("EN_PROCESO")).pack(side="left")
        ttk.Button(a, text="Cobrar y completar", command=self.cobrar).pack(side="left", padx=6)
        ttk.Button(a, text="Ver comprobante", style="Secundario.TButton", command=self.ver_comprobante).pack(side="left")
        ttk.Button(a, text="Cancelar cita", style="Secundario.TButton",
                   command=lambda: self.cambiar_estado("CANCELADA")).pack(side="left", padx=6)

    def refrescar(self):
        self.refrescar_combos()
        self.actualizar_horas()
        self.cargar()

    # ----- formulario -----
    def refrescar_combos(self):
        filas = db.consultar("SELECT v.id, v.placa, v.tipo, c.nombre FROM vehiculos v "
                             "JOIN clientes c ON c.id = v.cliente_id ORDER BY v.placa")
        self.mapa_veh = {f"{r['placa']} · {r['nombre']} ({r['tipo']})": (r["id"], r["tipo"]) for r in filas}
        self.cb_veh["values"] = list(self.mapa_veh)

    def filtrar_servicios(self, _e=None):
        info = self.mapa_veh.get(self.veh.get())
        if not info:
            return
        filas = db.consultar("SELECT id, nombre, precio FROM servicios WHERE activo AND tipo_vehiculo = %s "
                             "ORDER BY precio", (info[1],))
        self.mapa_srv = {f"{r['nombre']} — {gs(r['precio'])}": r["id"] for r in filas}
        self.cb_srv["values"] = list(self.mapa_srv)
        self.srv.set("")

    def actualizar_horas(self, _e=None):
        try:
            self.cb_hora["values"] = db.horarios_disponibles(self.fecha.get())
        except ValueError:
            self.cb_hora["values"] = []
        self.hora.set("")

    def agendar(self):
        info, sid = self.mapa_veh.get(self.veh.get()), self.mapa_srv.get(self.srv.get())
        if not (info and sid and self.hora.get()):
            return messagebox.showwarning("Datos incompletos", "Elija vehículo, servicio, fecha y hora.")
        try:
            n = db.crear_cita(info[0], sid, self.fecha.get(), self.hora.get(), "ESCRITORIO", self.obs.get())
        except ValueError as e:
            return messagebox.showerror("No se pudo agendar", str(e))
        messagebox.showinfo("Cita creada", f"Cita #{n} agendada correctamente.")
        self.obs.set("")
        self.fecha_ver.set(self.fecha.get())
        self.actualizar_horas()
        self.cargar()

    # ----- agenda -----
    def mover(self, dias):
        try:
            d = datetime.strptime(self.fecha_ver.get(), "%Y-%m-%d").date() + timedelta(days=dias)
        except ValueError:
            d = date.today()
        self.fecha_ver.set(d.isoformat())
        self.cargar()

    def hoy(self):
        self.fecha_ver.set(date.today().isoformat())
        self.cargar()

    def cargar(self):
        try:
            f = datetime.strptime(self.fecha_ver.get(), "%Y-%m-%d").date()
        except ValueError:
            return messagebox.showwarning("Fecha inválida", "Use el formato AAAA-MM-DD.")
        filas = db.consultar(
            "SELECT c.id, c.hora, cl.nombre, v.placa, s.nombre AS servicio, s.precio, c.estado, c.origen "
            "FROM citas c JOIN vehiculos v ON v.id = c.vehiculo_id JOIN clientes cl ON cl.id = v.cliente_id "
            "JOIN servicios s ON s.id = c.servicio_id WHERE c.fecha = %s ORDER BY c.hora, c.id", (f,))
        llenar(self.tv, [(r["id"], (r["hora"].strftime("%H:%M"), r["nombre"], r["placa"], r["servicio"],
                                    gs(r["precio"], False), r["estado"], r["origen"]),
                          ETIQUETAS.get(r["estado"], "")) for r in filas])
        activas = [r for r in filas if r["estado"] != "CANCELADA"]
        self.lbl.config(text=f"{len(activas)} citas activas · Ingreso esperado: {gs(sum(r['precio'] for r in activas))}")

    def _cita(self):
        cid = seleccionado(self.tv)
        if cid is None:
            messagebox.showinfo("Seleccione una cita", "Elija una cita de la lista.")
        return cid

    def cambiar_estado(self, nuevo):
        cid = self._cita()
        if cid is None:
            return
        db.ejecutar("UPDATE citas SET estado = %s WHERE id = %s AND estado NOT IN ('COMPLETADA','CANCELADA')",
                    (nuevo, cid))
        self.cargar()
        self.actualizar_horas()

    def ver_comprobante(self):
        cid = self._cita()
        if cid is None:
            return
        pago = db.pago_de_cita(cid)
        if not pago:
            return messagebox.showinfo("Sin comprobante", "Esta cita todavía no fue cobrada.")
        comprobante.abrir(pago)

    def cobrar(self):
        cid = self._cita()
        if cid is None:
            return
        estado = self.tv.set(str(cid), "estado")
        if estado in ("COMPLETADA", "CANCELADA"):
            return messagebox.showinfo("Cita cerrada", f"La cita ya está {estado.lower()}.")
        precio = float(db.consultar("SELECT s.precio FROM citas c JOIN servicios s ON s.id = c.servicio_id "
                                    "WHERE c.id = %s", (cid,))[0]["precio"])
        top = tk.Toplevel(self)
        top.title("Cobro")
        top.configure(bg=tema.CELESTE_CLARO)
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()
        m = ttk.Frame(top, padding=20)
        m.pack()
        metodo, desc = tk.StringVar(value="EFECTIVO"), tk.StringVar(value="0")
        ttk.Label(m, text="Subtotal").grid(row=0, column=0, sticky="e", pady=4, padx=(0, 8))
        ttk.Label(m, text=gs(precio), style="Sub.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(m, text="Descuento (%)").grid(row=1, column=0, sticky="e", pady=4, padx=(0, 8))
        ttk.Entry(m, textvariable=desc, width=8).grid(row=1, column=1, sticky="w")
        ttk.Label(m, text="Método de pago").grid(row=2, column=0, sticky="e", pady=4, padx=(0, 8))
        ttk.Combobox(m, textvariable=metodo, values=["EFECTIVO", "TARJETA", "TRANSFERENCIA"], state="readonly",
                     width=18).grid(row=2, column=1, sticky="w")
        ttk.Label(m, text="TOTAL A COBRAR").grid(row=3, column=0, sticky="e", pady=(12, 0), padx=(0, 8))
        total = ttk.Label(m, text=gs(precio), style="Titulo.TLabel")
        total.grid(row=3, column=1, sticky="w", pady=(12, 0))

        def porcentaje():
            try:
                return min(max(float(desc.get().replace(",", ".") or 0), 0), 100)
            except ValueError:
                return 0

        desc.trace_add("write", lambda *_: total.config(text=gs(precio - round(precio * porcentaje() / 100))))

        def confirmar():
            try:
                pct = float(desc.get().replace(",", ".") or 0)
            except ValueError:
                return messagebox.showwarning("Descuento inválido", "Escriba un número entre 0 y 100.", parent=top)
            try:
                r = db.cobrar_cita(cid, metodo.get(), pct)
            except Exception as e:
                return messagebox.showerror("No se pudo cobrar", db.mensaje_error(e), parent=top)
            top.destroy()
            self.cargar()
            self.actualizar_horas()
            if messagebox.askyesno("Cobro registrado", f"Total cobrado: {gs(r['monto'])}\n\n"
                                                       "¿Abrir el comprobante para imprimirlo?"):
                comprobante.abrir(r["pago_id"])

        ttk.Button(m, text="Cobrar", command=confirmar).grid(row=4, columnspan=2, pady=(16, 0), sticky="ew")

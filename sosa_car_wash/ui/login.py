import tkinter as tk
from tkinter import ttk, messagebox

from config import NEGOCIO
from database import db
from ui import tema


class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{NEGOCIO['nombre']} · Ingreso")
        self.resizable(False, False)
        tema.aplicar(self)
        self.usuario = None
        self.u, self.p = tk.StringVar(), tk.StringVar()

        tema.cabecera(self, NEGOCIO["nombre"], NEGOCIO["eslogan"]).pack(fill="x")
        tarjeta = tk.Frame(self, bg=tema.BLANCO, highlightbackground=tema.CELESTE, highlightthickness=1,
                           padx=32, pady=24)
        tarjeta.pack(padx=40, pady=30)
        tk.Label(tarjeta, text="Iniciar sesión", bg=tema.BLANCO, fg=tema.AZUL,
                 font=(tema.FUENTE, 15, "bold")).grid(columnspan=2, pady=(0, 14))
        for fila, (txt, var, oculto) in enumerate([("Usuario", self.u, ""), ("Contraseña", self.p, "•")], start=1):
            tk.Label(tarjeta, text=txt, bg=tema.BLANCO, fg=tema.AZUL_OSCURO).grid(row=fila, column=0, sticky="e",
                                                                                   pady=6, padx=(0, 8))
            e = ttk.Entry(tarjeta, textvariable=var, show=oculto, width=26)
            e.grid(row=fila, column=1)
            if fila == 1:
                e.focus()
        ttk.Button(tarjeta, text="Ingresar", command=self.ingresar).grid(row=3, columnspan=2, pady=(18, 0), sticky="ew")
        self.bind("<Return>", lambda _e: self.ingresar())

    def ingresar(self):
        try:
            usuario = db.autenticar(self.u.get().strip(), self.p.get())
        except Exception as e:
            return messagebox.showerror("Error de conexión",
                                        f"No se pudo consultar la base de datos:\n{db.mensaje_error(e)}")
        if usuario:
            self.usuario = usuario
            self.destroy()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")

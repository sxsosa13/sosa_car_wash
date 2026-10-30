"""Sosa Car Wash · Sistema de gestión para lavadero de autos y motos.
Ejecutar:  python main.py
"""
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

from config import NEGOCIO, WEB_PORT
from database import db
from ui import comprobante, tema
from ui.citas import CitasTab
from ui.clientes import ClientesTab
from ui.finanzas import FinanzasTab
from ui.inicio import InicioTab
from ui.insumos import InsumosTab
from ui.login import Login
from ui.reportes import ReportesTab
from ui.servicios import ServiciosTab
from web import server


class App(tk.Tk):
    def __init__(self, usuario):
        super().__init__()
        self.title(f"{NEGOCIO['nombre']} · Gestión de lavadero")
        self.geometry("1180x780")
        self.minsize(1020, 680)
        tema.aplicar(self)
        self.servidor = None

        menu = tk.Menu(self)
        archivo = tk.Menu(menu, tearoff=0)
        archivo.add_command(label="Abrir página web", command=self.abrir_web)
        archivo.add_command(label="Iniciar servidor web", command=self.iniciar_web)
        archivo.add_command(label="Abrir carpeta de comprobantes", command=comprobante.abrir_carpeta)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)
        menu.add_cascade(label="Archivo", menu=archivo)
        self.config(menu=menu)

        tema.cabecera(self, NEGOCIO["nombre"], NEGOCIO["eslogan"],
                      f"{usuario['nombre']} · {usuario['rol']}").pack(fill="x")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        admin = usuario["rol"] == "ADMIN"
        pestanas = [(InicioTab(self.nb, usuario), "Inicio"), (CitasTab(self.nb), "Agenda"),
                    (ClientesTab(self.nb), "Clientes y vehículos"), (InsumosTab(self.nb), "Insumos")]
        if admin:
            pestanas += [(ServiciosTab(self.nb), "Servicios"), (FinanzasTab(self.nb), "Finanzas"),
                         (ReportesTab(self.nb), "Reportes")]
        for widget, texto in pestanas:
            self.nb.add(widget, text=f"  {texto}  ")
        self.nb.bind("<<NotebookTabChanged>>", self.al_cambiar_pestana)

    def al_cambiar_pestana(self, _e=None):
        """Al entrar a una pestaña se recargan sus datos (incluye reservas hechas desde la web)."""
        try:
            widget = self.nb.nametowidget(self.nb.select())
            if hasattr(widget, "refrescar"):
                widget.refrescar()
        except Exception as e:
            messagebox.showerror("Error", db.mensaje_error(e))

    def iniciar_web(self):
        if self.servidor:
            return messagebox.showinfo("Servidor web", f"Ya está activo en http://localhost:{WEB_PORT}")
        try:
            self.servidor = server.iniciar_en_hilo()
        except OSError as e:
            return messagebox.showerror("Servidor web", f"No se pudo iniciar (¿puerto ocupado?):\n{e}")
        messagebox.showinfo("Servidor web", f"Página activa en http://localhost:{WEB_PORT}")

    def abrir_web(self):
        if not self.servidor:
            try:
                self.servidor = server.iniciar_en_hilo()
            except OSError as e:
                return messagebox.showerror("Servidor web", f"No se pudo iniciar (¿puerto ocupado?):\n{e}")
        webbrowser.open(f"http://localhost:{WEB_PORT}")


def main():
    try:
        db.inicializar()
    except Exception as e:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("Base de datos", f"No se pudo conectar a PostgreSQL:\n\n{db.mensaje_error(e)}\n\n"
                                              "Ejecute primero «Configurar base de datos» (configurar_bd.py) y revise "
                                              "que el servicio de PostgreSQL esté iniciado.")
        return
    login = Login()
    login.mainloop()
    if login.usuario:
        App(login.usuario).mainloop()


if __name__ == "__main__":
    main()

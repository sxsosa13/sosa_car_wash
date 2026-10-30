"""Tema visual de Sosa Car Wash: azul, celeste y blanco."""
import tkinter as tk
from tkinter import ttk

AZUL_OSCURO = "#0B2A57"
AZUL = "#1565C0"
AZUL_MEDIO = "#1E88E5"
CELESTE = "#4FC3F7"
CELESTE_SUAVE = "#B3E5FC"
CELESTE_CLARO = "#E3F2FD"
BLANCO = "#FFFFFF"
GRIS = "#5B7186"
FUENTE = "Segoe UI"


def aplicar(root):
    root.configure(bg=CELESTE_CLARO)
    root.option_add("*TCombobox*Listbox.background", BLANCO)
    root.option_add("*TCombobox*Listbox.foreground", AZUL_OSCURO)
    root.option_add("*TCombobox*Listbox.selectBackground", AZUL_MEDIO)
    root.option_add("*TCombobox*Listbox.selectForeground", BLANCO)
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=CELESTE_CLARO, foreground=AZUL_OSCURO, font=(FUENTE, 10))
    s.configure("TFrame", background=CELESTE_CLARO)
    s.configure("TLabel", background=CELESTE_CLARO, foreground=AZUL_OSCURO)
    s.configure("TLabelframe", background=CELESTE_CLARO, bordercolor=CELESTE, relief="solid")
    s.configure("TLabelframe.Label", background=CELESTE_CLARO, foreground=AZUL, font=(FUENTE, 10, "bold"))
    s.configure("TButton", background=AZUL, foreground=BLANCO, padding=(12, 6), borderwidth=0,
                focusthickness=0, font=(FUENTE, 10, "bold"))
    s.map("TButton", background=[("active", AZUL_MEDIO), ("pressed", AZUL_OSCURO)])
    s.configure("Secundario.TButton", background=CELESTE, foreground=AZUL_OSCURO)
    s.map("Secundario.TButton", background=[("active", CELESTE_SUAVE), ("pressed", CELESTE)])
    s.configure("TEntry", fieldbackground=BLANCO, padding=5, bordercolor=CELESTE, lightcolor=CELESTE,
                darkcolor=CELESTE)
    s.configure("TCombobox", fieldbackground=BLANCO, padding=4, bordercolor=CELESTE, arrowcolor=AZUL)
    s.configure("TNotebook", background=CELESTE_CLARO, borderwidth=0)
    s.configure("TNotebook.Tab", background=CELESTE_SUAVE, foreground=AZUL_OSCURO, padding=(16, 8),
                font=(FUENTE, 10, "bold"))
    s.map("TNotebook.Tab", background=[("selected", AZUL)], foreground=[("selected", BLANCO)])
    s.configure("Treeview", background=BLANCO, fieldbackground=BLANCO, rowheight=26, bordercolor=CELESTE,
                foreground=AZUL_OSCURO)
    s.configure("Treeview.Heading", background=AZUL, foreground=BLANCO, font=(FUENTE, 10, "bold"),
                padding=6, relief="flat")
    s.map("Treeview.Heading", background=[("active", AZUL_MEDIO)])
    s.map("Treeview", background=[("selected", AZUL_MEDIO)], foreground=[("selected", BLANCO)])
    s.configure("Vertical.TScrollbar", background=CELESTE, troughcolor=CELESTE_CLARO, bordercolor=CELESTE_CLARO,
                arrowcolor=AZUL)
    s.configure("Titulo.TLabel", font=(FUENTE, 18, "bold"), foreground=AZUL)
    s.configure("Sub.TLabel", font=(FUENTE, 12, "bold"), foreground=AZUL)
    s.configure("Cifra.TLabel", font=(FUENTE, 19, "bold"), foreground=AZUL, background=BLANCO)
    s.configure("Mini.TLabel", font=(FUENTE, 9), foreground=GRIS, background=BLANCO)


def logo(parent, tam=46, fondo=AZUL_OSCURO):
    """Logotipo: círculo celeste con una gota de agua blanca."""
    c = tk.Canvas(parent, width=tam, height=tam, bg=fondo, highlightthickness=0)
    c.create_oval(2, 2, tam - 2, tam - 2, fill=CELESTE, outline=BLANCO, width=2)
    p = [(.50, .16), (.70, .50), (.72, .62), (.62, .76), (.50, .80), (.38, .76), (.28, .62), (.30, .50)]
    c.create_polygon([v * tam for xy in p for v in xy], fill=BLANCO, outline="", smooth=True)
    return c


def cabecera(parent, nombre, eslogan, derecha=""):
    """Barra superior azul con logo y nombre del negocio."""
    barra = tk.Frame(parent, bg=AZUL_OSCURO)
    logo(barra).pack(side="left", padx=(14, 10), pady=8)
    bloque = tk.Frame(barra, bg=AZUL_OSCURO)
    bloque.pack(side="left")
    tk.Label(bloque, text=nombre.upper(), bg=AZUL_OSCURO, fg=BLANCO, font=(FUENTE, 17, "bold")).pack(anchor="w")
    tk.Label(bloque, text=eslogan, bg=AZUL_OSCURO, fg=CELESTE, font=(FUENTE, 9)).pack(anchor="w")
    etiqueta = tk.Label(barra, text=derecha, bg=AZUL_OSCURO, fg=CELESTE_SUAVE, font=(FUENTE, 10))
    etiqueta.pack(side="right", padx=16)
    return barra

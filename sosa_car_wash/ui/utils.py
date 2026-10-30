"""Utilidades de interfaz reutilizables."""
import tkinter as tk
from tkinter import ttk

from ui import tema


def tabla(parent, columnas, alto=10):
    """Treeview con scroll. columnas = [(clave, titulo, ancho[, anclaje]), ...]. Devuelve (marco, tree)."""
    marco = ttk.Frame(parent)
    tv = ttk.Treeview(marco, columns=[c[0] for c in columnas], show="headings", height=alto,
                      selectmode="browse")
    for col in columnas:
        clave, titulo, ancho = col[:3]
        tv.heading(clave, text=titulo)
        tv.column(clave, width=ancho, anchor=col[3] if len(col) > 3 else "w")
    tv.tag_configure("par", background="#F1F8FE")
    tv.tag_configure("proceso", background=tema.CELESTE_SUAVE)
    tv.tag_configure("completada", foreground=tema.AZUL)
    tv.tag_configure("cancelada", foreground="#90A4AE")
    tv.tag_configure("alerta", foreground="#C62828")
    sb = ttk.Scrollbar(marco, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return marco, tv


def llenar(tv, filas):
    """filas = [(id, (valores...)[, etiqueta]), ...]"""
    tv.delete(*tv.get_children())
    for i, fila in enumerate(filas):
        iid, valores = fila[0], fila[1]
        tag = fila[2] if len(fila) > 2 and fila[2] else ("par" if i % 2 else "")
        tv.insert("", "end", iid=str(iid), values=valores, tags=(tag,) if tag else ())


def seleccionado(tv):
    sel = tv.selection()
    return int(sel[0]) if sel else None


def tarjeta(parent, titulo):
    """Tarjeta blanca con un título pequeño y una cifra grande. Devuelve (marco, etiqueta_cifra)."""
    marco = tk.Frame(parent, bg=tema.BLANCO, highlightbackground=tema.CELESTE, highlightthickness=1,
                     padx=14, pady=10)
    ttk.Label(marco, text=titulo, style="Mini.TLabel").pack(anchor="w")
    cifra = ttk.Label(marco, text="—", style="Cifra.TLabel")
    cifra.pack(anchor="w")
    return marco, cifra


def a_entero(texto):
    """'150.000' -> 150000 (guaraníes: solo dígitos)."""
    digitos = "".join(ch for ch in str(texto) if ch.isdigit())
    if not digitos:
        raise ValueError("Ingrese un monto válido (solo números).")
    return int(digitos)


def a_numero(texto):
    """'2,5' -> 2.5"""
    try:
        return float(str(texto).strip().replace(",", "."))
    except ValueError:
        raise ValueError("Ingrese un número válido.")


def pedir_datos(parent, titulo, campos, texto_boton="Aceptar"):
    """Diálogo modal. campos = [(clave, etiqueta, valor_inicial)]. Devuelve dict o None si se cancela."""
    top = tk.Toplevel(parent)
    top.title(titulo)
    top.configure(bg=tema.CELESTE_CLARO)
    top.resizable(False, False)
    top.transient(parent.winfo_toplevel())
    top.grab_set()
    marco = ttk.Frame(top, padding=18)
    marco.pack()
    variables, resultado = {}, {}
    for i, (clave, etiqueta, inicial) in enumerate(campos):
        ttk.Label(marco, text=etiqueta).grid(row=i, column=0, sticky="e", pady=4, padx=(0, 8))
        variables[clave] = tk.StringVar(value=inicial)
        e = ttk.Entry(marco, textvariable=variables[clave], width=30)
        e.grid(row=i, column=1, pady=4)
        if i == 0:
            e.focus()

    def aceptar(_e=None):
        resultado.update({k: v.get().strip() for k, v in variables.items()})
        top.destroy()

    botones = ttk.Frame(marco)
    botones.grid(row=len(campos), columnspan=2, pady=(12, 0))
    ttk.Button(botones, text=texto_boton, command=aceptar).pack(side="left", padx=4)
    ttk.Button(botones, text="Cancelar", style="Secundario.TButton", command=top.destroy).pack(side="left", padx=4)
    top.bind("<Return>", aceptar)
    top.wait_window()
    return resultado or None


def barras(canvas, datos, formato=str, color=tema.AZUL_MEDIO):
    """Gráfico de barras horizontales. datos = [(etiqueta, valor), ...]. Se redibuja al cambiar de tamaño."""
    canvas._datos = (datos, formato, color)
    if not getattr(canvas, "_ligado", False):
        canvas.bind("<Configure>", lambda _e: _dibujar_barras(canvas))
        canvas._ligado = True
    _dibujar_barras(canvas)


def _dibujar_barras(c):
    datos, formato, color = c._datos
    c.delete("all")
    ancho = max(c.winfo_width(), 380)
    if not datos:
        c.create_text(ancho // 2, 90, text="Sin datos en el período", fill=tema.GRIS, font=(tema.FUENTE, 10))
        return
    maximo = max(float(v) for _, v in datos) or 1
    inicio, reserva = 190, 120
    for i, (etiqueta, valor) in enumerate(datos[:10]):
        y = 12 + i * 34
        c.create_text(6, y + 11, anchor="w", text=str(etiqueta)[:26], fill=tema.AZUL_OSCURO, font=(tema.FUENTE, 9))
        largo = max(int((ancho - inicio - reserva) * float(valor) / maximo), 2)
        c.create_rectangle(inicio, y, inicio + largo, y + 22, fill=color, outline="")
        c.create_text(inicio + largo + 6, y + 11, anchor="w", text=formato(valor), fill=tema.AZUL_OSCURO,
                      font=(tema.FUENTE, 9, "bold"))

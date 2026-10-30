"""Crea la base de datos, las tablas y los datos iniciales (usa la conexión de config_local.json).
    python setup_db.py          -> estructura + usuarios, servicios e insumos iniciales
    python setup_db.py --demo   -> además carga clientes, citas, cobros e ingresos/egresos de ejemplo
"""
import os
import sys

from database import db

db.inicializar()
print("✔ Base de datos lista (tablas, usuarios, servicios e insumos iniciales).")

if "--demo" in sys.argv:
    if db.consultar("SELECT 1 FROM clientes LIMIT 1"):
        print("• Ya existen clientes; no se cargaron datos de ejemplo.")
    else:
        with open(os.path.join("sql", "datos_demo.sql"), encoding="utf-8") as f:
            db.ejecutar(f.read())
        db.sincronizar_pagos()
        print("✔ Datos de ejemplo cargados.")

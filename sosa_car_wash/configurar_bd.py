"""Asistente de primera vez: conecta con PostgreSQL, crea la base 'aquawash',
las tablas, los usuarios, los insumos y (opcional) datos de ejemplo. Todo desde VS Code.

    python configurar_bd.py
"""
import getpass
import json
import os
import sys

import psycopg2

AQUI = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(AQUI, "config_local.json")


def mensaje(e):
    # PostgreSQL en español devuelve tildes en cp1252; recuperamos el texto real
    if isinstance(e, UnicodeDecodeError):
        return e.object.decode("cp1252", errors="replace")
    return str(e)


def preguntar(texto, defecto):
    valor = input(f"{texto} [{defecto}]: ").strip()
    return valor or defecto


def main():
    print("=" * 56)
    print(" Sosa Car Wash · Configuración de la base de datos")
    print("=" * 56)
    print("Presione Enter para aceptar el valor entre corchetes.\n")
    try:
        cfg = {
            "host": preguntar("Servidor", "localhost"),
            "port": int(preguntar("Puerto", "5432")),
            "user": preguntar("Usuario de PostgreSQL", "postgres"),
            "dbname": preguntar("Nombre de la base a crear", "aquawash"),
        }
    except ValueError:
        print("✖ El puerto debe ser un número (normalmente 5432).")
        return 1
    cfg["password"] = getpass.getpass("Contraseña de PostgreSQL (no se muestra al escribir): ")

    print("\nProbando conexión…")
    try:
        con = psycopg2.connect(host=cfg["host"], port=cfg["port"], user=cfg["user"],
                               password=cfg["password"], dbname="postgres", connect_timeout=5)
        con.close()
    except Exception as e:
        print("\n✖ No se pudo conectar a PostgreSQL:\n  ", mensaje(e).strip())
        print("\nQué revisar:")
        print(" • 'autentificación' / 'password' -> la contraseña es incorrecta.")
        print(" • 'conexión rehusada' / 'refused' -> el servicio no está iniciado:")
        print("     Windows + R > services.msc > 'postgresql-x64-…' > Iniciar.")
        print(" • Puerto distinto de 5432 -> ejecute de nuevo e indique el puerto correcto.")
        print(" • Sin PostgreSQL instalado -> instálelo, o use Docker: docker compose up -d")
        return 1
    print("✔ Conexión correcta.")

    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"✔ Datos de conexión guardados en {os.path.basename(RUTA)}")

    sys.path.insert(0, AQUI)
    from database import db            # se importa ahora para leer la configuración nueva

    db.inicializar()
    print(f"✔ Base '{cfg['dbname']}' lista (tablas, usuarios, servicios e insumos; si ya existía, se actualizó sin perder datos).")

    if input("\n¿Cargar datos de ejemplo (clientes, vehículos, citas)? [S/n]: ").strip().lower() != "n":
        if db.consultar("SELECT 1 FROM clientes LIMIT 1"):
            print("• Ya hay clientes registrados; no se cargaron datos de ejemplo.")
        else:
            with open(os.path.join(AQUI, "sql", "datos_demo.sql"), encoding="utf-8") as f:
                db.ejecutar(f.read())
            db.sincronizar_pagos()
            print("✔ Datos de ejemplo cargados.")

    print("\nListo. Ahora:")
    print(" • Ejecute la aplicación con F5 > «Sosa Car Wash · 2) Aplicación de escritorio»")
    print(" • Vea y consulte la base en la barra lateral SQLTools (conexión «Sosa Car Wash (PostgreSQL)»)")
    print(" • Usuario del programa: admin / admin123")
    return 0


if __name__ == "__main__":
    sys.exit(main())

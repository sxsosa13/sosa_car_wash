"""Pone una contraseña nueva al usuario 'postgres' (PostgreSQL 9.3 o superior).

REQUISITO: que en pg_hba.conf las líneas 127.0.0.1/32 y ::1/128 estén en 'trust'
y el servicio reiniciado (así PostgreSQL deja entrar sin contraseña un momento).

    python restablecer_clave.py
"""
import sys

import psycopg2
from psycopg2 import sql


def mensaje(e):
    if isinstance(e, UnicodeDecodeError):
        return e.object.decode("cp1252", errors="replace")
    return str(e)


def main():
    usuario = input("Usuario a restablecer [postgres]: ").strip() or "postgres"
    puerto = int(input("Puerto [5432]: ").strip() or "5432")
    clave = input("Contraseña NUEVA (sin tildes, ñ ni espacios) [aquawash123]: ").strip() or "aquawash123"
    if not clave.isascii() or " " in clave:
        print("✖ Use solo letras, números y símbolos simples, sin tildes ni espacios.")
        return 1
    try:
        con = psycopg2.connect(host="localhost", port=puerto, user=usuario,
                               dbname="postgres", connect_timeout=5)
        con.autocommit = True
        with con.cursor() as cur:
            cur.execute(sql.SQL("ALTER USER {} PASSWORD {}").format(
                sql.Identifier(usuario), sql.Literal(clave)))
        con.close()
    except Exception as e:
        print("\n✖ No se pudo cambiar la contraseña:\n  ", mensaje(e).strip())
        print("\nSi dice 'autentificación' o 'no password supplied': pg_hba.conf todavía no está en")
        print("'trust' o falta reiniciar el servicio (Restart-Service -Name postgresql-9.3).")
        return 1
    print(f"\n✔ Contraseña de '{usuario}' cambiada a: {clave}")
    print("Ahora vuelva a poner 'md5' en pg_hba.conf, reinicie el servicio y ejecute:")
    print("    python configurar_bd.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())

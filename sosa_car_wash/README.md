# Sosa Car Wash · Sistema de gestión de lavadero de autos y motos

Python 3 · Tkinter · PostgreSQL (9.3 o superior) · Página web de reservas · Todo administrable desde Visual Studio Code

## Qué incluye
- **Escritorio (Tkinter), paleta azul / celeste / blanco:** Inicio (resumen del día), Agenda, Clientes y vehículos, Insumos, Servicios, Finanzas (ingresos, egresos y balance) y Reportes.
- **Moneda:** guaraníes (Gs.), sin decimales.
- **Cobro con descuento** y **comprobante imprimible** (se abre en el navegador: Ctrl+P).
- **Insumos:** stock, compras (generan un egreso automático) y consumos, con alerta de stock bajo.
- **Finanzas:** libro de ingresos y egresos, balance del período y gráfico de 6 meses.
- **Página web** con reservas en línea, seguimiento de la reserva (turno + placa) y sección de contacto.

## 1. Requisitos (instalar una sola vez)
1. **Python 3.10+** (marque *Add Python to PATH*). En Linux: `sudo apt install python3-tk`.
2. **PostgreSQL 9.3 o superior**. Anote la contraseña del usuario `postgres`.
3. **Visual Studio Code** con las extensiones recomendadas (Python, SQLTools y SQLTools PostgreSQL Driver).

## 2. Abrir el proyecto
**Archivo > Abrir carpeta…** y elija la carpeta que contiene `main.py` (la de adentro, no la que la envuelve).
Acepte confiar en los autores y la instalación de extensiones recomendadas.

## 3. Preparar el entorno (terminal de VS Code)
```
python -m venv venv
venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

## 4. Crear o actualizar la base de datos
Pulse **F5** y elija **«Sosa Car Wash · 1) Configurar base de datos (primera vez)»**
(o en la terminal: `python configurar_bd.py`). Responda servidor, puerto, usuario y contraseña de PostgreSQL.

- **Base nueva:** se crean las tablas, usuarios, servicios e insumos iniciales.
- **Ya tenía la versión anterior (base `aquawash`):** use el mismo nombre de base; el sistema la **actualiza sin perder datos**
  (agrega los campos nuevos, pasa los precios a guaraníes y crea las tablas de insumos y finanzas).
- Si no recuerda la contraseña de PostgreSQL: `python restablecer_clave.py` (requiere dejar temporalmente `trust` en `pg_hba.conf`).

## 5. Ejecutar
**F5 > «Sosa Car Wash · 2) Aplicación de escritorio»** (o `python main.py`).

| Usuario  | Contraseña   | Rol      | Acceso |
|----------|--------------|----------|--------|
| admin    | admin123     | ADMIN    | Todo |
| operador | operador123  | OPERADOR | Inicio, Agenda, Clientes e Insumos |

Cambie estas contraseñas antes de usar el sistema en serio.

## 6. Página web
Menú **Archivo > Abrir página web** (http://localhost:8000), o F5 > «Solo servidor web».
Los datos de contacto (teléfono, WhatsApp, correo, dirección, RUC) se editan en `config.py`, sección `NEGOCIO`.
El cliente consulta su reserva con el **número de turno + la placa**.

## 7. Administrar la base dentro de VS Code
Barra lateral **SQLTools** > conexión «Sosa Car Wash (PostgreSQL)» > Connect. Abra `sql/consultas.sql`,
seleccione una consulta y pulse **Ctrl+E, Ctrl+E**. Datos de ejemplo: `python setup_db.py --demo`.

## 8. Estructura
```
main.py  setup_db.py  configurar_bd.py  restablecer_clave.py  config.py  formato.py
database/  schema.sql, db.py          (datos y reglas de negocio)
ui/        tema, login, inicio, citas, clientes, insumos, servicios, finanzas, reportes, comprobante, utils
web/       server.py, index.html
sql/       consultas.sql, datos_demo.sql
comprobantes/   (se crea sola; aquí se guardan los comprobantes)
.vscode/   SQLTools, F5 y tareas ya configurados
```

## 9. Problemas frecuentes
- **«password authentication failed»:** contraseña incorrecta; vuelva a ejecutar el asistente.
- **«connection refused»:** el servicio de PostgreSQL no está iniciado.
- **«No module named psycopg2»:** `python -m pip install -r requirements.txt`.
- **«No module named tkinter»** (Linux): `sudo apt install python3-tk`.
- **La página web no carga servicios:** la base no está configurada o PostgreSQL está apagado.

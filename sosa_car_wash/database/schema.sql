-- Sosa Car Wash · Esquema PostgreSQL (compatible con PostgreSQL 9.3 o superior)
-- La aplicación ejecuta este archivo sola al iniciar. También puede pegarlo en SQLTools.

CREATE TABLE IF NOT EXISTS meta (
    clave VARCHAR(40) PRIMARY KEY,
    valor VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id      SERIAL PRIMARY KEY,
    usuario VARCHAR(30)  UNIQUE NOT NULL,
    clave   VARCHAR(200) NOT NULL,
    nombre  VARCHAR(80)  NOT NULL,
    rol     VARCHAR(10)  NOT NULL DEFAULT 'OPERADOR' CHECK (rol IN ('ADMIN','OPERADOR'))
);

CREATE TABLE IF NOT EXISTS clientes (
    id        SERIAL PRIMARY KEY,
    nombre    VARCHAR(80) NOT NULL,
    documento VARCHAR(20),
    telefono  VARCHAR(25) NOT NULL,
    email     VARCHAR(100),
    creado    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id         SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tipo       VARCHAR(5) NOT NULL CHECK (tipo IN ('AUTO','MOTO')),
    placa      VARCHAR(12) UNIQUE NOT NULL,
    marca      VARCHAR(40),
    modelo     VARCHAR(40),
    color      VARCHAR(25)
);

CREATE TABLE IF NOT EXISTS servicios (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(60) NOT NULL,
    tipo_vehiculo VARCHAR(5)  NOT NULL CHECK (tipo_vehiculo IN ('AUTO','MOTO')),
    precio        NUMERIC(12,2) NOT NULL CHECK (precio >= 0),
    duracion_min  INT NOT NULL DEFAULT 60 CHECK (duracion_min > 0),
    activo        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS citas (
    id          SERIAL PRIMARY KEY,
    vehiculo_id INT  NOT NULL REFERENCES vehiculos(id),
    servicio_id INT  NOT NULL REFERENCES servicios(id),
    fecha       DATE NOT NULL,
    hora        TIME NOT NULL,
    estado      VARCHAR(12) NOT NULL DEFAULT 'PENDIENTE'
                CHECK (estado IN ('PENDIENTE','EN_PROCESO','COMPLETADA','CANCELADA')),
    origen      VARCHAR(10) NOT NULL DEFAULT 'ESCRITORIO' CHECK (origen IN ('ESCRITORIO','WEB')),
    observacion TEXT,
    creado      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pagos (
    id        SERIAL PRIMARY KEY,
    cita_id   INT UNIQUE NOT NULL REFERENCES citas(id),
    subtotal  NUMERIC(12,2) NOT NULL DEFAULT 0,
    descuento NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto     NUMERIC(12,2) NOT NULL,
    metodo    VARCHAR(15) NOT NULL CHECK (metodo IN ('EFECTIVO','TARJETA','TRANSFERENCIA')),
    fecha     TIMESTAMP DEFAULT NOW()
);

-- Libro de ingresos y egresos (los cobros de servicios y las compras de insumos entran solos)
CREATE TABLE IF NOT EXISTS movimientos (
    id          SERIAL PRIMARY KEY,
    fecha       DATE NOT NULL DEFAULT CURRENT_DATE,
    tipo        VARCHAR(7) NOT NULL CHECK (tipo IN ('INGRESO','EGRESO')),
    categoria   VARCHAR(40) NOT NULL,
    descripcion VARCHAR(150),
    monto       NUMERIC(14,2) NOT NULL CHECK (monto >= 0),
    origen      VARCHAR(10) NOT NULL DEFAULT 'MANUAL' CHECK (origen IN ('MANUAL','SERVICIO','INSUMO')),
    pago_id     INT UNIQUE REFERENCES pagos(id),
    creado      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insumos (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(60) UNIQUE NOT NULL,
    unidad         VARCHAR(15) NOT NULL DEFAULT 'unidad',
    stock          NUMERIC(12,2) NOT NULL DEFAULT 0,
    stock_minimo   NUMERIC(12,2) NOT NULL DEFAULT 0,
    costo_unitario NUMERIC(12,2) NOT NULL DEFAULT 0,
    activo         BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS insumo_movs (
    id          SERIAL PRIMARY KEY,
    insumo_id   INT NOT NULL REFERENCES insumos(id),
    tipo        VARCHAR(8) NOT NULL CHECK (tipo IN ('COMPRA','CONSUMO')),
    cantidad    NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    costo_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    nota        VARCHAR(150),
    fecha       TIMESTAMP DEFAULT NOW()
);

-- Índices (los crea la aplicación; compatible con PostgreSQL 9.3):
-- CREATE INDEX idx_citas_fecha ON citas (fecha, hora);
-- CREATE INDEX idx_mov_fecha ON movimientos (fecha);

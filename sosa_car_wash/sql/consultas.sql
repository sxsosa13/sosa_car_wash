-- Sosa Car Wash · Consultas de administración
-- En VS Code (SQLTools): conéctese a «Sosa Car Wash (PostgreSQL)», seleccione una consulta
-- y pulse Ctrl+E y luego Ctrl+E (o clic derecho > Run selected query).

-- 1) Citas de hoy
SELECT c.id, c.hora, cl.nombre AS cliente, v.placa, s.nombre AS servicio, c.estado, c.origen
FROM citas c
JOIN vehiculos v ON v.id = c.vehiculo_id
JOIN clientes cl ON cl.id = v.cliente_id
JOIN servicios s ON s.id = c.servicio_id
WHERE c.fecha = CURRENT_DATE
ORDER BY c.hora;

-- 2) Ingresos por día (últimos 30 días)
SELECT fecha::date AS dia, SUM(monto) AS total, SUM(descuento) AS descuentos, COUNT(*) AS cobros
FROM pagos
WHERE fecha >= CURRENT_DATE - 30
GROUP BY 1 ORDER BY 1 DESC;

-- 3) Balance del mes (ingresos - egresos)
SELECT tipo, SUM(monto) AS total
FROM movimientos
WHERE fecha >= date_trunc('month', CURRENT_DATE)
GROUP BY tipo;

-- 4) Egresos por categoría (mes actual)
SELECT categoria, SUM(monto) AS total
FROM movimientos
WHERE tipo = 'EGRESO' AND fecha >= date_trunc('month', CURRENT_DATE)
GROUP BY categoria ORDER BY total DESC;

-- 5) Libro de ingresos y egresos
SELECT fecha, tipo, categoria, descripcion, monto, origen
FROM movimientos ORDER BY fecha DESC, id DESC;

-- 6) Insumos con stock bajo
SELECT nombre, unidad, stock, stock_minimo
FROM insumos WHERE stock <= stock_minimo ORDER BY nombre;

-- 7) Inventario valorizado
SELECT nombre, stock, unidad, costo_unitario, stock * costo_unitario AS valor
FROM insumos ORDER BY valor DESC;

-- 8) Servicios más solicitados
SELECT s.nombre, COUNT(*) AS veces
FROM citas c JOIN servicios s ON s.id = c.servicio_id
WHERE c.estado <> 'CANCELADA'
GROUP BY s.nombre ORDER BY veces DESC;

-- 9) Reservas hechas desde la página web
SELECT c.id AS turno, c.fecha, c.hora, v.placa, c.estado
FROM citas c JOIN vehiculos v ON v.id = c.vehiculo_id
WHERE c.origen = 'WEB' ORDER BY c.fecha DESC, c.hora;

-- 10) Conteo de registros por tabla
SELECT 'clientes' AS tabla, COUNT(*) FROM clientes
UNION ALL SELECT 'vehiculos', COUNT(*) FROM vehiculos
UNION ALL SELECT 'servicios', COUNT(*) FROM servicios
UNION ALL SELECT 'citas', COUNT(*) FROM citas
UNION ALL SELECT 'pagos', COUNT(*) FROM pagos
UNION ALL SELECT 'movimientos', COUNT(*) FROM movimientos
UNION ALL SELECT 'insumos', COUNT(*) FROM insumos;

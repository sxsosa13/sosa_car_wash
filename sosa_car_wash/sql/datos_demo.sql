-- Datos de ejemplo para pruebas y sustentación (python setup_db.py --demo  o  el asistente configurar_bd.py)
INSERT INTO clientes (nombre, documento, telefono, email) VALUES
 ('María Gómez',    '4.123.456', '0981 111 222', 'maria@correo.com'),
 ('Carlos Benítez', '3.456.789', '0982 333 444', NULL),
 ('Lucía Duarte',   '5.678.901', '0983 555 666', 'lucia@correo.com'),
 ('Jorge Ramírez',  '2.345.678', '0984 777 888', NULL);

INSERT INTO vehiculos (cliente_id, tipo, placa, marca, modelo, color) VALUES
 ((SELECT id FROM clientes WHERE nombre = 'María Gómez'),    'AUTO', 'ABC123', 'Toyota', 'Corolla', 'Blanco'),
 ((SELECT id FROM clientes WHERE nombre = 'Carlos Benítez'), 'AUTO', 'DEF456', 'Honda',  'Civic',   'Gris'),
 ((SELECT id FROM clientes WHERE nombre = 'Carlos Benítez'), 'MOTO', 'MOT789', 'Yamaha', 'FZ 150',  'Negro'),
 ((SELECT id FROM clientes WHERE nombre = 'Lucía Duarte'),   'MOTO', 'MOT321', 'Honda',  'CB 125',  'Rojo'),
 ((SELECT id FROM clientes WHERE nombre = 'Jorge Ramírez'),  'AUTO', 'GHI654', 'Kia',    'Rio',     'Azul');

INSERT INTO citas (vehiculo_id, servicio_id, fecha, hora, estado, origen) VALUES
 ((SELECT id FROM vehiculos WHERE placa = 'ABC123'), (SELECT id FROM servicios WHERE nombre = 'Lavado completo'),                CURRENT_DATE - 3, '09:00', 'COMPLETADA', 'ESCRITORIO'),
 ((SELECT id FROM vehiculos WHERE placa = 'MOT789'), (SELECT id FROM servicios WHERE nombre = 'Lavado de moto'),                 CURRENT_DATE - 3, '10:00', 'COMPLETADA', 'WEB'),
 ((SELECT id FROM vehiculos WHERE placa = 'DEF456'), (SELECT id FROM servicios WHERE nombre = 'Lavado + encerado'),              CURRENT_DATE - 2, '11:00', 'COMPLETADA', 'ESCRITORIO'),
 ((SELECT id FROM vehiculos WHERE placa = 'GHI654'), (SELECT id FROM servicios WHERE nombre = 'Lavado básico'),                  CURRENT_DATE - 1, '15:00', 'COMPLETADA', 'WEB'),
 ((SELECT id FROM vehiculos WHERE placa = 'MOT321'), (SELECT id FROM servicios WHERE nombre = 'Lavado de moto'),                 CURRENT_DATE - 1, '16:00', 'CANCELADA',  'WEB'),
 ((SELECT id FROM vehiculos WHERE placa = 'ABC123'), (SELECT id FROM servicios WHERE nombre = 'Lavado básico'),                  CURRENT_DATE,     '14:00', 'PENDIENTE',  'ESCRITORIO'),
 ((SELECT id FROM vehiculos WHERE placa = 'MOT321'), (SELECT id FROM servicios WHERE nombre = 'Lavado + lubricación de cadena'), CURRENT_DATE,     '15:00', 'PENDIENTE',  'WEB'),
 ((SELECT id FROM vehiculos WHERE placa = 'DEF456'), (SELECT id FROM servicios WHERE nombre = 'Lavado completo'),                CURRENT_DATE + 1, '09:00', 'PENDIENTE',  'WEB');

INSERT INTO pagos (cita_id, subtotal, descuento, monto, metodo, fecha)
SELECT c.id, s.precio, 0, s.precio, (ARRAY['EFECTIVO','TARJETA','TRANSFERENCIA'])[1 + c.id % 3], c.fecha + c.hora
FROM citas c JOIN servicios s ON s.id = c.servicio_id
WHERE c.estado = 'COMPLETADA';

-- Un cobro con 10 % de descuento
UPDATE pagos SET descuento = round(subtotal * 0.10), monto = subtotal - round(subtotal * 0.10)
WHERE id = (SELECT MIN(id) FROM pagos);

-- Ingresos de los cobros al libro contable
INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen, pago_id)
SELECT p.fecha::date, 'INGRESO', 'Servicios', 'Cobro de cita #' || p.cita_id, p.monto, 'SERVICIO', p.id
FROM pagos p WHERE NOT EXISTS (SELECT 1 FROM movimientos m WHERE m.pago_id = p.id);

-- Egresos e ingresos manuales de ejemplo
INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen) VALUES
 (CURRENT_DATE - 5, 'EGRESO',  'Alquiler',          'Alquiler del local',        1200000, 'MANUAL'),
 (CURRENT_DATE - 4, 'EGRESO',  'Servicios básicos', 'Agua y electricidad',        380000, 'MANUAL'),
 (CURRENT_DATE - 3, 'EGRESO',  'Sueldos',           'Adelanto de personal',       900000, 'MANUAL'),
 (CURRENT_DATE - 2, 'INGRESO', 'Venta de productos','Venta de aromatizantes',      60000, 'MANUAL');

-- Compra y consumo de insumos de ejemplo
INSERT INTO insumo_movs (insumo_id, tipo, cantidad, costo_total, nota, fecha)
SELECT id, 'COMPRA', 10, 300000, 'Compra al proveedor', NOW() - interval '4 days' FROM insumos WHERE nombre = 'Shampoo automotriz';
INSERT INTO movimientos (fecha, tipo, categoria, descripcion, monto, origen)
VALUES (CURRENT_DATE - 4, 'EGRESO', 'Insumos', 'Compra de Shampoo automotriz', 300000, 'INSUMO');
INSERT INTO insumo_movs (insumo_id, tipo, cantidad, costo_total, nota, fecha)
SELECT id, 'CONSUMO', 2, 0, 'Uso en lavados del día', NOW() - interval '1 day' FROM insumos WHERE nombre = 'Shampoo automotriz';
UPDATE insumos SET stock = stock - 2 WHERE nombre = 'Shampoo automotriz';
-- Un insumo con stock bajo para mostrar la alerta del panel de inicio
UPDATE insumos SET stock = 2 WHERE nombre = 'Desengrasante';

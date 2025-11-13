SELECT data->>'nombre' AS producto
FROM productos
WHERE data->>'color' = 'Rojo';

CREATE INDEX idx_data_gin ON productos USING GIN (data);

EXPLAIN ANALYZE SELECT * FROM productos
WHERE data @> '{"color": "Rojo"}';
EXPLAIN ANALYZE SELECT * FROM productos
WHERE data @> '{"color": "Rojo"}';

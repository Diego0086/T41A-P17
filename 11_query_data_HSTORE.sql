--basicos------------------------
SELECT nombre
FROM productos
WHERE atributos -> 'color' = 'rojo';

UPDATE productos
SET atributos = atributos || 'peso=>"30 kg"'
WHERE nombre = 'Piano';

UPDATE productos
SET atributos = delete(atributos, 'color')
WHERE nombre = 'Libro';
--intermedios------------------------------
SELECT id, nombre
FROM productos
WHERE atributos ? 'marca';

SELECT nombre, atributos
FROM productos
WHERE 
    atributos -> 'marca' = 'Sony'
    AND
    (atributos -> 'precio')::numeric > 500;
    
SELECT skeys(atributos) AS clave, svals(atributos) AS valor
FROM productos;

SELECT COUNT(*) AS total_color
FROM productos
WHERE atributos ? 'color';

--avanzados-----------------------------------------
CREATE INDEX idx_atributos_gin ON productos USING GIN (atributos);

SELECT 
    atributos -> 'marca' AS marca, 
    COUNT(*) AS total              
FROM productos
GROUP BY 
    atributos -> 'marca';         
    
SELECT 
    nombre, 
    hstore_to_json(atributos) AS atributos_en_json
FROM productos;    

SELECT nombre, atributos
FROM productos
WHERE atributos ?& ARRAY['color', 'peso'];

CREATE OR REPLACE FUNCTION resumir_producto(
    p_nombre TEXT, 
    p_atributos HSTORE
)
RETURNS TEXT AS $$
DECLARE
    v_marca TEXT;
    v_color TEXT;
BEGIN
    v_marca := COALESCE(p_atributos -> 'marca', 'Desconocida');
    v_color := COALESCE(p_atributos -> 'color', 'N/A');

    RETURN format('Producto %s: marca=%s, color=%s', p_nombre, v_marca, v_color);
END;
$$ LANGUAGE plpgsql;

SELECT resumir_producto(nombre, atributos) AS resumen
FROM productos;

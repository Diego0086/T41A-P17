DO $$
BEGIN
    
    IF EXISTS (
        SELECT 1 FROM productos 
        WHERE data->>'nombre' = 'Laptop' 
          AND (data->>'precio')::numeric = 1200.50
    ) THEN
        RAISE NOTICE 'Precio correcto para Laptop';
    ELSE
        RAISE EXCEPTION 'Precio incorrecto para Laptop';
    END IF;

    IF EXISTS (
        SELECT 1 FROM productos 
        WHERE data->>'nombre' = 'Teclado' 
          AND data->>'color' = 'Negro'
    ) THEN
        RAISE NOTICE 'Color correcto para Teclado';
    ELSE
        RAISE EXCEPTION 'Color incorrecto para Teclado';
    END IF;

    IF EXISTS (
        SELECT 1 FROM productos 
        WHERE (data->>'stock')::numeric = 40
    ) THEN
        RAISE NOTICE 'Stock correcto';
    ELSE
        RAISE EXCEPTION 'Stock incorrecto';
    END IF;

END;
$$;

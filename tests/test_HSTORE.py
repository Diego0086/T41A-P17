import psycopg2
import pytest
from psycopg2.extras import register_hstore

def test_hstore_lifecycle():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname='test_db',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        register_hstore(conn)
        
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS productos CASCADE;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
        
        cur.execute("""
            CREATE TABLE productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                atributos HSTORE
            );
        """)

        cur.execute("""
            INSERT INTO productos(nombre, atributos) VALUES 
              ('Laptop', 'marca=>"Dell", color=>"plateado", peso=>"1.5 kg"'),
              ('Tenis',  'marca=>"Nike", color=>"rojo", peso=>"0.3 kg"'),
              ('Piano',  'marca=>"Yamaha", color=>"gris", peso=>"80 kg"'),
              ('Libro',  'marca=>"Patito", color=>"blanco", peso=>"0.5 kg"'),
              ('Audífonos', 'marca=>"Sony", precio=>"1200.50", color=>"Negro"'),
              ('Guitarra','marca=>"Fender", color=>"amarillo", peso=>"3.5 kg"');
        """)
        
        cur.execute("SELECT nombre FROM productos WHERE atributos -> 'color' = 'rojo';")
        resultado = cur.fetchone()
        assert resultado[0] == 'Tenis', "El producto rojo debería ser Tenis."

        cur.execute("""
            UPDATE productos
            SET atributos = atributos || 'peso=>"30 kg"'
            WHERE nombre = 'Piano';
        """)
        
        cur.execute("SELECT atributos -> 'peso' FROM productos WHERE nombre = 'Piano';")
        peso_piano = cur.fetchone()[0]
        assert peso_piano == '30 kg', "El peso del Piano no se actualizó correctamente."

        cur.execute("""
            UPDATE productos
            SET atributos = delete(atributos, 'color')
            WHERE nombre = 'Libro';
        """)
        
        cur.execute("SELECT atributos ? 'color' FROM productos WHERE nombre = 'Libro';")
        tiene_color = cur.fetchone()[0]
        assert tiene_color is False, "El Libro no debería tener la clave color después del delete."

        cur.execute("""
            SELECT nombre 
            FROM productos
            WHERE atributos -> 'marca' = 'Sony'
            AND (atributos -> 'precio')::numeric > 500;
        """)
        prod_caro = cur.fetchone()[0]
        assert prod_caro == 'Audífonos', "Falló la consulta compleja con casteo numérico."

        cur.execute("SELECT COUNT(*) FROM productos WHERE atributos ? 'color';")
        total_con_color = cur.fetchone()[0]
        assert total_con_color == 5, f"Se esperaban 5 productos con color, se encontraron {total_con_color}."

        cur.execute("SELECT COUNT(*) FROM productos WHERE atributos ?& ARRAY['color', 'peso'];")
        total_ambos = cur.fetchone()[0]
        assert total_ambos == 4, f"Se esperaban 4 productos con color Y peso, se encontraron {total_ambos}."

        cur.execute("""
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
        """)

        cur.execute("SELECT resumir_producto(nombre, atributos) FROM productos WHERE nombre = 'Tenis';")
        resumen = cur.fetchone()[0]
        expected_str = "Producto Tenis: marca=Nike, color=rojo"
        assert resumen == expected_str, f"La función devolvió un formato incorrecto: {resumen}"

        cur.execute("SELECT resumir_producto(nombre, atributos) FROM productos WHERE nombre = 'Libro';")
        resumen_libro = cur.fetchone()[0]
        expected_libro = "Producto Libro: marca=Patito, color=N/A"
        assert resumen_libro == expected_libro, "La función no manejó correctamente el atributo faltante (COALESCE)."

        cur.execute("SELECT hstore_to_json(atributos) FROM productos WHERE nombre = 'Laptop';")
        json_resultado = cur.fetchone()[0]
        assert json_resultado['marca'] == 'Dell'
        assert json_resultado['peso'] == '1.5 kg'

    finally:
        if conn:
            conn.rollback() 
            cur.close()
            conn.close()

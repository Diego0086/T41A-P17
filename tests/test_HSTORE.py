import psycopg2
import pytest
from psycopg2.extras import register_hstore
from decimal import Decimal

def test_hstore_lifecycle():
    conn = None
    cur = None 
    try:
        conn = psycopg2.connect(
            dbname='test_db',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS productos_hstore CASCADE;")
        
        cur.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
        
        register_hstore(conn)
        
        cur.execute("""
            CREATE TABLE productos_hstore (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                atributos HSTORE
            );
        """)
        cur.execute("""
            INSERT INTO productos_hstore(nombre, atributos) VALUES 
              ('Laptop', 'marca=>"Dell", color=>"plateado", peso=>"1.5 kg"'),
              ('Tenis',  'marca=>"Nike", color=>"rojo", peso=>"0.3 kg"'),
              ('Piano',  'marca=>"Yamaha", color=>"gris", peso=>"80 kg"'),
              ('Libro',  'marca=>"Patito", color=>"blanco", peso=>"0.5 kg"'),
              ('Audífonos', 'marca=>"Sony", precio=>"1200.50", color=>"Negro"'),
              ('Guitarra','marca=>"Fender", color=>"amarillo", peso=>"3.5 kg"');
        """)
        cur.execute("UPDATE productos_hstore SET atributos = atributos || 'peso=>\"30 kg\"' WHERE nombre = 'Piano';")
        cur.execute("UPDATE productos_hstore SET atributos = delete(atributos, 'color') WHERE nombre = 'Libro';")

        cur.execute("""
            SELECT skeys(atributos), svals(atributos) 
            FROM productos_hstore 
            WHERE nombre = 'Laptop';
        """)
        fila = cur.fetchone()
        llaves = fila[0] 
        valores = fila[1] 
        
        assert 'marca' in llaves and 'color' in llaves
        assert 'Dell' in valores and 'plateado' in valores

        cur.execute("SELECT COUNT(*) FROM productos_hstore WHERE atributos ? 'color';")
        total_con_color = cur.fetchone()[0]
        assert total_con_color == 5, f"Se esperaban 5 productos con color, llegaron {total_con_color}"

        cur.execute("CREATE INDEX idx_atributos_gin ON productos_hstore USING GIN (atributos);")
        
        cur.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'productos_hstore' AND indexname = 'idx_atributos_gin';
        """)
        assert cur.fetchone() is not None, "El índice GIN no se creó correctamente."

        cur.execute("""
            SELECT atributos -> 'marca' as marca, COUNT(*) 
            FROM productos_hstore 
            GROUP BY atributos -> 'marca';
        """)
        resultados_group = cur.fetchall()
        assert len(resultados_group) == 6

        cur.execute("""
            SELECT hstore_to_json(atributos) 
            FROM productos_hstore 
            WHERE nombre = 'Tenis';
        """)
        json_result = cur.fetchone()[0]
        if isinstance(json_result, dict):
            assert json_result['color'] == 'rojo'
        else:
            assert '"color": "rojo"' in str(json_result) or "'color': 'rojo'" in str(json_result) 

        cur.execute("""
            SELECT nombre, atributos 
            FROM productos_hstore 
            WHERE atributos ?& ARRAY['color', 'peso'];
        """)
        lista_ambos = cur.fetchall()
        assert len(lista_ambos) == 4, f"Se esperaban 4 productos con color y peso. Obtenidos: {len(lista_ambos)}"

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

        cur.execute("SELECT resumir_producto(nombre, atributos) FROM productos_hstore WHERE nombre = 'Guitarra';")
        resumen_guitarra = cur.fetchone()[0]
        assert resumen_guitarra == "Producto Guitarra: marca=Fender, color=amarillo"

        cur.execute("SELECT resumir_producto(nombre, atributos) FROM productos_hstore WHERE nombre = 'Libro';")
        resumen_libro = cur.fetchone()[0]
        assert resumen_libro == "Producto Libro: marca=Patito, color=N/A"

    finally:
        if conn:
            if cur:
                cur.close()
            conn.close()

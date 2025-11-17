import psycopg2
import pytest
from decimal import Decimal

def test_jsonb_features():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname='test_db',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT data->>'nombre' 
            FROM productos 
            WHERE data->>'color' = 'Rojo'
            ORDER BY data->>'nombre';
        """)
        resultados_rojos = cur.fetchall()
        nombres_rojos = [fila[0] for fila in resultados_rojos]
        
        assert 'Laptop' in nombres_rojos
        assert 'Silla' in nombres_rojos
        assert len(nombres_rojos) == 2

        cur.execute("""
            SELECT (data->>'precio')::numeric 
            FROM productos 
            WHERE data->>'nombre' = 'Laptop';
        """)
        precio_laptop = cur.fetchone()[0]
        assert precio_laptop == Decimal('1200.50'), "El precio de la Laptop en el JSONB no es correcto."

        cur.execute("""
            SELECT data->>'color' 
            FROM productos 
            WHERE data->>'nombre' = 'Teclado';
        """)
        color_teclado = cur.fetchone()[0]
        assert color_teclado == 'Negro', "El color del Teclado debería ser Negro."

        cur.execute("""
            SELECT COUNT(*) 
            FROM productos 
            WHERE (data->>'stock')::int = 40;
        """)
        conteo_stock_40 = cur.fetchone()[0]
        assert conteo_stock_40 >= 1, "No se encontró ningún producto con stock 40."

        cur.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'productos' AND indexname = 'idx_data_gin';
        """)
        index_exists = cur.fetchone()
        assert index_exists is not None, "El índice GIN para JSONB no se creó correctamente."

    finally:
        if conn:
            cur.close()
            conn.close()

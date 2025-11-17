import psycopg2
import pytest
from decimal import Decimal

def test_jsonb_features():
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

        cur.execute("DROP TABLE IF EXISTS productos CASCADE;")
        
        cur.execute("""
            CREATE TABLE productos (
                id SERIAL PRIMARY KEY,
                data JSONB
            );
        """)

        cur.execute("""
            INSERT INTO productos (data) VALUES 
            ('{"nombre": "Laptop", "precio": 1200.50, "stock": 16, "color": "Rojo"}'),
            ('{"nombre": "Teclado", "precio": 75.99, "stock": 40, "color": "Negro"}'),
            ('{"nombre": "Mouse", "precio": 25.00, "stock": 5, "color": "Verde"}'),
            ('{"nombre": "Monitor", "precio": 299.99, "stock": 58, "color": "Negro"}'),
            ('{"nombre": "Silla", "precio": 150.75, "stock": 2, "color": "Rojo"}');
        """)
        
        cur.execute("CREATE INDEX idx_data_gin ON productos USING GIN (data);")

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
        assert precio_laptop == Decimal('1200.50')

        cur.execute("""
            SELECT data->>'color' 
            FROM productos 
            WHERE data->>'nombre' = 'Teclado';
        """)
        color_teclado = cur.fetchone()[0]
        assert color_teclado == 'Negro'

        cur.execute("""
            SELECT COUNT(*) 
            FROM productos 
            WHERE (data->>'stock')::int = 40;
        """)
        conteo_stock_40 = cur.fetchone()[0]
        assert conteo_stock_40 >= 1

    finally:
        if conn:
            if cur:
                cur.close()
            conn.close()

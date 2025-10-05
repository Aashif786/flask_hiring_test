from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL, MySQLdb
from datetime import datetime
from config import Config
from typing import Any, List, Tuple

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

# ------------------ Products ------------------
@app.route('/products')
def products() -> Any:
    with mysql.connection.cursor() as cur:  # type: ignore
        cur.execute("SELECT * FROM product")
        products: List[Tuple] = cur.fetchall()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product() -> Any:
    if request.method == 'POST':
        pid = request.form['product_id']
        name = request.form['name']
        desc = request.form['description']
        with mysql.connection.cursor() as cur: # type: ignore
            cur.execute(
                "INSERT INTO product (product_id, name, description) VALUES (%s, %s, %s)",
                (pid, name, desc)
            )
            mysql.connection.commit() # type: ignore
        return redirect(url_for('products'))
    return render_template('add_product.html')

# ------------------ Locations ------------------
@app.route('/locations')
def locations() -> Any:
    with mysql.connection.cursor() as cur: # type: ignore
        cur.execute("SELECT * FROM location")
        locations: List[Tuple] = cur.fetchall()
    return render_template('locations.html', locations=locations)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location() -> Any:
    if request.method == 'POST':
        lid = request.form['location_id']
        name = request.form['name']
        with mysql.connection.cursor() as cur: # type: ignore
            cur.execute("INSERT INTO location (location_id, name) VALUES (%s, %s)", (lid, name))
            mysql.connection.commit() # type: ignore
        return redirect(url_for('locations'))
    return render_template('add_location.html')

# ------------------ Product Movements ------------------
@app.route('/movements')
def movements() -> Any:
    with mysql.connection.cursor() as cur: # type: ignore
        cur.execute("""
            SELECT pm.movement_id, pm.timestamp, p.name, pm.from_location, pm.to_location, pm.qty
            FROM product_movement pm
            JOIN product p ON pm.product_id = p.product_id
        """)
        movements: List[Tuple] = cur.fetchall()
    return render_template('movements.html', movements=movements)

@app.route('/add_movement', methods=['GET', 'POST'])
def add_movement() -> Any:
    with mysql.connection.cursor() as cur: # type: ignore
        cur.execute("SELECT product_id, name FROM product")
        products: List[Tuple] = cur.fetchall()
        cur.execute("SELECT location_id, name FROM location")
        locations: List[Tuple] = cur.fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_loc = request.form.get('from_location') or None
        to_loc = request.form.get('to_location') or None
        qty = request.form['qty']
        with mysql.connection.cursor() as cur: # type: ignore
            cur.execute("""
                INSERT INTO product_movement (product_id, from_location, to_location, qty, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_id, from_loc, to_loc, qty, datetime.now()))
            mysql.connection.commit() # type: ignore
        return redirect(url_for('movements'))

    return render_template('add_movement.html', products=products, locations=locations)

# ------------------ Report ------------------
@app.route('/report')
def report() -> Any:
    query = """
        SELECT p.name AS product, l.name AS location,
        COALESCE(SUM(CASE WHEN pm.to_location = l.location_id THEN pm.qty ELSE 0 END), 0) -
        COALESCE(SUM(CASE WHEN pm.from_location = l.location_id THEN pm.qty ELSE 0 END), 0) AS qty
        FROM product p
        CROSS JOIN location l
        LEFT JOIN product_movement pm ON p.product_id = pm.product_id
        GROUP BY p.name, l.name
        ORDER BY p.name, l.name;
    """
    with mysql.connection.cursor() as cur: # type: ignore
        cur.execute(query)
        data: List[Tuple] = cur.fetchall()
    return render_template('report.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request, redirect, render_template_string
import sqlite3
import os

app = Flask(name)

DATABASE = "store.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


HTML = """
<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>فروشگاه من</title>
<style>
body {
    font-family: Tahoma;
    direction: rtl;
    max-width: 900px;
    margin: 40px auto;
    padding: 20px;
}
input, button {
    padding: 10px;
    margin: 5px;
}
button {
    cursor: pointer;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 30px;
}
th, td {
    border: 1px solid #ccc;
    padding: 12px;
    text-align: center;
}
.out {
    color: red;
}
</style>
</head>

<body>

<h1>فروشگاه من</h1>

<h2>ثبت کالا</h2>

<form method="POST" action="/add">
<input type="text" name="name" placeholder="نام کالا" required>
<input type="number" name="price" placeholder="قیمت" required>
<input type="number" name="quantity" placeholder="تعداد" min="0" required>
<button type="submit">ثبت کالا</button>
</form>

<h2>جستجوی کالا</h2>

<form method="GET">
<input type="text" name="search" placeholder="نام کالا" value="{{ search }}">
<button type="submit">جستجو</button>
</form>

<h2>کالاها</h2>

<table>
<tr>
<th>نام</th>
<th>قیمت</th>
<th>موجودی</th>
<th>فروش</th>
</tr>

{% for product in products %}
<tr>
<td>{{ product["name"] }}</td>

<td>
{{ "{:,}".format(product["price"]) }}
تومان
</td>

<td>
{% if product["quantity"] == 0 %}
<span class="out">تمام شده</span>
{% else %}
{{ product["quantity"] }}
{% endif %}
</td>

<td>
{% if product["quantity"] > 0 %}
<form method="POST" action="/sell">
<input type="hidden" name="id" value="{{ product['id'] }}">
<input type="number" name="quantity" value="1" min="1"
max="{{ product['quantity'] }}" required>
<button type="submit">فروش</button>
</form>
{% else %}
تمام شده
{% endif %}
</td>
</tr>
{% endfor %}

</table>

</body>
</html>
"""


@app.route("/")
def index():
    search = request.args.get("search", "")

    conn = get_db()

    if search:
        products = conn.execute(
            """
            SELECT * FROM products
            WHERE name LIKE ?
            ORDER BY id DESC
            """,
            ("%" + search + "%",),
        ).fetchall()
    else:
        products = conn.execute(
            """
            SELECT * FROM products
            ORDER BY id DESC
            """
        ).fetchall()

    conn.close()

    return render_template_string(
        HTML,
        products=products,
        search=search
    )


@app.route("/add", methods=["POST"])
def add_product():
    name = request.form["name"]
    price = int(request.form["price"])
    quantity = int(request.form["quantity"])

    conn = get_db()

    conn.execute(
        """
        INSERT INTO products
        (name, price, quantity)
        VALUES (?, ?, ?)
        """,
        (name, price, quantity),
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/sell", methods=["POST"])
def sell():
    product_id = int(request.form["id"])
    sell_quantity = int(request.form["quantity"])

    conn = get_db()

    product = conn.execute(
        """
        SELECT * FROM products
        WHERE id = ?
        """,
        (product_id,),
    ).fetchone()

    if product is None:
        conn.close()
        return "کالا پیدا نشد"

    if sell_quantity <= 0:
        conn.close()
        return "تعداد فروش نامعتبر است"

    if sell_quantity > product["quantity"]:
        conn.close()
        return "موجودی کافی نیست"

    new_quantity = product["quantity"] - sell_quantity
    conn.execute(
        """
        UPDATE products
        SET quantity = ?
        WHERE id = ?
        """,
        (new_quantity, product_id),
    )

    conn.commit()
    conn.close()

    return redirect("/")


if name == "main":
    init_db()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

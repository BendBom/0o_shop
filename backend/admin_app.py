import os
from functools import wraps

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import httpx

from config import FLASK_SECRET_KEY

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>O_Shop Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #111; color: #eee; padding: 2rem; }
        h1 { font-size: 1.8rem; margin-bottom: 1rem; border-bottom: 1px solid #333; padding-bottom: .5rem; }
        h2 { font-size: 1.2rem; margin: 1.5rem 0 .5rem; }
        .flash { background: #333; padding: .5rem 1rem; border-left: 3px solid #fff; margin-bottom: 1rem; }
        .flash.error { border-left-color: #f44; }
        form { margin-bottom: 1.5rem; }
        input, textarea { background: #222; color: #eee; border: 1px solid #444; padding: .5rem; margin: .25rem 0; width: 100%; max-width: 400px; display: block; }
        button { background: #eee; color: #111; border: none; padding: .5rem 1.5rem; cursor: pointer; margin-top: .5rem; font-weight: bold; }
        button:hover { background: #ccc; }
        button.danger { background: #c33; color: #fff; }
        button.danger:hover { background: #a22; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { text-align: left; padding: .5rem; border-bottom: 1px solid #333; }
        th { color: #aaa; font-size: .85rem; text-transform: uppercase; }
        a { color: #ccc; }
        .container { max-width: 900px; margin: auto; }
        .nav { margin-bottom: 2rem; }
        .nav a { margin-right: 1rem; text-decoration: none; color: #aaa; }
        .nav a:hover { color: #fff; }
    </style>
</head>
<body>
<div class="container">
    {% block content %}{% endblock %}
</div>
</body>
</html>
"""

LOGIN_PAGE = (
    '{% extends "base" %}'
    "{% block content %}"
    "<h1>Admin Login</h1>"
    "{% for m in get_flashed_messages() %}<div class='flash error'>{{ m }}</div>{% endfor %}"
    '<form method="POST">'
    '<input name="username" placeholder="Username" required>'
    '<input name="password" type="password" placeholder="Password" required>'
    "<button>Login</button>"
    "</form>"
    "{% endblock %}"
)

DASHBOARD_PAGE = (
    '{% extends "base" %}'
    "{% block content %}"
    '<div class="nav"><a href="/admin">Products</a> <a href="/admin/logout">Logout</a></div>'
    "<h1>Products</h1>"
    "{% for m in get_flashed_messages() %}<div class='flash'>{{ m }}</div>{% endfor %}"
    "<h2>Add Product</h2>"
    '<form method="POST" action="/admin/products/add">'
    '<input name="name" placeholder="Product Name" required>'
    '<textarea name="description" placeholder="Description"></textarea>'
    '<input name="price" type="number" step="0.01" placeholder="Price" required>'
    '<input name="stock" type="number" placeholder="Stock" required>'
    '<input name="image_url" placeholder="Image URL (optional)">'
    "<button>Add Product</button>"
    "</form>"
    "<h2>All Products</h2>"
    "<table><tr><th>ID</th><th>Name</th><th>Price</th><th>Stock</th><th>Action</th></tr>"
    "{% for p in products %}"
    "<tr><td>{{ p.id }}</td><td>{{ p.name }}</td><td>${{ '%.2f' | format(p.price) }}</td>"
    "<td>{{ p.stock }}</td>"
    '<td><form method="POST" action="/admin/products/delete/{{ p.id }}" style="display:inline">'
    '<button class="danger" type="submit">Delete</button></form></td></tr>'
    "{% endfor %}"
    "</table>"
    "{% endblock %}"
)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_token" not in session:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


def api_headers():
    return {"Authorization": f"Bearer {session.get('admin_token', '')}"}


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            resp = httpx.post(
                f"{API_BASE}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                me_resp = httpx.get(
                    f"{API_BASE}/api/auth/me",
                    headers={"Authorization": f"Bearer {data['access_token']}"},
                    timeout=10,
                )
                if me_resp.status_code == 200 and me_resp.json().get("role") == "admin":
                    session["admin_token"] = data["access_token"]
                    return redirect(url_for("admin_dashboard"))
                else:
                    flash("Access denied: admin role required")
            else:
                flash("Invalid credentials")
        except Exception:
            flash("API connection error")

    return render_template_string(
        ADMIN_TEMPLATE.replace("{% block content %}{% endblock %}", "") +
        LOGIN_PAGE.replace('{% extends "base" %}', "").replace("{% block content %}", "").replace("{% endblock %}", ""),
    )


@app.route("/admin")
@login_required
def admin_dashboard():
    try:
        resp = httpx.get(f"{API_BASE}/api/products/?limit=100", timeout=10)
        products = resp.json() if resp.status_code == 200 else []
    except Exception:
        products = []

    template = ADMIN_TEMPLATE.replace(
        "{% block content %}{% endblock %}",
        DASHBOARD_PAGE
        .replace('{% extends "base" %}', "")
        .replace("{% block content %}", "")
        .replace("{% endblock %}", ""),
    )
    return render_template_string(template, products=products)


@app.route("/admin/products/add", methods=["POST"])
@login_required
def admin_add_product():
    payload = {
        "name": request.form.get("name", ""),
        "description": request.form.get("description", ""),
        "price": float(request.form.get("price", 0)),
        "stock": int(request.form.get("stock", 0)),
        "image_url": request.form.get("image_url", "") or None,
    }
    try:
        resp = httpx.post(
            f"{API_BASE}/api/products/",
            json=payload,
            headers=api_headers(),
            timeout=10,
        )
        if resp.status_code == 201:
            flash("Product added")
        else:
            flash(f"Error: {resp.text}")
    except Exception as e:
        flash(f"API error: {e}")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def admin_delete_product(product_id):
    try:
        resp = httpx.delete(
            f"{API_BASE}/api/products/{product_id}",
            headers=api_headers(),
            timeout=10,
        )
        if resp.status_code == 204:
            flash("Product deleted")
        else:
            flash(f"Error: {resp.text}")
    except Exception as e:
        flash(f"API error: {e}")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_token", None)
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

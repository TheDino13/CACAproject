import os
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation

import psycopg
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-development-key")


@contextmanager
def database_cursor():
    connection = psycopg.connect(
        dbname=os.environ.get("POSTGRES_DB", "pizzeriadb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        connect_timeout=5,
    )
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS menu_items (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(120) NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        price NUMERIC(10, 2) NOT NULL CHECK (price >= 0)
                    )
                    """
                )
                yield cursor
    finally:
        connection.close()


def item_fields():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        raise ValueError("Name is required.")

    try:
        price = Decimal(request.form.get("price", ""))
    except InvalidOperation as error:
        raise ValueError("Enter a valid price.") from error

    if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
        raise ValueError("Price must be non-negative and have no more than two decimal places.")

    return name, description, price


@app.get("/")
def index():
    try:
        with database_cursor() as cursor:
            cursor.execute(
                "SELECT id, name, description, price FROM menu_items ORDER BY id"
            )
            items = cursor.fetchall()
    except psycopg.Error:
        return (
            render_template("index.html", items=[], database_error=True),
            503,
        )

    return render_template("index.html", items=items, database_error=False)


@app.post("/items")
def create_item():
    try:
        fields = item_fields()
        with database_cursor() as cursor:
            cursor.execute(
                "INSERT INTO menu_items (name, description, price) VALUES (%s, %s, %s)",
                fields,
            )
        flash("Menu item added.", "success")
    except ValueError as error:
        flash(str(error), "error")
    except psycopg.Error:
        flash("Could not connect to the database.", "error")
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/update")
def update_item(item_id):
    try:
        fields = item_fields()
        with database_cursor() as cursor:
            cursor.execute(
                "UPDATE menu_items SET name = %s, description = %s, price = %s WHERE id = %s",
                (*fields, item_id),
            )
        flash("Changes saved.", "success")
    except ValueError as error:
        flash(str(error), "error")
    except psycopg.Error:
        flash("Could not connect to the database.", "error")
    return redirect(url_for("index"))


@app.post("/items/<int:item_id>/delete")
def delete_item(item_id):
    try:
        with database_cursor() as cursor:
            cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
        flash("Menu item deleted.", "success")
    except psycopg.Error:
        flash("Could not connect to the database.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
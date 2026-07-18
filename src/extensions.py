import sqlite3
from flask import current_app, g
from werkzeug.security import generate_password_hash


import os

def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        try:
            g.db = sqlite3.connect(db_path, timeout=5)
        except sqlite3.OperationalError:
            # Fallback to a writable file inside instance_path (works around locked temp files on Windows)
            os.makedirs(current_app.instance_path, exist_ok=True)
            fallback = os.path.join(current_app.instance_path, "quotes_fallback.sqlite3")
            g.db = sqlite3.connect(fallback, timeout=5)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            quote_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash
        """,
        (
            current_app.config["ADMIN_USERNAME"],
            generate_password_hash(current_app.config["ADMIN_PASSWORD"]),
        ),
    )
    db.commit()

import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        DATABASE=os.path.join(app.instance_path, "quotes.sqlite3"),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "change-me"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(_=None):
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
                app.config["ADMIN_USERNAME"],
                generate_password_hash(app.config["ADMIN_PASSWORD"]),
            ),
        )
        db.commit()

    @app.before_request
    def ensure_db():
        init_db()

    app.teardown_appcontext(close_db)

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                return redirect(url_for("admin_login", next=request.path))
            return view(**kwargs)

        return wrapped_view

    @app.route("/")
    def index():
        search = request.args.get("q", "").strip()
        quote_date = request.args.get("date", "").strip()

        query = "SELECT id, text, quote_date FROM quotes"
        clauses = []
        params = []

        if quote_date:
            clauses.append("quote_date = ?")
            params.append(quote_date)
        if search:
            clauses.append("LOWER(text) LIKE ?")
            params.append(f"%{search.lower()}%")

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY quote_date DESC, id DESC"

        quotes = get_db().execute(query, params).fetchall()
        return render_template("index.html", quotes=quotes, search=search, quote_date=quote_date)

    @app.route("/admin")
    @login_required
    def admin_index():
        quotes = get_db().execute(
            "SELECT id, text, quote_date FROM quotes ORDER BY quote_date DESC, id DESC"
        ).fetchall()
        return render_template("admin_index.html", quotes=quotes)

    @app.route("/admin/login", methods=("GET", "POST"))
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = get_db().execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(request.args.get("next") or url_for("admin_index"))

            flash("Invalid credentials.")

        return render_template("admin_login.html")

    @app.route("/admin/logout", methods=("POST",))
    @login_required
    def admin_logout():
        session.clear()
        return redirect(url_for("index"))

    @app.route("/admin/quotes/new", methods=("GET", "POST"))
    @login_required
    def admin_new_quote():
        if request.method == "POST":
            text = request.form.get("text", "").strip()
            quote_date = request.form.get("quote_date", "").strip()

            if not text:
                flash("Quote text is required.")
            elif not _is_valid_date(quote_date):
                flash("Quote date must be in YYYY-MM-DD format.")
            else:
                timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
                db = get_db()
                db.execute(
                    "INSERT INTO quotes (text, quote_date, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (text, quote_date, timestamp, timestamp),
                )
                db.commit()
                return redirect(url_for("admin_index"))

        return render_template("admin_quote_form.html", quote=None)

    @app.route("/admin/quotes/<int:quote_id>/edit", methods=("GET", "POST"))
    @login_required
    def admin_edit_quote(quote_id):
        db = get_db()
        quote = db.execute(
            "SELECT id, text, quote_date FROM quotes WHERE id = ?", (quote_id,)
        ).fetchone()
        if quote is None:
            return redirect(url_for("admin_index"))

        if request.method == "POST":
            text = request.form.get("text", "").strip()
            quote_date = request.form.get("quote_date", "").strip()

            if not text:
                flash("Quote text is required.")
            elif not _is_valid_date(quote_date):
                flash("Quote date must be in YYYY-MM-DD format.")
            else:
                db.execute(
                    "UPDATE quotes SET text = ?, quote_date = ?, updated_at = ? WHERE id = ?",
                    (text, quote_date, datetime.now(timezone.utc).isoformat(timespec="seconds"), quote_id),
                )
                db.commit()
                return redirect(url_for("admin_index"))

        return render_template("admin_quote_form.html", quote=quote)

    return app


def _is_valid_date(raw_date: str) -> bool:
    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

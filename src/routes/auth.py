from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from ..extensions import get_db
from ..services.auth_service import login_required, _is_valid_date
from datetime import datetime, timezone

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin")
@login_required
def admin_index():
    quotes = get_db().execute(
        "SELECT id, text, quote_date FROM quotes ORDER BY quote_date DESC, id DESC"
    ).fetchall()
    return render_template("admin_index.html", quotes=quotes)


@auth_bp.route("/admin/login", methods=("GET", "POST"))
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
            return redirect(url_for("auth.admin_index"))

        flash("Invalid credentials.")

    return render_template("admin_login.html")


@auth_bp.route("/admin/logout", methods=("POST",))
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for("main.index"))


@auth_bp.route("/admin/quotes/new", methods=("GET", "POST"))
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
            return redirect(url_for("auth.admin_index"))

    return render_template("admin_quote_form.html", quote=None)


@auth_bp.route("/admin/quotes/<int:quote_id>/edit", methods=("GET", "POST"))
@login_required
def admin_edit_quote(quote_id):
    db = get_db()
    quote = db.execute(
        "SELECT id, text, quote_date FROM quotes WHERE id = ?", (quote_id,)
    ).fetchone()
    if quote is None:
        return redirect(url_for("auth.admin_index"))

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
            return redirect(url_for("auth.admin_index"))

    return render_template("admin_quote_form.html", quote=quote)


@auth_bp.route("/admin/quotes/<int:quote_id>/delete", methods=("GET",))
@login_required
def admin_delete_quote(quote_id):
    db = get_db()
    db.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    db.commit()
    return redirect(url_for("auth.admin_index"))


from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from ..extensions import get_db
from ..services.auth_service import login_required, _is_valid_date
from datetime import datetime, timezone
import os
import uuid
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_DIMENSION = 512  # Target bounding box dimension in pixels


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        raise ValueError('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WebP')

    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    try:
        # Open the image stream directly from memory
        img = Image.open(file.stream)

        # Verify if dimensions exceed the specified threshold
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            # calculate aspect ratio preservation parameters
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

        # Save processed image to disk, matching its original format or setting quality constraints
        # EXIF orientation data is preserved by default if parsed correctly
        img.save(filepath, format=img.format, quality=100, optimize=True)
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")

    return filename


def delete_upload_file(image_path):
    if not image_path:
        return
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    filepath = os.path.join(upload_dir, image_path)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/admin")
@login_required
def admin_index():
    quotes = get_db().execute(
        "SELECT id, text, quote_date, image_path FROM quotes ORDER BY quote_date DESC, id DESC"
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
        image_file = request.files.get("image")

        if not text:
            flash("Quote text is required.")
        elif not _is_valid_date(quote_date):
            flash("Quote date must be in YYYY-MM-DD format.")
        else:
            try:
                image_path = None
                if image_file and image_file.filename != '':
                    image_path = save_upload_file(image_file)

                timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
                db = get_db()
                db.execute(
                    "INSERT INTO quotes (text, quote_date, image_path, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (text, quote_date, image_path, timestamp, timestamp),
                )
                db.commit()
                return redirect(url_for("auth.admin_index"))
            except ValueError as e:
                flash(str(e))

    return render_template("admin_quote_form.html", quote=None)


@auth_bp.route("/admin/quotes/<int:quote_id>/edit", methods=("GET", "POST"))
@login_required
def admin_edit_quote(quote_id):
    db = get_db()
    quote = db.execute(
        "SELECT id, text, quote_date, image_path FROM quotes WHERE id = ?", (quote_id,)
    ).fetchone()
    if quote is None:
        return redirect(url_for("auth.admin_index"))

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        quote_date = request.form.get("quote_date", "").strip()
        image_file = request.files.get("image")

        if not text:
            flash("Quote text is required.")
        elif not _is_valid_date(quote_date):
            flash("Quote date must be in YYYY-MM-DD format.")
        else:
            try:
                image_path = quote['image_path']
                if image_file and image_file.filename != '':
                    delete_upload_file(image_path)
                    image_path = save_upload_file(image_file)

                db.execute(
                    "UPDATE quotes SET text = ?, quote_date = ?, image_path = ?, updated_at = ? WHERE id = ?",
                    (text, quote_date, image_path, datetime.now(timezone.utc).isoformat(timespec="seconds"), quote_id),
                )
                db.commit()
                return redirect(url_for("auth.admin_index"))
            except ValueError as e:
                flash(str(e))

    return render_template("admin_quote_form.html", quote=quote)


@auth_bp.route("/admin/quotes/<int:quote_id>/delete", methods=("GET",))
@login_required
def admin_delete_quote(quote_id):
    db = get_db()
    quote = db.execute("SELECT image_path FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    if quote:
        delete_upload_file(quote['image_path'])
    db.execute("DELETE FROM quotes WHERE id = ?", (quote_id,))
    db.commit()
    return redirect(url_for("auth.admin_index"))


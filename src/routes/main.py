from flask import Blueprint, render_template, request
from ..extensions import get_db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    search = request.args.get("q", "").strip()
    quote_date = request.args.get("date", "").strip()

    query = "SELECT id, text, quote_date, image_path FROM quotes"
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

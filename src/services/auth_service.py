from functools import wraps
from flask import session, redirect, url_for
from datetime import datetime


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.admin_login"))
        return view(**kwargs)

    return wrapped_view


def _is_valid_date(raw_date: str) -> bool:
    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
        return True
    except ValueError:
        return False

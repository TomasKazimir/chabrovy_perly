from flask import Flask
from dotenv import load_dotenv
import os

from .extensions import init_db, close_db
from .routes.main import main_bp
from .routes.auth import auth_bp

load_dotenv()

def create_app(test_config=None):
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app = Flask(__name__, instance_relative_config=True, template_folder=template_dir)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY",),
        DATABASE=os.path.join(app.instance_path, "quotes.sqlite3"),
        ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME",),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD",),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5MB max file size
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    # register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    @app.before_request
    def _ensure_db():
        init_db()

    app.teardown_appcontext(close_db)

    # Maintain legacy endpoint names used by templates/tests (alias blueprint endpoints)
    alias_map = {
        'index': 'main.index',
        'admin_index': 'auth.admin_index',
        'admin_login': 'auth.admin_login',
        'admin_logout': 'auth.admin_logout',
    }
    for alias, original in alias_map.items():
        if original in app.view_functions:
            app.view_functions[alias] = app.view_functions[original]

    return app

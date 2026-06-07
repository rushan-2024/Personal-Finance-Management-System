from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Register blueprints
    from app.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.goals import goals_bp
    from app.routes.reports import reports_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(transactions_bp, url_prefix="/transactions")
    app.register_blueprint(budgets_bp, url_prefix="/budgets")
    app.register_blueprint(goals_bp, url_prefix="/goals")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Custom Jinja2 filters ──────────────────────────────────────────────
    @app.template_filter("inr")
    def inr_filter(value):
        """Format a number with comma separators, 0 decimal places."""
        try:
            return "{:,.0f}".format(float(value))
        except (TypeError, ValueError):
            return "0"

    @app.template_filter("inr2")
    def inr2_filter(value):
        """Format a number with comma separators, 2 decimal places."""
        try:
            return "{:,.2f}".format(float(value))
        except (TypeError, ValueError):
            return "0.00"

    return app

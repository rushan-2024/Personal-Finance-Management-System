from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime, timezone
from app import db, limiter
from app.models import User, Category

auth_bp = Blueprint("auth", __name__)

DEFAULT_CATEGORIES = [
    # Income
    {"name": "Salary",      "icon": "ti-briefcase",    "color": "#1D9E75", "type": "income"},
    {"name": "Freelance",   "icon": "ti-code",         "color": "#1D9E75", "type": "income"},
    {"name": "Investment",  "icon": "ti-chart-line",   "color": "#185FA5", "type": "income"},
    {"name": "Gift",        "icon": "ti-gift",         "color": "#534AB7", "type": "income"},
    {"name": "Other Income","icon": "ti-plus-circle",  "color": "#1D9E75", "type": "income"},
    # Expense
    {"name": "Housing",     "icon": "ti-home",         "color": "#E24B4A", "type": "expense"},
    {"name": "Food",        "icon": "ti-tools-kitchen-2","color":"#BA7517","type": "expense"},
    {"name": "Transport",   "icon": "ti-car",          "color": "#185FA5", "type": "expense"},
    {"name": "Shopping",    "icon": "ti-shopping-bag", "color": "#534AB7", "type": "expense"},
    {"name": "Health",      "icon": "ti-heart-rate-monitor","color":"#E24B4A","type":"expense"},
    {"name": "Education",   "icon": "ti-book",         "color": "#185FA5", "type": "expense"},
    {"name": "Entertainment","icon":"ti-device-tv",    "color": "#BA7517", "type": "expense"},
    {"name": "Utilities",   "icon": "ti-bolt",         "color": "#534AB7", "type": "expense"},
    {"name": "Other Expense","icon":"ti-minus-circle", "color": "#888780", "type": "expense"},
]


def _seed_categories(user_id):
    for cat in DEFAULT_CATEGORIES:
        db.session.add(Category(
            name=cat["name"], icon=cat["icon"],
            color=cat["color"], type=cat["type"],
            is_default=True, user_id=user_id,
        ))
    db.session.commit()


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        data = request.form
        name  = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        confirm  = data.get("confirm_password", "")

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("auth/signup.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/signup.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/signup.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/signup.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        _seed_categories(user.id)

        login_user(user)
        flash(f"Welcome to FinFlow, {name}! 🎉", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.name     = request.form.get("name", current_user.name).strip()
        current_user.currency = request.form.get("currency", current_user.currency)
        current_user.email_notifications = bool(request.form.get("email_notifications"))
        new_pass = request.form.get("new_password", "")
        if new_pass:
            if len(new_pass) < 8:
                flash("Password must be at least 8 characters.", "danger")
                return redirect(url_for("auth.profile"))
            current_user.set_password(new_pass)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html")

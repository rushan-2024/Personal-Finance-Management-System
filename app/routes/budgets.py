from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Budget, Category
from app.services import get_budget_status

budgets_bp = Blueprint("budgets", __name__)


@budgets_bp.route("/")
@login_required
def index():
    budgets    = get_budget_status(current_user.id)
    categories = Category.query.filter(
        (Category.user_id == current_user.id) | (Category.is_default == True),
        Category.type == "expense",
    ).all()
    today = date.today()
    return render_template("budgets/index.html", budgets=budgets,
                           categories=categories, today=today)


@budgets_bp.route("/add", methods=["POST"])
@login_required
def add():
    today = date.today()
    try:
        budget = Budget(
            user_id=current_user.id,
            name=request.form["name"].strip(),
            amount=float(request.form["amount"]),
            month=int(request.form.get("month", today.month)),
            year=int(request.form.get("year", today.year)),
            category_id=request.form.get("category_id", type=int),
            alert_threshold=float(request.form.get("alert_threshold", 80)),
        )
        db.session.add(budget)
        db.session.commit()
        flash("Budget created! ✅", "success")
    except (ValueError, KeyError) as e:
        flash(f"Invalid data: {e}", "danger")
    return redirect(url_for("budgets.index"))


@budgets_bp.route("/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    flash("Budget removed.", "info")
    return redirect(url_for("budgets.index"))

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Goal

goals_bp = Blueprint("goals", __name__)

GOAL_ICONS = [
    ("ti-device-laptop", "Laptop / Tech"),
    ("ti-beach", "Vacation"),
    ("ti-shield-check", "Emergency Fund"),
    ("ti-home", "House / Property"),
    ("ti-car", "Vehicle"),
    ("ti-heart-rate-monitor", "Health"),
    ("ti-school", "Education"),
    ("ti-diamond", "Wedding"),
    ("ti-target", "General Goal"),
]


@goals_bp.route("/")
@login_required
def index():
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.created_at.desc()).all()
    return render_template("goals/index.html", goals=goals, icons=GOAL_ICONS)


@goals_bp.route("/add", methods=["POST"])
@login_required
def add():
    try:
        deadline_str = request.form.get("deadline", "")
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date() if deadline_str else None

        goal = Goal(
            user_id=current_user.id,
            name=request.form["name"].strip(),
            description=request.form.get("description", "").strip() or None,
            target_amount=float(request.form["target_amount"]),
            saved_amount=float(request.form.get("saved_amount", 0)),
            deadline=deadline,
            icon=request.form.get("icon", "ti-target"),
            color=request.form.get("color", "#185FA5"),
        )
        db.session.add(goal)
        db.session.commit()
        flash("Goal created! 🎯", "success")
    except (ValueError, KeyError) as e:
        flash(f"Invalid data: {e}", "danger")
    return redirect(url_for("goals.index"))


@goals_bp.route("/update/<int:goal_id>", methods=["POST"])
@login_required
def update(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    try:
        contribute = float(request.form.get("contribute", 0))
        goal.saved_amount = min(goal.saved_amount + contribute, goal.target_amount)
        if goal.saved_amount >= goal.target_amount:
            goal.is_completed = True
            flash(f"🎉 Goal '{goal.name}' completed!", "success")
        else:
            flash(f"Added ₹{contribute:,.0f} to '{goal.name}'!", "success")
        db.session.commit()
    except ValueError:
        flash("Invalid amount.", "danger")
    return redirect(url_for("goals.index"))


@goals_bp.route("/delete/<int:goal_id>", methods=["POST"])
@login_required
def delete(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash("Goal removed.", "info")
    return redirect(url_for("goals.index"))

"""
REST API – /api/v1/
JWT-protected endpoints for mobile / third-party clients.
"""
from datetime import datetime, date, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, verify_jwt_in_request,
)

from app import db, limiter
from app.models import User, Transaction, Budget, Goal, Category
from app.services import (
    get_dashboard_summary, get_monthly_chart_data,
    get_category_breakdown, get_budget_status, get_ai_insights,
)

api_bp = Blueprint("api", __name__)


def _ok(data=None, msg="success", status=200):
    return jsonify({"status": "success", "message": msg, "data": data}), status


def _err(msg="error", status=400):
    return jsonify({"status": "error", "message": msg}), status


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_bp.post("/auth/register")
@limiter.limit("10 per hour")
def api_register():
    body  = request.get_json(silent=True) or {}
    name  = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    pw    = body.get("password", "")

    if not all([name, email, pw]):
        return _err("name, email, and password are required.", 422)
    if len(pw) < 8:
        return _err("Password must be at least 8 characters.", 422)
    if User.query.filter_by(email=email).first():
        return _err("Email already registered.", 409)

    user = User(name=name, email=email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()

    return _ok({"user": user.to_dict()}, "User registered successfully.", 201)


@api_bp.post("/auth/login")
@limiter.limit("20 per hour")
def api_login():
    body  = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    pw    = body.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(pw) or not user.is_active:
        return _err("Invalid credentials.", 401)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    access  = create_access_token(identity=user.id)
    refresh = create_refresh_token(identity=user.id)
    return _ok({"access_token": access, "refresh_token": refresh, "user": user.to_dict()})


@api_bp.post("/auth/refresh")
@jwt_required(refresh=True)
def api_refresh():
    uid    = get_jwt_identity()
    access = create_access_token(identity=uid)
    return _ok({"access_token": access})


@api_bp.get("/auth/me")
@jwt_required()
def api_me():
    user = db.session.get(User, get_jwt_identity())
    return _ok(user.to_dict())


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@api_bp.get("/transactions")
@jwt_required()
def api_list_transactions():
    uid  = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per  = min(request.args.get("per_page", 20, type=int), 100)

    query = Transaction.query.filter_by(user_id=uid).order_by(Transaction.date.desc())

    if t := request.args.get("type"):
        query = query.filter(Transaction.type == t)
    if cat := request.args.get("category_id", type=int):
        query = query.filter(Transaction.category_id == cat)

    pag = query.paginate(page=page, per_page=per)
    return _ok({
        "transactions": [t.to_dict() for t in pag.items],
        "total": pag.total, "pages": pag.pages, "page": page,
    })


@api_bp.post("/transactions")
@jwt_required()
def api_create_transaction():
    uid  = get_jwt_identity()
    body = request.get_json(silent=True) or {}

    try:
        txn = Transaction(
            user_id=uid,
            amount=float(body["amount"]),
            type=body["type"],
            description=body.get("description", ""),
            date=datetime.strptime(body["date"], "%Y-%m-%d").date(),
            category_id=body.get("category_id"),
            currency=body.get("currency", "INR"),
            tags=body.get("tags"),
        )
        db.session.add(txn)
        db.session.commit()
        return _ok(txn.to_dict(), "Transaction created.", 201)
    except (KeyError, ValueError) as e:
        return _err(str(e), 422)


@api_bp.put("/transactions/<int:txn_id>")
@jwt_required()
def api_update_transaction(txn_id):
    uid  = get_jwt_identity()
    txn  = Transaction.query.filter_by(id=txn_id, user_id=uid).first_or_404()
    body = request.get_json(silent=True) or {}

    if "amount"      in body: txn.amount      = float(body["amount"])
    if "type"        in body: txn.type        = body["type"]
    if "description" in body: txn.description = body["description"]
    if "date"        in body: txn.date        = datetime.strptime(body["date"], "%Y-%m-%d").date()
    if "category_id" in body: txn.category_id = body["category_id"]

    db.session.commit()
    return _ok(txn.to_dict())


@api_bp.delete("/transactions/<int:txn_id>")
@jwt_required()
def api_delete_transaction(txn_id):
    uid = get_jwt_identity()
    txn = Transaction.query.filter_by(id=txn_id, user_id=uid).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    return _ok(msg="Transaction deleted.")


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@api_bp.get("/analytics/summary")
@jwt_required()
def api_summary():
    return _ok(get_dashboard_summary(get_jwt_identity()))


@api_bp.get("/analytics/monthly")
@jwt_required()
def api_monthly():
    months = min(request.args.get("months", 6, type=int), 24)
    return _ok(get_monthly_chart_data(get_jwt_identity(), months))


@api_bp.get("/analytics/categories")
@jwt_required()
def api_categories():
    return _ok(get_category_breakdown(get_jwt_identity()))


@api_bp.get("/analytics/insights")
@jwt_required()
def api_insights():
    return _ok(get_ai_insights(get_jwt_identity()))


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

@api_bp.get("/budgets")
@jwt_required()
def api_budgets():
    return _ok(get_budget_status(get_jwt_identity()))


@api_bp.post("/budgets")
@jwt_required()
def api_create_budget():
    uid  = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    today = date.today()
    try:
        b = Budget(
            user_id=uid,
            name=body["name"],
            amount=float(body["amount"]),
            month=body.get("month", today.month),
            year=body.get("year", today.year),
            category_id=body.get("category_id"),
            alert_threshold=body.get("alert_threshold", 80),
        )
        db.session.add(b)
        db.session.commit()
        return _ok(b.to_dict(), "Budget created.", 201)
    except (KeyError, ValueError) as e:
        return _err(str(e), 422)


@api_bp.delete("/budgets/<int:budget_id>")
@jwt_required()
def api_delete_budget(budget_id):
    uid = get_jwt_identity()
    b   = Budget.query.filter_by(id=budget_id, user_id=uid).first_or_404()
    db.session.delete(b)
    db.session.commit()
    return _ok(msg="Budget deleted.")


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

@api_bp.get("/goals")
@jwt_required()
def api_goals():
    uid   = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=uid).all()
    return _ok([g.to_dict() for g in goals])


@api_bp.post("/goals")
@jwt_required()
def api_create_goal():
    uid  = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    try:
        deadline = (
            datetime.strptime(body["deadline"], "%Y-%m-%d").date()
            if body.get("deadline") else None
        )
        g = Goal(
            user_id=uid,
            name=body["name"],
            target_amount=float(body["target_amount"]),
            saved_amount=float(body.get("saved_amount", 0)),
            deadline=deadline,
            icon=body.get("icon", "ti-target"),
            color=body.get("color", "#185FA5"),
        )
        db.session.add(g)
        db.session.commit()
        return _ok(g.to_dict(), "Goal created.", 201)
    except (KeyError, ValueError) as e:
        return _err(str(e), 422)


@api_bp.patch("/goals/<int:goal_id>/contribute")
@jwt_required()
def api_contribute_goal(goal_id):
    uid  = get_jwt_identity()
    goal = Goal.query.filter_by(id=goal_id, user_id=uid).first_or_404()
    body = request.get_json(silent=True) or {}
    try:
        amount = float(body["amount"])
        goal.saved_amount = min(goal.saved_amount + amount, goal.target_amount)
        if goal.saved_amount >= goal.target_amount:
            goal.is_completed = True
        db.session.commit()
        return _ok(goal.to_dict())
    except (KeyError, ValueError) as e:
        return _err(str(e), 422)


@api_bp.delete("/goals/<int:goal_id>")
@jwt_required()
def api_delete_goal(goal_id):
    uid  = get_jwt_identity()
    goal = Goal.query.filter_by(id=goal_id, user_id=uid).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return _ok(msg="Goal deleted.")


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@api_bp.get("/categories")
@jwt_required()
def api_categories_list():
    uid  = get_jwt_identity()
    cats = Category.query.filter(
        (Category.user_id == uid) | (Category.is_default == True)
    ).all()
    return _ok([c.to_dict() for c in cats])

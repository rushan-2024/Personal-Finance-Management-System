from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
import os

from app import db
from app.models import Transaction, Category
from app.services import scan_receipt

transactions_bp = Blueprint("transactions", __name__)


def _get_user_categories():
    return Category.query.filter(
        (Category.user_id == current_user.id) | (Category.is_default == True)
    ).all()


@transactions_bp.route("/")
@login_required
def index():
    page     = request.args.get("page", 1, type=int)
    per_page = 15
    q        = request.args.get("q", "").strip()
    cat_id   = request.args.get("category", type=int)
    txn_type = request.args.get("type", "")
    start    = request.args.get("start", "")
    end      = request.args.get("end", "")

    query = Transaction.query.filter_by(user_id=current_user.id)

    if q:
        query = query.filter(Transaction.description.ilike(f"%{q}%"))
    if cat_id:
        query = query.filter(Transaction.category_id == cat_id)
    if txn_type in ("income", "expense"):
        query = query.filter(Transaction.type == txn_type)
    if start:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(start, "%Y-%m-%d").date())
        except ValueError:
            pass
    if end:
        try:
            query = query.filter(Transaction.date <= datetime.strptime(end, "%Y-%m-%d").date())
        except ValueError:
            pass

    transactions = query.order_by(Transaction.date.desc()).paginate(page=page, per_page=per_page)
    categories   = _get_user_categories()

    return render_template(
        "transactions/index.html",
        transactions=transactions,
        categories=categories,
        filters={"q": q, "category": cat_id, "type": txn_type, "start": start, "end": end},
    )


@transactions_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    categories = _get_user_categories()

    if request.method == "POST":
        try:
            amount      = float(request.form["amount"])
            txn_type    = request.form["type"]
            description = request.form.get("description", "").strip()
            txn_date    = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            cat_id      = request.form.get("category_id", type=int)
            tags        = request.form.get("tags", "").strip()

            if amount <= 0:
                flash("Amount must be positive.", "danger")
                return render_template("transactions/form.html", categories=categories, action="add")

            txn = Transaction(
                user_id=current_user.id,
                amount=amount,
                type=txn_type,
                description=description,
                date=txn_date,
                category_id=cat_id,
                currency=current_user.currency,
                tags=tags or None,
            )
            db.session.add(txn)
            db.session.commit()
            flash("Transaction added successfully! ✅", "success")
            return redirect(url_for("transactions.index"))

        except (ValueError, KeyError) as e:
            flash(f"Invalid data: {e}", "danger")

    return render_template("transactions/form.html", categories=categories, action="add",
                           today=date.today().strftime("%Y-%m-%d"))


@transactions_bp.route("/edit/<int:txn_id>", methods=["GET", "POST"])
@login_required
def edit(txn_id):
    txn        = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()
    categories = _get_user_categories()

    if request.method == "POST":
        try:
            txn.amount      = float(request.form["amount"])
            txn.type        = request.form["type"]
            txn.description = request.form.get("description", "").strip()
            txn.date        = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            txn.category_id = request.form.get("category_id", type=int)
            txn.tags        = request.form.get("tags", "").strip() or None
            db.session.commit()
            flash("Transaction updated! ✅", "success")
            return redirect(url_for("transactions.index"))
        except (ValueError, KeyError) as e:
            flash(f"Invalid data: {e}", "danger")

    return render_template("transactions/form.html", txn=txn, categories=categories, action="edit")


@transactions_bp.route("/delete/<int:txn_id>", methods=["POST"])
@login_required
def delete(txn_id):
    txn = Transaction.query.filter_by(id=txn_id, user_id=current_user.id).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    flash("Transaction deleted.", "info")
    return redirect(url_for("transactions.index"))


@transactions_bp.route("/scan-receipt", methods=["POST"])
@login_required
def scan_receipt_route():
    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["receipt"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename  = f"receipt_{current_user.id}_{int(datetime.now().timestamp())}.png"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    result = scan_receipt(save_path)
    return jsonify(result)

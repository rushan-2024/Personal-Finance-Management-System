"""
run.py – Application entry point.
Usage:
    python run.py                   # development
    flask db init && flask db migrate && flask db upgrade  # DB migrations
    gunicorn -w 4 "run:app"         # production
"""
import os
from app import create_app, db
from app.models import User, Category, Transaction, Budget, Goal, Notification

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db,
        User=User,
        Category=Category,
        Transaction=Transaction,
        Budget=Budget,
        Goal=Goal,
        Notification=Notification,
    )


@app.context_processor
def inject_globals():
    """Inject current date into all templates."""
    from datetime import date
    return dict(today=date.today(), today_date=date.today())


@app.cli.command("seed-demo")
def seed_demo():
    """Seed a demo user with sample transactions."""
    from datetime import date, timedelta
    import random

    demo_email = "demo@finflow.app"
    if User.query.filter_by(email=demo_email).first():
        print("Demo user already exists.")
        return

    user = User(name="Demo User", email=demo_email)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Seed default categories
    from app.auth import _seed_categories, DEFAULT_CATEGORIES
    _seed_categories(user.id)

    cats = Category.query.filter_by(user_id=user.id).all()
    income_cats  = [c for c in cats if c.type == "income"]
    expense_cats = [c for c in cats if c.type == "expense"]

    today = date.today()
    for i in range(90):
        d = today - timedelta(days=i)
        # Income once a month
        if d.day == 1:
            db.session.add(Transaction(
                user_id=user.id, amount=75000, type="income",
                description="Monthly Salary", date=d,
                category_id=income_cats[0].id if income_cats else None,
                currency="INR",
            ))
        # 2-4 expenses per week
        if i % 3 == 0:
            cat = random.choice(expense_cats)
            amt = round(random.uniform(200, 8000), 2)
            db.session.add(Transaction(
                user_id=user.id, amount=amt, type="expense",
                description=f"{cat.name} expense", date=d,
                category_id=cat.id, currency="INR",
            ))

    # Sample goals
    db.session.add(Goal(
        user_id=user.id, name="Emergency Fund",
        target_amount=250000, saved_amount=195000,
        icon="ti-shield-check", color="#1D9E75",
    ))
    db.session.add(Goal(
        user_id=user.id, name="New MacBook",
        target_amount=160000, saved_amount=101000,
        icon="ti-device-laptop", color="#185FA5",
        deadline=date(today.year, today.month + 3 if today.month <= 9 else today.month - 9, 1),
    ))

    # Sample budgets
    expense_cats_slice = expense_cats[:5]
    budget_amounts = [15000, 10000, 7000, 8000, 3000]
    for cat, amt in zip(expense_cats_slice, budget_amounts):
        db.session.add(Budget(
            user_id=user.id, name=cat.name,
            amount=amt, month=today.month, year=today.year,
            category_id=cat.id, alert_threshold=80,
        ))

    db.session.commit()
    print(f"Demo user created: {demo_email} / password123")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)

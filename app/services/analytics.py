"""
analytics.py – All data-crunching for charts, summaries, and AI insights.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import extract, func

from app import db
from app.models import Transaction, Budget, Goal, Notification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _txn_df(user_id: int, months: int = 6) -> pd.DataFrame:
    """Return a DataFrame of the user's transactions for the last *months*."""
    cutoff = date.today() - timedelta(days=months * 30)
    rows = (
        db.session.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.date >= cutoff)
        .all()
    )
    if not rows:
        return pd.DataFrame(columns=["date", "amount", "type", "category"])

    data = [
        {
            "date": t.date,
            "amount": t.amount,
            "type": t.type,
            "category": t.category.name if t.category else "Uncategorized",
        }
        for t in rows
    ]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

def get_dashboard_summary(user_id: int) -> dict[str, Any]:
    today = date.today()
    month_start = today.replace(day=1)

    income = (
        db.session.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.date >= month_start,
        )
        .scalar()
        or 0
    )
    expense = (
        db.session.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= month_start,
        )
        .scalar()
        or 0
    )
    balance = income - expense
    savings_rate = round((balance / income) * 100, 1) if income else 0

    recent = (
        Transaction.query.filter_by(user_id=user_id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(8)
        .all()
    )

    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "savings_rate": savings_rate,
        "recent_transactions": [t.to_dict() for t in recent],
    }


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def get_monthly_chart_data(user_id: int, months: int = 6) -> dict:
    """Income vs expense per month for the last *months*."""
    df = _txn_df(user_id, months)
    labels, income_data, expense_data = [], [], []

    today = date.today()
    for i in range(months - 1, -1, -1):
        # walk backwards month by month
        m = (today.month - i - 1) % 12 + 1
        y = today.year - ((today.month - i - 1) // 12)
        label = f"{calendar.month_abbr[m]} {str(y)[-2:]}"
        labels.append(label)

        if df.empty:
            income_data.append(0)
            expense_data.append(0)
        else:
            mask = (df["date"].dt.month == m) & (df["date"].dt.year == y)
            inc = df[mask & (df["type"] == "income")]["amount"].sum()
            exp = df[mask & (df["type"] == "expense")]["amount"].sum()
            income_data.append(round(inc, 2))
            expense_data.append(round(exp, 2))

    return {"labels": labels, "income": income_data, "expense": expense_data}


def get_category_breakdown(user_id: int) -> dict:
    """Expense breakdown by category for current month."""
    today = date.today()
    rows = (
        db.session.query(
            func.coalesce(Transaction.category_id, 0).label("cat_id"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == today.month,
            extract("year", Transaction.date) == today.year,
        )
        .group_by(Transaction.category_id)
        .all()
    )

    from app.models import Category as Cat

    labels, values, colors = [], [], []
    for row in rows:
        cat = db.session.get(Cat, row.cat_id) if row.cat_id else None
        labels.append(cat.name if cat else "Uncategorized")
        values.append(round(row.total, 2))
        colors.append(cat.color if cat else "#888780")

    pie_items = [{"label": l, "value": v, "color": c} for l, v, c in zip(labels, values, colors)]
    return {"labels": labels, "values": values, "colors": colors, "pie_items": pie_items}


def get_savings_trend(user_id: int, months: int = 6) -> dict:
    data = get_monthly_chart_data(user_id, months)
    rates = []
    for inc, exp in zip(data["income"], data["expense"]):
        rate = round(((inc - exp) / inc) * 100, 1) if inc else 0
        rates.append(max(0, rate))
    return {"labels": data["labels"], "savings_rate": rates}


# ---------------------------------------------------------------------------
# Budget analysis
# ---------------------------------------------------------------------------

def get_budget_status(user_id: int) -> list[dict]:
    today = date.today()
    budgets = Budget.query.filter_by(
        user_id=user_id, month=today.month, year=today.year
    ).all()

    result = []
    for b in budgets:
        spent = (
            db.session.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.type == "expense",
                extract("month", Transaction.date) == today.month,
                extract("year", Transaction.date) == today.year,
            )
            .scalar()
            or 0
        )
        pct = round((spent / b.amount) * 100, 1) if b.amount else 0
        status = "danger" if pct >= 100 else "warning" if pct >= b.alert_threshold else "success"

        # Auto-notify
        if pct >= b.alert_threshold:
            _maybe_notify(
                user_id=user_id,
                title=f"Budget alert: {b.name}",
                message=f"You've used {pct:.0f}% of your {b.name} budget.",
                ntype="warning",
                dedup_key=f"budget-{b.id}-{today.month}-{today.year}",
            )

        result.append({**b.to_dict(), "spent": round(spent, 2), "percent": pct, "status": status})

    return result


def _maybe_notify(user_id, title, message, ntype, dedup_key):
    """Create a notification only if it doesn't already exist this month."""
    exists = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.title == title,
    ).first()
    if not exists:
        db.session.add(
            Notification(user_id=user_id, title=title, message=message, type=ntype)
        )
        db.session.commit()


# ---------------------------------------------------------------------------
# AI-style insights (rule-based)
# ---------------------------------------------------------------------------

def get_ai_insights(user_id: int) -> list[dict]:
    df = _txn_df(user_id, 3)
    insights = []

    if df.empty:
        insights.append({
            "icon": "ti-info-circle", "color": "#185FA5",
            "bg": "#E6F1FB", "title": "No data yet",
            "desc": "Add some transactions to start receiving personalised insights.",
        })
        return insights

    today = date.today()
    this_month = df[
        (df["date"].dt.month == today.month) & (df["date"].dt.year == today.year)
    ]
    last_month = df[
        (df["date"].dt.month == (today.month - 1 or 12))
    ]

    # 1. Savings rate
    inc = this_month[this_month["type"] == "income"]["amount"].sum()
    exp = this_month[this_month["type"] == "expense"]["amount"].sum()
    if inc > 0:
        rate = (inc - exp) / inc * 100
        if rate >= 30:
            insights.append({
                "icon": "ti-trending-up", "color": "#1D9E75", "bg": "#E1F5EE",
                "title": f"Great savings rate: {rate:.0f}%",
                "desc": "You're saving more than 30% of your income this month. Keep it up!",
            })
        elif rate < 10:
            insights.append({
                "icon": "ti-alert-triangle", "color": "#E24B4A", "bg": "#FCEBEB",
                "title": f"Low savings rate: {rate:.0f}%",
                "desc": "You're saving less than 10% of income. Try reducing discretionary spending.",
            })

    # 2. Top spending category
    if not this_month.empty:
        exp_df = this_month[this_month["type"] == "expense"]
        if not exp_df.empty:
            top_cat = exp_df.groupby("category")["amount"].sum().idxmax()
            top_amt = exp_df.groupby("category")["amount"].sum().max()
            insights.append({
                "icon": "ti-flame", "color": "#BA7517", "bg": "#FAEEDA",
                "title": f"Top spend: {top_cat}",
                "desc": f"You've spent ₹{top_amt:,.0f} on {top_cat} this month — your biggest expense category.",
            })

    # 3. Month-over-month expense change
    this_exp = this_month[this_month["type"] == "expense"]["amount"].sum()
    last_exp = last_month[last_month["type"] == "expense"]["amount"].sum()
    if last_exp > 0:
        change = ((this_exp - last_exp) / last_exp) * 100
        if change > 15:
            insights.append({
                "icon": "ti-arrows-up", "color": "#E24B4A", "bg": "#FCEBEB",
                "title": f"Expenses up {change:.0f}% vs last month",
                "desc": f"Your spending rose from ₹{last_exp:,.0f} to ₹{this_exp:,.0f}. Review recent transactions.",
            })
        elif change < -10:
            insights.append({
                "icon": "ti-arrows-down", "color": "#1D9E75", "bg": "#E1F5EE",
                "title": f"Expenses down {abs(change):.0f}% vs last month",
                "desc": f"Great job! You reduced spending from ₹{last_exp:,.0f} to ₹{this_exp:,.0f}.",
            })

    # 4. Weekend vs weekday
    exp_df = df[df["type"] == "expense"].copy()
    if not exp_df.empty:
        exp_df["dow"] = exp_df["date"].dt.dayofweek
        wknd = exp_df[exp_df["dow"] >= 5]["amount"].mean()
        wkdy = exp_df[exp_df["dow"] < 5]["amount"].mean()
        if wknd and wkdy and wknd > wkdy * 1.5:
            insights.append({
                "icon": "ti-calendar-event", "color": "#534AB7", "bg": "#EEEDFE",
                "title": "Weekend spending spike",
                "desc": f"You spend {wknd/wkdy:.1f}x more per transaction on weekends. Plan weekend activities in advance.",
            })

    # 5. Investment nudge
    if inc > 0 and this_exp / inc < 0.6:
        surplus = round(inc - this_exp, 0)
        insights.append({
            "icon": "ti-bulb", "color": "#185FA5", "bg": "#E6F1FB",
            "title": "Invest your surplus",
            "desc": f"You have a surplus of ₹{surplus:,.0f} this month. Consider investing ₹{surplus*0.5:,.0f} in an index fund SIP.",
        })

    return insights[:6]  # cap at 6

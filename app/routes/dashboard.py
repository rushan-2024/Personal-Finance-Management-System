from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services import (
    get_dashboard_summary, get_monthly_chart_data,
    get_category_breakdown, get_budget_status, get_ai_insights,
)
from app.models import Notification

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    summary     = get_dashboard_summary(current_user.id)
    chart_data  = get_monthly_chart_data(current_user.id)
    pie_data    = get_category_breakdown(current_user.id)
    budgets     = get_budget_status(current_user.id)
    insights    = get_ai_insights(current_user.id)
    unread_notifs = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    return render_template(
        "dashboard/index.html",
        summary=summary,
        chart_data=chart_data,
        pie_data=pie_data,
        budgets=budgets,
        insights=insights,
        unread_notifs=unread_notifs,
    )

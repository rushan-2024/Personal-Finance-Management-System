"""
email_service.py – Send transactional and report emails via Flask-Mail.
"""
from __future__ import annotations

from datetime import date
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail


MONTHLY_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:600px;margin:auto;color:#2C2C2A">
  <div style="background:#1D9E75;padding:24px;border-radius:12px 12px 0 0;">
    <h1 style="color:#fff;margin:0;font-size:22px;">⚡ FinFlow Monthly Report</h1>
    <p style="color:#9FE1CB;margin:4px 0 0;">{{ month_label }}</p>
  </div>
  <div style="border:0.5px solid #D3D1C7;border-top:none;padding:24px;border-radius:0 0 12px 12px;">
    <table width="100%" cellspacing="0" cellpadding="8">
      <tr>
        <td style="background:#E1F5EE;border-radius:8px;text-align:center;padding:16px;">
          <div style="font-size:12px;color:#0F6E56;">INCOME</div>
          <div style="font-size:22px;font-weight:600;color:#1D9E75;">₹{{ income }}</div>
        </td>
        <td width="12"></td>
        <td style="background:#FCEBEB;border-radius:8px;text-align:center;padding:16px;">
          <div style="font-size:12px;color:#993C1D;">EXPENSE</div>
          <div style="font-size:22px;font-weight:600;color:#E24B4A;">₹{{ expense }}</div>
        </td>
        <td width="12"></td>
        <td style="background:#E6F1FB;border-radius:8px;text-align:center;padding:16px;">
          <div style="font-size:12px;color:#0C447C;">SAVINGS</div>
          <div style="font-size:22px;font-weight:600;color:#185FA5;">₹{{ savings }}</div>
        </td>
      </tr>
    </table>
    {% if insights %}
    <h3 style="margin:24px 0 8px;">🧠 AI Insights</h3>
    <ul style="padding-left:20px;color:#5F5E5A;">
      {% for ins in insights %}
      <li style="margin-bottom:6px;">{{ ins }}</li>
      {% endfor %}
    </ul>
    {% endif %}
    <div style="margin-top:24px;padding-top:16px;border-top:0.5px solid #D3D1C7;font-size:12px;color:#888780;">
      You're receiving this because email notifications are enabled in your FinFlow account.
    </div>
  </div>
</body>
</html>
"""

BUDGET_ALERT_TEMPLATE = """
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:500px;margin:auto;">
  <div style="background:#E24B4A;padding:20px;border-radius:12px 12px 0 0;">
    <h2 style="color:#fff;margin:0;">⚠️ Budget Alert</h2>
  </div>
  <div style="border:0.5px solid #D3D1C7;border-top:none;padding:20px;border-radius:0 0 12px 12px;">
    <p>Hi {{ name }},</p>
    <p>You've used <strong>{{ percent }}%</strong> of your <strong>{{ budget_name }}</strong> budget.</p>
    <p>Spent: ₹{{ spent }} of ₹{{ limit }}</p>
    <p style="color:#888780;font-size:12px;">Manage your budgets in FinFlow to stay on track.</p>
  </div>
</body>
</html>
"""


def send_monthly_report(
    to: str,
    name: str,
    income: float,
    expense: float,
    month_label: str,
    insights: list[str] | None = None,
) -> bool:
    try:
        html = render_template_string(
            MONTHLY_REPORT_TEMPLATE,
            month_label=month_label,
            income=f"{income:,.2f}",
            expense=f"{expense:,.2f}",
            savings=f"{income - expense:,.2f}",
            insights=insights or [],
        )
        msg = Message(
            subject=f"FinFlow — Your {month_label} Financial Report",
            recipients=[to],
            html=html,
        )
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error(f"Failed to send monthly report to {to}: {exc}")
        return False


def send_budget_alert(
    to: str,
    name: str,
    budget_name: str,
    percent: float,
    spent: float,
    limit: float,
) -> bool:
    try:
        html = render_template_string(
            BUDGET_ALERT_TEMPLATE,
            name=name,
            budget_name=budget_name,
            percent=f"{percent:.0f}",
            spent=f"{spent:,.2f}",
            limit=f"{limit:,.2f}",
        )
        msg = Message(
            subject=f"FinFlow — Budget Alert: {budget_name}",
            recipients=[to],
            html=html,
        )
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error(f"Budget alert email failed: {exc}")
        return False

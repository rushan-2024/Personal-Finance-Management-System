from datetime import date, datetime
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services import export_csv, export_excel, export_pdf

reports_bp = Blueprint("reports", __name__)


def _parse_dates():
    today  = date.today()
    start_str = request.args.get("start", today.replace(day=1).strftime("%Y-%m-%d"))
    end_str   = request.args.get("end",   today.strftime("%Y-%m-%d"))
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end   = datetime.strptime(end_str,   "%Y-%m-%d").date()
    except ValueError:
        start = today.replace(day=1)
        end   = today
    return start, end


@reports_bp.route("/")
@login_required
def index():
    today = date.today()
    return render_template("reports/index.html",
                           default_start=today.replace(day=1).strftime("%Y-%m-%d"),
                           default_end=today.strftime("%Y-%m-%d"))


@reports_bp.route("/export/csv")
@login_required
def export_csv_route():
    start, end = _parse_dates()
    buf = export_csv(current_user.id, start, end)
    fname = f"finflow_{start}_{end}.csv"
    return send_file(buf, mimetype="text/csv",
                     as_attachment=True, download_name=fname)


@reports_bp.route("/export/excel")
@login_required
def export_excel_route():
    start, end = _parse_dates()
    buf = export_excel(current_user.id, start, end)
    fname = f"finflow_{start}_{end}.xlsx"
    return send_file(buf,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=fname)


@reports_bp.route("/export/pdf")
@login_required
def export_pdf_route():
    start, end = _parse_dates()
    buf = export_pdf(current_user.id, start, end, user_name=current_user.name)
    fname = f"finflow_{start}_{end}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=fname)

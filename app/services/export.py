"""
export.py – Generate PDF, Excel, and CSV financial reports.
"""
from __future__ import annotations

import io
import csv
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from app.models import Transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_transactions(user_id: int, start: date, end: date):
    return (
        Transaction.query
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .order_by(Transaction.date)
        .all()
    )


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def export_csv(user_id: int, start: date, end: date) -> io.BytesIO:
    txns = _get_transactions(user_id, start, end)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Description", "Category", "Type", "Amount", "Currency"])
    for t in txns:
        writer.writerow([
            t.date.strftime("%d-%m-%Y"),
            t.description or "",
            t.category.name if t.category else "Uncategorized",
            t.type.title(),
            t.amount,
            t.currency,
        ])
    return io.BytesIO(buf.getvalue().encode())


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

def export_excel(user_id: int, start: date, end: date) -> io.BytesIO:
    txns = _get_transactions(user_id, start, end)
    rows = [
        {
            "Date": t.date.strftime("%d-%m-%Y"),
            "Description": t.description or "",
            "Category": t.category.name if t.category else "Uncategorized",
            "Type": t.type.title(),
            "Amount": t.amount,
            "Currency": t.currency,
        }
        for t in txns
    ]
    df = pd.DataFrame(rows)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")

        # Summary sheet
        if not df.empty:
            income  = df[df["Type"] == "Income"]["Amount"].sum()
            expense = df[df["Type"] == "Expense"]["Amount"].sum()
            summary = pd.DataFrame({
                "Metric": ["Total Income", "Total Expense", "Net Savings", "Savings Rate"],
                "Value": [
                    income, expense, income - expense,
                    f"{(income - expense) / income * 100:.1f}%" if income else "N/A",
                ],
            })
            summary.to_excel(writer, index=False, sheet_name="Summary")

    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def export_pdf(user_id: int, start: date, end: date, user_name: str = "User") -> io.BytesIO:
    txns = _get_transactions(user_id, start, end)
    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    GREEN  = colors.HexColor("#1D9E75")
    RED    = colors.HexColor("#E24B4A")
    DARK   = colors.HexColor("#2C2C2A")
    LIGHT  = colors.HexColor("#F1EFE8")

    title_style = ParagraphStyle("title", parent=styles["Title"],
        fontSize=22, textColor=GREEN, alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
    label_style = ParagraphStyle("label", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("value", parent=styles["Normal"],
        fontSize=12, textColor=DARK, fontName="Helvetica-Bold")

    elements = []

    # Header
    elements.append(Paragraph("FinFlow", title_style))
    elements.append(Paragraph(
        f"Financial Report · {user_name} · "
        f"{start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')}",
        sub_style,
    ))
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    elements.append(Spacer(1, 0.4*cm))

    # Summary cards
    income  = sum(t.amount for t in txns if t.type == "income")
    expense = sum(t.amount for t in txns if t.type == "expense")
    savings = income - expense
    rate    = f"{(savings / income * 100):.1f}%" if income else "N/A"

    summary_data = [
        ["Total Income", "Total Expense", "Net Savings", "Savings Rate"],
        [
            f"₹{income:,.2f}",
            f"₹{expense:,.2f}",
            f"₹{savings:,.2f}",
            rate,
        ],
    ]
    summary_table = Table(summary_data, colWidths=[4.5*cm]*4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.grey),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("FONTSIZE",   (0, 1), (-1, 1), 13),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0, 1), (0, 1), GREEN),
        ("TEXTCOLOR",  (1, 1), (1, 1), RED),
        ("TEXTCOLOR",  (2, 1), (2, 1), GREEN),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.white]),
        ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, colors.HexColor("#D3D1C7")),
        ("PADDING",    (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.6*cm))

    # Transactions table
    elements.append(Paragraph("Transaction Details", styles["Heading2"]))
    elements.append(Spacer(1, 0.2*cm))

    if txns:
        headers = ["Date", "Description", "Category", "Type", "Amount"]
        rows = [headers] + [
            [
                t.date.strftime("%d %b %Y"),
                (t.description or "")[:35],
                t.category.name if t.category else "—",
                t.type.title(),
                f"₹{t.amount:,.2f}",
            ]
            for t in txns
        ]
        col_widths = [2.5*cm, 6*cm, 3.5*cm, 2.5*cm, 3*cm]
        txn_table = Table(rows, colWidths=col_widths, repeatRows=1)
        txn_style = [
            ("BACKGROUND",  (0, 0), (-1, 0), GREEN),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ALIGN",       (4, 0), (4, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D1C7")),
            ("INNERGRID",   (0, 0), (-1, -1), 0.25, colors.HexColor("#D3D1C7")),
            ("PADDING",     (0, 0), (-1, -1), 6),
        ]
        # Colour income/expense rows
        for i, t in enumerate(txns, start=1):
            col = GREEN if t.type == "income" else RED
            txn_style.append(("TEXTCOLOR", (4, i), (4, i), col))

        txn_table.setStyle(TableStyle(txn_style))
        elements.append(txn_table)
    else:
        elements.append(Paragraph("No transactions found for the selected period.", styles["Normal"]))

    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D3D1C7")))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        f"Generated by FinFlow on {date.today().strftime('%d %b %Y')}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(elements)
    buf.seek(0)
    return buf

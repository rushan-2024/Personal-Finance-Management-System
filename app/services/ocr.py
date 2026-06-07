"""
ocr.py – Receipt scanning using Tesseract OCR + OpenCV.
Returns extracted amount, date, and merchant name.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _preprocess(image_path: str) -> "np.ndarray | None":
    """Grayscale + threshold for better OCR accuracy."""
    if not OCR_AVAILABLE:
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )
    return thresh


def _extract_amount(text: str) -> float | None:
    """Find the largest currency amount in the OCR text."""
    # Patterns: ₹1,234.56  |  Rs. 500  |  1234.00  |  TOTAL 999
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([\d,]+\.?\d*)",
        r"(?:total|amount|grand\s*total|net\s*amount)[:\s]*([\d,]+\.?\d*)",
        r"([\d,]+\.\d{2})",
    ]
    amounts = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            try:
                amounts.append(float(m.group(1).replace(",", "")))
            except ValueError:
                pass
    return max(amounts) if amounts else None


def _extract_date(text: str) -> date | None:
    """Try several date formats from the OCR text."""
    formats = [
        (r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b", "%d-%m-%Y"),
        (r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b", "%Y-%m-%d"),
        (r"\b(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})\b", "%d %b %Y"),
    ]
    for pat, fmt in formats:
        m = re.search(pat, text)
        if m:
            try:
                raw = "-".join(m.groups())
                return datetime.strptime(raw, fmt.replace("/", "-")).date()
            except ValueError:
                pass
    return None


def _extract_merchant(text: str) -> str | None:
    """Heuristic: first non-empty line is usually the merchant/store name."""
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 3 and not re.match(r"^[\d\s\W]+$", line):
            return line[:80]
    return None


def scan_receipt(image_path: str) -> dict:
    """
    Scan a receipt image and return extracted fields.

    Returns:
        {
            "amount": float | None,
            "date": str | None,         # ISO format YYYY-MM-DD
            "merchant": str | None,
            "raw_text": str,
            "success": bool,
            "error": str | None,
        }
    """
    if not OCR_AVAILABLE:
        return {
            "amount": None, "date": None, "merchant": None,
            "raw_text": "", "success": False,
            "error": "OCR libraries (pytesseract, opencv) not installed.",
        }

    if not Path(image_path).exists():
        return {
            "amount": None, "date": None, "merchant": None,
            "raw_text": "", "success": False,
            "error": "Image file not found.",
        }

    try:
        img = _preprocess(image_path)
        pil_img = Image.fromarray(img) if img is not None else Image.open(image_path)
        raw_text = pytesseract.image_to_string(pil_img, lang="eng")

        amount   = _extract_amount(raw_text)
        txn_date = _extract_date(raw_text)
        merchant = _extract_merchant(raw_text)

        return {
            "amount":   amount,
            "date":     txn_date.isoformat() if txn_date else None,
            "merchant": merchant,
            "raw_text": raw_text,
            "success":  True,
            "error":    None,
        }
    except Exception as exc:
        return {
            "amount": None, "date": None, "merchant": None,
            "raw_text": "", "success": False,
            "error": str(exc),
        }

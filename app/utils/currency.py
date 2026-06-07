"""
currency.py – Live exchange rate fetching (with fallback static rates).
"""
from __future__ import annotations

import os
import requests
from functools import lru_cache
from datetime import datetime, timedelta

# Fallback static rates relative to INR (updated manually when API unavailable)
FALLBACK_RATES = {
    "INR": 1.0,
    "USD": 0.012,
    "EUR": 0.011,
    "GBP": 0.0095,
    "JPY": 1.83,
    "AED": 0.044,
    "SGD": 0.016,
    "AUD": 0.018,
}

_cache: dict[str, tuple[datetime, dict]] = {}


def get_rates(base: str = "INR") -> dict[str, float]:
    """
    Return exchange rates with *base* as 1.0.
    Uses exchangeratesapi.io if EXCHANGE_RATE_API is set, otherwise fallback.
    Results cached for 1 hour.
    """
    api_key = os.environ.get("EXCHANGE_RATE_API")
    now = datetime.utcnow()

    if base in _cache:
        cached_at, rates = _cache[base]
        if now - cached_at < timedelta(hours=1):
            return rates

    if api_key:
        try:
            url = f"https://api.exchangeratesapi.io/v1/latest?access_key={api_key}&base={base}"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get("success") and "rates" in data:
                rates = data["rates"]
                rates[base] = 1.0
                _cache[base] = (now, rates)
                return rates
        except Exception:
            pass

    # Fallback: convert FALLBACK_RATES to requested base
    if base not in FALLBACK_RATES:
        return FALLBACK_RATES

    base_rate = FALLBACK_RATES[base]
    rates = {currency: round(r / base_rate, 6) for currency, r in FALLBACK_RATES.items()}
    _cache[base] = (now, rates)
    return rates


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert *amount* from one currency to another."""
    if from_currency == to_currency:
        return amount
    rates = get_rates(from_currency)
    rate = rates.get(to_currency)
    if rate is None:
        raise ValueError(f"Unknown currency: {to_currency}")
    return round(amount * rate, 2)

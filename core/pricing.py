import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Safe imports for package or standalone use
try:
    from .utils import logger, FMP_BASE_URL, FMP_API_KEY
    from .manual_config import get_manual_price
except ImportError:
    from utils import logger, FMP_BASE_URL, FMP_API_KEY
    from manual_config import get_manual_price


def get_current_price(symbol, date=None, verbose=True):
    """
    Fetch stock closing price with fallback: FMP → yfinance → manual config.
    Returns float price (₹) or 0.0 if all sources fail.
    """
    # print(f"Price of {symbol} on {date}!!!!!!!!!!!!!!")
    if verbose:
        logger.info(f"Requesting price for {symbol}, date: {date}")

    # --- Parse date safely ---
    if not date:
        price_date = datetime.now().date()
    elif isinstance(date, (datetime, pd.Timestamp)):
        price_date = date.date()
    else:
        try:
            parsed = pd.to_datetime(date, errors='coerce')
            if pd.isna(parsed):
                parsed = pd.to_datetime(date, dayfirst=True, errors='coerce')
            price_date = parsed.date() if pd.notna(parsed) else datetime.now().date()
        except Exception as e:
            if verbose:
                logger.warning(f"Invalid date format '{date}': {e}")
            price_date = datetime.now().date()

    # --- Try FMP API first ---
    for suffix in [".NS", ".BO"]:
        fmp_symbol = f"{symbol}{suffix}"
        try:
            endpoint = f"{FMP_BASE_URL}/historical-price-full/{fmp_symbol}"
            params = {
                "from": (price_date - timedelta(days=7)).strftime("%Y-%m-%d"),
                "to": (price_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "apikey": FMP_API_KEY,
            }

            response = requests.get(endpoint, params=params, timeout=10)
            if response.status_code != 200:
                continue

            try:
                data = response.json()
            except ValueError:
                if verbose:
                    logger.warning(f"Invalid JSON from FMP for {fmp_symbol}")
                continue

            hist = data.get("historical", [])
            if not hist:
                continue

            # exact date match
            for entry in hist:
                entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                if entry_date == price_date:
                    closing = float(entry["close"])
                    if verbose:
                        logger.info(f"✓ FMP: {fmp_symbol} on {entry_date} → ₹{closing}")
                    return closing

            # closest earlier available date
            entries_before = [
                e for e in hist
                if datetime.strptime(e["date"], "%Y-%m-%d").date() <= price_date
            ]
            if entries_before:
                best = max(entries_before,
                           key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d").date())
                entry_date = datetime.strptime(best["date"], "%Y-%m-%d").date()
                closing = float(best["close"])
                if verbose:
                    delta = (price_date - entry_date).days
                    logger.warning(f"⚠ FMP: Using {entry_date} ({delta}d earlier) → ₹{closing}")
                return closing

        except Exception as e:
            if verbose:
                logger.debug(f"FMP failed for {fmp_symbol}: {e}")
            continue

    # --- Try yfinance fallback ---
    yf_symbol = f"{symbol}.NS"
    try:
        if verbose:
            logger.info(f"Trying yfinance for {yf_symbol}")

        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=price_date - timedelta(days=30),
            end=price_date + timedelta(days=5)
        )

        if not hist.empty:
            try:
                closing = float(hist.loc[str(price_date), "Close"])
                if verbose:
                    logger.info(f"✓ yfinance: {symbol} on {price_date} → ₹{closing}")
                return closing
            except KeyError:
                # use closest earlier date
                hist_dates = hist.index.normalize()
                earlier = hist_dates[hist_dates <= pd.Timestamp(price_date)]
                if len(earlier) > 0:
                    best_date = earlier[-1]
                    closing = float(hist.loc[best_date, "Close"])
                    delta = (price_date - best_date.date()).days
                    if verbose:
                        logger.warning(f"⚠ yfinance: Using {best_date.date()} ({delta}d earlier) → ₹{closing}")
                    return closing
    except Exception as e:
        if verbose:
            logger.error(f"✗ yfinance failed for {yf_symbol}: {e}")

    # --- Manual config fallback ---
    manual_price = get_manual_price(symbol, date)
    if manual_price and manual_price > 0:
        if verbose:
            logger.info(f"✓ Manual config: {symbol} → ₹{manual_price}")
        return manual_price

    if verbose:
        logger.warning(f"✗ All sources failed for {symbol}")
    return 0.0




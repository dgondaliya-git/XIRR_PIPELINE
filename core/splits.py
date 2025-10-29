import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from .utils import logger, FMP_BASE_URL
from .manual_config import get_splits_from_manual_config


def get_splits_from_fmp(symbol, api_key):
    """Fetch splits from FMP API."""
    splits = []
    for suffix in [".NS", ".BO"]:
        fmp_symbol = f"{symbol}{suffix}"
        url = f"{FMP_BASE_URL}/historical-price-full/stock_split/{fmp_symbol}"

        try:
            response = requests.get(url, params={'apikey': api_key}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('historical'):
                    for split in data['historical']:
                        splits.append({
                            'date': datetime.strptime(split['date'], '%Y-%m-%d'),
                            'numerator': split['numerator'],
                            'denominator': split['denominator'],
                            'ratio': split['numerator'] / split['denominator']
                        })
                    break
        except Exception as e:
            logger.debug(f"FMP error for {fmp_symbol}: {e}")
            continue

    return sorted(splits, key=lambda x: x['date']) if splits else []


def get_splits_from_yfinance(symbol):
    """Fetch splits from Yahoo Finance."""
    splits = []
    for suffix in [".NS", ".BO"]:
        yf_symbol = f"{symbol}{suffix}"
        try:
            ticker = yf.Ticker(yf_symbol)
            split_data = ticker.splits

            if not split_data.empty:
                for date, ratio in split_data.items():
                    splits.append({
                        'date': date.to_pydatetime(),
                        'numerator': int(ratio) if ratio >= 1 else 1,
                        'denominator': 1 if ratio >= 1 else int(1/ratio),
                        'ratio': float(ratio)
                    })
                break
        except Exception as e:
            logger.debug(f"yfinance error for {yf_symbol}: {e}")
            continue

    return sorted(splits, key=lambda x: x['date']) if splits else []


def normalize_splits(splits):
    """Normalize splits list for comparison (by date only)."""
    if not splits:
        return set()
    return {s['date'].strftime('%Y-%m-%d') for s in splits}


def get_stock_splits(symbol, api_key):
    """
    Fetch stock split history with triple fallback: FMP → yfinance → manual config.
    Compares results and alerts if discrepancies found.

    Returns:
        list: Sorted list of split dictionaries with date, numerator, denominator, and ratio
    """
    # Try all three sources
    fmp_splits = get_splits_from_fmp(symbol, api_key)
    yf_splits = get_splits_from_yfinance(symbol)
    manual_splits = get_splits_from_manual_config(symbol)

    # Normalize for comparison
    fmp_dates = normalize_splits(fmp_splits)
    yf_dates = normalize_splits(yf_splits)
    manual_dates = normalize_splits(manual_splits)

    # Check for discrepancies
    all_dates = fmp_dates | yf_dates | manual_dates

    if len(all_dates) > 0:
        sources_found = []
        if fmp_dates:
            sources_found.append(f"FMP({len(fmp_dates)})")
        if yf_dates:
            sources_found.append(f"yfinance({len(yf_dates)})")
        if manual_dates:
            sources_found.append(f"MANUAL({len(manual_dates)})")

        # Check if results differ
        if len(sources_found) > 1 and not (fmp_dates == yf_dates == manual_dates):
            print(f"  ⚠️  {symbol}: SPLIT DATA MISMATCH - CHECK MANUALLY")
            print(f"      Sources: {', '.join(sources_found)}")
            if fmp_dates:
                print(f"      FMP dates: {sorted(fmp_dates)}")
            if yf_dates:
                print(f"      yfinance dates: {sorted(yf_dates)}")
            if manual_dates:
                print(f"      MANUAL dates: {sorted(manual_dates)}")

    # Return based on priority: Manual → FMP → yfinance
    if manual_splits:
        print(f"  ✓ Using MANUAL config for {symbol}")
        return manual_splits
    elif fmp_splits:
        return fmp_splits
    elif yf_splits:
        return yf_splits
    else:
        return []


# import requests
# import yfinance as yf
# import pandas as pd
# from datetime import datetime, timedelta
# from .utils import logger, FMP_BASE_URL
# from .manual_config import get_splits_from_manual_config


# def get_splits_from_fmp(symbol, api_key):
#     """Fetch splits from FMP API."""
#     splits = []
#     for suffix in [".NS", ".BO"]:
#         fmp_symbol = f"{symbol}{suffix}"
#         url = f"{FMP_BASE_URL}/historical-price-full/stock_split/{fmp_symbol}"

#         try:
#             response = requests.get(url, params={'apikey': api_key}, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 if data.get('historical'):
#                     for split in data['historical']:
#                         splits.append({
#                             'date': datetime.strptime(split['date'], '%Y-%m-%d'),
#                             'numerator': split['numerator'],
#                             'denominator': split['denominator'],
#                             'ratio': split['numerator'] / split['denominator']
#                         })
#                     break
#         except Exception as e:
#             logger.debug(f"FMP error for {fmp_symbol}: {e}")
#             continue

#     return sorted(splits, key=lambda x: x['date']) if splits else []


# def get_splits_from_yfinance(symbol):
#     """Fetch splits from Yahoo Finance."""
#     splits = []
#     for suffix in [".NS", ".BO"]:
#         yf_symbol = f"{symbol}{suffix}"
#         try:
#             ticker = yf.Ticker(yf_symbol)
#             split_data = ticker.splits

#             if not split_data.empty:
#                 for date, ratio in split_data.items():
#                     splits.append({
#                         'date': date.to_pydatetime(),
#                         'numerator': int(ratio) if ratio >= 1 else 1,
#                         'denominator': 1 if ratio >= 1 else int(1/ratio),
#                         'ratio': float(ratio)
#                     })
#                 break
#         except Exception as e:
#             logger.debug(f"yfinance error for {yf_symbol}: {e}")
#             continue

#     return sorted(splits, key=lambda x: x['date']) if splits else []


# def get_splits_from_nsepy(symbol):
#     """Fetch stock split details from NSEpy corporate actions."""
#     splits = []

#     try:
#         try:
#             from nsepy import get_corporate_actions
#         except ImportError:
#             try:
#                 from nsepy.history import get_corporate_actions
#             except ImportError:
#                 print("get_corporate_actions not available in this nsepy version")
#                 return []

#         start = datetime.now() - timedelta(days=3650)
#         end = datetime.now()

#         actions = get_corporate_actions(symbol=symbol, start=start, end=end)

#         if actions is None or actions.empty:
#             return []

#         mask = actions['purpose'].str.lower().str.contains('split', na=False)
#         split_rows = actions[mask]

#         for date, row in split_rows.iterrows():
#             purpose = str(row.get('purpose', '')).lower()

#             try:
#                 if 'from' in purpose and 'to' in purpose:
#                     from_part = purpose.split('from')[1].split('to')[0]
#                     to_part = purpose.split('to')[1]

#                     old_val = float(''.join(c for c in from_part if c.isdigit() or c == '.'))
#                     new_val = float(''.join(c for c in to_part if c.isdigit() or c == '.'))

#                     ratio = old_val / new_val if new_val > 0 else None

#                     splits.append({
#                         'date': pd.to_datetime(date),
#                         'old_face_value': old_val,
#                         'new_face_value': new_val,
#                         'split_ratio': f"{int(old_val)}:{int(new_val)}",
#                         'ratio': ratio
#                     })
#             except (ValueError, ZeroDivisionError) as parse_error:
#                 continue

#     except Exception as e:
#         logger.debug(f"Error fetching corporate actions for {symbol}: {e}")
#         return []

#     return sorted(splits, key=lambda x: x['date']) if splits else []


# def normalize_splits(splits):
#     """Normalize splits list for comparison (by date only)."""
#     if not splits:
#         return set()
#     return {s['date'].strftime('%Y-%m-%d') for s in splits}


# def get_stock_splits(symbol, api_key):
#     """
#     Fetch stock split history with quadruple fallback: FMP → yfinance → nsepy → manual config.
#     Compares results and alerts if discrepancies found.

#     Returns:
#         list: Sorted list of split dictionaries with date, numerator, denominator, and ratio
#     """
#     # Try all four sources
#     fmp_splits = get_splits_from_fmp(symbol, api_key)
#     yf_splits = get_splits_from_yfinance(symbol)
#     nsepy_splits = get_splits_from_nsepy(symbol)
#     manual_splits = get_splits_from_manual_config(symbol)

#     # Normalize for comparison
#     fmp_dates = normalize_splits(fmp_splits)
#     yf_dates = normalize_splits(yf_splits)
#     nsepy_dates = normalize_splits(nsepy_splits)
#     manual_dates = normalize_splits(manual_splits)

#     # Check for discrepancies
#     all_dates = fmp_dates | yf_dates | nsepy_dates | manual_dates

#     if len(all_dates) > 0:
#         sources_found = []
#         if fmp_dates:
#             sources_found.append(f"FMP({len(fmp_dates)})")
#         if yf_dates:
#             sources_found.append(f"yfinance({len(yf_dates)})")
#         if nsepy_dates:
#             sources_found.append(f"nsepy({len(nsepy_dates)})")
#         if manual_dates:
#             sources_found.append(f"MANUAL({len(manual_dates)})")

#         # Check if results differ
#         if len(sources_found) > 1 and not (fmp_dates == yf_dates == nsepy_dates == manual_dates):
#             print(f"  ⚠️  {symbol}: SPLIT DATA MISMATCH - CHECK MANUALLY")
#             print(f"      Sources: {', '.join(sources_found)}")
#             if fmp_dates:
#                 print(f"      FMP dates: {sorted(fmp_dates)}")
#             if yf_dates:
#                 print(f"      yfinance dates: {sorted(yf_dates)}")
#             if nsepy_dates:
#                 print(f"      nsepy dates: {sorted(nsepy_dates)}")
#             if manual_dates:
#                 print(f"      MANUAL dates: {sorted(manual_dates)}")

#     # Return based on priority: Manual → FMP → yfinance → nsepy
#     # Manual config has highest priority as it's user-verified
#     if manual_splits:
#         print(f"  ✓ Using MANUAL config for {symbol}")
#         return manual_splits
#     elif fmp_splits:
#         return fmp_splits
#     elif yf_splits:
#         return yf_splits
#     elif nsepy_splits:
#         return nsepy_splits
#     else:
#         return []
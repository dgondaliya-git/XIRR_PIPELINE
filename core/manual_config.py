import json
import os
from datetime import datetime
from .utils import logger, MANUAL_SPLITS_CONFIG, MANUAL_PRICES_CONFIG


def load_manual_prices():
    """
    Load manual stock prices from config file.

    Returns:
        dict: Dictionary with symbol as key and price info as value
    """
    if not os.path.exists(MANUAL_PRICES_CONFIG):
        # Create default config file with example
        default_config = {
            "EXAMPLE": {
                "price": 1500.50,
                "date": "2024-10-28",
                "note": "Manual price entry"
            }
        }
        os.makedirs(os.path.dirname(MANUAL_PRICES_CONFIG), exist_ok=True)
        with open(MANUAL_PRICES_CONFIG, 'w') as f:
            json.dump(default_config, f, indent=4)
        logger.info(f"Created default price config file: {MANUAL_PRICES_CONFIG}")
        return {}

    try:
        with open(MANUAL_PRICES_CONFIG, 'r') as f:
            config = json.load(f)

        # Remove example entries
        manual_prices = {k: v for k, v in config.items() if k != "EXAMPLE"}

        if manual_prices:
            logger.info(f"Loaded {len(manual_prices)} manual price(s)")

        return manual_prices

    except Exception as e:
        logger.error(f"Error loading manual prices config: {e}")
        return {}


def save_manual_price_template():
    """
    Save a template/example for manual prices configuration.
    """
    template = {
        "_instructions": {
            "format": "Add your stock prices below",
            "date_format": "YYYY-MM-DD",
            "usage": "If API fails to fetch price, manually add it here",
            "example": "Price will be used when date matches or as fallback"
        },
        "EXAMPLE": {
            "price": 1500.50,
            "date": "2024-10-28",
            "note": "Example manual price entry"
        },
        "RELIANCE": {
            "price": 2450.75,
            "date": "2024-10-28",
            "note": "Add actual price if APIs fail"
        }
    }

    filename = "manual_prices_template.json"
    with open(filename, 'w') as f:
        json.dump(template, f, indent=4)

    print(f"\n✓ Created template file: {filename}")
    print("  Copy this to 'config/manual_prices_config.json' and edit with your stock prices")


def get_manual_price(symbol, date=None):
    """
    Get manually configured price for a symbol.

    Args:
        symbol: Stock symbol
        date: Target date (optional)

    Returns:
        float: Price if found, None otherwise
    """
    manual_prices = load_manual_prices()

    if symbol in manual_prices:
        price_info = manual_prices[symbol]
        price = float(price_info.get('price', 0))
        config_date = price_info.get('date', '')
        note = price_info.get('note', '')

        logger.info(f"✓ MANUAL: {symbol} → ₹{price} (date: {config_date}, note: {note})")
        return price

    return None


def load_manual_splits():
    """
    Load manual stock splits from config file.

    Returns:
        dict: Dictionary with symbol as key and list of splits as value
    """
    if not os.path.exists(MANUAL_SPLITS_CONFIG):
        # Create default config file with example
        default_config = {
            "EXAMPLE": [
                {
                    "date": "2024-01-15",
                    "numerator": 10,
                    "denominator": 1,
                    "note": "10:1 stock split"
                }
            ]
        }
        os.makedirs(os.path.dirname(MANUAL_SPLITS_CONFIG), exist_ok=True)
        with open(MANUAL_SPLITS_CONFIG, 'w') as f:
            json.dump(default_config, f, indent=4)
        logger.info(f"Created default config file: {MANUAL_SPLITS_CONFIG}")
        return {}

    try:
        with open(MANUAL_SPLITS_CONFIG, 'r') as f:
            config = json.load(f)

        # Convert to internal format
        manual_splits = {}
        for symbol, splits in config.items():
            if symbol == "EXAMPLE":
                continue

            processed_splits = []
            for split in splits:
                processed_splits.append({
                    'date': datetime.strptime(split['date'], '%Y-%m-%d'),
                    'numerator': split['numerator'],
                    'denominator': split['denominator'],
                    'ratio': split['numerator'] / split['denominator'],
                    'note': split.get('note', '')
                })

            manual_splits[symbol] = sorted(processed_splits, key=lambda x: x['date'])

        return manual_splits

    except Exception as e:
        logger.error(f"Error loading manual splits config: {e}")
        return {}


def save_manual_split_template():
    """
    Save a template/example for manual splits configuration.
    """
    template = {
        "_instructions": {
            "format": "Add your stock splits below",
            "date_format": "YYYY-MM-DD",
            "ratio_calculation": "numerator/denominator = split ratio (e.g., 10/1 = 10x)",
            "example": "A 10:1 split means 1 old share becomes 10 new shares"
        },
        "EXAMPLE": [
            {
                "date": "2024-01-15",
                "numerator": 10,
                "denominator": 1,
                "note": "10:1 stock split - 1 share becomes 10"
            },
            {
                "date": "2023-06-20",
                "numerator": 5,
                "denominator": 1,
                "note": "5:1 stock split - 1 share becomes 5"
            }
        ],
        "RELIANCE": [
            {
                "date": "2017-09-29",
                "numerator": 1,
                "denominator": 1,
                "note": "Example: Add actual splits here if missing from APIs"
            }
        ]
    }

    filename = "manual_splits_template.json"
    with open(filename, 'w') as f:
        json.dump(template, f, indent=4)

    print(f"\n✓ Created template file: {filename}")
    print("  Copy this to 'config/manual_splits_config.json' and edit with your stock splits")


def get_splits_from_manual_config(symbol):
    """
    Fetch splits from manual configuration file.

    Args:
        symbol: Stock symbol

    Returns:
        list: List of split dictionaries
    """
    manual_splits = load_manual_splits()

    if symbol in manual_splits:
        splits = manual_splits[symbol]
        logger.info(f"Found {len(splits)} manual split(s) for {symbol}")
        return splits

    return []
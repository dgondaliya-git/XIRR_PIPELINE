import logging
from dotenv import load_dotenv
import os
load_dotenv()

# FMP API Configuration
FMP_API_KEY = os.environ.get("FMP_API_KEY")
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# Manual config files
MANUAL_SPLITS_CONFIG = "config/manual_splits_config.json"
MANUAL_PRICES_CONFIG = "config/manual_prices_config.json"


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


logger = setup_logging()
"""Configuration settings for Portfolio Analyzer"""

# File paths
INPUT_PORTFOLIO_FILE = 'D:\Algo analystics internship\XIRR_PIPELINE\outputs\current_portfolio.csv'
OUTPUT_INDIVIDUAL_FILE = 'D:\Algo analystics internship\XIRR_PIPELINE\outputs\portfolio_analysis_individual_stocks.csv'
OUTPUT_PORTFOLIO_FILE = 'D:\Algo analystics internship\XIRR_PIPELINE\outputs\portfolio_analysis_weighted_portfolio.csv'

# Analysis periods (in days)
ANALYSIS_PERIODS = {
    '3_months': 90,
    '6_months': 180,
    '1_year': 365
}

# Market settings
STOCK_EXCHANGE_SUFFIX = '.NS'  # NSE (National Stock Exchange of India)
TRADING_DAYS_PER_YEAR = 252

# Data fetching settings
BUFFER_DAYS = 30  # Extra days to fetch for data safety
MIN_DATA_POINTS = 10  # Minimum data points required for analysis

# Display settings
DECIMAL_PLACES = 2
SEPARATOR_LENGTH = 70
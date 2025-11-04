"""Module for fetching stock data from Yahoo Finance"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import portfolio_analyzer.config as config


class DataFetcher:
    """Handles fetching historical stock data"""
    
    def __init__(self, exchange_suffix: str = config.STOCK_EXCHANGE_SUFFIX):
        self.exchange_suffix = exchange_suffix
    
    def get_stock_data(self, symbol: str, period_days: int) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a single stock
        
        Args:
            symbol: Stock symbol (without exchange suffix)
            period_days: Number of days of historical data to fetch
            
        Returns:
            DataFrame with historical price data or None if fetch fails
        """
        try:
            ticker_symbol = f"{symbol}{self.exchange_suffix}"
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + config.BUFFER_DAYS)
            
            # Fetch data
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty or len(hist) < config.MIN_DATA_POINTS:
                return None
            
            # Use only the required period
            hist = hist.tail(period_days) if len(hist) > period_days else hist
            
            return hist
            
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a stock
        
        Args:
            symbol: Stock symbol (without exchange suffix)
            
        Returns:
            Current price or None if fetch fails
        """
        hist = self.get_stock_data(symbol, period_days=5)
        if hist is not None and not hist.empty:
            return hist['Close'].iloc[-1]
        return None
"""Module for calculating financial metrics"""

import numpy as np
import pandas as pd
from typing import Tuple
import portfolio_analyzer.config as config


class MetricsCalculator:
    """Calculates various financial metrics for stocks and portfolios"""
    
    @staticmethod
    def calculate_volatility(prices: pd.Series) -> float:
        """
        Calculate annualized volatility from price series
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Annualized volatility as a percentage
        """
        returns = prices.pct_change().dropna()
        volatility = returns.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR)
        return volatility * 100  # Convert to percentage
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """
        Calculate maximum drawdown from price series
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Maximum drawdown as a percentage
        """
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        return max_drawdown * 100  # Convert to percentage
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """
        Calculate daily returns from price series
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Series of daily returns
        """
        return prices.pct_change().dropna()
    
    def calculate_stock_metrics(self, prices: pd.Series) -> Tuple[float, float]:
        """
        Calculate both volatility and max drawdown for a stock
        
        Args:
            prices: Series of historical prices
            
        Returns:
            Tuple of (volatility, max_drawdown) both as percentages
        """
        volatility = self.calculate_volatility(prices)
        max_drawdown = self.calculate_max_drawdown(prices)
        return volatility, max_drawdown
    
    @staticmethod
    def calculate_portfolio_returns(returns_df: pd.DataFrame, 
                                   weights: pd.Series) -> pd.Series:
        """
        Calculate weighted portfolio returns
        
        Args:
            returns_df: DataFrame of individual stock returns
            weights: Series of portfolio weights (must sum to 1)
            
        Returns:
            Series of portfolio returns
        """
        return (returns_df * weights).sum(axis=1)
    
    def calculate_portfolio_metrics(self, returns_df: pd.DataFrame, 
                                   weights: pd.Series) -> Tuple[float, float]:
        """
        Calculate portfolio-level volatility and max drawdown
        
        Args:
            returns_df: DataFrame of individual stock returns
            weights: Series of portfolio weights
            
        Returns:
            Tuple of (portfolio_volatility, portfolio_max_drawdown)
        """
        portfolio_returns = self.calculate_portfolio_returns(returns_df, weights)
        
        # Calculate portfolio volatility
        portfolio_volatility = portfolio_returns.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR) * 100
        
        # Calculate portfolio max drawdown
        portfolio_cumulative = (1 + portfolio_returns).cumprod()
        running_max = portfolio_cumulative.expanding().max()
        drawdown = (portfolio_cumulative - running_max) / running_max
        portfolio_max_dd = drawdown.min() * 100
        
        return portfolio_volatility, portfolio_max_dd
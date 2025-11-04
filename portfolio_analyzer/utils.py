"""Utility functions and helpers"""

import pandas as pd
import os
from typing import Optional


def load_portfolio(filepath: str) -> Optional[pd.DataFrame]:
    """
    Load portfolio data from CSV file
    
    Args:
        filepath: Path to portfolio CSV file
        
    Returns:
        DataFrame with portfolio data or None if file not found
    """
    try:
        if not os.path.exists(filepath):
            print(f"Error: Portfolio file not found at {filepath}")
            return None
        
        portfolio = pd.read_csv(filepath)
        
        # Validate required columns
        required_columns = ['Symbol', 'CurrentQuantity']
        missing_columns = [col for col in required_columns if col not in portfolio.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return None
        
        print(f"Successfully loaded portfolio with {len(portfolio)} stocks")
        return portfolio
        
    except Exception as e:
        print(f"Error loading portfolio: {str(e)}")
        return None


def ensure_output_directory(filepath: str) -> None:
    """
    Ensure output directory exists
    
    Args:
        filepath: Full path to output file
    """
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")


def validate_portfolio_data(portfolio: pd.DataFrame) -> bool:
    """
    Validate portfolio data integrity
    
    Args:
        portfolio: DataFrame with portfolio data
        
    Returns:
        True if valid, False otherwise
    """
    if portfolio is None or portfolio.empty:
        print("Error: Portfolio is empty")
        return False
    
    # Check for negative quantities
    if (portfolio['CurrentQuantity'] < 0).any():
        print("Warning: Found negative quantities in portfolio")
    
    # Check for missing symbols
    if portfolio['Symbol'].isnull().any():
        print("Error: Found missing stock symbols")
        return False
    
    return True


def format_currency(value: float, currency: str = '₹') -> str:
    """
    Format currency value for display
    
    Args:
        value: Numeric value
        currency: Currency symbol
        
    Returns:
        Formatted string
    """
    return f"{currency}{value:,.2f}"


def format_percentage(value: float) -> str:
    """
    Format percentage value for display
    
    Args:
        value: Percentage value
        
    Returns:
        Formatted string
    """
    return f"{value:.2f}%"
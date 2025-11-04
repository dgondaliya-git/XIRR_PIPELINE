"""Core portfolio analysis module"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from .data_fetcher import DataFetcher
from .metrics_calculator import MetricsCalculator
import portfolio_analyzer.config as config


class PortfolioAnalyzer:
    """Main class for analyzing portfolios"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.metrics_calculator = MetricsCalculator()
    
    def analyze_individual_stock(self, symbol: str, period_days: int) -> Tuple[Optional[float], Optional[float]]:
        """
        Analyze a single stock for given period
        
        Args:
            symbol: Stock symbol
            period_days: Number of days to analyze
            
        Returns:
            Tuple of (volatility, max_drawdown) or (None, None) if data unavailable
        """
        hist = self.data_fetcher.get_stock_data(symbol, period_days)
        
        if hist is None or hist.empty:
            return None, None
        
        return self.metrics_calculator.calculate_stock_metrics(hist['Close'])
    
    def calculate_portfolio_weights(self, portfolio_data: pd.DataFrame, 
                                   period_days: int) -> Tuple[Dict, float, List[Dict]]:
        """
        Calculate portfolio weights and gather stock information
        
        Args:
            portfolio_data: DataFrame with portfolio holdings
            period_days: Number of days for analysis
            
        Returns:
            Tuple of (stock_prices_dict, total_value, stock_info_list)
        """
        stock_prices = {}
        stock_returns = {}
        stock_weights = {}
        total_value = 0
        valid_stocks = []
        
        print(f"\nFetching data for portfolio calculation...")
        
        for idx, row in portfolio_data.iterrows():
            symbol = row['Symbol']
            quantity = row['CurrentQuantity']
            
            hist = self.data_fetcher.get_stock_data(symbol, period_days)
            
            if hist is not None and not hist.empty:
                current_price = hist['Close'].iloc[-1]
                stock_value = current_price * quantity
                total_value += stock_value
                
                stock_prices[symbol] = hist['Close']
                stock_returns[symbol] = hist['Close'].pct_change().dropna()
                
                valid_stocks.append({
                    'Symbol': symbol,
                    'Quantity': quantity,
                    'CurrentPrice': current_price,
                    'Value': stock_value
                })
                print(f"  {symbol}: ₹{stock_value:,.2f}")
        
        if total_value == 0 or len(valid_stocks) == 0:
            return {}, 0, []
        
        # Calculate weights
        for stock in valid_stocks:
            stock['Weight'] = stock['Value'] / total_value
            stock_weights[stock['Symbol']] = stock['Weight']
        
        print(f"\nTotal Portfolio Value: ₹{total_value:,.2f}")
        
        return {
            'prices': stock_prices,
            'returns': stock_returns,
            'weights': stock_weights
        }, total_value, valid_stocks
    
    def analyze_portfolio(self, portfolio_data: pd.DataFrame, 
                         period_days: int) -> Tuple[Optional[float], Optional[float], List[Dict], float]:
        """
        Calculate portfolio-level metrics considering weights
        
        Args:
            portfolio_data: DataFrame with portfolio holdings
            period_days: Number of days for analysis
            
        Returns:
            Tuple of (volatility, max_drawdown, stock_info, total_value)
        """
        stock_data, total_value, valid_stocks = self.calculate_portfolio_weights(
            portfolio_data, period_days
        )
        
        if not stock_data or total_value == 0:
            return None, None, [], 0
        
        # Align all return series to same dates
        returns_df = pd.DataFrame(stock_data['returns'])
        returns_df = returns_df.dropna()
        
        if returns_df.empty:
            return None, None, valid_stocks, total_value
        
        # Calculate portfolio metrics
        weights_series = pd.Series(stock_data['weights'])
        portfolio_vol, portfolio_dd = self.metrics_calculator.calculate_portfolio_metrics(
            returns_df, weights_series
        )
        
        return portfolio_vol, portfolio_dd, valid_stocks, total_value
    
    def analyze_all_periods(self, portfolio_data: pd.DataFrame, 
                           periods: Dict[str, int]) -> Tuple[pd.DataFrame, Dict]:
        """
        Analyze portfolio across multiple time periods
        
        Args:
            portfolio_data: DataFrame with portfolio holdings
            periods: Dictionary mapping period names to days
            
        Returns:
            Tuple of (individual_results_df, portfolio_metrics_dict)
        """
        # Initialize results dataframe
        results = portfolio_data[['Symbol', 'CurrentQuantity']].copy()
        portfolio_metrics = {}
        
        for period_name, days in periods.items():
            print(f"\n{'='*config.SEPARATOR_LENGTH}")
            print(f"ANALYZING: {period_name.replace('_', ' ').upper()}")
            print(f"{'='*config.SEPARATOR_LENGTH}")
            
            # Individual stock metrics
            volatility_col = f'Volatility_{period_name}_%'
            drawdown_col = f'Max_Drawdown_{period_name}_%'
            
            results[volatility_col] = None
            results[drawdown_col] = None
            
            print("\nIndividual Stock Analysis:")
            print("-" * config.SEPARATOR_LENGTH)
            
            for idx, row in portfolio_data.iterrows():
                symbol = row['Symbol']
                print(f"Processing {symbol}...", end=' ')
                
                vol, dd = self.analyze_individual_stock(symbol, days)
                
                if vol is not None and dd is not None:
                    results.at[idx, volatility_col] = round(vol, config.DECIMAL_PLACES)
                    results.at[idx, drawdown_col] = round(dd, config.DECIMAL_PLACES)
                    print(f"✓ Vol: {vol:.2f}%, DD: {dd:.2f}%")
                else:
                    print("✗ No data")
            
            # Portfolio-level metrics
            print("\n" + "="*config.SEPARATOR_LENGTH)
            print("PORTFOLIO-LEVEL ANALYSIS (Weighted)")
            print("="*config.SEPARATOR_LENGTH)
            
            p_vol, p_dd, stock_info, total_val = self.analyze_portfolio(portfolio_data, days)
            
            if p_vol is not None:
                portfolio_metrics[period_name] = {
                    'volatility': p_vol,
                    'max_drawdown': p_dd,
                    'total_value': total_val,
                    'stock_info': stock_info
                }
                print(f"\n📊 PORTFOLIO METRICS ({period_name.replace('_', ' ')}):")
                print(f"  • Weighted Volatility: {p_vol:.2f}%")
                print(f"  • Weighted Max Drawdown: {p_dd:.2f}%")
            else:
                print(f"\n⚠️  Could not calculate portfolio metrics for {period_name}")
        
        return results, portfolio_metrics
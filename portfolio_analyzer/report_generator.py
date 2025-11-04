"""Module for generating analysis reports"""

import pandas as pd
from typing import Dict
import portfolio_analyzer.config as config


class ReportGenerator:
    """Generates and saves analysis reports"""
    
    @staticmethod
    def save_individual_results(results: pd.DataFrame, 
                               filepath: str = config.OUTPUT_INDIVIDUAL_FILE) -> None:
        """
        Save individual stock analysis results to CSV
        
        Args:
            results: DataFrame with individual stock metrics
            filepath: Output file path
        """
        results.to_csv(filepath, index=False)
        print(f"\n{'='*config.SEPARATOR_LENGTH}")
        print(f"Individual stock results saved to: {filepath}")
    
    @staticmethod
    def save_portfolio_results(portfolio_metrics: Dict, 
                              filepath: str = config.OUTPUT_PORTFOLIO_FILE) -> pd.DataFrame:
        """
        Save portfolio-level results to CSV
        
        Args:
            portfolio_metrics: Dictionary with portfolio metrics for each period
            filepath: Output file path
            
        Returns:
            DataFrame with portfolio summary
        """
        portfolio_summary = []
        for period_name, metrics in portfolio_metrics.items():
            portfolio_summary.append({
                'Period': period_name.replace('_', ' ').title(),
                'Portfolio_Volatility_%': round(metrics['volatility'], config.DECIMAL_PLACES),
                'Portfolio_Max_Drawdown_%': round(metrics['max_drawdown'], config.DECIMAL_PLACES),
                'Total_Portfolio_Value_₹': round(metrics['total_value'], config.DECIMAL_PLACES)
            })
        
        portfolio_df = pd.DataFrame(portfolio_summary)
        portfolio_df.to_csv(filepath, index=False)
        print(f"Portfolio-level results saved to: {filepath}")
        print(f"{'='*config.SEPARATOR_LENGTH}")
        
        return portfolio_df
    
    @staticmethod
    def print_individual_summary(results: pd.DataFrame, periods: Dict[str, int]) -> None:
        """
        Print summary statistics for individual stocks
        
        Args:
            results: DataFrame with individual stock metrics
            periods: Dictionary mapping period names to days
        """
        print("\n" + "="*config.SEPARATOR_LENGTH)
        print("SUMMARY - INDIVIDUAL STOCKS")
        print("="*config.SEPARATOR_LENGTH)
        
        for period_name in periods.keys():
            vol_col = f'Volatility_{period_name}_%'
            dd_col = f'Max_Drawdown_{period_name}_%'
            
            print(f"\n{period_name.replace('_', ' ').title()}:")
            print(f"  Average Volatility: {results[vol_col].mean():.2f}%")
            print(f"  Average Max Drawdown: {results[dd_col].mean():.2f}%")
            
            max_vol_idx = results[vol_col].idxmax()
            min_dd_idx = results[dd_col].idxmin()
            
            if pd.notna(max_vol_idx):
                print(f"  Highest Volatility: {results.loc[max_vol_idx, vol_col]:.2f}% "
                      f"({results.loc[max_vol_idx, 'Symbol']})")
            if pd.notna(min_dd_idx):
                print(f"  Worst Drawdown: {results.loc[min_dd_idx, dd_col]:.2f}% "
                      f"({results.loc[min_dd_idx, 'Symbol']})")
    
    @staticmethod
    def print_portfolio_summary(portfolio_df: pd.DataFrame) -> None:
        """
        Print portfolio summary table
        
        Args:
            portfolio_df: DataFrame with portfolio metrics
        """
        print("\n" + "="*config.SEPARATOR_LENGTH)
        print("SUMMARY - WEIGHTED PORTFOLIO")
        print("="*config.SEPARATOR_LENGTH)
        print(portfolio_df.to_string(index=False))
    
    @staticmethod
    def print_holdings_by_weight(portfolio_metrics: Dict) -> None:
        """
        Print holdings sorted by weight
        
        Args:
            portfolio_metrics: Dictionary with portfolio metrics
        """
        if not portfolio_metrics:
            return
        
        last_period = list(portfolio_metrics.keys())[-1]
        stock_info = portfolio_metrics[last_period]['stock_info']
        
        print("\n" + "="*config.SEPARATOR_LENGTH)
        print("HOLDINGS BY WEIGHT")
        print("="*config.SEPARATOR_LENGTH)
        
        stock_info_df = pd.DataFrame(stock_info)
        stock_info_df = stock_info_df.sort_values('Weight', ascending=False)
        stock_info_df['Weight_%'] = (stock_info_df['Weight'] * 100).round(config.DECIMAL_PLACES)
        
        print(stock_info_df[['Symbol', 'Quantity', 'CurrentPrice', 'Value', 'Weight_%']].to_string(index=False))
    
    def generate_complete_report(self, results: pd.DataFrame, 
                                portfolio_df: pd.DataFrame,
                                portfolio_metrics: Dict,
                                periods: Dict[str, int]) -> None:
        """
        Generate and print complete analysis report
        
        Args:
            results: DataFrame with individual stock metrics
            portfolio_df: DataFrame with portfolio summary
            portfolio_metrics: Dictionary with portfolio metrics
            periods: Dictionary mapping period names to days
        """
        self.print_individual_summary(results, periods)
        self.print_portfolio_summary(portfolio_df)
        self.print_holdings_by_weight(portfolio_metrics)
"""
Main entry point for Portfolio Analyzer

Usage:
    python main.py
"""

import warnings
warnings.filterwarnings('ignore')

from portfolio_analyzer import PortfolioAnalyzer, ReportGenerator
from portfolio_analyzer.utils import load_portfolio, validate_portfolio_data, ensure_output_directory
import XIRR_PIPELINE.portfolio_analyzer.config as config


def main():
    """Main execution function"""
    
    print("="*config.SEPARATOR_LENGTH)
    print("PORTFOLIO ANALYZER v1.0")
    print("="*config.SEPARATOR_LENGTH)
    
    # Load portfolio data
    print(f"\nLoading portfolio from: {config.INPUT_PORTFOLIO_FILE}")
    portfolio = load_portfolio(config.INPUT_PORTFOLIO_FILE)
    
    if portfolio is None:
        print("Failed to load portfolio. Exiting.")
        return
    
    # Validate portfolio data
    if not validate_portfolio_data(portfolio):
        print("Portfolio validation failed. Exiting.")
        return
    
    # Ensure output directories exist
    ensure_output_directory(config.OUTPUT_INDIVIDUAL_FILE)
    ensure_output_directory(config.OUTPUT_PORTFOLIO_FILE)
    
    # Initialize analyzer and report generator
    analyzer = PortfolioAnalyzer()
    reporter = ReportGenerator()
    
    # Perform analysis
    results, portfolio_metrics = analyzer.analyze_all_periods(
        portfolio, 
        config.ANALYSIS_PERIODS
    )
    
    # Save results
    reporter.save_individual_results(results)
    portfolio_df = reporter.save_portfolio_results(portfolio_metrics)
    
    # Generate reports
    reporter.generate_complete_report(
        results,
        portfolio_df,
        portfolio_metrics,
        config.ANALYSIS_PERIODS
    )
    
    print("\n" + "="*config.SEPARATOR_LENGTH)
    print("ANALYSIS COMPLETE")
    print("="*config.SEPARATOR_LENGTH)
    
    return results, portfolio_df


if __name__ == "__main__":
    results, portfolio_summary = main()
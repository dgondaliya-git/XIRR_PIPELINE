"""
Example script showing how to use Portfolio Analyzer as an imported package
"""

import warnings
warnings.filterwarnings('ignore')
import pandas as pd

# from portfolio_analyzer import (
#     PortfolioAnalyzer, 
#     ReportGenerator,
#     load_portfolio,
#     validate_portfolio_data
# )
from portfolio_analyzer import portfolio_analyzer,report_generator
from portfolio_analyzer.portfolio_analyzer import PortfolioAnalyzer
from portfolio_analyzer.report_generator import ReportGenerator
from portfolio_analyzer.utils import ensure_output_directory,validate_portfolio_data,load_portfolio
import portfolio_analyzer.config as config

# ============================================================================
# OPTION 1: Full Analysis (Same as main.py)
# ============================================================================

def run_full_analysis(current_portfolio=None, file_path=config.INPUT_PORTFOLIO_FILE):
    """Run complete portfolio analysis"""
    
    print(f"{file_path}.....")
    # Load portfolio
    portfolio = current_portfolio if current_portfolio is not None else load_portfolio(file_path)
    # if portfolio is None or not validate_portfolio_data(portfolio):
    if portfolio is None:
        print("Error loading portfolio")
        # Return empty DataFrame instead of None
        return {}, pd.DataFrame()
    
    # Ensure directories exist
    ensure_output_directory(config.OUTPUT_INDIVIDUAL_FILE)
    ensure_output_directory(config.OUTPUT_PORTFOLIO_FILE)
    
    # Initialize
    analyzer = PortfolioAnalyzer()
    reporter = ReportGenerator()
    
    # Run analysis
    results, portfolio_metrics = analyzer.analyze_all_periods(
        portfolio, 
        config.ANALYSIS_PERIODS
    )
    
    # Save and display results
    reporter.save_individual_results(results)
    portfolio_df = reporter.save_portfolio_results(portfolio_metrics)
    reporter.generate_complete_report(results, portfolio_df, portfolio_metrics, config.ANALYSIS_PERIODS)
    
    return results, portfolio_df


# ============================================================================
# OPTION 2: Analyze Single Stock
# ============================================================================

def analyze_single_stock(symbol, period_days=90):
    """Analyze a single stock"""
    
    analyzer = PortfolioAnalyzer()
    volatility, max_drawdown = analyzer.analyze_individual_stock(symbol, period_days)
    
    if volatility is not None:
        print(f"\n{symbol} Analysis ({period_days} days):")
        print(f"  Volatility: {volatility:.2f}%")
        print(f"  Max Drawdown: {max_drawdown:.2f}%")
        return volatility, max_drawdown
    else:
        print(f"Could not fetch data for {symbol}")
        return None, None


# ============================================================================
# OPTION 3: Custom Analysis with Specific Periods
# ============================================================================

def custom_analysis(portfolio_file, custom_periods):
    """Run analysis with custom time periods"""
    
    portfolio = load_portfolio(portfolio_file)
    if portfolio is None:
        return
    
    analyzer = PortfolioAnalyzer()
    reporter = ReportGenerator()
    
    results, portfolio_metrics = analyzer.analyze_all_periods(portfolio, custom_periods)
    
    # Display only (no saving)
    portfolio_df = reporter.save_portfolio_results(portfolio_metrics)
    reporter.print_portfolio_summary(portfolio_df)
    
    return results, portfolio_df


# ============================================================================
# OPTION 4: Get Portfolio Value Only
# ============================================================================

def get_portfolio_value(portfolio_file):
    """Get current portfolio value without full analysis"""
    
    portfolio = load_portfolio(portfolio_file)
    if portfolio is None:
        return 0
    
    analyzer = PortfolioAnalyzer()
    _, _, _, total_value = analyzer.analyze_portfolio(portfolio, period_days=5)
    
    print(f"\nCurrent Portfolio Value: ₹{total_value:,.2f}")
    return total_value


# ============================================================================
# OPTION 5: Analyze Specific Stocks from Portfolio
# ============================================================================

def analyze_specific_stocks(portfolio_file, stock_symbols, period_days=90):
    """Analyze only specific stocks from portfolio"""
    
    import pandas as pd
    
    portfolio = load_portfolio(portfolio_file)
    if portfolio is None:
        return
    
    # Filter portfolio
    filtered_portfolio = portfolio[portfolio['Symbol'].isin(stock_symbols)]
    
    if filtered_portfolio.empty:
        print("No matching stocks found")
        return
    
    analyzer = PortfolioAnalyzer()
    
    print(f"\nAnalyzing {len(filtered_portfolio)} stocks for {period_days} days:")
    print("-" * 60)
    
    results = []
    for _, row in filtered_portfolio.iterrows():
        symbol = row['Symbol']
        vol, dd = analyzer.analyze_individual_stock(symbol, period_days)
        
        if vol is not None:
            results.append({
                'Symbol': symbol,
                'Volatility_%': round(vol, 2),
                'Max_Drawdown_%': round(dd, 2)
            })
            print(f"{symbol}: Vol={vol:.2f}%, DD={dd:.2f}%")
    
    return pd.DataFrame(results)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    
    print("="*70)
    print("PORTFOLIO ANALYZER - PACKAGE USAGE EXAMPLES")
    print("="*70)
    
    # Example 1: Run full analysis
    print("\n[1] Running Full Analysis...")
    results, portfolio_summary = run_full_analysis()
    
    # Example 2: Analyze single stock
    print("\n[2] Analyzing Single Stock...")
    analyze_single_stock('RELIANCE', period_days=90)
    
    # Example 3: Custom periods
    print("\n[3] Custom Analysis with Different Periods...")
    custom_periods = {
        '1_month': 30,
        '2_months': 60,
    }
    custom_analysis(config.INPUT_PORTFOLIO_FILE, custom_periods)
    
    # Example 4: Get portfolio value
    print("\n[4] Getting Portfolio Value...")
    get_portfolio_value(config.INPUT_PORTFOLIO_FILE)
    
    # Example 5: Analyze specific stocks
    print("\n[5] Analyzing Specific Stocks...")
    analyze_specific_stocks(
        config.INPUT_PORTFOLIO_FILE, 
        ['RELIANCE', 'TCS', 'INFY'], 
        period_days=180
    )
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)
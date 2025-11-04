import pandas as pd
from datetime import datetime
import os

from core.utils import FMP_API_KEY
from core.manual_config import save_manual_price_template, save_manual_split_template
from core.tradebook import load_trade_data
from core.portfolio import calculate_portfolio_with_splits, calculate_simple_portfolio
from core.pricing import get_current_price
from core.splits import get_stock_splits, get_splits_from_fmp, get_splits_from_yfinance, normalize_splits
from core.manual_config import get_splits_from_manual_config
from core.xirr_calc import xirr


from core.compare_with_niftybees import Nifty_Bees_XIRR

# from portfolio_analyzer.portfolio_analyzer import PortfolioAnalyzer
from portfolio_analyzer.run_analysis import run_full_analysis


def main():
    """Main execution function."""
    print("=" * 60)
    print("STOCK PORTFOLIO ANALYZER WITH MANUAL CONFIG")
    print("=" * 60)

    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)

    # Check if user wants to create templates
    print("\nAvailable templates:")
    print("  1. Manual splits template")
    print("  2. Manual prices template")
    print("  3. Both templates")
    print("  4. Skip and continue")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == '1':
        save_manual_split_template()
        print("\nEdit 'manual_splits_config.json' to add your stock splits")
        print("Then run this script again.\n")
        return
    elif choice == '2':
        save_manual_price_template()
        print("\nEdit 'manual_prices_config.json' to add your stock prices")
        print("Then run this script again.\n")
        return
    elif choice == '3':
        save_manual_split_template()
        save_manual_price_template()
        print("\nEdit the config files and run this script again.\n")
        return

    file_path = input("\nEnter file path: ").strip()
    start_date = input("Start date (DD-MM-YYYY, or blank for all): ").strip() or None
    end_date = input("End date (DD-MM-YYYY, or blank for all): ").strip() or None

    print("\n" + "=" * 60)
    print("LOADING TRADE DATA")
    print("=" * 60)

    processed_df = load_trade_data(
        csv_path=file_path,
        start_date=start_date,
        end_date=end_date
    )
    print(f"\nTotal trades loaded: {len(processed_df)}")

    if FMP_API_KEY == "YOUR_FMP_API_KEY_HERE":
        print("\n" + "=" * 60)
        print("⚠️  FMP API KEY NOT PROVIDED")
        print("=" * 60)
        print("Calculating without split adjustments...")
        current_portfolio, daily = calculate_simple_portfolio(processed_df)

        print("\n" + "=" * 60)
        print("CURRENT PORTFOLIO (Without Split Adjustments):")
        print("=" * 60)
        print(current_portfolio.to_string(index=False))
    else:
        current_portfolio, daily, splits = calculate_portfolio_with_splits(
            processed_df, FMP_API_KEY
        )

        print("\n" + "=" * 60)
        print("FINAL CURRENT PORTFOLIO (With Split Adjustments):")
        print("=" * 60)

        if len(current_portfolio) > 0:
            print(current_portfolio.to_string(index=False))
            current_portfolio.to_csv("outputs/current_portfolio.csv", index=False)
        else:
            print("No open positions")

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)

    total_cashflow = processed_df['CashFlow'].sum()
    print(f"Total Cash Flow: ₹{total_cashflow:,.2f}")
    print(f"Number of unique stocks: {processed_df['Symbol'].nunique()}")
    print(f"Number of trades: {len(processed_df)}")

    print("\nFetching current prices (FMP → yfinance → manual config)...")
    portfolio_with_prices = current_portfolio.groupby('Symbol')['CurrentQuantity'].sum().reset_index()

    # symbols = portfolio_with_prices['Symbol'].unique()

    # prices = []
    # for idx, symbol in enumerate(portfolio_with_prices['Symbol'], 1):
    #     print(f"  [{idx}/{len(portfolio_with_prices)}] Fetching {symbol}...")
    #     price = get_current_price(symbol, date=end_date, verbose=False)
    #     print(f"{price}???????")
    #     prices.append(price)

    symbols = portfolio_with_prices['Symbol'].unique()

    prices = []
    for idx, symbol in enumerate(symbols, 1):
        print(f"  [{idx}/{len(symbols)}] Fetching {symbol}...")
        price = get_current_price(symbol, date=end_date, verbose=False)
        # print(f"→ Price: ₹{price}")
        prices.append(price)

    portfolio_with_prices['Current_Price'] = prices

    if end_date and str(end_date).strip():
        try:
            trade_date = pd.to_datetime(end_date, format='%d-%m-%Y')
        except ValueError:
            trade_date = pd.Timestamp.today()
    else:
        trade_date = pd.Timestamp.today()

    portfolio_with_prices['TradeDate'] = trade_date.strftime('%Y-%m-%d')
    portfolio_with_prices['CashFlow'] = (
        portfolio_with_prices['CurrentQuantity'] * portfolio_with_prices['Current_Price']
    )
    portfolio_with_prices.rename(columns={
        'CurrentQuantity': 'Side',
        'Current_Price': 'Price'
    }, inplace=True)

    portfolio_with_prices.to_csv("outputs/Final_portfolio_with_price.csv", index=False)
    print(portfolio_with_prices.to_string(index=False))
    print(f"\n✓ Saved outputs/Final_portfolio_with_price.csv")

    final = pd.concat([
        processed_df[['Symbol', 'TradeDate', 'Side', 'Price', 'CashFlow']],
        portfolio_with_prices
    ], ignore_index=True)

    final['TradeDate'] = pd.to_datetime(final['TradeDate'], errors='coerce')
    final = final.sort_values('TradeDate')
    final.to_csv("outputs/All_trades_with_current_portfolio.csv", index=False)
    print(f"✓ Saved outputs/All_trades_with_current_portfolio.csv")

    print("\nCalculating XIRR...")
    xirr_result = (
        final.groupby('Symbol')
        .apply(lambda g: xirr(g['CashFlow'], g['TradeDate']), include_groups=False)
        .reset_index(name='XIRR')
    )
    xirr_result['XIRR (%)'] = xirr_result['XIRR'] * 100

    overall_xirr = xirr(final['CashFlow'], final['TradeDate'])
    print(f"\n📈 Overall XIRR: {overall_xirr * 100:.2f}%")

    overall_row = pd.DataFrame([{
        'Symbol': 'Overall Portfolio',
        'XIRR': overall_xirr,
        'XIRR (%)': round(overall_xirr * 100, 2)
    }])
    xirr_result = pd.concat([xirr_result, overall_row], ignore_index=True)
    xirr_result.to_csv("outputs/XIRR_result.csv", index=False)
    print(f"✓ Saved outputs/XIRR_result.csv")
    print(xirr_result.to_string(index=False))

    # Track stocks that need manual attention
    print("\n" + "=" * 60)
    print("STOCKS REQUIRING MANUAL ATTENTION")
    print("=" * 60)

    # Find stocks with split mismatches (nsepy removed)
    stocks_with_split_mismatch = []
    for symbol in symbols:
        fmp_splits = get_splits_from_fmp(symbol, FMP_API_KEY)
        yf_splits = get_splits_from_yfinance(symbol)
        manual_splits = get_splits_from_manual_config(symbol)

        fmp_dates = normalize_splits(fmp_splits)
        yf_dates = normalize_splits(yf_splits)
        manual_dates = normalize_splits(manual_splits)

        sources_count = sum([bool(fmp_dates), bool(yf_dates), bool(manual_dates)])

        if sources_count > 1 and not (fmp_dates == yf_dates == manual_dates):
            stocks_with_split_mismatch.append(symbol)

    # Find stocks with missing or zero prices
    stocks_with_price_issues = []
    for idx, row in portfolio_with_prices.iterrows():
        if row['Price'] == 0.0 or pd.isna(row['Price']):
            stocks_with_price_issues.append(row['Symbol'])

    manual_attention_needed = []

    if stocks_with_split_mismatch:
        print("\n⚠️  STOCKS WITH SPLIT DATA MISMATCHES:")
        for symbol in stocks_with_split_mismatch:
            print(f"   • {symbol}")
            manual_attention_needed.append({
                'Symbol': symbol,
                'Issue': 'Split data mismatch across sources',
                'Action': 'Verify splits manually and add to manual_splits_config.json'
            })
    else:
        print("\n✓ No split data mismatches found")

    if stocks_with_price_issues:
        print("\n⚠️  STOCKS WITH MISSING/ZERO CURRENT PRICES:")
        for symbol in stocks_with_price_issues:
            print(f"   • {symbol}")
            manual_attention_needed.append({
                'Symbol': symbol,
                'Issue': 'Current price unavailable',
                'Action': 'Add price to manual_prices_config.json or verify ticker symbol'
            })
    else:
        print("\n✓ All stock prices fetched successfully")

    if manual_attention_needed:
        attention_df = pd.DataFrame(manual_attention_needed)
        attention_df.to_csv("outputs/stocks_needing_manual_attention.csv", index=False)
        print(f"\n✓ Saved outputs/stocks_needing_manual_attention.csv")
        print(f"\nTotal stocks needing attention: {len(manual_attention_needed)}")

        print("\n" + "=" * 60)
        print("HOW TO FIX ISSUES:")
        print("=" * 60)
        print("\nFor split mismatches:")
        print("  1. Check outputs/stocks_needing_manual_attention.csv")
        print("  2. Verify correct split dates from company announcements")
        print("  3. Add verified splits to config/manual_splits_config.json")

        print("\nFor missing prices:")
        print("  1. Check if stock is delisted or ticker changed")
        print("  2. Find correct price from broker/exchange")
        print("  3. Add price to config/manual_prices_config.json")

        print("\nExample manual_prices_config.json entry:")
        print('  "SYMBOL": {')
        print('    "price": 1234.56,')
        print('    "date": "2024-10-28",')
        print('    "note": "Manual entry - stock delisted"')
        print('  }')
    else:
        print("\n✅ All stocks processed successfully - no manual attention needed!")

    print("\n" + "=" * 60)
    print("✓ Analysis complete! Check output CSV files.")
    print("=" * 60)

    print("\nGenerated files:")
    print("  • outputs/current_portfolio.csv - Your current holdings")
    print("  • outputs/Final_portfolio_with_price.csv - Holdings with current prices")
    print("  • outputs/All_trades_with_current_portfolio.csv - Complete trade history")
    print("  • outputs/XIRR_result.csv - Return calculations")
    if manual_attention_needed:
        print("  • outputs/stocks_needing_manual_attention.csv - Issues to resolve")
    
    # current_portfolio = pd.read_csv("outputs/current_portfolio.csv")
    # ETF symbol you want to process (example: 'NIFTYBEES')
    etf_symbol = "NIFTYBEES"

    # Create the XIRR calculator object
    xirr_calc = Nifty_Bees_XIRR(file_path, etf=etf_symbol, verbose=True)

    # Run the XIRR calculation
    xirr_value = xirr_calc.calculate_xirr()

    # Print result
    if xirr_value is not None:
        print(f"\nFinal {etf_symbol} XIRR: {xirr_value * 100:.2f}%")
    else:
        print(f"\nNo valid cash flows found for {etf_symbol}.")
    
    results, summary = run_full_analysis(current_portfolio)
    print("portfolio analyzer executed successfully.\n") 
    dic = {'Symbol':'NIFTYBEES', 'CurrentQuantity':1}
    df = pd.DataFrame([dic])
    results1, summary1 = run_full_analysis(df)
    print("portfolio analyzer executed successfully for NIFTYBEES.\n") 
    

if __name__ == "__main__":
    main()



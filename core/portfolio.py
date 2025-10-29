import pandas as pd
from .splits import get_stock_splits


def calculate_portfolio_with_splits(df, api_key):
    """Calculate current portfolio quantities accounting for stock splits."""
    df = df.sort_values('TradeDate').reset_index(drop=True)

    print("\n" + "="*60)
    print("Step 1: Grouping trades by ISIN and Trade Date...")
    print("="*60)

    daily_trades = df.groupby(['ISIN', 'TradeDate']).agg(
        Symbol=('Symbol', 'first'),
        Side=('Side', 'sum'),
        Quantity=('Quantity', 'sum'),
        CashFlow=('CashFlow', 'sum'),
        Price=('Price', 'mean')
    ).reset_index()

    print(f"Total daily aggregated entries: {len(daily_trades)}")

    symbols = daily_trades['Symbol'].unique()

    print("\n" + "="*60)
    print("Step 2: Fetching stock split data (Manual → FMP → yfinance → nsepy)...")
    print("="*60)

    splits_data = {}
    for symbol in symbols:
        splits = get_stock_splits(symbol, api_key)
        if splits:
            splits_data[symbol] = splits
            print(f"{symbol}: Found {len(splits)} split(s)")
            for split in splits:
                note = split.get('note', '')
                note_str = f" - {note}" if note else ""
                print(f"  - {split['date'].strftime('%Y-%m-%d')}: "
                      f"{split['numerator']}:{split['denominator']} "
                      f"({split['ratio']:.4f}x){note_str}")
        else:
            print(f"{symbol}: No splits found")

    print("\n" + "="*60)
    print("Step 3: Calculating positions with split adjustments...")
    print("="*60)

    portfolio = {}

    for symbol in symbols:
        symbol_trades = daily_trades[daily_trades['Symbol'] == symbol].sort_values('TradeDate')

        for isin in symbol_trades['ISIN'].unique():
            isin_symbol_trades = symbol_trades[symbol_trades['ISIN'] == isin]
            adjusted_quantity = 0

            for _, trade in isin_symbol_trades.iterrows():
                trade_date = trade['TradeDate']
                side = trade['Side']
                split_multiplier = 1.0

                if symbol in splits_data:
                    for split in splits_data[symbol]:
                        split_date = split['date']
                        split_ratio = split['ratio']

                        # print(split_date, split_date.tzinfo)
                        # print(trade_date, trade_date.tzinfo)
                        # split_date = split_date.replace(tzinfo=None)
                        # trade_date = trade_date.replace(tzinfo=None)
            
                        if split_date.replace(tzinfo=None) > trade_date.replace(tzinfo=None):
                            split_multiplier *= split_ratio

                adjusted_quantity += -side * split_multiplier

            portfolio[isin] = [symbol, adjusted_quantity]

    results = []
    for isin, data in portfolio.items():
        symbol, quantity = data
        if abs(quantity) > 0.001:
            results.append({
                'Symbol': symbol,
                'ISIN': isin,
                'CurrentQuantity': round(quantity, 4),
                'Status': 'Long' if quantity > 0 else 'Short'
            })

    results_df = pd.DataFrame(results)
    return results_df, daily_trades, splits_data


def calculate_simple_portfolio(df):
    """Calculate portfolio without split adjustments."""
    df = df.sort_values('TradeDate').reset_index(drop=True)

    daily_trades = df.groupby(['Symbol', 'TradeDate']).agg({
        'Quantity': 'sum',
        'CashFlow': 'sum'
    }).reset_index()

    portfolio = df.groupby('Symbol').agg({
        'Quantity': 'sum',
        'ISIN': 'first'
    }).reset_index()

    portfolio = portfolio[abs(portfolio['Quantity']) > 0.001].copy()
    portfolio.rename(columns={'Quantity': 'CurrentQuantity'}, inplace=True)
    portfolio['Status'] = portfolio['CurrentQuantity'].apply(
        lambda x: 'Long' if x > 0 else 'Short'
    )

    return portfolio, daily_trades
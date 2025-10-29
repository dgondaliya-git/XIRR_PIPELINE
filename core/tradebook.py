import pandas as pd


def preprocess_tradebook(df):
    """Clean and standardize tradebook data."""
    df["Quantity"] = pd.to_numeric(
        df["Quantity"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    ).astype("Int64")

    df["Price"] = pd.to_numeric(
        df["Price"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    )

    df["Trade Date"] = pd.to_datetime(df["Trade Date"], errors="coerce", dayfirst=True)

    text_columns = [
        "Symbol", "ISIN", "Exchange", "Segment", "Series",
        "Trade Type", "Trade ID", "Order ID", "Order Execution Time", "Confirm Side"
    ]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("string")

    df['Side'] = df.apply(
        lambda x: -x['Quantity'] if x['Confirm Side'] == 'buy' else x['Quantity'],
        axis=1
    )

    df['CashFlow'] = df['Side'] * df['Price']

    def last_nonempty(series):
        import numpy as np
        s = series.replace('', pd.NA).dropna()
        return s.iloc[-1] if not s.empty else np.nan

    df['Symbol'] = df.groupby('ISIN')['Symbol'].transform(last_nonempty)
    df['ISIN'] = df.groupby('Symbol')['ISIN'].transform(last_nonempty)

    return df


def load_trade_data(csv_path=None, df=None, start_date=None, end_date=None):
    """Load and filter trade data from CSV or DataFrame."""
    if df is None:
        df = pd.read_csv(csv_path)

    df.columns = df.columns.str.strip()
    df = preprocess_tradebook(df)

    df['TradeDate'] = df['Trade Date']

    if 'ISIN' not in df.columns:
        df['ISIN'] = 'N/A'

    mask = pd.Series(True, index=df.index)

    if start_date and str(start_date).strip():
        start = pd.to_datetime(start_date, format='%d-%m-%Y')
        mask &= df['TradeDate'] >= start

    if end_date and str(end_date).strip():
        end = pd.to_datetime(end_date, format='%d-%m-%Y')
        mask &= df['TradeDate'] <= end

    filtered_df = df[mask]

    return filtered_df[['Symbol', 'ISIN', 'TradeDate', 'Price', 'Side', 'Quantity', 'CashFlow']]
import pandas as pd
from core.pricing import get_current_price
from core.tradebook import load_trade_data
from core.xirr_calc import xirr


class Nifty_Bees_XIRR:
    def __init__(self, tradebook_csv_path, etf, verbose=False):
        self.tradebook_csv_path = tradebook_csv_path
        self.trade_data = load_trade_data(csv_path=self.tradebook_csv_path)
        self.etf = etf
        self.verbose = verbose

    def process_data(self):
        df = self.trade_data.copy()
        
        cash_flows = (
            df[["TradeDate", "CashFlow"]]
            .dropna()
            .sort_values(by="TradeDate")
            .groupby("TradeDate", as_index=False)["CashFlow"]
            .sum()
        )

        return cash_flows

    def process_etf(self, df: pd.DataFrame, etf: str) -> pd.DataFrame:
        df = df.copy()
        grouped_df = df.groupby("TradeDate", as_index=False)["CashFlow"].sum()

        if self.verbose:
            print(f"\nProcessing ETF: {etf}")

        # Fetch prices
        grouped_df[f"{etf}_Price"] = grouped_df["TradeDate"].apply(
            lambda d: get_current_price(etf, d)
        )

        current_units = 0
        qty_list, cf_list = [], []
        missing_price_days = 0

        for _, row in grouped_df.iterrows():
            price = row[f"{etf}_Price"]
            cashflow = row["CashFlow"]
            qty, cf = 0, 0.0

            if price > 0:
                if cashflow < 0:
                    # BUY
                    units_to_buy = int(abs(cashflow) // price)
                    if units_to_buy > 0:
                        qty = -units_to_buy
                        cf = -units_to_buy * price
                        current_units += units_to_buy
                elif cashflow > 0:
                    # SELL (only up to holdings)
                    units_to_sell = int(min(cashflow // price, current_units))
                    if units_to_sell > 0:
                        qty = units_to_sell
                        cf = units_to_sell * price
                        current_units -= units_to_sell
            else:
                missing_price_days += 1

            qty_list.append(qty)
            cf_list.append(cf)

        grouped_df[f"{etf}_Qty"] = qty_list
        grouped_df[f"{etf}_CashFlow"] = cf_list

        if missing_price_days > 0:
            print(f"⚠️ {etf} has {missing_price_days} days with price = 0.")

        # Final holdings valuation
        end_date = grouped_df["TradeDate"].max()
        dic = {
            "TradeDate": end_date,
            "CashFlow": 0.0,
            f"{etf}_Price": get_current_price(etf, end_date),
            f"{etf}_Qty": grouped_df[f"{etf}_Qty"].sum()*-1,
        }
        dic[f"{etf}_CashFlow"] = dic[f"{etf}_Qty"] * dic[f"{etf}_Price"]

        full_final_etfs = pd.concat([grouped_df, pd.DataFrame([dic])], ignore_index=True)
        return full_final_etfs

    def calculate_xirr(self, etf: str = None):
        etf = etf or self.etf
        print(f"{etf} XIRR Calculation:")

        preprocessed_data = self.process_data()
        full_final_etfs = self.process_etf(preprocessed_data, etf)

        full_final_etfs["TradeDate"] = pd.to_datetime(full_final_etfs["TradeDate"], errors="coerce", dayfirst=True)
        full_final_etfs["CashFlow"] = pd.to_numeric(full_final_etfs[f"{etf}_CashFlow"], errors="coerce")


        xir = xirr(
            full_final_etfs[f"{etf}_CashFlow"],
            full_final_etfs["TradeDate"],
        )

        print(f"  • {etf} XIRR: {xir * 100:.2f}%\n")
        return xir

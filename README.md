# XIRR Portfolio Analyzer

Calculate XIRR (Extended Internal Rate of Return) for stock portfolios with automated price fetching and split handling.

## Features

- 📊 Trade data processing and portfolio analysis
- 💰 Automated price fetching (FMP API, yfinance)
- 🔄 Stock split handling (automated + manual)
- 📈 XIRR calculation for investment returns
- 📝 Manual price/split configuration support

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Configuration

Edit JSON files in `config/` for manual prices and splits:
- `manual_prices_config.json` - Custom stock prices
- `manual_splits_config.json` - Manual split ratios

## Outputs

Generated CSV files in `outputs/`:
- `current_portfolio.csv` - Current holdings
- `Final_portfolio_with_price.csv` - Portfolio with prices
- `All_trades_with_current_portfolio.csv` - Complete trade history
- `XIRR_result.csv` - XIRR calculation results
- `stocks_needing_manual_attention.csv` - Stocks requiring manual input

## Structure

```
stock_portfolio_analyzer/
├── main.py
├── config/          # Manual configurations
├── core/            # Core logic modules
└── outputs/         # Generated reports
```

## Requirements

- Python 3.x
- FMP API key (optional)
- Internet connection for price fetching
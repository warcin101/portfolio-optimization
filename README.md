# ETF Portfolio Tracker

A local Streamlit dashboard for managing a passive ETF portfolio. It pulls live prices via yfinance, computes HRP target weights, and generates buy and rebalance signals — all denominated in PLN.

The app is built to work with any broker — the only broker-specific piece is the data ingestion plugin in `src/xtb.py`, which reads XTB's XLSX account export. Adapting it for another brokerage means writing a similar parser that returns holdings as `{ticker: value}`. XTB's individual-user API has been discontinued, so the integration relies on the manual XLSX export instead. Brokerages that still expose an API could support more real-time data flows through the same plugin interface.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Adding your XTB holdings

1. In XTB, export your account as an XLSX file (account statement → open positions).
2. Drop the file into `data-archive/xtb-portfolio-export-snapshot/`. Name format: `account_<anything>_YYYY-MM-DD.xlsx`.
3. Restart the app — it picks up the file with the most recent date automatically.

> `data-archive/xtb-portfolio-export-snapshot/account_example_2026-05-20.xlsx` is **sample data only** — fictional positions and PLN values, no real account information.

## Tabs

| Tab | What it does |
|-----|-------------|
| **Portfolio** | Current holdings vs HRP target weights |
| **Monthly Buy** | Buy-only signal: allocates new capital toward target weights without selling |
| **Yearly Rebalance** | Concentration alert (a holding above 20% of the portfolio *and* above 2× its target) plus informational drift and BUY/SELL/HOLD columns |
| **Backtest** | Walk-forward backtest comparing HRP, Equal Weight, and Risk Parity |

## Asset universe

8 UCITS ETFs covering US equity, Europe, Japan, Emerging Markets, Healthcare, Global REITs, and Gold — chosen to suit the author's needs. The universe is easy to adapt: edit `src/universe.py` to add, remove, or swap tickers for your own allocation strategy.

## Notes

- Price history is cached in `data-archive/prices.parquet`. Delete it and click **Refresh prices** to force a fresh download.
- Optimization and backtesting run on USD prices (currency-agnostic log returns). All display values are converted to PLN using the live PLNUSD rate from yfinance.
- The **Yearly Rebalance** tab is informational, not prescriptive. It shows what selling and buying would be needed to return to target weights — whether to act on it is entirely up to you. Drift from the current target alone is not treated as a signal, because HRP targets move month to month and the strategy is buy-only; the concentration alert is the guardrail for one holding running away after a price rally.

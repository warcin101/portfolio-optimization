import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "data-archive"
CACHE_FILE = CACHE_DIR / "prices.parquet"


def fetch_prices(tickers, start="2005-01-01", refresh=False):
    CACHE_DIR.mkdir(exist_ok=True)
    if not refresh and CACHE_FILE.exists():
        return pd.read_parquet(CACHE_FILE)
    # threads=False avoids yfinance's internal SQLite "database is locked" error
    raw = yf.download(tickers, start=start, auto_adjust=True, progress=False, threads=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    prices = prices.reindex(columns=tickers)
    prices.to_parquet(CACHE_FILE)
    return prices


def monthly_prices(prices):
    # ffill before resampling fills trading halts / data gaps within a month
    return prices.ffill().resample("ME").last()


def simple_returns(prices):
    return monthly_prices(prices).pct_change(fill_method=None).dropna(how="all")


def log_returns(prices):
    mp = monthly_prices(prices)
    lr = np.log(mp / mp.shift(1))
    # Drop only rows where EVERY ticker is NaN, not rows where any ticker is NaN.
    # This preserves history even when one ticker has a gap.
    return lr.dropna(how="all")


def load_holdings(csv_path):
    path = Path(csv_path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "ticker", "action", "quantity", "price_per_unit", "currency", "fee"])
    df = pd.read_csv(path, parse_dates=["date"])
    df["quantity"] = df["quantity"].where(df["action"] == "buy", -df["quantity"])
    return df


def current_holdings(csv_path):
    df = load_holdings(csv_path)
    if df.empty:
        return pd.Series(dtype=float)
    net = df.groupby("ticker")["quantity"].sum()
    return net[net > 0]

import yfinance as yf
import pandas as pd
from pathlib import Path
from universe import UCITS_MAP

_UCITS_TO_US = {v: k for k, v in UCITS_MAP.items()}

SNAPSHOT_DIR = Path(__file__).parent.parent / "data-archive" / "xtb-portfolio-export-snapshot"


def get_plnusd_rate():
    """Fetch current PLN/USD exchange rate (daily close, last available)."""
    raw = yf.download("PLNUSD=X", period="5d", auto_adjust=True, progress=False, threads=False)
    return float(raw["Close"].dropna().iloc[-1])


def parse_xtb_export(path):
    """
    Read an XTB account XLSX export and return current holdings as
    {us_ticker: value_pln} using the raw PLN purchase value from the export.
    """
    xl = pd.ExcelFile(Path(path))

    sheet = next(s for s in xl.sheet_names if s.upper().startswith("OPEN POSITION"))

    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    header_idx = raw.apply(lambda r: "Symbol" in r.values, axis=1).idxmax()

    df = pd.read_excel(xl, sheet_name=sheet, header=header_idx)
    df = df.dropna(subset=["Symbol"])
    df = df[~df["Symbol"].astype(str).str.lower().isin(["total", "symbol"])]

    df["us_ticker"] = df["Symbol"].map(_UCITS_TO_US)
    df = df.dropna(subset=["us_ticker"])

    df["value_pln"] = df["Purchase value"]

    grouped = df.groupby("us_ticker").agg(
        value_pln=("value_pln", "sum"),
        volume=("Volume", "sum"),
        ucits_ticker=("Symbol", "first"),
    )
    return grouped


def find_latest_xtb_export():
    """Return the snapshot with the most recent export date in its filename, or None."""
    def _export_date(p):
        try:
            return p.stem.rsplit("_", 1)[-1]  # trailing YYYY-MM-DD segment
        except Exception:
            return ""
    files = sorted(SNAPSHOT_DIR.glob("account_*.xlsx"), key=_export_date)
    return files[-1] if files else None
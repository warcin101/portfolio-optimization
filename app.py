import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from universe import TICKERS, METADATA, UCITS_MAP
from data import fetch_prices, log_returns, simple_returns
from optimize import hrp_weights, equal_weights
from signals import monthly_buy_signal, yearly_rebalance_signal, CONCENTRATION_FLOOR, CONCENTRATION_MULT
from backtest import walk_forward, performance_stats
from xtb import parse_xtb_export, find_latest_xtb_export, get_plnusd_rate

XTB_EXPORT = find_latest_xtb_export()

st.set_page_config(page_title="ETF Portfolio Tracker", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Helvetica, Arial, sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("ETF Portfolio Tracker")

with st.sidebar:
    st.header("Settings")
    refresh = st.button("Refresh prices")
    monthly_budget = st.number_input("Monthly budget (PLN)", min_value=500, max_value=200000, value=5000, step=500)
    lookback = st.slider("Lookback months", 6, 36, 24)

# No st.cache_data: fetch_prices already caches in parquet, and a Streamlit cache keyed on
# the button flag serves stale pre-refresh data on the next rerun (flag flips back to False).
def load_prices(refresh_flag):
    with st.spinner("Fetching prices..."):
        return fetch_prices(TICKERS, refresh=refresh_flag)

prices = load_prices(refresh)

if prices is None or prices.empty:
    st.error("Could not load price data. Check your internet connection.")
    st.stop()

log_ret = log_returns(prices)
simple_ret = simple_returns(prices)

_plnusd = get_plnusd_rate()
_usdpln = 1.0 / _plnusd
latest_prices_pln = prices.iloc[-1] * _usdpln

_xtb = parse_xtb_export(XTB_EXPORT) if XTB_EXPORT else pd.DataFrame(columns=["value_pln", "volume", "ucits_ticker"])
holdings_value_pln = _xtb["value_pln"] if not _xtb.empty else pd.Series(dtype=float)
holdings_volume = _xtb["volume"] if not _xtb.empty else pd.Series(dtype=float)
# Equivalent US quantities: PLN value / PLN price — keeps signal functions unchanged
holdings_qty = (holdings_value_pln / latest_prices_pln.reindex(holdings_value_pln.index)).dropna()

target_weights = hrp_weights(log_ret.tail(lookback))

tab1, tab2, tab3, tab4 = st.tabs(["Portfolio", "Monthly Buy", "Yearly Rebalance", "Backtest"])

with tab1:
    st.subheader("Current Holdings")

    if holdings_qty.empty:
        st.info("No holdings yet. Drop an XTB account export (account_*.xlsx) in the project folder to see your portfolio here.")
    else:
        current_values = (holdings_qty * latest_prices_pln).dropna()
        total_value = current_values.sum()
        current_w = current_values / total_value

        overview = pd.DataFrame({
            "XTB Ticker": pd.Series({t: UCITS_MAP.get(t) or "—" for t in current_w.index}),
            "Qty (XTB)": holdings_volume.reindex(current_w.index),
            "Value (PLN)": current_values,
            "Current Weight": current_w,
            "Target Weight": target_weights.reindex(current_w.index, fill_value=0),
        }).dropna(subset=["Value (PLN)"])
        overview["Drift"] = overview["Current Weight"] - overview["Target Weight"]

        st.metric("Total Portfolio Value", f"{total_value:,.2f} PLN")
        st.dataframe(
            overview.style.format({
                "Qty (XTB)": "{:.4f}",
                "Value (PLN)": "{:,.2f} PLN",
                "Current Weight": "{:.1%}",
                "Target Weight": "{:.1%}",
                "Drift": "{:+.1%}",
            }),
            width='stretch',
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Current", x=overview.index, y=overview["Current Weight"]))
        fig.add_trace(go.Bar(name="Target (HRP)", x=overview.index, y=overview["Target Weight"]))
        fig.update_layout(barmode="group", yaxis_tickformat=".0%", title="Current vs Target Weights")
        st.plotly_chart(fig, width='stretch')

    st.subheader("HRP Target Weights (full universe)")
    tw_df = target_weights.reset_index()
    tw_df.columns = ["Ticker", "Weight"]
    tw_df["Name"] = tw_df["Ticker"].map(lambda t: METADATA.get(t, {}).get("name", t))
    fig2 = px.pie(tw_df, values="Weight", names="Ticker", hover_data=["Name"],
                  title="HRP Target Allocation")
    st.plotly_chart(fig2, width='stretch')

with tab2:
    st.subheader(f"Monthly Buy Signal — Budget: {monthly_budget:,.0f} PLN")
    st.caption("Buy-only: allocates new capital to move portfolio toward HRP targets without selling.")

    signal = monthly_buy_signal(
        holdings_qty if not holdings_qty.empty else pd.Series(dtype=float),
        target_weights,
        monthly_budget,
        latest_prices_pln,
    )

    display = signal[signal["buy_pln"] > 0.01].copy()
    display["buy_qty"] = display["buy_pln"] / latest_prices_pln.reindex(display.index)
    display["XTB Ticker"] = display.index.map(lambda t: UCITS_MAP.get(t) or "—")

    st.dataframe(
        display[["XTB Ticker", "buy_pln", "buy_qty", "new_weight", "target_weight", "drift_after"]].style.format({
            "buy_pln": "{:,.2f} PLN",
            "buy_qty": "{:.4f}",
            "new_weight": "{:.1%}",
            "target_weight": "{:.1%}",
            "drift_after": "{:+.1%}",
        }),
        width='stretch',
    )

    fig3 = px.bar(display.reset_index(names="Ticker"), x="Ticker", y="buy_pln",
                  labels={"buy_pln": "Amount to buy (PLN)"},
                  title="Capital Deployment This Month")
    st.plotly_chart(fig3, width='stretch')

with tab3:
    st.subheader("Yearly Rebalance Check")

    if holdings_qty.empty:
        st.info("No holdings to analyse. Drop an XTB account export to see rebalance recommendations.")
    else:
        rebal_df, _ = yearly_rebalance_signal(holdings_qty, target_weights, latest_prices_pln)

        over_cap = rebal_df[rebal_df["over_cap"]]
        if not over_cap.empty:
            flagged = ", ".join(f"{t} {r.current_weight:.0%} (target {r.target_weight:.0%})" for t, r in over_cap.iterrows())
            st.error(
                f"Concentration alert — {flagged}: above {CONCENTRATION_FLOOR:.0%} and {CONCENTRATION_MULT:.0f}× target. "
                "Monthly buys already skip it; trimming is your call (selling realises 19% tax on gains)."
            )
        else:
            st.success(f"No concentration alert — no holding above {CONCENTRATION_FLOOR:.0%} and {CONCENTRATION_MULT:.0f}× its target.")
        st.caption("Drift and trade columns are informational: HRP targets move month to month, so drift alone is not a rebalance signal.")

        rebal_df["XTB Ticker"] = rebal_df.index.map(lambda t: UCITS_MAP.get(t) or "—")
        st.dataframe(
            rebal_df[["XTB Ticker", "current_weight", "target_weight", "drift", "trade_pln", "action", "over_cap"]].style.format({
                "current_weight": "{:.1%}",
                "target_weight": "{:.1%}",
                "drift": "{:+.1%}",
                "trade_pln": "{:+,.2f} PLN",
            }).applymap(
                lambda v: "color: red" if v == "SELL" else ("color: green" if v == "BUY" else ""),
                subset=["action"],
            ),
            width='stretch',
        )

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Current", x=rebal_df.index, y=rebal_df["current_weight"]))
        fig4.add_trace(go.Bar(name="Target", x=rebal_df.index, y=rebal_df["target_weight"]))
        fig4.update_layout(barmode="group", yaxis_tickformat=".0%", title="Current vs Target — Rebalance View")
        st.plotly_chart(fig4, width='stretch')

with tab4:
    st.subheader("Walk-forward Backtest")

    strategy = st.selectbox("Strategy", ["hrp", "equal", "rp"],
                             format_func=lambda s: {"hrp": "HRP", "equal": "Equal Weight", "rp": "Risk Parity"}[s])

    with st.spinner("Running backtest..."):
        nav, weights_hist = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy=strategy)

    stats = performance_stats(nav)
    cols = st.columns(len(stats))
    for col, (k, v) in zip(cols, stats.items()):
        col.metric(k, v)

    fig5 = px.line(nav, title=f"Portfolio NAV — {strategy.upper()} (base 100)",
                   labels={"value": "NAV", "index": "Date"})
    st.plotly_chart(fig5, width='stretch')

    st.subheader("HRP vs Equal Weight vs Risk Parity")
    with st.spinner("Running comparison..."):
        nav_hrp, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="hrp")
        nav_eq, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="equal")
        nav_rp, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="rp")

    comparison = pd.DataFrame({"HRP": nav_hrp, "Equal Weight": nav_eq, "Risk Parity": nav_rp}).dropna()
    fig6 = px.line(comparison, title="Strategy Comparison (base 100)")
    st.plotly_chart(fig6, width='stretch')

    stats_all = {
        "HRP": performance_stats(nav_hrp),
        "Equal Weight": performance_stats(nav_eq),
        "Risk Parity": performance_stats(nav_rp),
    }
    st.dataframe(pd.DataFrame(stats_all).T, width='stretch')

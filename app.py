import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from universe import TICKERS, METADATA, UCITS_MAP
from data import fetch_prices, log_returns, simple_returns, current_holdings
from optimize import hrp_weights, equal_weights
from signals import monthly_buy_signal, yearly_rebalance_signal
from backtest import walk_forward, performance_stats

HOLDINGS_CSV = Path(__file__).parent / "movs_etf.csv"

st.set_page_config(page_title="ETF Portfolio Tracker", layout="wide")
st.title("ETF Portfolio Tracker")

with st.sidebar:
    st.header("Settings")
    refresh = st.button("Refresh prices")
    monthly_budget = st.number_input("Monthly budget (USD)", min_value=50, max_value=50000, value=500, step=50)
    drift_threshold = st.slider("Drift threshold (%)", 1, 20, 5) / 100
    lookback = st.slider("Lookback months", 6, 36, 24)

@st.cache_data(show_spinner="Fetching prices...")
def load_prices(refresh_flag):
    return fetch_prices(TICKERS, refresh=refresh_flag)

prices = load_prices(refresh)

if prices is None or prices.empty:
    st.error("Could not load price data. Check your internet connection.")
    st.stop()

log_ret = log_returns(prices)
simple_ret = simple_returns(prices)

holdings_qty = current_holdings(HOLDINGS_CSV)
latest_prices = prices.iloc[-1]

target_weights = hrp_weights(log_ret.tail(lookback))

tab1, tab2, tab3, tab4 = st.tabs(["Portfolio", "Monthly Buy", "Yearly Rebalance", "Backtest"])

with tab1:
    st.subheader("Current Holdings")

    if holdings_qty.empty:
        st.info("No holdings yet. Add transactions to movs_etf.csv to see your portfolio here.")
    else:
        current_values = (holdings_qty * latest_prices).dropna()
        total_value = current_values.sum()
        current_w = current_values / total_value

        overview = pd.DataFrame({
            "XTB Ticker": pd.Series({t: UCITS_MAP.get(t) or "—" for t in current_w.index}),
            "Qty": holdings_qty,
            "Price (USD)": latest_prices,
            "Value (USD)": current_values,
            "Current Weight": current_w,
            "Target Weight": target_weights.reindex(current_w.index, fill_value=0),
        }).dropna(subset=["Value (USD)"])
        overview["Drift"] = overview["Current Weight"] - overview["Target Weight"]

        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        st.dataframe(
            overview.style.format({
                "Price (USD)": "${:.2f}",
                "Value (USD)": "${:,.2f}",
                "Current Weight": "{:.1%}",
                "Target Weight": "{:.1%}",
                "Drift": "{:+.1%}",
            }),
            use_container_width=True,
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Current", x=overview.index, y=overview["Current Weight"]))
        fig.add_trace(go.Bar(name="Target (HRP)", x=overview.index, y=overview["Target Weight"]))
        fig.update_layout(barmode="group", yaxis_tickformat=".0%", title="Current vs Target Weights")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("HRP Target Weights (full universe)")
    tw_df = target_weights.reset_index()
    tw_df.columns = ["Ticker", "Weight"]
    tw_df["Name"] = tw_df["Ticker"].map(lambda t: METADATA.get(t, {}).get("name", t))
    fig2 = px.pie(tw_df, values="Weight", names="Ticker", hover_data=["Name"],
                  title="HRP Target Allocation")
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader(f"Monthly Buy Signal — Budget: ${monthly_budget:,.0f}")
    st.caption("Buy-only: allocates new capital to move portfolio toward HRP targets without selling.")

    signal = monthly_buy_signal(
        holdings_qty if not holdings_qty.empty else pd.Series(dtype=float),
        target_weights,
        monthly_budget,
        latest_prices,
    )

    display = signal[signal["buy_usd"] > 0.01].copy()
    display["buy_qty"] = display["buy_usd"] / latest_prices.reindex(display.index)
    display["XTB Ticker"] = display.index.map(lambda t: UCITS_MAP.get(t) or "—")

    st.dataframe(
        display[["XTB Ticker", "buy_usd", "buy_qty", "new_weight", "target_weight", "drift_after"]].style.format({
            "buy_usd": "${:,.2f}",
            "buy_qty": "{:.4f}",
            "new_weight": "{:.1%}",
            "target_weight": "{:.1%}",
            "drift_after": "{:+.1%}",
        }),
        use_container_width=True,
    )

    fig3 = px.bar(display.reset_index(names="Ticker"), x="Ticker", y="buy_usd",
                  labels={"buy_usd": "Amount to buy (USD)"},
                  title="Capital Deployment This Month")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Yearly Rebalance Check")

    if holdings_qty.empty:
        st.info("No holdings to analyse. Add transactions to movs_etf.csv first.")
    else:
        rebal_df, should_rebalance = yearly_rebalance_signal(
            holdings_qty, target_weights, latest_prices, drift_threshold
        )

        if should_rebalance:
            st.warning(f"Rebalancing recommended — one or more positions drifted >{drift_threshold:.0%} from target.")
        else:
            st.success(f"Portfolio is on track — all positions within {drift_threshold:.0%} of target.")

        rebal_df["XTB Ticker"] = rebal_df.index.map(lambda t: UCITS_MAP.get(t) or "—")
        st.dataframe(
            rebal_df[["XTB Ticker", "current_weight", "target_weight", "drift", "trade_usd", "action"]].style.format({
                "current_weight": "{:.1%}",
                "target_weight": "{:.1%}",
                "drift": "{:+.1%}",
                "trade_usd": "${:+,.2f}",
            }).applymap(
                lambda v: "color: red" if v == "SELL" else ("color: green" if v == "BUY" else ""),
                subset=["action"],
            ),
            use_container_width=True,
        )

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(name="Current", x=rebal_df.index, y=rebal_df["current_weight"]))
        fig4.add_trace(go.Bar(name="Target", x=rebal_df.index, y=rebal_df["target_weight"]))
        fig4.update_layout(barmode="group", yaxis_tickformat=".0%", title="Current vs Target — Rebalance View")
        st.plotly_chart(fig4, use_container_width=True)

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
    st.plotly_chart(fig5, use_container_width=True)

    st.subheader("HRP vs Equal Weight vs Risk Parity")
    with st.spinner("Running comparison..."):
        nav_hrp, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="hrp")
        nav_eq, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="equal")
        nav_rp, _ = walk_forward(log_ret, simple_ret, lookback_months=lookback, strategy="rp")

    comparison = pd.DataFrame({"HRP": nav_hrp, "Equal Weight": nav_eq, "Risk Parity": nav_rp}).dropna()
    fig6 = px.line(comparison, title="Strategy Comparison (base 100)")
    st.plotly_chart(fig6, use_container_width=True)

    stats_all = {
        "HRP": performance_stats(nav_hrp),
        "Equal Weight": performance_stats(nav_eq),
        "Risk Parity": performance_stats(nav_rp),
    }
    st.dataframe(pd.DataFrame(stats_all).T, use_container_width=True)
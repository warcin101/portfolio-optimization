import pandas as pd


def monthly_buy_signal(holdings_qty, target_weights, new_capital, latest_prices):
    """
    Buy-only signal: allocate new_capital to move portfolio toward target weights.
    holdings_qty: pd.Series, ticker -> quantity held
    target_weights: pd.Series, ticker -> target weight (sum to 1)
    latest_prices: pd.Series, ticker -> current price (PLN)
    Returns: pd.DataFrame with columns [ticker, buy_pln, buy_qty, new_weight]
    """
    current_values = (holdings_qty * latest_prices).fillna(0)
    total_current = current_values.sum()
    total_future = total_current + new_capital

    target_values = target_weights * total_future
    gap = (target_values - current_values).clip(lower=0)

    if gap.sum() == 0:
        gap = target_weights * new_capital

    buy_pln = gap / gap.sum() * new_capital
    buy_qty = (buy_pln / latest_prices).fillna(0)

    total_new_values = current_values + buy_pln
    new_weights = total_new_values / total_new_values.sum()

    result = pd.DataFrame({
        "buy_pln": buy_pln,
        "buy_qty": buy_qty,
        "new_weight": new_weights,
        "target_weight": target_weights,
    }).fillna(0)
    result["drift_after"] = result["new_weight"] - result["target_weight"]
    return result.sort_values("buy_pln", ascending=False)


# Concentration alert: a holding is flagged when its weight is above BOTH the floor and
# MULT x its current target. Buy-only can't sell, so a price run-up (e.g. gold) can leave one
# ticker dominating risk; drift vs the noisy HRP target is too noisy to catch that.
CONCENTRATION_FLOOR = 0.20
CONCENTRATION_MULT = 2.0


def yearly_rebalance_signal(holdings_qty, target_weights, latest_prices, drift_threshold=0.05):
    """
    Analyse drift from target and recommend rebalancing trades if needed.
    Returns: pd.DataFrame with current/target weights, drift, suggested trades, over_cap flag.
    """
    current_values = (holdings_qty * latest_prices).fillna(0)
    total = current_values.sum()

    if total == 0:
        return pd.DataFrame(), False

    current_weights = current_values / total
    all_tickers = target_weights.index.union(current_weights.index)
    cw = current_weights.reindex(all_tickers, fill_value=0)
    tw = target_weights.reindex(all_tickers, fill_value=0)
    drift = cw - tw

    should_rebalance = (drift.abs() > drift_threshold).any()

    target_values = tw * total
    trade_pln = target_values - current_values.reindex(all_tickers, fill_value=0)

    result = pd.DataFrame({
        "current_weight": cw,
        "target_weight": tw,
        "drift": drift,
        "trade_pln": trade_pln,
        "over_cap": (cw > CONCENTRATION_FLOOR) & (cw > CONCENTRATION_MULT * tw),
    })
    result["action"] = result["trade_pln"].apply(
        lambda x: "BUY" if x > 0 else ("SELL" if x < 0 else "HOLD")
    )
    return result.sort_values("drift", ascending=False), should_rebalance

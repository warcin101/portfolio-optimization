# Not currently used in the portfolio process. Kept for potential future use as a
# momentum tilt (universe filter or weight overlay) on top of the HRP allocation.
import pandas as pd


def momentum_12_1(monthly_returns):
    # skip last month (t-1 reversal), cumulate prior 11 months → price move P_{t-12} to P_{t-1}
    scores = monthly_returns.shift(1).rolling(11).apply(
        lambda x: (1 + x).prod() - 1, raw=True
    )
    ranks = scores.rank(axis=1, ascending=True)
    return scores, ranks


def momentum_weights(monthly_returns, top_n=None):
    scores, ranks = momentum_12_1(monthly_returns)
    latest_ranks = ranks.iloc[-1].dropna()
    if top_n:
        latest_ranks = latest_ranks.nlargest(top_n)
    weights = latest_ranks / latest_ranks.sum()
    return weights.rename("momentum_weight")

import pandas as pd
import numpy as np
from optimize import hrp_weights, equal_weights, risk_parity_weights


def walk_forward(log_ret, simple_ret, lookback_months=12, strategy="hrp"):
    nav = pd.Series(index=simple_ret.index, dtype=float)
    weights_hist = pd.DataFrame(index=simple_ret.index, columns=simple_ret.columns, dtype=float)

    nav.iloc[lookback_months - 1] = 100.0

    for i in range(lookback_months, len(simple_ret)):
        window = log_ret.iloc[i - lookback_months:i]

        if strategy == "hrp":
            w = hrp_weights(window)
        elif strategy == "equal":
            w = equal_weights(simple_ret.columns.tolist())
        elif strategy == "rp":
            w = risk_parity_weights(window)
        else:
            raise ValueError(strategy)

        w = w.reindex(simple_ret.columns, fill_value=0)
        weights_hist.iloc[i] = w

        port_ret = (w * simple_ret.iloc[i].reindex(w.index, fill_value=0)).sum()
        nav.iloc[i] = nav.iloc[i - 1] * (1 + port_ret)

    return nav.dropna(), weights_hist.dropna()


def performance_stats(nav):
    rets = nav.pct_change().dropna()
    n_years = len(rets) / 12

    cagr = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    vol = rets.std() * np.sqrt(12)
    sharpe = (rets.mean() * 12) / vol if vol > 0 else 0.0

    roll_max = nav.cummax()
    dd = (nav - roll_max) / roll_max
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0.0

    return {
        "CAGR": f"{cagr:.2%}",
        "Volatility (ann.)": f"{vol:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_dd:.2%}",
        "Calmar Ratio": f"{calmar:.2f}",
    }

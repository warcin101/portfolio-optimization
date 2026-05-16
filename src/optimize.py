import numpy as np
import pandas as pd
import riskfolio as rp


def hrp_weights(log_returns_df):
    clean = (
        log_returns_df
        .replace([np.inf, -np.inf], np.nan)
        .dropna(axis=1, how="any")
        .dropna()
    )
    clean = clean.loc[:, clean.std() > 1e-10]

    # Riskfolio needs at least as many observations as assets to compute a valid
    # covariance/correlation matrix; fall back to equal weight if data is thin.
    if clean.shape[0] < 6 or clean.shape[1] < 2:
        n = log_returns_df.shape[1]
        return pd.Series(1 / n, index=log_returns_df.columns, name="hrp_weight")

    port = rp.HCPortfolio(returns=clean)
    weights = port.optimization(
        model="HRP",
        codependence="pearson",
        rm="MV",
        rf=0,
        linkage="ward",
        max_k=10,
        leaf_order=True,
    )
    return weights.squeeze().reindex(log_returns_df.columns, fill_value=0).rename("hrp_weight")


def equal_weights(tickers):
    n = len(tickers)
    return pd.Series(1 / n, index=tickers, name="eq_weight")


def risk_parity_weights(log_returns_df):
    clean = (
        log_returns_df
        .replace([np.inf, -np.inf], np.nan)
        .dropna(axis=1, how="any")
        .dropna()
    )
    clean = clean.loc[:, clean.std() > 1e-10]
    vols = clean.std()
    inv_vol = 1 / vols
    weights = inv_vol / inv_vol.sum()
    return weights.reindex(log_returns_df.columns, fill_value=0).rename("rp_weight")
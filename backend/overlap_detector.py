"""
Residual correlation analysis and hierarchical clustering.
Detects hidden shared risk beyond market beta.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


def compute_residual_correlations(
    prices: pd.DataFrame,
    market_returns: pd.Series = None,
) -> pd.DataFrame:
    """Regress each stock on market returns (OLS), extract residuals, correlate.

    If market_returns is None, uses equal-weighted portfolio of all holdings as proxy.
    """
    returns = prices.pct_change().dropna()

    if market_returns is None:
        market_returns = returns.mean(axis=1)

    # Align indices
    common_idx = returns.index.intersection(market_returns.index)
    returns = returns.loc[common_idx]
    market_returns = market_returns.loc[common_idx]

    residuals = pd.DataFrame(index=returns.index)

    for col in returns.columns:
        y = returns[col].values
        X = sm.add_constant(market_returns.values)
        try:
            model = sm.OLS(y, X).fit()
            residuals[col] = model.resid
        except Exception:
            residuals[col] = y  # fallback to raw returns

    return residuals.corr()


def cluster_holdings(
    corr_matrix: pd.DataFrame,
    n_clusters: int = None,
) -> dict[str, int]:
    """Hierarchical clustering on correlation matrix.

    Args:
        corr_matrix: Pairwise correlation matrix
        n_clusters: Number of clusters. If None, auto-detect.

    Returns:
        {ticker: cluster_id, ...}
    """
    tickers = list(corr_matrix.columns)
    n = len(tickers)

    if n <= 1:
        return {tickers[0]: 0} if n == 1 else {}

    # Convert correlation to distance: d = sqrt(2 * (1 - rho))
    corr_vals = corr_matrix.values.copy()
    np.fill_diagonal(corr_vals, 1.0)
    # Clip to valid range for numerical stability
    corr_vals = np.clip(corr_vals, -1.0, 1.0)
    dist_matrix = np.sqrt(2.0 * (1.0 - corr_vals))
    np.fill_diagonal(dist_matrix, 0.0)

    # Make symmetric
    dist_matrix = (dist_matrix + dist_matrix.T) / 2.0

    # Convert to condensed form for scipy
    condensed = squareform(dist_matrix, checks=False)

    # Hierarchical clustering (Ward's method)
    Z = linkage(condensed, method="average")

    if n_clusters is None:
        # Auto-detect: use max 5 clusters or n/2, whichever is smaller
        max_k = min(5, max(2, n // 2))
        # Use distance threshold at 70th percentile of linkage distances
        threshold = np.percentile(Z[:, 2], 70)
        labels = fcluster(Z, t=threshold, criterion="distance")
        # Ensure we don't get too many clusters
        if len(set(labels)) > max_k:
            labels = fcluster(Z, t=max_k, criterion="maxclust")
    else:
        labels = fcluster(Z, t=n_clusters, criterion="maxclust")

    return {tickers[i]: int(labels[i]) for i in range(n)}


def analyze_idiosyncratic_risk(
    prices: pd.DataFrame,
    weights: dict[str, float],
    market_returns: pd.Series = None,
) -> dict:
    """Full idiosyncratic risk analysis: residual correlations + clustering.

    Returns:
        {
            "residual_correlations": {ticker: {ticker: corr, ...}},
            "clusters": {ticker: cluster_id, ...},
            "cluster_summary": [{cluster_id, tickers, combined_weight}, ...],
            "high_residual_pairs": [{ticker1, ticker2, residual_corr}, ...],
        }
    """
    tickers = [t for t in weights.keys() if t in prices.columns]
    if len(tickers) < 2:
        return {
            "residual_correlations": {},
            "clusters": {t: 0 for t in tickers},
            "cluster_summary": [],
            "high_residual_pairs": [],
        }

    prices_subset = prices[tickers]
    resid_corr = compute_residual_correlations(prices_subset, market_returns)
    clusters = cluster_holdings(resid_corr)

    # Cluster summary
    cluster_ids = sorted(set(clusters.values()))
    cluster_summary = []
    for cid in cluster_ids:
        members = [t for t, c in clusters.items() if c == cid]
        combined_weight = sum(weights.get(t, 0) for t in members)
        cluster_summary.append({
            "cluster_id": cid,
            "tickers": members,
            "combined_weight": round(combined_weight, 4),
        })

    # Find high residual correlation pairs (>0.3, excluding self)
    high_pairs = []
    for i, t1 in enumerate(tickers):
        for j, t2 in enumerate(tickers):
            if j <= i:
                continue
            rc = resid_corr.loc[t1, t2]
            if abs(rc) > 0.3:
                high_pairs.append({
                    "ticker1": t1,
                    "ticker2": t2,
                    "residual_corr": round(float(rc), 4),
                })

    high_pairs.sort(key=lambda x: abs(x["residual_corr"]), reverse=True)

    return {
        "residual_correlations": resid_corr.to_dict(),
        "clusters": clusters,
        "cluster_summary": cluster_summary,
        "high_residual_pairs": high_pairs,
    }

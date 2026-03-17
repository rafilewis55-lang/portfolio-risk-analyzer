"""
Core portfolio math: HHI, N_eff, diversification ratio, marginal risk contributions.
All matrix operations use numpy vectorized ops.
"""

import numpy as np
import pandas as pd


def compute_hhi(weights: dict[str, float]) -> float:
    """Herfindahl-Hirschman Index = sum of squared weights. Range [1/N, 1.0]."""
    w = np.array(list(weights.values()))
    return float(np.sum(w ** 2))


def compute_correlation_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    """Pairwise correlation matrix from price DataFrame (columns = tickers)."""
    returns = prices.pct_change().dropna()
    return returns.corr()


def compute_covariance_matrix(prices: pd.DataFrame) -> pd.DataFrame:
    """Annualized covariance matrix from daily price DataFrame."""
    returns = prices.pct_change().dropna()
    return returns.cov() * 252


def compute_n_eff(corr_matrix: pd.DataFrame) -> float:
    """Effective number of bets via eigenvalue decomposition.
    N_eff = (sum(eigenvalues))^2 / sum(eigenvalues^2).
    Always <= N (number of holdings).
    """
    eigenvalues = np.linalg.eigvalsh(corr_matrix.values)
    eigenvalues = eigenvalues[eigenvalues > 0]  # numerical stability
    sum_eig = np.sum(eigenvalues)
    sum_eig_sq = np.sum(eigenvalues ** 2)
    return float(sum_eig ** 2 / sum_eig_sq)


def compute_diversification_ratio(
    weights: dict[str, float],
    individual_vols: dict[str, float],
    portfolio_vol: float,
) -> float:
    """DR = (sum of w_i * sigma_i) / sigma_portfolio. Always >= 1.0."""
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    sigma = np.array([individual_vols[t] for t in tickers])
    weighted_sum = float(np.dot(w, sigma))
    return weighted_sum / portfolio_vol if portfolio_vol > 0 else 1.0


def compute_portfolio_volatility(
    weights: dict[str, float],
    cov_matrix: pd.DataFrame,
) -> float:
    """Annualized portfolio volatility = sqrt(w' * Cov * w)."""
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    cov = cov_matrix.loc[tickers, tickers].values
    port_var = float(w @ cov @ w)
    return float(np.sqrt(port_var))


def compute_marginal_risk_contributions(
    weights: dict[str, float],
    cov_matrix: pd.DataFrame,
) -> dict[str, float]:
    """Euler decomposition: MRC_i = w_i * (Cov * w)_i / sigma_portfolio.
    Sum of MRCs = portfolio volatility.
    """
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    cov = cov_matrix.loc[tickers, tickers].values
    port_var = float(w @ cov @ w)
    port_vol = np.sqrt(port_var)
    if port_vol == 0:
        return {t: 0.0 for t in tickers}
    # Marginal contribution = w_i * (Cov @ w)_i / sigma_p
    cov_w = cov @ w
    mrc = w * cov_w / port_vol
    return {t: float(mrc[i]) for i, t in enumerate(tickers)}


def compute_individual_volatilities(prices: pd.DataFrame) -> dict[str, float]:
    """Annualized volatility per ticker from daily prices."""
    returns = prices.pct_change().dropna()
    vols = returns.std() * np.sqrt(252)
    return {col: float(vols[col]) for col in prices.columns}


def compute_distance_to_diversification(
    n_eff: float,
    n_holdings: int,
    benchmark_n_eff: float = 30.0,
) -> float:
    """How far the portfolio is from well-diversified.
    0.0 = perfectly diversified (n_eff >= benchmark), 1.0 = single stock.
    """
    target = min(benchmark_n_eff, n_holdings)
    if target <= 1:
        return 0.0
    score = 1.0 - (n_eff - 1.0) / (target - 1.0)
    return float(np.clip(score, 0.0, 1.0))


def run_full_portfolio_analysis(
    prices: pd.DataFrame,
    weights: dict[str, float],
) -> dict:
    """Run all portfolio math and return consolidated results."""
    corr = compute_correlation_matrix(prices)
    cov = compute_covariance_matrix(prices)
    hhi = compute_hhi(weights)
    n_eff = compute_n_eff(corr)
    ind_vols = compute_individual_volatilities(prices)
    port_vol = compute_portfolio_volatility(weights, cov)
    dr = compute_diversification_ratio(weights, ind_vols, port_vol)
    mrc = compute_marginal_risk_contributions(weights, cov)
    dist = compute_distance_to_diversification(n_eff, len(weights))

    return {
        "hhi": hhi,
        "n_eff": n_eff,
        "diversification_ratio": dr,
        "portfolio_volatility": port_vol,
        "distance_to_diversification": dist,
        "individual_volatilities": ind_vols,
        "marginal_risk_contributions": mrc,
        "correlation_matrix": corr.to_dict(),
        "covariance_matrix": cov.to_dict(),
    }

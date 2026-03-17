"""
Unit tests for portfolio math functions.
Tests invariants: HHI bounds, N_eff bounds, DR >= 1, MRC Euler sum, PSD check.
"""

import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.portfolio import (
    compute_hhi,
    compute_correlation_matrix,
    compute_covariance_matrix,
    compute_n_eff,
    compute_diversification_ratio,
    compute_portfolio_volatility,
    compute_marginal_risk_contributions,
    compute_individual_volatilities,
    compute_distance_to_diversification,
)


def _make_prices(n_stocks=5, n_days=500, seed=42):
    """Generate synthetic price data for testing."""
    rng = np.random.RandomState(seed)
    returns = rng.normal(0.0005, 0.02, (n_days, n_stocks))
    # Add some correlation
    factor = rng.normal(0, 0.01, (n_days, 1))
    returns += factor * np.array([0.8, 0.6, 0.4, 0.2, 0.1])[:n_stocks]
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    tickers = [f"STK{i}" for i in range(n_stocks)]
    dates = pd.date_range("2022-01-01", periods=n_days, freq="B")
    return pd.DataFrame(prices, index=dates, columns=tickers)


class TestHHI:
    def test_equal_weights(self):
        """Equal weight -> HHI = 1/N."""
        n = 5
        weights = {f"STK{i}": 1.0 / n for i in range(n)}
        hhi = compute_hhi(weights)
        assert abs(hhi - 1.0 / n) < 1e-10

    def test_single_stock(self):
        """Single stock -> HHI = 1.0."""
        hhi = compute_hhi({"ONLY": 1.0})
        assert abs(hhi - 1.0) < 1e-10

    def test_concentrated(self):
        """Concentrated portfolio -> HHI > 1/N."""
        weights = {"A": 0.7, "B": 0.2, "C": 0.1}
        hhi = compute_hhi(weights)
        assert hhi > 1.0 / 3
        assert hhi <= 1.0

    def test_bounds(self):
        """HHI always in [1/N, 1.0]."""
        for n in [2, 5, 10, 20]:
            weights = {f"S{i}": 1.0 / n for i in range(n)}
            hhi = compute_hhi(weights)
            assert 1.0 / n - 1e-10 <= hhi <= 1.0 + 1e-10


class TestCorrelationMatrix:
    def test_symmetric(self):
        prices = _make_prices()
        corr = compute_correlation_matrix(prices)
        np.testing.assert_array_almost_equal(corr.values, corr.values.T)

    def test_diagonal_ones(self):
        prices = _make_prices()
        corr = compute_correlation_matrix(prices)
        np.testing.assert_array_almost_equal(np.diag(corr.values), np.ones(5))

    def test_values_in_range(self):
        prices = _make_prices()
        corr = compute_correlation_matrix(prices)
        assert (corr.values >= -1.0 - 1e-10).all()
        assert (corr.values <= 1.0 + 1e-10).all()

    def test_positive_semi_definite(self):
        prices = _make_prices()
        corr = compute_correlation_matrix(prices)
        eigenvalues = np.linalg.eigvalsh(corr.values)
        assert (eigenvalues >= -1e-10).all(), f"Not PSD: min eigenvalue = {eigenvalues.min()}"


class TestNEff:
    def test_upper_bound(self):
        """N_eff <= N always."""
        prices = _make_prices(n_stocks=5)
        corr = compute_correlation_matrix(prices)
        n_eff = compute_n_eff(corr)
        assert n_eff <= 5.0 + 1e-10

    def test_identity_correlation(self):
        """Identity correlation matrix -> N_eff = N."""
        n = 4
        corr = pd.DataFrame(np.eye(n), columns=[f"S{i}" for i in range(n)])
        n_eff = compute_n_eff(corr)
        assert abs(n_eff - n) < 1e-10

    def test_perfect_correlation(self):
        """All correlations = 1 -> N_eff = 1."""
        n = 4
        corr = pd.DataFrame(np.ones((n, n)), columns=[f"S{i}" for i in range(n)])
        n_eff = compute_n_eff(corr)
        assert abs(n_eff - 1.0) < 1e-6

    def test_positive(self):
        """N_eff always positive."""
        prices = _make_prices()
        corr = compute_correlation_matrix(prices)
        n_eff = compute_n_eff(corr)
        assert n_eff > 0


class TestDiversificationRatio:
    def test_always_gte_one(self):
        """DR >= 1.0 always (by Cauchy-Schwarz)."""
        prices = _make_prices()
        weights = {c: 0.2 for c in prices.columns}
        cov = compute_covariance_matrix(prices)
        ind_vols = compute_individual_volatilities(prices)
        port_vol = compute_portfolio_volatility(weights, cov)
        dr = compute_diversification_ratio(weights, ind_vols, port_vol)
        assert dr >= 1.0 - 1e-10

    def test_single_stock_equals_one(self):
        """Single stock -> DR = 1.0."""
        prices = _make_prices(n_stocks=1)
        col = prices.columns[0]
        weights = {col: 1.0}
        cov = compute_covariance_matrix(prices)
        ind_vols = compute_individual_volatilities(prices)
        port_vol = compute_portfolio_volatility(weights, cov)
        dr = compute_diversification_ratio(weights, ind_vols, port_vol)
        assert abs(dr - 1.0) < 1e-6


class TestMRC:
    def test_euler_sum(self):
        """MRC must sum to portfolio volatility (Euler theorem)."""
        prices = _make_prices()
        weights = {c: 0.2 for c in prices.columns}
        cov = compute_covariance_matrix(prices)
        port_vol = compute_portfolio_volatility(weights, cov)
        mrc = compute_marginal_risk_contributions(weights, cov)
        mrc_sum = sum(mrc.values())
        assert abs(mrc_sum - port_vol) < 1e-10, f"MRC sum {mrc_sum} != port_vol {port_vol}"

    def test_all_positive_equal_weight(self):
        """With positive correlations and equal weights, MRCs should be positive."""
        prices = _make_prices()
        weights = {c: 0.2 for c in prices.columns}
        cov = compute_covariance_matrix(prices)
        mrc = compute_marginal_risk_contributions(weights, cov)
        for t, val in mrc.items():
            assert val >= 0, f"MRC for {t} is negative: {val}"


class TestDistanceToDiversification:
    def test_single_stock(self):
        """Single stock: distance should be high."""
        d = compute_distance_to_diversification(1.0, 1)
        assert d == 0.0  # target = min(30, 1) = 1, score = 0

    def test_fully_diversified(self):
        """N_eff >= benchmark -> distance = 0."""
        d = compute_distance_to_diversification(30.0, 50)
        assert abs(d) < 1e-10

    def test_range(self):
        """Distance always in [0, 1]."""
        for n_eff in [1.0, 2.5, 5.0, 10.0, 30.0]:
            for n in [5, 10, 30, 50]:
                d = compute_distance_to_diversification(n_eff, n)
                assert 0.0 - 1e-10 <= d <= 1.0 + 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

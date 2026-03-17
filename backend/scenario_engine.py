"""
Scenario stress test engine.
Computes stressed risk scores, per-stock impacts, Monte Carlo loss distributions,
and hedge recommendations for 12 crisis scenarios.
"""

import os
import json
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR = os.path.join(BASE_DIR, "research")

# Module-level cache
_scenarios_cache = None


def load_scenarios() -> dict:
    """Load scenario definitions from research/scenarios.json, with caching."""
    global _scenarios_cache
    if _scenarios_cache is not None:
        return _scenarios_cache
    path = os.path.join(RESEARCH_DIR, "scenarios.json")
    with open(path, "r", encoding="utf-8") as f:
        _scenarios_cache = json.load(f)
    return _scenarios_cache


def get_scenario_list() -> list[dict]:
    """Return summary list of all scenarios for the frontend."""
    scenarios = load_scenarios()
    result = []
    for sid, s in scenarios.items():
        result.append({
            "id": sid,
            "name": s["name"],
            "emoji": s["emoji"],
            "category": s["category"],
            "confidence": s["confidence"],
            "description": s["description"],
        })
    return result


def compute_stressed_risk_scores(existing_risk_scores: dict, scenario: dict) -> dict:
    """
    Apply scenario shock multipliers to existing risk factor scores.

    Args:
        existing_risk_scores: analysisData.risk_factors with per_holding, portfolio_weighted, benchmark
        scenario: single scenario dict from scenarios.json

    Returns:
        {
            per_holding: {ticker: {factor: stressed_score}},
            portfolio_weighted: {factor: stressed_weighted},
            deltas: {ticker: {factor: delta}},
            portfolio_deltas: {factor: delta},
        }
    """
    multipliers = scenario["factor_shock_multipliers"]
    per_holding_orig = existing_risk_scores.get("per_holding", {})
    weighted_orig = existing_risk_scores.get("portfolio_weighted", {})

    stressed_per_holding = {}
    deltas = {}

    for ticker, scores in per_holding_orig.items():
        stressed = {}
        ticker_deltas = {}
        for factor, score in scores.items():
            mult = multipliers.get(factor, 1.0)
            new_score = min(10, max(1, round(score * mult)))
            stressed[factor] = new_score
            ticker_deltas[factor] = round(new_score - score, 1)
        stressed_per_holding[ticker] = stressed
        deltas[ticker] = ticker_deltas

    # Recompute portfolio weighted using original weights from the weighted scores
    # We need to infer weights or recompute from scratch
    # Since we only have per_holding and portfolio_weighted, we reconstruct weights
    # by using the fact that portfolio_weighted = sum(w_i * score_i)
    # But we don't have weights here, so we'll compute a simple average as fallback
    # The caller should pass weights separately or we compute from the portfolio_weighted ratio

    # For portfolio_weighted stressed scores, recompute from per-holding stressed
    # We'll estimate weights from the original data
    tickers = list(per_holding_orig.keys())
    if not tickers:
        return {
            "per_holding": {},
            "portfolio_weighted": {},
            "deltas": {},
            "portfolio_deltas": {},
        }

    # Estimate weights by solving for each factor
    # Simple approach: apply same multiplier to portfolio_weighted
    stressed_weighted = {}
    portfolio_deltas = {}
    for factor, orig_val in weighted_orig.items():
        mult = multipliers.get(factor, 1.0)
        new_val = round(min(10.0, max(1.0, orig_val * mult)), 2)
        stressed_weighted[factor] = new_val
        portfolio_deltas[factor] = round(new_val - orig_val, 2)

    return {
        "per_holding": stressed_per_holding,
        "portfolio_weighted": stressed_weighted,
        "deltas": deltas,
        "portfolio_deltas": portfolio_deltas,
    }


def compute_stock_scenario_impact(
    ticker: str,
    weight: float,
    industry: str,
    risk_scores: dict,
    scenario: dict,
    time_horizon: str,
    individual_volatility: float = 0.30,
    median_volatility: float = 0.30,
) -> dict:
    """
    Compute expected return impact for a single stock under a scenario.

    Returns:
        {
            ticker, weight, expected_return, std_dev, weighted_impact,
            primary_channel, channel_contributions
        }
    """
    # Base equity shock for time horizon
    shocks = scenario["asset_class_shocks"].get(time_horizon, scenario["asset_class_shocks"]["3_month"])
    base_mean = shocks["equity_mean"]
    base_std = shocks["equity_std"]

    # Sector adjustment
    sector_modifier = 0.0
    sector_adj = scenario.get("sector_adjustments", {})
    if industry in sector_adj:
        sector_modifier = sector_adj[industry]["return_modifier"]
    else:
        # Try partial match
        industry_lower = industry.lower()
        for key, adj in sector_adj.items():
            if key.lower() in industry_lower or industry_lower in key.lower():
                sector_modifier = adj["return_modifier"]
                break

    # Sensitivity from stressed composite score
    multipliers = scenario["factor_shock_multipliers"]
    stressed_scores = []
    for factor, score in risk_scores.items():
        mult = multipliers.get(factor, 1.0)
        stressed_scores.append(min(10, max(1, score * mult)))
    stressed_composite = np.mean(stressed_scores) if stressed_scores else 5.0
    sensitivity = stressed_composite / 5.0  # 5 = neutral, >1 = more sensitive

    # Expected return
    expected_return = base_mean * sensitivity + sector_modifier

    # Standard deviation scaled by individual volatility
    vol_ratio = individual_volatility / median_volatility if median_volatility > 0 else 1.0
    std_dev = base_std * np.sqrt(max(vol_ratio, 0.5))

    # Weighted impact on portfolio
    weighted_impact = expected_return * weight

    # Channel attribution
    channels = scenario.get("transmission_channels", [])
    channel_contributions = []
    total_channel_weight = 0
    for ch in channels:
        # Find most relevant factor for this channel
        contribution = ch["weight"] * abs(expected_return)
        channel_contributions.append({
            "channel": ch["channel"],
            "contribution": round(contribution, 4),
            "historical_analogue": ch.get("historical_analogue", ""),
            "description": ch.get("description", ""),
        })
        total_channel_weight += contribution

    # Normalize contributions
    if total_channel_weight > 0:
        for cc in channel_contributions:
            cc["contribution_pct"] = round(cc["contribution"] / total_channel_weight * 100, 1)

    # Primary channel = largest weight
    primary_channel = channels[0]["channel"] if channels else "General Market"

    return {
        "ticker": ticker,
        "weight": weight,
        "industry": industry,
        "expected_return": round(expected_return, 4),
        "std_dev": round(std_dev, 4),
        "weighted_impact": round(weighted_impact, 4),
        "sensitivity": round(sensitivity, 2),
        "sector_modifier": round(sector_modifier, 4),
        "primary_channel": primary_channel,
        "channel_contributions": channel_contributions,
    }


def run_monte_carlo(
    stock_impacts: list[dict],
    correlation_matrix: dict,
    scenario: dict,
    time_horizon: str,
    n_simulations: int = 10000,
) -> dict:
    """
    Vectorized Monte Carlo simulation of portfolio returns under stress scenario.

    Returns:
        {
            percentiles: {p5, p25, p50, p75, p95},
            prob_loss_gt_10pct, prob_loss_gt_20pct, prob_positive,
            simulation_stats: {mean, std, min, max}
        }
    """
    n_stocks = len(stock_impacts)
    if n_stocks == 0:
        return _empty_mc_result()

    tickers = [s["ticker"] for s in stock_impacts]
    means = np.array([s["expected_return"] for s in stock_impacts])
    stds = np.array([s["std_dev"] for s in stock_impacts])
    weights = np.array([s["weight"] for s in stock_impacts])

    # Build correlation matrix
    corr = np.eye(n_stocks)
    for i, t1 in enumerate(tickers):
        for j, t2 in enumerate(tickers):
            if i != j:
                # Get correlation from existing matrix
                val = 0.5  # default
                if correlation_matrix:
                    t1_corr = correlation_matrix.get(t1, {})
                    val = t1_corr.get(t2, 0.5)
                corr[i, j] = val

    # Apply crisis correlation boost
    boost = scenario.get("crisis_correlation_boost", 0.2)
    stressed_corr = corr.copy()
    for i in range(n_stocks):
        for j in range(n_stocks):
            if i != j:
                stressed_corr[i, j] = min(1.0, corr[i, j] + boost)

    # Build covariance matrix
    cov = np.outer(stds, stds) * stressed_corr

    # Ensure positive semi-definite via eigenvalue clipping
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    eigenvalues = np.maximum(eigenvalues, 1e-8)
    cov = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    # Symmetrize
    cov = (cov + cov.T) / 2

    # Run simulation — fully vectorized
    np.random.seed(42)  # Reproducible
    simulated_returns = np.random.multivariate_normal(means, cov, size=n_simulations)
    # Shape: (n_simulations, n_stocks)

    # Portfolio returns
    portfolio_returns = simulated_returns @ weights

    # Extract statistics
    percentiles = {
        "p5": round(float(np.percentile(portfolio_returns, 5)), 4),
        "p25": round(float(np.percentile(portfolio_returns, 25)), 4),
        "p50": round(float(np.percentile(portfolio_returns, 50)), 4),
        "p75": round(float(np.percentile(portfolio_returns, 75)), 4),
        "p95": round(float(np.percentile(portfolio_returns, 95)), 4),
    }

    prob_loss_gt_10 = round(float(np.mean(portfolio_returns < -0.10)), 4)
    prob_loss_gt_20 = round(float(np.mean(portfolio_returns < -0.20)), 4)
    prob_positive = round(float(np.mean(portfolio_returns > 0)), 4)

    return {
        "percentiles": percentiles,
        "prob_loss_gt_10pct": prob_loss_gt_10,
        "prob_loss_gt_20pct": prob_loss_gt_20,
        "prob_positive": prob_positive,
        "simulation_stats": {
            "mean": round(float(np.mean(portfolio_returns)), 4),
            "std": round(float(np.std(portfolio_returns)), 4),
            "min": round(float(np.min(portfolio_returns)), 4),
            "max": round(float(np.max(portfolio_returns)), 4),
        },
    }


def _empty_mc_result() -> dict:
    return {
        "percentiles": {"p5": 0, "p25": 0, "p50": 0, "p75": 0, "p95": 0},
        "prob_loss_gt_10pct": 0,
        "prob_loss_gt_20pct": 0,
        "prob_positive": 0,
        "simulation_stats": {"mean": 0, "std": 0, "min": 0, "max": 0},
    }


def compute_scenario_portfolio_summary(
    stock_impacts: list[dict],
    monte_carlo_results: dict,
    scenario: dict,
    time_horizon: str,
    portfolio_value: float = None,
) -> dict:
    """
    Aggregate stock-level impacts into portfolio summary.

    Returns full summary dict for the frontend.
    """
    # Sort stocks by expected return (worst first)
    sorted_stocks = sorted(stock_impacts, key=lambda s: s["expected_return"])

    # Portfolio expected return
    portfolio_expected = sum(s["weighted_impact"] for s in stock_impacts)

    # Transmission channel breakdown (aggregate across stocks)
    channel_map = {}
    for s in stock_impacts:
        for cc in s.get("channel_contributions", []):
            name = cc["channel"]
            if name not in channel_map:
                channel_map[name] = {
                    "channel": name,
                    "total_contribution": 0,
                    "historical_analogue": cc.get("historical_analogue", ""),
                    "description": cc.get("description", ""),
                }
            channel_map[name]["total_contribution"] += cc["contribution"] * s["weight"]
    channels_sorted = sorted(channel_map.values(), key=lambda c: c["total_contribution"], reverse=True)

    # Dollar estimates
    dollar_estimates = None
    if portfolio_value and portfolio_value > 0:
        mc = monte_carlo_results
        dollar_estimates = {
            "expected_loss": round(portfolio_expected * portfolio_value, 2),
            "worst_case_p5": round(mc["percentiles"]["p5"] * portfolio_value, 2),
            "best_case_p95": round(mc["percentiles"]["p95"] * portfolio_value, 2),
            "median": round(mc["percentiles"]["p50"] * portfolio_value, 2),
        }

    # Time horizon labels
    horizon_labels = {
        "1_week": "1 Week",
        "3_month": "3 Months",
        "1_year": "1 Year",
    }

    return {
        "scenario_id": None,  # Filled by caller
        "scenario_name": scenario["name"],
        "scenario_emoji": scenario["emoji"],
        "scenario_category": scenario["category"],
        "scenario_confidence": scenario["confidence"],
        "time_horizon": time_horizon,
        "time_horizon_label": horizon_labels.get(time_horizon, time_horizon),
        "portfolio_expected_return": round(portfolio_expected, 4),
        "stock_impacts": sorted_stocks,
        "monte_carlo": monte_carlo_results,
        "transmission_channels": channels_sorted[:6],
        "dollar_estimates": dollar_estimates,
    }


def get_protection_recommendations(
    scenario: dict,
    stock_impacts: list[dict],
    industry_map: dict = None,
) -> list[dict]:
    """
    Template-based hedge recommendations based on scenario category.

    Returns top 3-4 recommendations with rationale and instruments.
    """
    category = scenario.get("category", "MACRO")
    recs = []

    # Category-specific recommendations
    if category == "GEOPOLITICAL":
        recs.append({
            "recommendation": "Add gold/precious metals exposure",
            "rationale": "Gold historically rallies 10-20% during geopolitical crises as a safe haven asset.",
            "instruments": ["GLD (SPDR Gold Trust)", "IAU (iShares Gold Trust)", "Physical gold"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Buy VIX call options or VIX ETFs",
            "rationale": "Volatility spikes sharply during geopolitical events. VIX typically doubles in crisis scenarios.",
            "instruments": ["VIX calls", "UVXY (ProShares Ultra VIX)", "VIXY"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Add put protection on most exposed holdings",
            "rationale": "Put spreads on your highest-sensitivity holdings limit downside at lower cost than selling.",
            "instruments": ["Put spreads on top-3 exposed tickers", "Portfolio put on SPY"],
            "effectiveness": "MEDIUM",
        })
        recs.append({
            "recommendation": "Increase allocation to defense sector",
            "rationale": "Defense contractors typically outperform during military escalation scenarios.",
            "instruments": ["ITA (iShares US Aerospace & Defense)", "LMT", "RTX", "NOC"],
            "effectiveness": "MEDIUM",
        })

    elif category == "MACRO":
        scenario_name = scenario.get("name", "")
        if "rate" in scenario_name.lower():
            recs.append({
                "recommendation": "Buy TLT put options or short long-duration bonds",
                "rationale": "Long-duration Treasuries lose 15-20% per 100bp rate increase. Puts profit from this move.",
                "instruments": ["TLT puts", "TBT (ProShares UltraShort 20+ Year)", "FLOT (floating rate)"],
                "effectiveness": "HIGH",
            })
            recs.append({
                "recommendation": "Rotate toward financial/bank holdings",
                "rationale": "Banks benefit from higher net interest margins when rates rise.",
                "instruments": ["XLF (Financial Select SPDR)", "KBE (SPDR S&P Bank ETF)"],
                "effectiveness": "MEDIUM",
            })
        else:
            recs.append({
                "recommendation": "Increase allocation to quality/low-volatility factor",
                "rationale": "Quality stocks with strong balance sheets outperform in recessions by 5-10% annually.",
                "instruments": ["QUAL (iShares MSCI USA Quality)", "USMV (Min Volatility)", "Treasury bonds"],
                "effectiveness": "HIGH",
            })
            recs.append({
                "recommendation": "Reduce exposure to high-leverage, cyclical holdings",
                "rationale": "High-leverage companies face refinancing risk and earnings decline amplified by debt service.",
                "instruments": ["Trim cyclical positions", "Add consumer staples (XLP)", "Add utilities (XLU)"],
                "effectiveness": "HIGH",
            })
        recs.append({
            "recommendation": "Add put protection on broad market index",
            "rationale": "SPY puts provide portfolio-level downside protection during systemic macro events.",
            "instruments": ["SPY put spreads", "Collar strategy on largest positions"],
            "effectiveness": "MEDIUM",
        })
        recs.append({
            "recommendation": "Increase cash/short-term Treasury allocation",
            "rationale": "Cash provides optionality to buy at lower prices and reduces portfolio drawdown.",
            "instruments": ["SHV (Short Treasury Bond ETF)", "BIL (SPDR 1-3 Month T-Bill)", "Money market"],
            "effectiveness": "MEDIUM",
        })

    elif category == "SECTOR":
        recs.append({
            "recommendation": "Buy sector-specific put options",
            "rationale": "Targeted puts on the affected sector provide direct hedge without broad market exposure loss.",
            "instruments": ["XLK puts (tech sector)", "SMH puts (semiconductors)", "Sector-specific ETF puts"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Rotate toward value and defensive sectors",
            "rationale": "Value stocks outperform growth by 10-20% during sector bubble corrections.",
            "instruments": ["VTV (Vanguard Value ETF)", "XLP (Consumer Staples)", "XLV (Healthcare)"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Reduce concentration in affected sector",
            "rationale": "Portfolio is overweight the sector at risk. Trimming reduces direct exposure.",
            "instruments": ["Reduce largest sector positions", "Reallocate to uncorrelated sectors"],
            "effectiveness": "MEDIUM",
        })

    elif category == "COMMODITY":
        recs.append({
            "recommendation": "Add commodity/energy exposure as a hedge",
            "rationale": "Energy stocks and commodity ETFs benefit directly from commodity price spikes.",
            "instruments": ["USO (US Oil Fund)", "XLE (Energy Select SPDR)", "DBC (Invesco DB Commodity)"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Buy inflation-protected securities",
            "rationale": "Commodity shocks drive inflation. TIPS and real assets protect purchasing power.",
            "instruments": ["TIP (iShares TIPS Bond ETF)", "VTIP (Vanguard Short-Term TIPS)", "Real estate"],
            "effectiveness": "MEDIUM",
        })
        recs.append({
            "recommendation": "Reduce exposure to transportation and consumer discretionary",
            "rationale": "Airlines, trucking, and discretionary retail are most hurt by energy cost spikes.",
            "instruments": ["Trim airline/transport positions", "Reduce retail exposure"],
            "effectiveness": "MEDIUM",
        })

    elif category == "REGULATORY":
        recs.append({
            "recommendation": "Diversify across sectors to reduce regulatory concentration",
            "rationale": "Regulatory actions are sector-specific. Broader diversification limits single-sector impact.",
            "instruments": ["VTI (Total Market)", "Reduce tech overweight", "Add industrials/healthcare"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Rotate toward smaller-cap and value stocks",
            "rationale": "Antitrust actions target mega-caps. Small/mid-cap and value stocks may benefit from reduced competition.",
            "instruments": ["IWM (Russell 2000)", "VBR (Vanguard Small-Cap Value)", "AVUV"],
            "effectiveness": "MEDIUM",
        })
        recs.append({
            "recommendation": "Add put protection on most exposed mega-cap positions",
            "rationale": "Targeted puts on holdings most exposed to regulatory risk limit worst-case losses.",
            "instruments": ["Put spreads on largest tech holdings", "Collar strategies"],
            "effectiveness": "MEDIUM",
        })

    elif category == "CURRENCY":
        recs.append({
            "recommendation": "Increase allocation to international/non-USD assets",
            "rationale": "International stocks gain in USD terms when the dollar weakens. Non-USD bonds provide further hedge.",
            "instruments": ["VXUS (International ETF)", "EFA (EAFE)", "BNDX (International Bond)"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Add gold and commodity exposure",
            "rationale": "Dollar-denominated commodities and gold rally when the dollar weakens.",
            "instruments": ["GLD (Gold)", "DBC (Commodities)", "SLV (Silver)"],
            "effectiveness": "HIGH",
        })
        recs.append({
            "recommendation": "Favor companies with high international revenue",
            "rationale": "Companies earning abroad benefit from translation effects when reporting in weaker USD.",
            "instruments": ["Overweight high-international-revenue holdings", "Multinational large-caps"],
            "effectiveness": "MEDIUM",
        })

    return recs[:4]

"""
10-Factor risk scoring engine.
Loads industry→score mappings from research/risk_factor_scores.json,
then weights by portfolio allocation.
"""

import os
import json
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR = os.path.join(BASE_DIR, "research")

RISK_FACTORS = [
    "interest_rate_risk",
    "china_revenue_risk",
    "geopolitical_country_risk",
    "currency_risk",
    "regulatory_policy_risk",
    "leverage_credit_risk",
    "earnings_cyclicality",
    "sector_concentration",
    "supply_chain_concentration",
    "esg_energy_transition_risk",
]

RISK_FACTOR_LABELS = {
    "interest_rate_risk": "Interest Rate Risk",
    "china_revenue_risk": "China Revenue Risk",
    "geopolitical_country_risk": "Geopolitical/Country Risk",
    "currency_risk": "Currency Risk",
    "regulatory_policy_risk": "Regulatory/Policy Risk",
    "leverage_credit_risk": "Leverage/Credit Risk",
    "earnings_cyclicality": "Earnings Cyclicality",
    "sector_concentration": "Sector Concentration",
    "supply_chain_concentration": "Supply Chain Concentration",
    "esg_energy_transition_risk": "ESG/Energy Transition Risk",
}

# S&P 500 benchmark scores (market-average exposure)
SP500_BENCHMARK = {
    "interest_rate_risk": 5,
    "china_revenue_risk": 4,
    "geopolitical_country_risk": 4,
    "currency_risk": 5,
    "regulatory_policy_risk": 4,
    "leverage_credit_risk": 4,
    "earnings_cyclicality": 5,
    "sector_concentration": 3,
    "supply_chain_concentration": 4,
    "esg_energy_transition_risk": 4,
}


def _load_risk_scores() -> dict:
    """Load industry→risk score mappings from research JSON.
    Returns dict of {industry_name: {factor: score, ...}}.
    """
    path = os.path.join(RESEARCH_DIR, "risk_factor_scores.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        raw = json.load(f)

    # Handle nested structure: raw["industries"][industry_name]["risk_scores"]
    industries = raw.get("industries", raw)
    result = {}
    if isinstance(industries, dict):
        for name, data in industries.items():
            if isinstance(data, dict) and "risk_scores" in data:
                scores = data["risk_scores"]
                # Normalize factor key names (handle _risk suffix variants)
                result[name] = _normalize_factor_keys(scores)
            elif isinstance(data, dict):
                result[name] = _normalize_factor_keys(data)
    return result


# Map variant key names to canonical factor names
_FACTOR_ALIASES = {
    "sector_concentration_risk": "sector_concentration",
    "supply_chain_concentration_risk": "supply_chain_concentration",
    "esg_energy_transition": "esg_energy_transition_risk",
}


def _normalize_factor_keys(scores: dict) -> dict:
    """Normalize factor key variants to canonical names."""
    result = {}
    for k, v in scores.items():
        canonical = _FACTOR_ALIASES.get(k, k)
        if canonical in RISK_FACTORS:
            result[canonical] = int(v)
    return result


def _get_industry_scores(industry: str, risk_data: dict) -> dict[str, int]:
    """Get risk scores for a specific Damodaran industry."""
    if industry in risk_data:
        scores = risk_data[industry]
        if isinstance(scores, dict):
            return {f: int(scores.get(f, 5)) for f in RISK_FACTORS}

    # Case-insensitive fallback
    industry_lower = industry.lower()
    for key, scores in risk_data.items():
        if key.lower() == industry_lower:
            if isinstance(scores, dict):
                return {f: int(scores.get(f, 5)) for f in RISK_FACTORS}

    # Fuzzy fallback: strip trailing 's', check substring
    industry_stem = industry_lower.rstrip("s")
    best_match = None
    best_score = 0
    for key, scores in risk_data.items():
        key_lower = key.lower()
        key_stem = key_lower.rstrip("s")
        # Exact stem match
        if key_stem == industry_stem:
            if isinstance(scores, dict):
                return {f: int(scores.get(f, 5)) for f in RISK_FACTORS}
        # Substring containment
        if industry_stem in key_lower or key_stem in industry_lower:
            overlap = len(set(industry_lower.split()) & set(key_lower.split()))
            if overlap > best_score:
                best_score = overlap
                best_match = scores

    if best_match and isinstance(best_match, dict) and best_score >= 1:
        return {f: int(best_match.get(f, 5)) for f in RISK_FACTORS}

    # Fallback: return moderate scores
    return {f: 5 for f in RISK_FACTORS}


def score_portfolio_risk_factors(
    tickers: list[str],
    weights: dict[str, float],
    industry_map: dict[str, str],
    damodaran_data: dict = None,
) -> dict:
    """Score portfolio across 10 risk factors.

    Returns:
        {
            "per_holding": {ticker: {factor: score, ...}, ...},
            "portfolio_weighted": {factor: weighted_score, ...},
            "benchmark": {factor: sp500_score, ...},
            "overall_score": float,
            "risk_grade": str,  # A-F
        }
    """
    risk_data = _load_risk_scores()

    per_holding = {}
    for ticker in tickers:
        industry = industry_map.get(ticker, "Diversified")
        scores = _get_industry_scores(industry, risk_data)
        per_holding[ticker] = scores

    # Portfolio-weighted scores
    portfolio_weighted = {}
    for factor in RISK_FACTORS:
        weighted_score = sum(
            weights.get(t, 0) * per_holding[t][factor]
            for t in tickers
        )
        portfolio_weighted[factor] = round(weighted_score, 2)

    # Overall score = average of weighted factor scores
    overall = np.mean(list(portfolio_weighted.values()))

    # Risk grade
    grade = _score_to_grade(overall)

    return {
        "per_holding": per_holding,
        "portfolio_weighted": portfolio_weighted,
        "benchmark": SP500_BENCHMARK,
        "overall_score": round(float(overall), 2),
        "risk_grade": grade,
    }


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score <= 3.0:
        return "A"  # Low risk
    elif score <= 4.5:
        return "B"
    elif score <= 5.5:
        return "C"
    elif score <= 7.0:
        return "D"
    else:
        return "F"  # Very high risk


def detect_risk_overlaps(
    risk_scores: dict,
    weights: dict[str, float],
    threshold: float = 6.0,
) -> list[dict]:
    """Detect risk themes where multiple holdings score above threshold.

    Returns list of overlap dicts:
        {
            "factor": str,
            "factor_label": str,
            "tickers": [str, ...],
            "combined_weight": float,
            "avg_score": float,
            "severity": str,  # LOW, MEDIUM, HIGH, CRITICAL
        }
    """
    per_holding = risk_scores["per_holding"]
    overlaps = []

    for factor in RISK_FACTORS:
        # Find tickers scoring above threshold for this factor
        high_scorers = []
        for ticker, scores in per_holding.items():
            if scores[factor] >= threshold:
                high_scorers.append(ticker)

        if len(high_scorers) < 2:
            continue

        combined_weight = sum(weights.get(t, 0) for t in high_scorers)
        avg_score = np.mean([per_holding[t][factor] for t in high_scorers])

        # Severity based on combined weight and average score
        if combined_weight >= 0.6 and avg_score >= 8:
            severity = "CRITICAL"
        elif combined_weight >= 0.4 or avg_score >= 8:
            severity = "HIGH"
        elif combined_weight >= 0.25:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        overlaps.append({
            "factor": factor,
            "factor_label": RISK_FACTOR_LABELS[factor],
            "tickers": high_scorers,
            "combined_weight": round(combined_weight, 4),
            "avg_score": round(float(avg_score), 1),
            "severity": severity,
        })

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    overlaps.sort(key=lambda x: (severity_order.get(x["severity"], 4), -x["combined_weight"]))

    return overlaps

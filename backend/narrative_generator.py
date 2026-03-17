"""
Template-based risk narrative generator. No Claude API — pure f-string templates.
"""


def generate_narrative(analysis: dict, data: dict) -> str:
    """Generate 3-4 paragraph risk narrative from analysis results."""
    risk = analysis.get("risk_factors", {})
    portfolio = analysis.get("portfolio_metrics", {})
    overlaps = analysis.get("overlaps", [])

    grade = risk.get("risk_grade", "C")
    overall_score = risk.get("overall_score", 5.0)
    hhi = portfolio.get("hhi", 0.0)
    n_eff = portfolio.get("n_eff", 1.0)
    dr = portfolio.get("diversification_ratio", 1.0)
    n_holdings = len(analysis.get("tickers", []))

    # Executive summary
    exec_summary = _exec_summary(grade, overall_score, n_holdings, hhi)

    # Key risk drivers
    risk_drivers = _risk_drivers(risk, overlaps)

    # Diversification assessment
    div_assessment = _diversification_assessment(hhi, n_eff, dr, n_holdings)

    # Recommendations
    recommendations = _recommendations(grade, overlaps, hhi, n_eff)

    return f"{exec_summary}\n\n{risk_drivers}\n\n{div_assessment}\n\n{recommendations}"


def _exec_summary(grade: str, score: float, n_holdings: int, hhi: float) -> str:
    grade_desc = {
        "A": "low overall risk",
        "B": "moderate-low risk",
        "C": "moderate risk",
        "D": "elevated risk",
        "F": "high risk",
    }
    desc = grade_desc.get(grade, "moderate risk")

    if grade in ("A", "B"):
        tone = "The portfolio exhibits a conservative risk profile"
    elif grade == "C":
        tone = "The portfolio carries a balanced risk profile with some areas of concern"
    else:
        tone = "The portfolio exhibits elevated risk that warrants attention"

    return (
        f"**Executive Summary:** This {n_holdings}-holding portfolio receives an overall "
        f"risk grade of {grade} ({desc}), with a composite score of {score:.1f}/10. "
        f"{tone}. The Herfindahl-Hirschman Index of {hhi:.4f} "
        f"{'indicates significant concentration' if hhi > 0.25 else 'suggests reasonable weight distribution'}."
    )


def _risk_drivers(risk: dict, overlaps: list) -> str:
    weighted = risk.get("portfolio_weighted", {})
    benchmark = risk.get("benchmark", {})

    if not weighted:
        return "**Key Risk Drivers:** Insufficient data to assess individual risk factors."

    # Top 3 risk factors
    sorted_factors = sorted(weighted.items(), key=lambda x: x[1], reverse=True)
    top3 = sorted_factors[:3]

    from backend.risk_factors import RISK_FACTOR_LABELS
    factor_strs = []
    for factor, score in top3:
        label = RISK_FACTOR_LABELS.get(factor, factor)
        bench = benchmark.get(factor, 5)
        vs_bench = "above" if score > bench else "below" if score < bench else "at"
        factor_strs.append(f"{label} ({score:.1f}/10, {vs_bench} S&P 500 benchmark of {bench})")

    factors_text = ", ".join(factor_strs[:2])
    if len(factor_strs) > 2:
        factors_text += f", and {factor_strs[2]}"

    overlap_text = ""
    critical = [o for o in overlaps if o["severity"] == "CRITICAL"]
    high = [o for o in overlaps if o["severity"] == "HIGH"]
    if critical:
        names = [o["factor_label"] for o in critical]
        overlap_text = (
            f" Critical risk overlaps detected in {', '.join(names)}, "
            f"where multiple holdings share concentrated exposure."
        )
    elif high:
        names = [o["factor_label"] for o in high]
        overlap_text = f" Notable risk overlaps exist in {', '.join(names)}."

    return (
        f"**Key Risk Drivers:** The top risk factors are {factors_text}.{overlap_text}"
    )


def _diversification_assessment(hhi: float, n_eff: float, dr: float, n: int) -> str:
    if n <= 1:
        return (
            "**Diversification Assessment:** With a single holding, the portfolio has "
            "no diversification benefit. All risk is concentrated in one position."
        )

    if n_eff >= 4 and dr >= 1.3:
        quality = "strong"
        detail = (
            f"The effective number of bets (N_eff = {n_eff:.1f}) indicates meaningful "
            f"independent risk sources, and the diversification ratio of {dr:.2f} "
            f"confirms that combining these holdings reduces portfolio risk well below "
            f"the weighted average of individual risks."
        )
    elif n_eff >= 2:
        quality = "moderate"
        detail = (
            f"While N_eff of {n_eff:.1f} shows some independent risk drivers, "
            f"the portfolio could benefit from broader exposure. "
            f"The diversification ratio of {dr:.2f} indicates "
            f"{'meaningful' if dr >= 1.15 else 'limited'} risk reduction from diversification."
        )
    else:
        quality = "weak"
        detail = (
            f"N_eff of {n_eff:.1f} against {n} holdings reveals that despite holding "
            f"multiple names, the portfolio behaves like {n_eff:.0f}-{min(n_eff+1, n):.0f} "
            f"independent bets. Holdings are highly correlated, reducing the "
            f"diversification benefit."
        )

    return f"**Diversification Assessment:** Diversification quality is {quality}. {detail}"


def _recommendations(grade: str, overlaps: list, hhi: float, n_eff: float) -> str:
    recs = []

    if hhi > 0.25:
        recs.append(
            "Consider rebalancing to reduce position concentration — "
            "no single holding should exceed 25% of portfolio weight"
        )

    critical = [o for o in overlaps if o["severity"] in ("CRITICAL", "HIGH")]
    if critical:
        factors = list(set(o["factor_label"] for o in critical))
        recs.append(
            f"Address concentrated exposure to {', '.join(factors)} "
            f"by adding holdings with low scores in these risk dimensions"
        )

    if n_eff < 3:
        recs.append(
            "Improve effective diversification by adding holdings from "
            "uncorrelated sectors or asset classes (e.g., fixed income, commodities, "
            "international equities)"
        )

    if grade in ("D", "F"):
        recs.append(
            "The overall risk grade suggests the portfolio may underperform "
            "in adverse scenarios — review whether the risk level aligns with "
            "investment objectives and time horizon"
        )

    if not recs:
        return (
            "**Recommendations:** The portfolio's risk profile appears well-managed. "
            "Continue monitoring for changes in sector dynamics and macroeconomic conditions."
        )

    bullets = "\n".join(f"  - {r}" for r in recs)
    return f"**Recommendations:**\n{bullets}"


def generate_scenario_narrative(summary: dict, scenario: dict, time_horizon: str) -> str:
    """Generate stress test narrative from scenario results. Template-based f-strings."""
    horizon_labels = {"1_week": "1 week", "3_month": "3 months", "1_year": "1 year"}
    horizon_label = horizon_labels.get(time_horizon, time_horizon)
    name = scenario["name"]
    confidence = scenario["confidence"]
    category = scenario["category"]
    expected = summary.get("portfolio_expected_return", 0)
    mc = summary.get("monte_carlo", {})
    percentiles = mc.get("percentiles", {})
    prob_loss_10 = mc.get("prob_loss_gt_10pct", 0)
    prob_loss_20 = mc.get("prob_loss_gt_20pct", 0)

    # Impact summary paragraph
    direction = "decline" if expected < 0 else "gain"
    impact_para = (
        f"**Scenario Impact — {name}:** Over a {horizon_label} horizon, "
        f"this {confidence}-confidence {category.lower()} scenario is expected to produce "
        f"a portfolio {direction} of {abs(expected)*100:.1f}%. "
        f"The Monte Carlo simulation (10,000 runs) shows a median outcome of "
        f"{percentiles.get('p50', 0)*100:.1f}%, with a 5th-95th percentile range of "
        f"{percentiles.get('p5', 0)*100:.1f}% to {percentiles.get('p95', 0)*100:.1f}%."
    )

    if prob_loss_10 > 0.05:
        impact_para += f" There is a {prob_loss_10*100:.0f}% probability of losses exceeding 10%."
    if prob_loss_20 > 0.05:
        impact_para += f" The probability of losses exceeding 20% is {prob_loss_20*100:.0f}%."

    # Worst-hit holdings paragraph
    stocks = summary.get("stock_impacts", [])
    worst = [s for s in stocks if s["expected_return"] < 0][:3]
    if worst:
        worst_strs = []
        for s in worst:
            worst_strs.append(
                f"{s['ticker']} ({s['expected_return']*100:.1f}%, primary channel: {s['primary_channel']})"
            )
        holdings_para = (
            f"**Most Affected Holdings:** The worst-hit positions are {', '.join(worst_strs)}."
        )
        # Any positive performers?
        gainers = [s for s in stocks if s["expected_return"] > 0]
        if gainers:
            gainer_strs = [f"{s['ticker']} ({s['expected_return']*100:+.1f}%)" for s in gainers[:2]]
            holdings_para += f" Potential outperformers: {', '.join(gainer_strs)}."
    else:
        holdings_para = "**Most Affected Holdings:** No holdings show significant negative impact."

    # Transmission channels paragraph
    channels = summary.get("transmission_channels", [])[:3]
    if channels:
        ch_strs = []
        for ch in channels:
            analogue = ch.get("historical_analogue", "")
            ch_str = f"{ch['channel']}"
            if analogue:
                ch_str += f" (historical analogue: {analogue})"
            ch_strs.append(ch_str)
        channels_para = (
            f"**Key Transmission Channels:**\n"
            + "\n".join(f"  - {s}" for s in ch_strs)
        )
    else:
        channels_para = "**Key Transmission Channels:** General market risk-off dynamics."

    # Protection suggestions paragraph
    protections = summary.get("protections", [])[:3]
    if protections:
        prot_strs = []
        for p in protections:
            instruments = ", ".join(p.get("instruments", [])[:3])
            prot_strs.append(f"{p['recommendation']} — {p['rationale']} Instruments: {instruments}")
        prot_para = (
            f"**Suggested Hedges:**\n"
            + "\n".join(f"  - {s}" for s in prot_strs)
        )
    else:
        prot_para = "**Suggested Hedges:** Consider broad market put protection and increased cash allocation."

    return f"{impact_para}\n\n{holdings_para}\n\n{channels_para}\n\n{prot_para}"

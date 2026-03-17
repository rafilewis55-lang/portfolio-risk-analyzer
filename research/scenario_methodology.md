# Scenario Stress Test Methodology

## Overview

12 macro/geopolitical/sector scenarios designed to stress-test portfolio risk factor scores and estimate loss distributions via Monte Carlo simulation. Each scenario defines factor shock multipliers, asset class return shocks, sector-specific adjustments, and transmission channels.

## Data Sources & Calibration

### Factor Shock Multipliers
Multipliers represent how much each risk factor score is amplified under the scenario. Calibrated from:
- **Historical drawdown decomposition**: 2000-01 dot-com bust, 2008-09 GFC, 2020 COVID crash, 2022 rate hiking cycle
- **Academic literature**: Ang & Bekaert (2002) regime-switching models, Chow et al. (1999) crisis correlation dynamics
- **Industry stress testing frameworks**: Fed CCAR scenarios, EBA stress tests, BlackRock Aladdin scenario library

### Asset Class Shocks
Base equity return distributions (mean + std dev) for 3 time horizons:
- **1-week**: Calibrated to historical worst-week drawdowns for each scenario type
- **3-month**: Primary horizon. Calibrated to historical crisis peak-to-trough durations
- **1-year**: Full-cycle impact including partial recovery. Based on 12-month post-crisis returns

Sources:
- S&P 500, Nasdaq, MSCI World drawdown data (1970-2025)
- Bloomberg terminal crisis event studies
- Damodaran annual equity risk premium dataset

### Sector Adjustments
Industry-specific return modifiers applied on top of base equity shock:
- Calibrated from sector-level drawdown differentials during historical analogues
- Damodaran industry classification (94 US industries) used for matching
- Energy sector positive adjustments during geopolitical/commodity shocks based on 1973, 1979, 1990, 2022 oil events

### Transmission Channels
Each scenario includes 3-6 channels explaining how the shock propagates:
- Weights sum to 1.0 within each scenario
- Historical analogues with quantified impact cited for each channel
- Channel attribution uses weight × relevant factor score for portfolio-level decomposition

### Crisis Correlation Boost
During crises, asset correlations increase (Longin & Solnik 2001). The boost parameter:
- HIGH confidence scenarios: +0.20 (well-documented crisis dynamics)
- MEDIUM confidence scenarios: +0.25-0.30 (more uncertainty → fatter tails)
- LOW confidence scenarios: +0.30-0.35 (tail scenarios → maximum correlation stress)

### Monte Carlo Simulation
- 10,000 simulations per scenario using multivariate normal with stressed covariance
- Covariance matrix built from stressed correlations and individual stock std devs
- PSD enforcement via eigenvalue clipping (negative eigenvalues → 1e-8)
- Vectorized numpy implementation (no Python loops over simulations)

## Confidence Levels

| Level | Meaning | Historical Precedent | Spread Factor |
|-------|---------|---------------------|---------------|
| HIGH | Multiple historical precedents, well-understood dynamics | 3+ events in last 50 years | 1.0x |
| MEDIUM | Some precedent, but dynamics may differ | 1-2 partial analogues | 1.2x |
| LOW | Unprecedented or extreme tail risk | No close analogue | 1.5x |

## Scenario Categories

| Category | Risk Factors Most Affected | Typical Hedge |
|----------|---------------------------|---------------|
| GEOPOLITICAL | geopolitical_country_risk, supply_chain, china_revenue | Gold, VIX, defense stocks |
| MACRO | interest_rate_risk, leverage_credit, earnings_cyclicality | TLT puts, floating rate, quality factor |
| SECTOR | sector_concentration, earnings_cyclicality | Sector puts, value rotation |
| COMMODITY | esg_energy_transition, earnings_cyclicality | Commodity futures, energy equities |
| REGULATORY | regulatory_policy_risk, sector_concentration | Diversification, value rotation |
| CURRENCY | currency_risk, interest_rate_risk | FX hedges, international diversification |

## Validation Requirements

### Directional Checks (test portfolio: NVDA 40%, AAPL 25%, JPM 20%, XOM 15%)
1. Taiwan invasion: NVDA loss > JPM loss (supply chain concentration = 3.5x)
2. Rate shock: JPM impact less negative than NVDA (banks benefit from NIM expansion)
3. AI bubble burst: NVDA loss > XOM loss (sector concentration = 2.5x)
4. Oil shock: XOM positive return modifier (+0.15)
5. China hard landing: AAPL loss > JPM loss (china_revenue_risk = 3.0x)
6. US severe recession: all four stocks negative

### Math Integrity
- All stressed scores clipped to [1, 10]
- Monte Carlo percentiles monotonically increasing (p5 < p25 < p50 < p75 < p95)
- LOW confidence scenarios have wider p5-p95 spread than HIGH confidence
- Portfolio median ≈ weighted sum of individual expected returns (± 2%)

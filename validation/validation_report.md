# Portfolio Risk Analyzer — Validation Report

**Date:** 2026-03-17
**Server:** http://localhost:8000
**Total Checks:** 47
**PASS:** 47  |  **FAIL:** 0  |  **Pass Rate:** 100.0%

---

## Portfolio A — Concentrated Tech (NVDA 40%, AMD 30%, TSM 20%, ASML 10%)

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Portfolio A: N_eff < 2.0 | n_eff=1.8605056736050378 |
| PASS | Portfolio A: HHI > 0.25 | hhi=0.3000 |
| PASS | Portfolio A: China risk is HIGH (weighted >= 6.0) | portfolio_weighted_china=8.0 | per_holding={'NVDA': 8, 'AMD': 8, 'TSM': 8} |
| PASS | Portfolio A: Supply chain concentration HIGH (>= 6.0) | portfolio_weighted_supply_chain=10.0 |
| PASS | Portfolio A: All risk scores in [1,10] | Checked 40 scores |
| PASS | Portfolio A: Correlation matrix diagonal=1.0 | Checked 4 diagonal entries |
| PASS | Portfolio A: Correlation matrix symmetric | Checked 16 pairs |
| PASS | Portfolio A: Correlation values in [-1,1] | All 16 values checked |
| PASS | Portfolio A: MRC values sum to portfolio_vol | MRC_sum=0.415791, port_vol=0.415791, tol=0.000416 |
| PASS | Portfolio A: Overlap severity levels valid | Checked 6 overlaps |
| PASS | Portfolio A: Risk grade is A-F | grade=D |

## Portfolio B — False Diversification (AAPL/MSFT/GOOGL/META 25% each)

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Portfolio B: N_eff in [1.0, 3.0] | n_eff=2.539542253995625 |
| PASS | Portfolio B: HHI = 0.25 (equal-weight 4 stocks) | hhi=0.250000 |
| PASS | Portfolio B: Has regulatory overlap | severity=HIGH, tickers=['AAPL', 'MSFT', 'GOOGL', 'META'] |
| PASS | Portfolio B / AAPL: china_revenue_risk >= 6 | aapl_china=8 |
| PASS | Portfolio B: All risk scores in [1,10] | Checked 40 scores |
| PASS | Portfolio B: Correlation matrix diagonal=1.0 | Checked 4 diagonal entries |
| PASS | Portfolio B: Correlation matrix symmetric | Checked 16 pairs |
| PASS | Portfolio B: Correlation values in [-1,1] | All 16 values checked |
| PASS | Portfolio B: MRC values sum to portfolio_vol | MRC_sum=0.223199, port_vol=0.223199, tol=0.000223 |
| PASS | Portfolio B: Overlap severity levels valid | Checked 5 overlaps |
| PASS | Portfolio B: Risk grade is A-F | grade=C |

## Portfolio C — Reasonably Diversified (AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD)

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Portfolio C: N_eff > 3.0 | n_eff=5.231541522138491 |
| PASS | Portfolio C: DR > 1.2 | dr=1.8362297216438024 |
| PASS | Portfolio C: Fewer HIGH/CRITICAL overlaps than A or B | Portfolio C has 4 HIGH/CRITICAL overlaps | A=6, B=5 |
| PASS | Portfolio C / JPM: interest_rate_risk score present | jpm_interest_rate_risk=5 |
| PASS | Portfolio C: All risk scores in [1,10] | Checked 70 scores |
| PASS | Portfolio C: Correlation matrix diagonal=1.0 | Checked 7 diagonal entries |
| PASS | Portfolio C: Correlation matrix symmetric | Checked 49 pairs |
| PASS | Portfolio C: Correlation values in [-1,1] | All 49 values checked |
| PASS | Portfolio C: MRC values sum to portfolio_vol | MRC_sum=0.118450, port_vol=0.118450, tol=0.000118 |
| PASS | Portfolio C: Overlap severity levels valid | Checked 4 overlaps |
| PASS | Portfolio C: Risk grade is A-F | grade=C |

## Portfolio D — Single Stock (NVDA 100%)

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Portfolio D: HHI = 1.0 exactly | hhi=1.0 |
| PASS | Portfolio D: N_eff = 1.0 exactly | n_eff=1.0 |
| PASS | Portfolio D: DR = 1.0 exactly | dr=1.0000000000000002 |
| PASS | Portfolio D: All risk scores in [1,10] | Checked 10 scores |
| PASS | Portfolio D: Risk grade is A-F | grade=D |
| PASS | Portfolio D: Correlation matrix is 1x1 = [[1.0]] | corr_dict={'NVDA': {'NVDA': 1.0}} |

## Cross-Portfolio & Specific Factor Checks

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Portfolio B / AAPL: china_revenue_risk >= 6 | aapl_china=8 |
| PASS | JPM interest_rate_risk != NVDA interest_rate_risk | nvda_ir=3, jpm_ir=5 |
| PASS | AAPL: china_revenue_risk >= 6 | china_revenue_risk=8 |

## File Generation (Excel / PDF)

| Result | Check | Detail |
|--------|-------|--------|
| PASS | Excel: HTTP 200 response | status=200 |
| PASS | Excel: Non-empty binary response | size=15223 bytes |
| PASS | Excel: Valid xlsx magic bytes (PK) | first_bytes=504b0304 |
| PASS | PDF: HTTP 200 response | status=200 |
| PASS | PDF: Non-empty binary response | size=8457 bytes |
| PASS | PDF: Valid PDF header (%PDF) | first_bytes=b'%PDF-1.4' |

---

## Summary

- Total checks run: **47**
- Passed: **47**
- Failed: **0**
- Pass rate: **100.0%**

## Raw API Results

### Key Metrics Per Portfolio

| Portfolio | HHI | N_eff | DR | Port_Vol | Risk_Grade | Num_Overlaps |
|-----------|-----|-------|----|----------|------------|--------------|
| A (NVDA/AMD/TSM/ASML) | 0.3000 | 1.861 | 1.174 | 0.4158 | D | 6 |
| B (AAPL/MSFT/GOOGL/META) | 0.2500 | 2.540 | 1.313 | 0.2232 | C | 5 |
| C (AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD) | 0.1450 | 5.232 | 1.836 | 0.1184 | C | 4 |
| D (NVDA) | 1.0000 | 1.000 | 1.000 | 0.4930 | D | 0 |

### Risk Factor Scores Per Portfolio (Portfolio-Weighted)

| Factor | Port A | Port B | Port C | Port D | SP500 Benchmark |
|--------|--------|--------|--------|--------|-----------------|
| interest_rate_risk | 3.0 | 3.25 | 4.3 | 3.0 | 5 |
| china_revenue_risk | 8.0 | 6.25 | 5.25 | 8.0 | 4 |
| geopolitical_country_risk | 7.0 | 4.5 | 5.5 | 7.0 | 4 |
| currency_risk | 7.0 | 6.75 | 5.75 | 7.0 | 5 |
| regulatory_policy_risk | 5.0 | 6.5 | 5.65 | 5.0 | 4 |
| leverage_credit_risk | 1.0 | 1.75 | 2.65 | 1.0 | 4 |
| earnings_cyclicality | 6.0 | 7.75 | 5.4 | 6.0 | 5 |
| sector_concentration | 7.0 | 6.0 | 4.85 | 7.0 | 3 |
| supply_chain_concentration | 10.0 | 5.0 | 4.15 | 10.0 | 4 |
| esg_energy_transition_risk | 5.0 | 3.0 | 4.75 | 5.0 | 4 |

### Overlaps Per Portfolio

#### Portfolio A — NVDA/AMD/TSM/ASML
| Factor | Tickers | Combined Weight | Avg Score | Severity |
|--------|---------|-----------------|-----------|----------|
| China Revenue Risk | NVDA, AMD, TSM, ASML | 1.0 | 8.0 | CRITICAL |
| Supply Chain Concentration | NVDA, AMD, TSM, ASML | 1.0 | 10.0 | CRITICAL |
| Geopolitical/Country Risk | NVDA, AMD, TSM, ASML | 1.0 | 7.0 | HIGH |
| Currency Risk | NVDA, AMD, TSM, ASML | 1.0 | 7.0 | HIGH |
| Earnings Cyclicality | NVDA, AMD, TSM, ASML | 1.0 | 6.0 | HIGH |
| Sector Concentration | NVDA, AMD, TSM, ASML | 1.0 | 7.0 | HIGH |

#### Portfolio B — AAPL/MSFT/GOOGL/META
| Factor | Tickers | Combined Weight | Avg Score | Severity |
|--------|---------|-----------------|-----------|----------|
| Earnings Cyclicality | MSFT, GOOGL, META | 0.75 | 8.7 | CRITICAL |
| Currency Risk | AAPL, MSFT, GOOGL, META | 1.0 | 6.8 | HIGH |
| Regulatory/Policy Risk | AAPL, MSFT, GOOGL, META | 1.0 | 6.5 | HIGH |
| Sector Concentration | AAPL, MSFT, GOOGL, META | 1.0 | 6.0 | HIGH |
| China Revenue Risk | AAPL, GOOGL, META | 0.75 | 6.7 | HIGH |

#### Portfolio C — AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD
| Factor | Tickers | Combined Weight | Avg Score | Severity |
|--------|---------|-----------------|-----------|----------|
| Currency Risk | AAPL, XOM, JNJ, PG | 0.6 | 6.2 | HIGH |
| Regulatory/Policy Risk | AAPL, XOM, JNJ, BRK-B | 0.55 | 6.8 | HIGH |
| Geopolitical/Country Risk | AAPL, XOM, GLD | 0.45 | 7.0 | HIGH |
| Earnings Cyclicality | XOM, BRK-B, GLD | 0.4 | 7.3 | HIGH |

#### Portfolio D — NVDA
No overlaps detected.

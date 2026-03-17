# Portfolio Risk Exposure Analyzer — Methodology

**Version:** 1.0
**Last Updated:** 2026-03-17
**Data Sources:** Damodaran (January 2026), Country ERP spreadsheet (ctryprem.xlsx)

---

## 1. Risk Factor Definitions and Scoring Rubrics

All risk factors are scored on a **1–10 integer scale** where **1 = lowest risk** and **10 = highest risk**. Scores are assigned per Damodaran industry. Portfolio-level scores are computed as allocation-weighted averages across constituent industries.

---

### Factor 1: Interest Rate Risk

**Definition:** Sensitivity of the sector's equity valuation to changes in the 10-year US Treasury yield. Industries with long-duration cash flows (utilities, REITs, life insurance) see larger valuation declines when rates rise. High-growth sectors with near-term cash flow reinvestment also carry duration risk but for different reasons (discount rate sensitivity on distant terminal values).

**Scoring rubric:**

| Score | Sector Characteristics |
|-------|----------------------|
| 1–2   | Short-duration, non-rate-sensitive (short-cycle tech, commodities without leverage) |
| 3–4   | Moderate duration, modest rate sensitivity (software, pharma, food processing) |
| 5–6   | Moderate leverage or moderate duration (industrials, chemicals, hotels) |
| 7–8   | High leverage or long duration (cable TV, power, building materials, insurance) |
| 9–10  | Extreme rate sensitivity: REITs, banks (net interest margin), life insurers, utilities |

**Key examples:**
- Utility (General): 8 — regulated utilities are effectively long-duration bonds; rising rates increase their cost of capital materially
- R.E.I.T.: 9 — debt-financed, low cap rates, highly sensitive to treasury yield spreads
- Insurance (Life): 9 — ALM duration mismatch; portfolio marks down with rising rates
- Software (System & Application): 3 — cash-generative, low leverage, near-term cash flows

---

### Factor 2: China Revenue Risk

**Definition:** Estimated percentage of sector revenues derived from China, including direct sales, manufacturing, and supply chain exposure. Captures both tariff risk, regulatory scrutiny (export controls), and potential demand disruption.

**Scoring rubric:**

| Score | Estimated China Revenue Exposure |
|-------|----------------------------------|
| 1–2   | <5% (domestic services, regional banks, domestic utilities) |
| 3–4   | 5–15% (diversified consumer, food, healthcare services) |
| 5–6   | 15–30% (industrial machinery, autos, chemicals, pharma) |
| 7–8   | 30–50% (semiconductors, electronics, apparel, telecom equipment) |
| 9–10  | >50% (pure-play China-exposed or TSMC/chip manufacturing dependent) |

**Key examples:**
- Semiconductor: 8 — >35% of global chip sales to Chinese customers; export controls risk
- Telecom. Equipment: 8 — high China manufacturing and sales exposure
- Apparel: 7 — manufacturing concentrated in Asia including China
- Banks (Regional): 2 — predominantly domestic US business

---

### Factor 3: Geopolitical/Country Risk

**Definition:** Exposure to emerging market and frontier market revenues, operations in politically unstable regions, reliance on commodity extraction from high-risk geographies, or sectors directly tied to defense/government spending in volatile regions.

**Scoring rubric:**

| Score | Geopolitical Exposure |
|-------|----------------------|
| 1–2   | Purely domestic, low EM exposure (domestic utilities, regional banks) |
| 3–4   | Limited EM presence, diversified geographically (food, consumer staples) |
| 5–6   | Material EM exposure or commodity-linked (mining, engineering, diversified industrials) |
| 7–8   | Significant EM operations, geopolitical dependency (oil/gas, defense, metals) |
| 9–10  | Primarily EM/frontier operations, high conflict-zone exposure |

---

### Factor 4: Currency Risk

**Definition:** Percentage of revenues and costs denominated in foreign currencies, creating translation and transaction risk. Global multinationals with >40% non-USD revenues carry the highest exposure. Commodity sectors have indirect exposure through USD-priced commodities.

**Scoring rubric:**

| Score | Foreign Revenue Exposure |
|-------|--------------------------|
| 1–3   | <10% foreign revenue (domestic utilities, regional banks, domestic services) |
| 4–5   | 10–30% foreign revenue (diversified consumer, building materials) |
| 6–7   | 30–55% foreign revenue (tech, pharma, industrials) |
| 8–9   | >55% foreign revenue (global software, luxury goods, diversified multinationals) |
| 10    | Nearly entirely foreign denominated |

---

### Factor 5: Regulatory/Policy Risk

**Definition:** Sensitivity to government regulation, policy changes, antitrust action, price controls, or licensing requirements. Highly regulated industries face binary risk events; less regulated industries face gradual policy drift.

**Scoring rubric:**

| Score | Regulatory Exposure |
|-------|---------------------|
| 1–2   | Minimal regulation, competitive markets (pure-play software, internet services) |
| 3–4   | Standard commercial regulation (manufacturing, retail, food processing) |
| 5–6   | Moderate regulation (energy production, environmental services, chemicals) |
| 7–8   | Heavy regulation or price controls (healthcare, telecom, financial services) |
| 9–10  | Extreme regulatory exposure, rate setting, or government as primary customer (banking, utilities, pharma reimbursement) |

---

### Factor 6: Leverage/Credit Risk

**Definition:** Derived **quantitatively** from Damodaran D/E ratios. Higher financial leverage amplifies downside in economic contractions and increases default risk. Financial companies (banks, insurers) carry structural leverage that is regulated and partially collateralized.

**Formula — D/E to Score mapping:**

| D/E Ratio (%) | Score |
|---------------|-------|
| ≤ 5%          | 1     |
| ≤ 15%         | 2     |
| ≤ 25%         | 3     |
| ≤ 35%         | 4     |
| ≤ 50%         | 5     |
| ≤ 75%         | 6     |
| ≤ 100%        | 7     |
| ≤ 150%        | 8     |
| ≤ 250%        | 9     |
| > 250%        | 10    |

**Source:** `damodaran_betas.json` → `de_ratio_pct` field.

**Key examples:**
- Semiconductor: D/E = 2.59% → score 1 (virtually debt-free)
- Rubber & Tires: D/E = 358.47% → score 10 (extreme leverage)
- Financial Svcs. (Non-bank & Insurance): D/E = 272.13% → score 10
- Utility (General): D/E = 81.48% → score 7

---

### Factor 7: Earnings Cyclicality

**Definition:** Derived **quantitatively** from Damodaran standard deviation of operating income. High variability indicates pro-cyclical earnings, amplifying portfolio drawdowns in recessions. Commodity and transportation sectors show the highest cyclicality.

**Formula — Std Dev of Operating Income to Score mapping:**

| Std Dev Op Income (%) | Score |
|----------------------|-------|
| ≤ 10%                | 1     |
| ≤ 15%                | 2     |
| ≤ 20%                | 3     |
| ≤ 28%                | 4     |
| ≤ 38%                | 5     |
| ≤ 52%                | 6     |
| ≤ 70%                | 7     |
| ≤ 100%               | 8     |
| ≤ 185%               | 9     |
| > 185%               | 10    |

When `std_dev_op_income_pct` is `null` (financials with non-standard income accounting), a neutral score of **5** is assigned.

**Source:** `damodaran_betas.json` → `std_dev_op_income_pct` field.

**Key examples:**
- Coal & Related Energy: 242.50% std dev → score 10
- Air Transport: 210.43% → score 10
- Software (Internet): 234.02% → score 10
- Food Processing: 9.38% → score 1
- Telecom. Services: 9.46% → score 1
- Packaging & Container: 13.14% → score 2

---

### Factor 8: Sector Concentration Risk

**Definition:** Tendency of the sector to be dominated by a small number of firms, creating idiosyncratic risk in index-weighted portfolios. Measured by typical GICS concentration, market cap concentration, and HHI tendencies within the Damodaran industry bucket.

**Scoring rubric:**

| Score | Concentration Characteristics |
|-------|-------------------------------|
| 1–2   | Many small firms, fragmented markets |
| 3–4   | Moderately fragmented, no dominant player >30% share |
| 5–6   | Oligopolistic tendencies, 3–5 dominant players |
| 7–8   | Highly concentrated, 1–3 firms dominate (semis, mega-cap tech, banks) |
| 9–10  | Near-monopoly or duopoly market structure |

---

### Factor 9: Supply Chain Concentration Risk

**Definition:** Dependency on concentrated suppliers, particularly Taiwan Semiconductor Manufacturing Company (TSMC) and the broader semiconductor supply chain including advanced packaging (OSAT), wafer fabrication, and rare earth materials. Industries with deep chip content score highest.

**Scoring rubric:**

| Score | Supply Chain Characteristics |
|-------|------------------------------|
| 1–2   | No meaningful semiconductor or concentrated input dependency (software, services, domestic food) |
| 3–4   | Modest chip content, diversified supply chain (industrial machinery, consumer goods) |
| 5–6   | Meaningful chip content, partially concentrated supply (autos, medical devices, telecom) |
| 7–8   | High chip content, significant TSMC exposure (networking equipment, data storage, PCs) |
| 9–10  | Extreme concentration: direct TSMC/advanced fab customers (Semiconductors, Semiconductor Equip score 10) |

---

### Factor 10: ESG / Energy Transition Risk

**Definition:** Exposure to fossil fuel assets, carbon-intensive operations, regulatory carbon pricing, stranded asset risk, and difficulty transitioning to lower-carbon business models. High scores indicate sectors that face existential decarbonization pressure.

**Scoring rubric:**

| Score | ESG/Carbon Characteristics |
|-------|---------------------------|
| 1–2   | Net-zero aligned or inherently clean (software, healthcare, water utilities, biotech) |
| 3–4   | Moderate footprint, manageable transition (diversified consumer, light manufacturing) |
| 5–6   | Carbon-intensive but transitioning (autos, utilities with renewable mix, chemicals) |
| 7–8   | High carbon intensity, transition costly (steel, mining, heavy chemicals, shipping) |
| 9–10  | Fossil fuel core business model, high stranded asset risk (coal=10, oil/gas=8-9) |

---

## 2. Portfolio Math Formulas

### 2.1 Herfindahl-Hirschman Index (HHI) — Concentration

The HHI measures portfolio concentration using position weights:

```
HHI = Σᵢ wᵢ²
```

Where `wᵢ` is the weight of asset `i` in the portfolio (as a decimal, e.g. 0.05 for 5%).

**Range:** 1/N (perfectly equal weights) to 1.0 (single position). Multiply by 10,000 for the traditional HHI scale.

**Interpretation:**
- HHI < 0.10 (< 1,000): Well-diversified
- HHI 0.10–0.18 (1,000–1,800): Moderately concentrated
- HHI > 0.18 (> 1,800): Highly concentrated

### 2.2 Effective Number of Assets (N_eff) — Eigenvalue Method

The eigenvalue-based effective N captures correlation-adjusted diversification using the covariance matrix of returns:

```
N_eff = (Σᵢ λᵢ)² / Σᵢ λᵢ²
```

Where `λᵢ` are the eigenvalues of the portfolio covariance matrix Σ.

Equivalently using portfolio variance decomposition:
```
N_eff = 1 / Σᵢ (sᵢ²)
```

Where `sᵢ = wᵢ σᵢ / σ_p` is the contribution of asset `i` to portfolio volatility (normalized).

**Interpretation:** N_eff = k means the portfolio behaves as if it holds k uncorrelated equal-weight positions. Lower N_eff relative to actual N indicates high factor or correlation clustering.

### 2.3 Diversification Ratio (DR)

The Diversification Ratio compares the weighted average of individual asset volatilities to the portfolio volatility:

```
DR = (Σᵢ wᵢ σᵢ) / σ_p
```

Where:
- `wᵢ` = weight of asset `i`
- `σᵢ` = volatility (std dev) of asset `i` returns
- `σ_p` = portfolio volatility = √(w' Σ w)

**Range:** DR ≥ 1 always. DR = 1 implies all assets are perfectly correlated (no diversification benefit). Higher DR = better diversification. A DR of 1.4 means the portfolio's volatility is 40% below the average individual asset volatility.

### 2.4 Marginal Risk Contribution (MRC) — Euler Decomposition

Euler's theorem decomposes portfolio variance additively. The marginal risk contribution of asset `i` is:

```
MRC_i = wᵢ × (∂σ_p / ∂wᵢ)
      = wᵢ × (Σw)ᵢ / σ_p
```

Where `(Σw)ᵢ` is the `i`-th element of the matrix-vector product Σw (the covariance of asset `i` with the portfolio).

**Risk Contribution (RC):**
```
RC_i = MRC_i  (already weighted)
```

**Percentage Risk Contribution:**
```
%RC_i = RC_i / σ_p
```

**Property:** Σᵢ RC_i = σ_p (they sum to total portfolio volatility). This allows attributing each position's contribution to total portfolio risk.

**Risk Parity target:** Set wᵢ such that RC_i = RC_j for all i, j (equal risk contribution).

---

## 3. Data Sources and Limitations

### 3.1 Damodaran Beta Dataset

**File:** `research/damodaran_betas.json`
**Source:** https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html
**As-of date:** January 2026
**Coverage:** ~94 US industries, 5,994 firms total

**Fields provided:**
- Levered (equity) beta
- Debt-to-equity ratio (%)
- Effective tax rate (%)
- Unlevered (asset) beta
- Cash as % of firm value
- Cash-adjusted unlevered beta
- HiLo risk measure
- Standard deviation of equity returns
- Standard deviation of operating income (earnings volatility)

**Limitations:**
- US-centric: betas based on US-listed firms; global peers may differ
- Quarterly data: industry composition shifts over time; semiconductor D/E ratios post-AI capex surge may be underestimated
- `std_dev_op_income_pct` is null for banks, money center banks, and brokerage firms — these use non-standard income statements
- D/E ratios for financial firms (banks, insurance) reflect regulatory leverage, not operational leverage; their leverage scores are structurally incomparable to non-financials
- Industry classification uses Damodaran's proprietary scheme, which does not map 1:1 to GICS or SIC codes

### 3.2 Country ERP Dataset

**File:** `research/country_erp.json`
**Source:** https://pages.stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx
**As-of date:** January 2026 (sovereign ratings updated February 2026)
**Coverage:** 165 rated countries + 21 frontier/unrated countries = 178 total

**Methodology (Damodaran's):**
1. Start with implied ERP for S&P 500 = 4.23% (mature market ERP)
2. For each country, add a country risk premium (CRP) based on:
   - Moody's sovereign rating → default spread
   - CDS spread (where available, preferred over rating-based spread)
   - Multiply default spread by equity volatility ratio (~1.52x) to convert credit spread to equity premium
3. Total ERP = Mature market ERP (4.23%) + Country Risk Premium

**Fields:**
- `moodys_rating`: Moody's local currency sovereign rating
- `rating_based_default_spread`: Default spread implied by Moody's rating (decimal)
- `equity_risk_premium`: Total ERP for equity investors in that country (decimal)
- `country_risk_premium`: Additional premium above US/mature market (decimal)
- `cds_spread`: 10-year CDS spread as of 12/31/2025 (decimal, null if unavailable)
- `frontier_market`: True for countries without sovereign ratings (PRS methodology used)

**Limitations:**
- CDS spreads unavailable for ~70% of countries; rating-based spreads used instead
- Ratings lag credit events; spreads can widen sharply before downgrades
- Equity volatility multiplier (1.52x) is estimated from recent EM data and can fluctuate
- Frontier markets use PRS composite political risk scores as a fallback — less precise
- Does not capture sub-sovereign risk (provincial/state bonds) or corporate-sovereign spread gaps

### 3.3 yfinance Sector/Industry Mapping

**File:** `research/risk_factor_scores.json` → `yfinance_to_damodaran_mapping`

yfinance uses GICS-derived sector and industry strings that differ from Damodaran's industry names. The mapping provides:
1. **Exact match** on `(sector, industry)` pair (key: `"sector|industry"`)
2. **Sector-only fallback** when the exact industry string is not found

**Limitations:**
- yfinance industry strings can change across API versions
- Some tickers report incorrect or generic sector/industry data
- Many Damodaran industries span multiple GICS sub-industries
- Conglomerates and diversified companies may map poorly to a single Damodaran industry

---

## 4. Aggregating Industry Scores to Portfolio Level

### 4.1 Weighted Average Risk Score

For a portfolio with N positions, the portfolio-level score for risk factor `f` is:

```
Score_portfolio(f) = Σᵢ [ wᵢ × Score_industry_i(f) ]
```

Where:
- `wᵢ` = allocation weight of position `i` (sums to 1.0)
- `Score_industry_i(f)` = integer score (1–10) for factor `f` assigned to the Damodaran industry of position `i`

The result is a continuous value in [1, 10].

### 4.2 Composite Risk Score per Industry

Each industry also carries a composite risk score = simple average of all 10 factor scores:

```
Composite_i = (1/10) × Σ_f Score_i(f)
```

This provides a single-number risk ranking for industry comparison but should not replace the factor-level granularity for portfolio construction decisions.

### 4.3 Portfolio Composite Risk Score

```
Portfolio_Composite = Σᵢ wᵢ × Composite_i
```

### 4.4 Factor Heat Map Interpretation

For each factor `f`, define the **concentration-adjusted factor exposure**:

```
FactorExposure(f) = Score_portfolio(f) × HHI_portfolio
```

High HHI + high factor score = amplified risk from both concentration and inherent factor sensitivity.

### 4.5 Mapping Tickers Without Damodaran Industry Match

When a ticker's yfinance sector/industry pair does not appear in the exact mapping:
1. Try sector-only fallback from `sector_only_fallback` dictionary
2. If sector also unknown, assign default neutral industry: `"Business & Consumer Services"` (composite score ~3.8)
3. Flag the ticker as `"industry_match": "fallback"` or `"industry_match": "default"` in output

---

## 5. Portfolio Risk Score Aggregation — Step-by-Step

1. **Fetch ticker data:** For each ticker, retrieve sector and industry strings from yfinance
2. **Map to Damodaran industry:** Use `yfinance_to_damodaran_mapping.exact_mapping` with `"sector|industry"` key; fall back to `sector_only_fallback`
3. **Load factor scores:** From `risk_factor_scores.json` → `industries[damodaran_industry].risk_scores`
4. **Weight scores:** Multiply each factor score by the ticker's portfolio weight
5. **Sum across positions:** Sum weighted scores for each of the 10 factors
6. **Compute portfolio metrics:** HHI, N_eff, DR, MRC from position weights and return covariance matrix
7. **Report:** Factor scores, composite score, diversification metrics, and per-factor heat map

---

## 6. Formula Reference Summary

| Metric | Formula |
|--------|---------|
| HHI | `Σ wᵢ²` |
| N_eff (HHI-based) | `1 / HHI` |
| N_eff (eigenvalue) | `(Σ λᵢ)² / Σ λᵢ²` |
| Diversification Ratio | `(Σ wᵢ σᵢ) / σ_p` |
| Portfolio Variance | `w' Σ w` |
| Portfolio Volatility | `√(w' Σ w)` |
| MRC_i | `wᵢ (Σw)ᵢ / σ_p` |
| Portfolio Factor Score | `Σ wᵢ × Score_i(f)` |
| Composite Industry Score | `mean(10 factor scores)` |

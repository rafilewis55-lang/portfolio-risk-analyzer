"""
Portfolio Risk Analyzer — Comprehensive Validation Script
Runs all 4 test portfolios, validates JSON responses, Excel, and PDF.
Writes results to validation/validation_report.md.
"""

import sys
import math
import json
import requests

BASE_URL = "http://localhost:8000"
REPORT_LINES = []
PASS = 0
FAIL = 0


# ─── Helpers ────────────────────────────────────────────────────────────────

def record(label: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    entry = f"| {status} | {label} |"
    if detail:
        entry += f" {detail} |"
    else:
        entry += " |"
    REPORT_LINES.append(entry)
    symbol = "PASS" if passed else "FAIL"
    print(f"  [{symbol}] {label}: {detail}")


def post_analyze(tickers, weights):
    payload = {"tickers": tickers, "weights": weights}
    r = requests.post(f"{BASE_URL}/api/analyze", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def post_excel(tickers, weights):
    payload = {"tickers": tickers, "weights": weights}
    r = requests.post(f"{BASE_URL}/api/analyze/excel", json=payload, timeout=120)
    return r


def post_pdf(tickers, weights):
    payload = {"tickers": tickers, "weights": weights}
    r = requests.post(f"{BASE_URL}/api/analyze/pdf", json=payload, timeout=120)
    return r


def section(title: str):
    # Only print to console; the report writer builds its own structure
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_risk_scores_in_range(data: dict, portfolio_name: str):
    """All per-holding risk scores are in [1, 10]."""
    per_holding = data.get("risk_factors", {}).get("per_holding", {})
    all_ok = True
    bad = []
    for ticker, scores in per_holding.items():
        for factor, score in scores.items():
            if not (1 <= score <= 10):
                all_ok = False
                bad.append(f"{ticker}.{factor}={score}")
    record(f"{portfolio_name}: All risk scores in [1,10]", all_ok,
           f"Checked {sum(len(s) for s in per_holding.values())} scores" + (f" | BAD: {bad}" if bad else ""))


def check_correlation_matrix(data: dict, portfolio_name: str):
    """Correlation matrix is symmetric with diagonal=1.0, values in [-1,1]."""
    corr_dict = data.get("portfolio_metrics", {}).get("correlation_matrix", {})
    if not corr_dict:
        record(f"{portfolio_name}: Correlation matrix exists", False, "No correlation_matrix in response")
        return

    tickers = list(corr_dict.keys())
    n = len(tickers)

    # Build 2D matrix
    matrix = {}
    for t1 in tickers:
        matrix[t1] = {}
        for t2 in tickers:
            matrix[t1][t2] = corr_dict.get(t1, {}).get(t2)

    # Check diagonal = 1.0
    diag_ok = True
    diag_bad = []
    for t in tickers:
        val = matrix[t].get(t)
        if val is None or not math.isclose(val, 1.0, abs_tol=1e-6):
            diag_ok = False
            diag_bad.append(f"{t}={val}")
    record(f"{portfolio_name}: Correlation matrix diagonal=1.0", diag_ok,
           f"Checked {n} diagonal entries" + (f" | BAD: {diag_bad}" if diag_bad else ""))

    # Check symmetry
    sym_ok = True
    sym_bad = []
    for t1 in tickers:
        for t2 in tickers:
            v1 = matrix[t1].get(t2)
            v2 = matrix[t2].get(t1)
            if v1 is None or v2 is None or not math.isclose(v1, v2, abs_tol=1e-8):
                sym_ok = False
                sym_bad.append(f"{t1},{t2}: {v1} vs {v2}")
    record(f"{portfolio_name}: Correlation matrix symmetric", sym_ok,
           f"Checked {n*n} pairs" + (f" | BAD: {sym_bad[:3]}" if sym_bad else ""))

    # Check values in [-1, 1]
    range_ok = True
    range_bad = []
    for t1 in tickers:
        for t2 in tickers:
            val = matrix[t1].get(t2)
            if val is not None and not (-1.0 - 1e-9 <= val <= 1.0 + 1e-9):
                range_ok = False
                range_bad.append(f"{t1},{t2}={val}")
    record(f"{portfolio_name}: Correlation values in [-1,1]", range_ok,
           f"All {n*n} values checked" + (f" | OUT OF RANGE: {range_bad}" if range_bad else ""))


def check_mrc_sum(data: dict, portfolio_name: str):
    """Sum of MRC values equals portfolio volatility (within tolerance)."""
    metrics = data.get("portfolio_metrics", {})
    mrc = metrics.get("marginal_risk_contributions", {})
    port_vol = metrics.get("portfolio_volatility")
    if not mrc or port_vol is None:
        record(f"{portfolio_name}: MRC sum = portfolio vol", False, "Missing mrc or portfolio_volatility")
        return
    mrc_sum = sum(mrc.values())
    tol = max(1e-4, port_vol * 0.001)  # 0.1% tolerance
    ok = math.isclose(mrc_sum, port_vol, abs_tol=tol)
    record(f"{portfolio_name}: MRC values sum to portfolio_vol", ok,
           f"MRC_sum={mrc_sum:.6f}, port_vol={port_vol:.6f}, tol={tol:.6f}")


def check_severity_levels(data: dict, portfolio_name: str):
    """All overlaps have valid severity levels."""
    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    overlaps = data.get("overlaps", [])
    if not overlaps:
        record(f"{portfolio_name}: Overlap severity levels valid", True, "No overlaps found (trivially valid)")
        return
    bad = []
    for ov in overlaps:
        sev = ov.get("severity")
        if sev not in valid_severities:
            bad.append(f"{ov.get('factor')}={sev}")
    ok = len(bad) == 0
    record(f"{portfolio_name}: Overlap severity levels valid", ok,
           f"Checked {len(overlaps)} overlaps" + (f" | BAD: {bad}" if bad else ""))


def check_risk_grade(data: dict, portfolio_name: str):
    """Risk grade is A-F."""
    grade = data.get("risk_factors", {}).get("risk_grade")
    valid_grades = {"A", "B", "C", "D", "F"}
    ok = grade in valid_grades
    record(f"{portfolio_name}: Risk grade is A-F", ok, f"grade={grade}")


# ─── Portfolio A — Concentrated Tech ────────────────────────────────────────

def fetch_portfolio_a():
    tickers = ["NVDA", "AMD", "TSM", "ASML"]
    weights = [0.40, 0.30, 0.20, 0.10]
    data = post_analyze(tickers, weights)
    return data, tickers, weights


def validate_portfolio_a():
    """Fetch Portfolio A data."""
    tickers = ["NVDA", "AMD", "TSM", "ASML"]
    weights = [0.40, 0.30, 0.20, 0.10]
    data = post_analyze(tickers, weights)
    return data, tickers, weights


def validate_portfolio_a_results(data):
    metrics = data.get("portfolio_metrics", {})
    n_eff = metrics.get("n_eff")
    hhi = metrics.get("hhi")
    risk_factors = data.get("risk_factors", {})

    # N_eff < 2.0
    ok = n_eff is not None and n_eff < 2.0
    record("Portfolio A: N_eff < 2.0", ok, f"n_eff={n_eff}")

    # HHI > 0.25
    ok = hhi is not None and hhi > 0.25
    record("Portfolio A: HHI > 0.25", ok, f"hhi={hhi:.4f}" if hhi else "None")

    # China risk HIGH
    per_holding = risk_factors.get("per_holding", {})
    china_scores = {t: per_holding.get(t, {}).get("china_revenue_risk") for t in ["NVDA", "AMD", "TSM"]}
    port_china = risk_factors.get("portfolio_weighted", {}).get("china_revenue_risk")
    china_high = port_china is not None and port_china >= 6.0
    record("Portfolio A: China risk is HIGH (weighted >= 6.0)", china_high,
           f"portfolio_weighted_china={port_china} | per_holding={china_scores}")

    # Supply chain concentration HIGH
    port_sc = risk_factors.get("portfolio_weighted", {}).get("supply_chain_concentration")
    sc_high = port_sc is not None and port_sc >= 6.0
    record("Portfolio A: Supply chain concentration HIGH (>= 6.0)", sc_high,
           f"portfolio_weighted_supply_chain={port_sc}")

    # General checks
    check_risk_scores_in_range(data, "Portfolio A")
    check_correlation_matrix(data, "Portfolio A")
    check_mrc_sum(data, "Portfolio A")
    check_severity_levels(data, "Portfolio A")
    check_risk_grade(data, "Portfolio A")


# ─── Portfolio B — False Diversification ─────────────────────────────────────

def validate_portfolio_b():
    tickers = ["AAPL", "MSFT", "GOOGL", "META"]
    weights = [0.25, 0.25, 0.25, 0.25]
    data = post_analyze(tickers, weights)
    return data, tickers, weights


def validate_portfolio_b_results(data):
    metrics = data.get("portfolio_metrics", {})
    n_eff = metrics.get("n_eff")
    hhi = metrics.get("hhi")
    risk_factors = data.get("risk_factors", {})

    # N_eff between 1.0 and 3.0
    ok = n_eff is not None and 1.0 <= n_eff <= 3.0
    record("Portfolio B: N_eff in [1.0, 3.0]", ok, f"n_eff={n_eff}")

    # HHI = 0.25 (4 equal weights = 4 * 0.25^2 = 0.25)
    ok = hhi is not None and math.isclose(hhi, 0.25, abs_tol=1e-4)
    record("Portfolio B: HHI = 0.25 (equal-weight 4 stocks)", ok,
           f"hhi={hhi:.6f}" if hhi else "None")

    # Regulatory overlap (all face antitrust scrutiny).
    # NOTE: overlap detection threshold is >= 6.0. AAPL regulatory=3, others=5.
    # None reach 6.0 so no overlap is flagged — this is a DATA GAP in risk_factor_scores.json,
    # not a code bug. We record this as FAIL and document it.
    overlaps = data.get("overlaps", [])
    reg_overlap = [o for o in overlaps if o.get("factor") == "regulatory_policy_risk"]
    has_reg = len(reg_overlap) > 0
    per_holding = risk_factors.get("per_holding", {})
    reg_scores = {t: per_holding.get(t, {}).get("regulatory_policy_risk") for t in ["AAPL", "MSFT", "GOOGL", "META"]}
    if has_reg:
        reg_detail = f"severity={reg_overlap[0].get('severity')}, tickers={reg_overlap[0].get('tickers')}"
    else:
        reg_detail = f"No regulatory overlap (scores < threshold 6.0): {reg_scores} — DATA GAP: scores underestimate real-world antitrust exposure"
    record("Portfolio B: Has regulatory overlap", has_reg, reg_detail)

    # AAPL china_revenue_risk >= 6
    aapl_china = data.get("risk_factors", {}).get("per_holding", {}).get("AAPL", {}).get("china_revenue_risk")
    ok = aapl_china is not None and aapl_china >= 6
    record("Portfolio B / AAPL: china_revenue_risk >= 6", ok, f"aapl_china={aapl_china}")

    # General checks
    check_risk_scores_in_range(data, "Portfolio B")
    check_correlation_matrix(data, "Portfolio B")
    check_mrc_sum(data, "Portfolio B")
    check_severity_levels(data, "Portfolio B")
    check_risk_grade(data, "Portfolio B")

    return data  # return for AAPL china check


# ─── Portfolio C — Reasonably Diversified ────────────────────────────────────

def validate_portfolio_c():
    tickers = ["AAPL", "JPM", "XOM", "JNJ", "PG", "BRK-B", "GLD"]
    weights = [0.15, 0.15, 0.15, 0.15, 0.15, 0.10, 0.15]
    data = post_analyze(tickers, weights)
    return data, tickers, weights


def validate_portfolio_c_results(data, data_a=None, data_b=None):
    metrics = data.get("portfolio_metrics", {})
    n_eff = metrics.get("n_eff")
    dr = metrics.get("diversification_ratio")

    # N_eff > 3.0
    ok = n_eff is not None and n_eff > 3.0
    record("Portfolio C: N_eff > 3.0", ok, f"n_eff={n_eff}")

    # DR > 1.2
    ok = dr is not None and dr > 1.2
    record("Portfolio C: DR > 1.2", ok, f"dr={dr}")

    # Fewer HIGH/CRITICAL overlaps than A or B
    def count_high_critical(d):
        return sum(1 for o in d.get("overlaps", []) if o.get("severity") in ("HIGH", "CRITICAL"))

    c_count = count_high_critical(data)
    detail = f"Portfolio C has {c_count} HIGH/CRITICAL overlaps"
    if data_a and data_b:
        a_count = count_high_critical(data_a)
        b_count = count_high_critical(data_b)
        fewer = c_count < a_count or c_count < b_count
        detail += f" | A={a_count}, B={b_count}"
    else:
        fewer = True  # can't compare without data
    record("Portfolio C: Fewer HIGH/CRITICAL overlaps than A or B", fewer, detail)

    # JPM interest_rate_risk check (done here; will compare with NVDA later)
    jpm_ir = data.get("risk_factors", {}).get("per_holding", {}).get("JPM", {}).get("interest_rate_risk")
    record("Portfolio C / JPM: interest_rate_risk score present", jpm_ir is not None,
           f"jpm_interest_rate_risk={jpm_ir}")

    # General checks
    check_risk_scores_in_range(data, "Portfolio C")
    check_correlation_matrix(data, "Portfolio C")
    check_mrc_sum(data, "Portfolio C")
    check_severity_levels(data, "Portfolio C")
    check_risk_grade(data, "Portfolio C")

    return jpm_ir


# ─── Portfolio D — Single Stock ───────────────────────────────────────────────

def validate_portfolio_d():
    tickers = ["NVDA"]
    weights = [1.0]
    data = post_analyze(tickers, weights)
    return data, tickers, weights


def validate_portfolio_d_results(data):
    metrics = data.get("portfolio_metrics", {})
    hhi = metrics.get("hhi")
    n_eff = metrics.get("n_eff")
    dr = metrics.get("diversification_ratio")

    # HHI = 1.0 exactly
    ok = hhi is not None and math.isclose(hhi, 1.0, abs_tol=1e-9)
    record("Portfolio D: HHI = 1.0 exactly", ok, f"hhi={hhi}")

    # N_eff = 1.0 exactly
    ok = n_eff is not None and math.isclose(n_eff, 1.0, abs_tol=1e-6)
    record("Portfolio D: N_eff = 1.0 exactly", ok, f"n_eff={n_eff}")

    # DR = 1.0 exactly (single stock: weighted_vol / port_vol = 1.0)
    ok = dr is not None and math.isclose(dr, 1.0, abs_tol=1e-6)
    record("Portfolio D: DR = 1.0 exactly", ok, f"dr={dr}")

    # General checks
    check_risk_scores_in_range(data, "Portfolio D")
    check_risk_grade(data, "Portfolio D")

    # No meaningful correlation matrix check for single stock (1x1 = 1.0 trivially)
    corr_dict = metrics.get("correlation_matrix", {})
    single_corr_ok = len(corr_dict) == 1 and math.isclose(
        list(list(corr_dict.values())[0].values())[0], 1.0, abs_tol=1e-9
    )
    record("Portfolio D: Correlation matrix is 1x1 = [[1.0]]", single_corr_ok,
           f"corr_dict={corr_dict}")

    return data.get("risk_factors", {}).get("per_holding", {}).get("NVDA", {}).get("interest_rate_risk")


# ─── Cross-Portfolio Checks ───────────────────────────────────────────────────

def validate_cross_portfolio(nvda_ir, jpm_ir):
    section("Cross-Portfolio Checks")

    # JPM interest_rate_risk != NVDA interest_rate_risk
    if nvda_ir is not None and jpm_ir is not None:
        different = nvda_ir != jpm_ir
        record(
            "JPM interest_rate_risk != NVDA interest_rate_risk",
            different,
            f"nvda_ir={nvda_ir}, jpm_ir={jpm_ir}",
        )
    else:
        record(
            "JPM interest_rate_risk != NVDA interest_rate_risk",
            False,
            f"Missing data: nvda_ir={nvda_ir}, jpm_ir={jpm_ir}",
        )


# ─── Excel / PDF Validation ───────────────────────────────────────────────────

def validate_excel_and_pdf():
    section("Excel and PDF Generation")

    # Use a simple 2-ticker portfolio for speed
    tickers = ["AAPL", "MSFT"]
    weights = [0.5, 0.5]

    print("  Testing Excel generation...")
    try:
        r = post_excel(tickers, weights)
        ok_status = r.status_code == 200
        record("Excel: HTTP 200 response", ok_status, f"status={r.status_code}")

        content = r.content
        non_empty = len(content) > 0
        record("Excel: Non-empty binary response", non_empty, f"size={len(content)} bytes")

        # xlsx files start with PK (ZIP magic bytes: 0x50 0x4B)
        xlsx_magic = content[:2] == b'PK'
        record("Excel: Valid xlsx magic bytes (PK)", xlsx_magic,
               f"first_bytes={content[:4].hex()}")
    except Exception as e:
        record("Excel: HTTP 200 response", False, str(e))
        record("Excel: Non-empty binary response", False, "Skipped due to error")
        record("Excel: Valid xlsx magic bytes (PK)", False, "Skipped due to error")

    print("  Testing PDF generation...")
    try:
        r = post_pdf(tickers, weights)
        ok_status = r.status_code == 200
        record("PDF: HTTP 200 response", ok_status, f"status={r.status_code}")

        content = r.content
        non_empty = len(content) > 0
        record("PDF: Non-empty binary response", non_empty, f"size={len(content)} bytes")

        # PDF starts with %PDF
        pdf_magic = content[:4] == b'%PDF'
        record("PDF: Valid PDF header (%PDF)", pdf_magic,
               f"first_bytes={content[:8]}")
    except Exception as e:
        record("PDF: HTTP 200 response", False, str(e))
        record("PDF: Non-empty binary response", False, "Skipped due to error")
        record("PDF: Valid PDF header (%PDF)", False, "Skipped due to error")


# ─── AAPL China Check (standalone) ───────────────────────────────────────────

def validate_aapl_china(data_b):
    """Ensure AAPL china_revenue_risk >= 6 from Portfolio B data."""
    section("Specific Factor Checks")
    aapl_china = data_b.get("risk_factors", {}).get("per_holding", {}).get("AAPL", {}).get("china_revenue_risk")
    ok = aapl_china is not None and aapl_china >= 6
    record("AAPL: china_revenue_risk >= 6", ok, f"china_revenue_risk={aapl_china}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Portfolio Risk Analyzer — Validation Suite")
    print("=" * 60)

    all_data = {}
    data_a = data_b = data_c = data_d = None

    # ── Fetch all portfolio data ──────────────────────────────────────────────
    section("Fetching Portfolio A — Concentrated Tech (NVDA 40%, AMD 30%, TSM 20%, ASML 10%)")
    print("  Calling API (may take 30-60s)...")
    try:
        data_a, _, _ = validate_portfolio_a()
        all_data["A"] = data_a
        print("  API call succeeded.")
    except Exception as e:
        record("Portfolio A: API call succeeded", False, str(e))

    section("Fetching Portfolio B — False Diversification (AAPL/MSFT/GOOGL/META 25% each)")
    print("  Calling API (may take 30-60s)...")
    try:
        data_b, _, _ = validate_portfolio_b()
        all_data["B"] = data_b
        print("  API call succeeded.")
    except Exception as e:
        record("Portfolio B: API call succeeded", False, str(e))

    section("Fetching Portfolio C — Reasonably Diversified (AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD)")
    print("  Calling API (may take 30-60s)...")
    try:
        data_c, _, _ = validate_portfolio_c()
        all_data["C"] = data_c
        print("  API call succeeded.")
    except Exception as e:
        record("Portfolio C: API call succeeded", False, str(e))

    section("Fetching Portfolio D — Single Stock (NVDA 100%)")
    print("  Calling API (may take 30-60s)...")
    try:
        data_d, _, _ = validate_portfolio_d()
        all_data["D"] = data_d
        print("  API call succeeded.")
    except Exception as e:
        record("Portfolio D: API call succeeded", False, str(e))

    # ── Validate each portfolio ───────────────────────────────────────────────
    print("\n\nRunning validations...")

    nvda_ir = None
    jpm_ir = None

    section("Portfolio A — Concentrated Tech: Validation Checks")
    if data_a:
        validate_portfolio_a_results(data_a)
        nvda_ir = data_a.get("risk_factors", {}).get("per_holding", {}).get("NVDA", {}).get("interest_rate_risk")

    section("Portfolio B — False Diversification: Validation Checks")
    if data_b:
        validate_portfolio_b_results(data_b)

    section("Portfolio C — Reasonably Diversified: Validation Checks")
    if data_c:
        jpm_ir = validate_portfolio_c_results(data_c, data_a, data_b)

    section("Portfolio D — Single Stock: Validation Checks")
    if data_d:
        nvda_ir_d = validate_portfolio_d_results(data_d)
        if nvda_ir is None:
            nvda_ir = nvda_ir_d

    # Cross-portfolio
    validate_cross_portfolio(nvda_ir, jpm_ir)

    # AAPL China check
    if data_b:
        validate_aapl_china(data_b)

    # Excel / PDF
    validate_excel_and_pdf()

    # ── Write report ──────────────────────────────────────────────────────────
    write_report(all_data)


def write_report(all_data: dict):
    total = PASS + FAIL
    pct = (PASS / total * 100) if total > 0 else 0

    # ── Helper to build a section table from REPORT_LINES rows matching a prefix ──
    def section_rows(prefix: str) -> list[str]:
        """Return all REPORT_LINES rows whose label starts with prefix."""
        rows = [r for r in REPORT_LINES if f"| {prefix}" in r]
        if not rows:
            return []
        out = ["| Result | Check | Detail |", "|--------|-------|--------|"]
        out.extend(rows)
        return out

    # Prefixes used in each section
    A_prefix = "Portfolio A"
    B_prefix = "Portfolio B"
    C_prefix = "Portfolio C"
    D_prefix = "Portfolio D"

    def make_section(title: str, prefix: str) -> list[str]:
        rows = section_rows(prefix)
        out = [f"## {title}", ""]
        if rows:
            out.extend(rows)
        else:
            out.append("_No checks recorded for this section._")
        out.append("")
        return out

    lines = [
        "# Portfolio Risk Analyzer — Validation Report",
        "",
        f"**Date:** 2026-03-17",
        f"**Server:** http://localhost:8000",
        f"**Total Checks:** {total}",
        f"**PASS:** {PASS}  |  **FAIL:** {FAIL}  |  **Pass Rate:** {pct:.1f}%",
        "",
        "---",
        "",
    ]

    lines += make_section(
        "Portfolio A — Concentrated Tech (NVDA 40%, AMD 30%, TSM 20%, ASML 10%)",
        A_prefix,
    )
    lines += make_section(
        "Portfolio B — False Diversification (AAPL/MSFT/GOOGL/META 25% each)",
        B_prefix,
    )
    lines += make_section(
        "Portfolio C — Reasonably Diversified (AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD)",
        C_prefix,
    )
    lines += make_section(
        "Portfolio D — Single Stock (NVDA 100%)",
        D_prefix,
    )

    # Cross-portfolio and specific checks
    cross_rows = [r for r in REPORT_LINES if "JPM interest_rate" in r or "AAPL:" in r]
    lines += ["## Cross-Portfolio & Specific Factor Checks", ""]
    if cross_rows:
        lines += ["| Result | Check | Detail |", "|--------|-------|--------|"]
        lines += cross_rows
    lines.append("")

    # Excel / PDF
    excel_pdf_rows = [r for r in REPORT_LINES if "Excel:" in r or "PDF:" in r]
    lines += ["## File Generation (Excel / PDF)", ""]
    if excel_pdf_rows:
        lines += ["| Result | Check | Detail |", "|--------|-------|--------|"]
        lines += excel_pdf_rows
    lines.append("")

    lines += [
        "---",
        "",
        "## Summary",
        "",
        f"- Total checks run: **{total}**",
        f"- Passed: **{PASS}**",
        f"- Failed: **{FAIL}**",
        f"- Pass rate: **{pct:.1f}%**",
        "",
    ]

    # ── Raw API metrics table ──────────────────────────────────────────────────
    lines += [
        "## Raw API Results",
        "",
        "### Key Metrics Per Portfolio",
        "",
        "| Portfolio | HHI | N_eff | DR | Port_Vol | Risk_Grade | Num_Overlaps |",
        "|-----------|-----|-------|----|----------|------------|--------------|",
    ]
    portfolio_names = {
        "A": "NVDA/AMD/TSM/ASML",
        "B": "AAPL/MSFT/GOOGL/META",
        "C": "AAPL/JPM/XOM/JNJ/PG/BRK-B/GLD",
        "D": "NVDA",
    }
    for letter, data in all_data.items():
        m = data.get("portfolio_metrics", {})
        rf = data.get("risk_factors", {})
        hhi = m.get("hhi")
        n_eff = m.get("n_eff")
        dr = m.get("diversification_ratio")
        vol = m.get("portfolio_volatility")
        grade = rf.get("risk_grade")
        n_ov = len(data.get("overlaps", []))
        hhi_s = f"{hhi:.4f}" if hhi is not None else "N/A"
        n_eff_s = f"{n_eff:.3f}" if n_eff is not None else "N/A"
        dr_s = f"{dr:.3f}" if dr is not None else "N/A"
        vol_s = f"{vol:.4f}" if vol is not None else "N/A"
        lines.append(f"| {letter} ({portfolio_names.get(letter,'')}) | {hhi_s} | {n_eff_s} | {dr_s} | {vol_s} | {grade} | {n_ov} |")

    lines += [
        "",
        "### Risk Factor Scores Per Portfolio (Portfolio-Weighted)",
        "",
    ]
    factor_names = [
        "interest_rate_risk", "china_revenue_risk", "geopolitical_country_risk",
        "currency_risk", "regulatory_policy_risk", "leverage_credit_risk",
        "earnings_cyclicality", "sector_concentration", "supply_chain_concentration",
        "esg_energy_transition_risk",
    ]
    header = "| Factor | " + " | ".join(f"Port {l}" for l in all_data.keys()) + " | SP500 Benchmark |"
    sep = "|--------|" + "--------|" * len(all_data) + "-----------------|"
    lines += [header, sep]
    sp500_bench = {
        "interest_rate_risk": 5, "china_revenue_risk": 4, "geopolitical_country_risk": 4,
        "currency_risk": 5, "regulatory_policy_risk": 4, "leverage_credit_risk": 4,
        "earnings_cyclicality": 5, "sector_concentration": 3, "supply_chain_concentration": 4,
        "esg_energy_transition_risk": 4,
    }
    for f in factor_names:
        scores = []
        for letter, data in all_data.items():
            pw = data.get("risk_factors", {}).get("portfolio_weighted", {})
            scores.append(str(pw.get(f, "N/A")))
        bench = sp500_bench.get(f, "N/A")
        lines.append(f"| {f} | " + " | ".join(scores) + f" | {bench} |")

    lines += [
        "",
        "### Overlaps Per Portfolio",
        "",
    ]
    for letter, data in all_data.items():
        lines.append(f"#### Portfolio {letter} — {portfolio_names.get(letter,'')}")
        overlaps = data.get("overlaps", [])
        if not overlaps:
            lines.append("No overlaps detected.")
        else:
            lines.append("| Factor | Tickers | Combined Weight | Avg Score | Severity |")
            lines.append("|--------|---------|-----------------|-----------|----------|")
            for o in overlaps:
                lines.append(
                    f"| {o.get('factor_label', o.get('factor'))} "
                    f"| {', '.join(o.get('tickers', []))} "
                    f"| {o.get('combined_weight', 'N/A')} "
                    f"| {o.get('avg_score', 'N/A')} "
                    f"| {o.get('severity')} |"
                )
        lines.append("")

    report_path = "C:/Users/rafil/Documents/portfolio-risk-analyzer/validation/validation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n{'='*60}")
    print(f"  Validation complete: {PASS}/{total} checks passed ({pct:.1f}%)")
    print(f"  Report written to: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

"""
Multi-section PDF report generator using ReportLab.
Uses ReportLab XML tags for formatting — NO Unicode subscript/superscript.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# DB Blue in reportlab color format
DB_BLUE_COLOR = colors.HexColor("#0018A8")
DB_LIGHT_COLOR = colors.HexColor("#E8EDF2")
DB_MID_COLOR = colors.HexColor("#C7D3E3")


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=24,
        textColor=DB_BLUE_COLOR,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=DB_BLUE_COLOR,
        spaceBefore=20,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        "SubSection",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=DB_BLUE_COLOR,
        spaceBefore=12,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        "BodyJustified",
        parent=styles["Normal"],
        alignment=TA_JUSTIFY,
        fontSize=10,
        leading=14,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        "MetricLabel",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.gray,
    ))

    styles.add(ParagraphStyle(
        "MetricValue",
        parent=styles["Normal"],
        fontSize=14,
        textColor=DB_BLUE_COLOR,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
        alignment=TA_CENTER,
    ))

    return styles


def generate_pdf(analysis: dict) -> io.BytesIO:
    """Generate multi-section PDF report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = _get_styles()
    story = []

    _build_cover(story, styles, analysis)
    story.append(PageBreak())
    _build_diversification_scorecard(story, styles, analysis)
    story.append(PageBreak())
    _build_risk_heatmap(story, styles, analysis)
    story.append(PageBreak())
    _build_overlap_table(story, styles, analysis)
    _build_narrative(story, styles, analysis)
    story.append(PageBreak())
    _build_methodology(story, styles, analysis)

    doc.build(story)
    buf.seek(0)
    return buf


def _build_cover(story, styles, analysis):
    risk = analysis.get("risk_factors", {})
    portfolio = analysis.get("portfolio_metrics", {})
    tickers = analysis.get("tickers", [])
    grade = risk.get("risk_grade", "N/A")
    score = risk.get("overall_score", 0)

    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Portfolio Risk Exposure Analysis", styles["CoverTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="80%", color=DB_BLUE_COLOR, thickness=2))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph(
        f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Holdings:</b> {', '.join(tickers)}", styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Overall Risk Grade:</b> <font size='16' color='{'red' if grade in ('D','F') else '#0018A8'}'>"
        f"<b>{grade}</b></font> ({score:.1f}/10)",
        styles["Normal"],
    ))

    story.append(Spacer(1, 0.3 * inch))

    # Executive summary from narrative
    narrative = analysis.get("narrative", "")
    if narrative:
        # Extract first paragraph
        first_para = narrative.split("\n\n")[0].replace("**Executive Summary:** ", "")
        story.append(Paragraph(f"<b>Executive Summary:</b> {first_para}", styles["BodyJustified"]))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "Damodaran industry betas and country risk premiums as of January 2026. "
        "Source: pages.stern.nyu.edu/~adamodar. Data may be stale - check source for updates.",
        styles["Footer"],
    ))


def _build_diversification_scorecard(story, styles, analysis):
    portfolio = analysis.get("portfolio_metrics", {})

    story.append(Paragraph("Diversification Scorecard", styles["SectionTitle"]))

    metrics = [
        ["Metric", "Value", "Interpretation"],
        [
            "HHI",
            f"{portfolio.get('hhi', 0):.4f}",
            _hhi_interp(portfolio.get("hhi", 0)),
        ],
        [
            Paragraph("N<sub>eff</sub> (Effective Bets)", styles["Normal"]),
            f"{portfolio.get('n_eff', 0):.2f}",
            _neff_interp(portfolio.get("n_eff", 0), len(analysis.get("tickers", []))),
        ],
        [
            "Diversification Ratio",
            f"{portfolio.get('diversification_ratio', 0):.2f}",
            _dr_interp(portfolio.get("diversification_ratio", 0)),
        ],
        [
            "Portfolio Volatility (Ann.)",
            f"{portfolio.get('portfolio_volatility', 0):.1%}",
            "",
        ],
        [
            "Distance to Diversification",
            f"{portfolio.get('distance_to_diversification', 0):.2f}",
            _dist_interp(portfolio.get("distance_to_diversification", 0)),
        ],
    ]

    t = Table(metrics, colWidths=[2.2 * inch, 1.2 * inch, 3.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DB_BLUE_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, DB_MID_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, DB_LIGHT_COLOR]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)


def _hhi_interp(hhi):
    if hhi >= 0.5:
        return "Highly concentrated"
    elif hhi >= 0.25:
        return "Moderately concentrated"
    elif hhi >= 0.15:
        return "Unconcentrated"
    return "Well distributed"


def _neff_interp(n_eff, n):
    ratio = n_eff / n if n > 0 else 0
    if ratio >= 0.7:
        return f"Good: {n_eff:.0f} effective bets from {n} holdings"
    elif ratio >= 0.4:
        return f"Moderate: correlation reduces {n} holdings to {n_eff:.1f} effective bets"
    return f"Poor: {n} holdings behave like {n_eff:.1f} independent bets"


def _dr_interp(dr):
    if dr >= 1.4:
        return "Strong diversification benefit"
    elif dr >= 1.15:
        return "Moderate diversification benefit"
    return "Limited diversification benefit"


def _dist_interp(dist):
    if dist <= 0.3:
        return "Close to well-diversified"
    elif dist <= 0.6:
        return "Room for improvement"
    return "Far from diversified"


def _build_risk_heatmap(story, styles, analysis):
    risk = analysis.get("risk_factors", {})
    tickers = analysis.get("tickers", [])
    per_holding = risk.get("per_holding", {})
    weighted = risk.get("portfolio_weighted", {})

    from backend.risk_factors import RISK_FACTOR_LABELS, RISK_FACTORS

    story.append(Paragraph("Risk Factor Heatmap", styles["SectionTitle"]))

    # Build table data
    header = ["Factor"] + tickers + ["Portfolio"]
    data = [header]

    for factor in RISK_FACTORS:
        label = RISK_FACTOR_LABELS.get(factor, factor)
        row = [label]
        for t in tickers:
            score = per_holding.get(t, {}).get(factor, 5)
            row.append(str(score))
        pw = weighted.get(factor, 5)
        row.append(f"{pw:.1f}")
        data.append(row)

    col_width = min(1.0, 5.5 / max(len(tickers), 1))
    col_widths = [2.0 * inch] + [col_width * inch] * len(tickers) + [0.8 * inch]

    t = Table(data, colWidths=col_widths)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DB_BLUE_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, DB_MID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    # Color-code cells by score
    for r_idx in range(1, len(data)):
        for c_idx in range(1, len(data[r_idx])):
            try:
                val = float(data[r_idx][c_idx])
            except (ValueError, TypeError):
                continue
            if val >= 8:
                style_cmds.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#FF6B6B")))
            elif val >= 6:
                style_cmds.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#FFD700")))
            elif val <= 3:
                style_cmds.append(("BACKGROUND", (c_idx, r_idx), (c_idx, r_idx), colors.HexColor("#90EE90")))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)


def _build_overlap_table(story, styles, analysis):
    overlaps = analysis.get("overlaps", [])

    story.append(Paragraph("Idiosyncratic Risk Overlaps", styles["SectionTitle"]))

    if not overlaps:
        story.append(Paragraph(
            "No significant risk overlaps detected.",
            styles["BodyJustified"],
        ))
        return

    data = [["Risk Theme", "Tickers", "Combined Weight", "Avg Score", "Severity"]]
    for o in overlaps:
        data.append([
            o["factor_label"],
            ", ".join(o["tickers"]),
            f"{o['combined_weight']:.1%}",
            f"{o['avg_score']:.1f}",
            o["severity"],
        ])

    t = Table(data, colWidths=[2.0 * inch, 1.8 * inch, 1.2 * inch, 0.8 * inch, 1.0 * inch])

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DB_BLUE_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, DB_MID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    severity_colors = {
        "CRITICAL": colors.HexColor("#FF6B6B"),
        "HIGH": colors.HexColor("#FFA500"),
        "MEDIUM": colors.HexColor("#FFD700"),
        "LOW": colors.HexColor("#90EE90"),
    }

    for r_idx in range(1, len(data)):
        sev = data[r_idx][4]
        if sev in severity_colors:
            style_cmds.append(("BACKGROUND", (4, r_idx), (4, r_idx), severity_colors[sev]))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)


def _build_narrative(story, styles, analysis):
    narrative = analysis.get("narrative", "")
    if not narrative:
        return

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Risk Narrative", styles["SectionTitle"]))

    for para in narrative.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # Convert markdown bold to reportlab bold
        para = para.replace("**", "<b>", 1)
        para = para.replace("**", "</b>", 1)
        # Handle remaining bold markers
        while "**" in para:
            para = para.replace("**", "<b>", 1)
            para = para.replace("**", "</b>", 1)
        # Handle bullet points
        if para.startswith("  - "):
            lines = para.split("\n")
            for line in lines:
                line = line.strip().lstrip("- ")
                story.append(Paragraph(f"\u2022 {line}", styles["BodyJustified"]))
        else:
            story.append(Paragraph(para, styles["BodyJustified"]))


def _build_methodology(story, styles, analysis):
    story.append(Paragraph("Methodology & Data Sources", styles["SectionTitle"]))

    sections = [
        (
            "Portfolio Diversification Metrics",
            "HHI (Herfindahl-Hirschman Index) measures weight concentration as the sum of "
            "squared portfolio weights. N<sub>eff</sub> (effective number of bets) uses "
            "eigenvalue decomposition of the correlation matrix: "
            "N<sub>eff</sub> = (Sum of eigenvalues)<super>2</super> / "
            "Sum of eigenvalues<super>2</super>. "
            "The Diversification Ratio = weighted sum of individual volatilities / portfolio "
            "volatility, always >= 1.0. Marginal Risk Contributions use Euler decomposition "
            "and sum to portfolio volatility."
        ),
        (
            "Risk Factor Scoring",
            "Each holding is scored 1-10 across 10 risk factors based on its Damodaran "
            "industry classification. Scores are portfolio-weighted by allocation. "
            "Leverage/Credit Risk and Earnings Cyclicality use quantitative data from "
            "Damodaran (D/E ratios, operating income volatility). Other factors use "
            "sector-level classifications."
        ),
        (
            "Overlap Detection",
            "Risk overlaps are flagged when 2+ holdings score above 6.0 on the same "
            "risk factor. Severity is determined by combined weight and average score: "
            "CRITICAL (>60% weight and score >8), HIGH (>40% weight or score >8), "
            "MEDIUM (>25% weight), LOW (otherwise)."
        ),
        (
            "Data Sources",
            "Market data: Yahoo Finance (yfinance). Industry betas, D/E ratios: Damodaran "
            "(pages.stern.nyu.edu/~adamodar), as of January 2026. Country equity risk "
            "premiums: Damodaran ctryprem dataset."
        ),
    ]

    for title, body in sections:
        story.append(Paragraph(title, styles["SubSection"]))
        story.append(Paragraph(body, styles["BodyJustified"]))

    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Damodaran industry betas and country risk premiums as of January 2026. "
        "Source: pages.stern.nyu.edu/~adamodar. Data may be stale - check source for updates.",
        styles["Footer"],
    ))

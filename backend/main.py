"""
FastAPI entry point.
Routes: analyze (JSON), analyze/excel, analyze/pdf, health.
Serves frontend as static files.
"""

import os
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="Portfolio Risk Analyzer")


# ── Models ──────────────────────────────────────────────────────────────────

class PortfolioRequest(BaseModel):
    tickers: list[str]
    weights: list[float]  # as decimals (0.25 = 25%)
    lookback_years: int = 2


class AnalysisResponse(BaseModel):
    tickers: list[str]
    weights: dict[str, float]
    portfolio_metrics: dict
    risk_factors: dict
    overlaps: list
    idiosyncratic: dict
    narrative: str
    warnings: list[str]
    industry_map: dict




# ── Core analysis ───────────────────────────────────────────────────────────

def run_analysis(req: PortfolioRequest) -> dict:
    """Run full portfolio risk analysis."""
    from backend.data_fetcher import fetch_all_data
    from backend.portfolio import run_full_portfolio_analysis
    from backend.risk_factors import score_portfolio_risk_factors, detect_risk_overlaps
    from backend.overlap_detector import analyze_idiosyncratic_risk
    from backend.narrative_generator import generate_narrative

    # Normalize weights
    tickers = [t.upper().strip() for t in req.tickers]
    raw_weights = req.weights
    weight_sum = sum(raw_weights)
    if weight_sum > 0:
        normalized = [w / weight_sum for w in raw_weights]
    else:
        normalized = [1.0 / len(tickers)] * len(tickers)

    weights = {t: w for t, w in zip(tickers, normalized)}

    # Fetch data
    data = fetch_all_data(tickers, req.lookback_years)
    valid_tickers = data["valid_tickers"]
    warnings = data["warnings"]

    # Adjust weights for valid tickers only
    valid_weights = {t: weights[t] for t in valid_tickers if t in weights}
    if valid_weights:
        total = sum(valid_weights.values())
        valid_weights = {t: w / total for t, w in valid_weights.items()}

    # Portfolio math
    portfolio_metrics = run_full_portfolio_analysis(data["prices"][valid_tickers], valid_weights)

    # Risk factor scoring
    risk_factors = score_portfolio_risk_factors(
        valid_tickers, valid_weights, data["industry_map"], data["damodaran"]
    )

    # Overlap detection
    overlaps = detect_risk_overlaps(risk_factors, valid_weights)

    # Idiosyncratic risk
    idiosyncratic = analyze_idiosyncratic_risk(data["prices"], valid_weights)

    # Build analysis dict
    analysis = {
        "tickers": valid_tickers,
        "weights": valid_weights,
        "portfolio_metrics": portfolio_metrics,
        "risk_factors": risk_factors,
        "overlaps": overlaps,
        "idiosyncratic": idiosyncratic,
        "warnings": warnings,
        "industry_map": data["industry_map"],
        "damodaran_data": data["damodaran"],
    }

    # Narrative
    narrative = generate_narrative(analysis, data)
    analysis["narrative"] = narrative

    return analysis


# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/help", response_class=HTMLResponse)
async def serve_help():
    help_path = os.path.join(FRONTEND_DIR, "help.html")
    with open(help_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/analyze")
async def analyze(req: PortfolioRequest):
    try:
        result = run_analysis(req)
        # Convert non-serializable types
        return _serialize(result)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "detail": traceback.format_exc()},
        )


@app.post("/api/analyze/excel")
async def analyze_excel(req: PortfolioRequest):
    try:
        from backend.excel_generator import generate_excel

        result = run_analysis(req)
        buf = generate_excel(result)

        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=portfolio_risk_analysis.xlsx"},
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.post("/api/analyze/pdf")
async def analyze_pdf(req: PortfolioRequest):
    try:
        from backend.pdf_generator import generate_pdf

        result = run_analysis(req)
        buf = generate_pdf(result)

        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=portfolio_risk_analysis.pdf"},
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )



@app.post("/api/parse-portfolio")
async def parse_portfolio(request: Request):
    """Parse an uploaded Excel or CSV file to extract tickers and weights."""
    import io
    import re

    form = await request.form()
    file = form.get("file")
    if not file:
        return JSONResponse(status_code=400, content={"error": "No file uploaded"})

    filename = file.filename.lower()
    content = await file.read()

    try:
        if filename.endswith((".xlsx", ".xls")):
            holdings = _parse_excel(io.BytesIO(content))
        elif filename.endswith(".csv"):
            holdings = _parse_csv(content.decode("utf-8-sig"))
        else:
            return JSONResponse(status_code=400, content={"error": "Unsupported format. Use .xlsx, .xls, or .csv"})

        if not holdings:
            return JSONResponse(status_code=400, content={
                "error": "Could not find ticker/weight data. Make sure your file has tickers in one column and weights in another."
            })

        return {"holdings": holdings, "filename": file.filename}

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to parse file: {e}"})


def _is_ticker(val: str) -> bool:
    """Check if a string looks like a stock ticker."""
    import re
    val = str(val).strip()
    if not val or len(val) > 10:
        return False
    # Tickers: 1-5 uppercase letters, optionally with - or . (BRK-B, BRK.B)
    return bool(re.match(r'^[A-Z]{1,5}([.\-][A-Z]{1,2})?$', val.upper()))


def _is_weight(val) -> float | None:
    """Try to parse a value as a weight. Returns percentage (e.g., 25.0) or None."""
    if val is None:
        return None
    s = str(val).strip().rstrip('%')
    try:
        num = float(s)
        # If it looks like a decimal (0.0 to 1.0), convert to percentage
        if 0 < num <= 1.0 and '.' in s:
            return round(num * 100, 2)
        elif 0 < num <= 100:
            return round(num, 2)
        return None
    except (ValueError, TypeError):
        return None


def _parse_excel(buf) -> list[dict]:
    """Parse Excel file, dynamically finding ticker and weight columns."""
    import openpyxl

    wb = openpyxl.load_workbook(buf, read_only=True, data_only=True)
    ws = wb.active

    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))

    wb.close()
    return _extract_holdings_from_rows(rows)


def _parse_csv(text: str) -> list[dict]:
    """Parse CSV text, auto-detecting delimiter."""
    import csv
    import io

    # Auto-detect delimiter
    for delim in [',', '\t', ';']:
        reader = csv.reader(io.StringIO(text), delimiter=delim)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if rows and len(rows[0]) >= 2:
            return _extract_holdings_from_rows(rows)

    return []


def _extract_holdings_from_rows(rows: list[list]) -> list[dict]:
    """Find ticker and weight columns from a 2D array of rows."""
    if not rows:
        return []

    # Skip empty rows at the top
    while rows and all(not str(c).strip() for c in rows[0] if c is not None):
        rows.pop(0)

    if not rows:
        return []

    # Try to detect which columns are tickers and weights
    # Strategy: scan all columns, find the one with the most ticker-like values
    # and the one with the most weight-like values
    n_cols = max(len(r) for r in rows)

    # Check if first row is a header
    first_row = rows[0]
    header_keywords_ticker = {'ticker', 'symbol', 'stock', 'name', 'holding', 'security', 'position'}
    header_keywords_weight = {'weight', 'allocation', 'pct', 'percent', '%', 'share', 'proportion'}

    ticker_col = None
    weight_col = None
    data_start = 0

    # Check headers
    for i, cell in enumerate(first_row):
        if cell is None:
            continue
        val = str(cell).strip().lower()
        if any(kw in val for kw in header_keywords_ticker):
            ticker_col = i
        elif any(kw in val for kw in header_keywords_weight):
            weight_col = i

    if ticker_col is not None or weight_col is not None:
        data_start = 1  # skip header row

    # If headers didn't resolve both columns, scan data to find them
    if ticker_col is None or weight_col is None:
        col_ticker_scores = [0] * n_cols
        col_weight_scores = [0] * n_cols

        for row in rows[data_start:data_start + 20]:  # sample first 20 data rows
            for ci in range(min(len(row), n_cols)):
                cell = row[ci]
                if cell is None:
                    continue
                if _is_ticker(str(cell)):
                    col_ticker_scores[ci] += 1
                if _is_weight(cell) is not None:
                    col_weight_scores[ci] += 1

        if ticker_col is None:
            best = max(range(n_cols), key=lambda i: col_ticker_scores[i])
            if col_ticker_scores[best] > 0:
                ticker_col = best

        if weight_col is None:
            # Pick the best weight column that isn't the ticker column
            candidates = [(i, col_weight_scores[i]) for i in range(n_cols) if i != ticker_col]
            if candidates:
                best = max(candidates, key=lambda x: x[1])
                if best[1] > 0:
                    weight_col = best[0]

    if ticker_col is None or weight_col is None:
        return []

    # Extract holdings
    holdings = []
    for row in rows[data_start:]:
        if ticker_col >= len(row) or weight_col >= len(row):
            continue

        ticker_val = str(row[ticker_col]).strip().upper() if row[ticker_col] else ""
        weight_val = _is_weight(row[weight_col])

        if _is_ticker(ticker_val) and weight_val is not None:
            holdings.append({"ticker": ticker_val, "weight": weight_val})

    return holdings


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Static files ────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _serialize(obj):
    """Recursively convert numpy/pandas types to JSON-safe Python types."""
    import numpy as np
    import pandas as pd

    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj

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

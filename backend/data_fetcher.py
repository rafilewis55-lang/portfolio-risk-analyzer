"""
Data fetching layer: yfinance prices/fundamentals, Damodaran betas, country ERP.
File-based caching with TTL. Retry logic on all API calls.
"""

import os
import json
import pickle
import time
import numpy as np
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import httpx
from difflib import SequenceMatcher

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
RESEARCH_DIR = os.path.join(BASE_DIR, "research")

CACHE_TTL_PRICES = 86400       # 24 hours
CACHE_TTL_FUNDAMENTALS = 86400 # 24 hours
CACHE_TTL_DAMODARAN = 604800   # 7 days

os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(name: str) -> str:
    return os.path.join(CACHE_DIR, name)


def _cache_valid(path: str, ttl: int) -> bool:
    if not os.path.exists(path):
        return False
    age = time.time() - os.path.getmtime(path)
    return age < ttl


def _retry(func, *args, retries=3, delay=2, **kwargs):
    """Retry a function up to `retries` times with `delay` seconds between."""
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


# ── yfinance layer ──────────────────────────────────────────────────────────

def fetch_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """Batch download prices via yf.download(). Returns DataFrame with Close prices."""
    cache_key = f"prices_{'_'.join(sorted(tickers))}_{period}.pkl"
    path = _cache_path(cache_key)

    if _cache_valid(path, CACHE_TTL_PRICES):
        with open(path, "rb") as f:
            return pickle.load(f)

    def _download():
        data = yf.download(tickers, period=period, progress=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"]
        else:
            prices = data[["Close"]]
            prices.columns = tickers
        return prices.dropna(how="all")

    prices = _retry(_download)

    with open(path, "wb") as f:
        pickle.dump(prices, f)

    return prices


def fetch_fundamentals(ticker: str) -> dict:
    """Fetch yfinance Ticker.info for a single ticker."""
    cache_key = f"fundamentals_{ticker}.json"
    path = _cache_path(cache_key)

    if _cache_valid(path, CACHE_TTL_FUNDAMENTALS):
        with open(path, "r") as f:
            return json.load(f)

    def _get_info():
        t = yf.Ticker(ticker)
        info = t.info
        # Convert non-serializable values
        clean = {}
        for k, v in info.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                clean[k] = v
            else:
                clean[k] = str(v)
        return clean

    info = _retry(_get_info)

    with open(path, "w") as f:
        json.dump(info, f, indent=2)

    return info


# ── Damodaran layer ─────────────────────────────────────────────────────────

def fetch_damodaran_betas() -> dict:
    """Parse Damodaran betas. Returns {industry_name: {levered_beta, ...}, ...}."""
    cache_key = "damodaran_betas_parsed.json"
    path = _cache_path(cache_key)

    if _cache_valid(path, CACHE_TTL_DAMODARAN):
        with open(path, "r") as f:
            return json.load(f)

    # Try live fetch
    try:
        betas = _parse_damodaran_betas_html()
        with open(path, "w") as f:
            json.dump(betas, f, indent=2)
        return betas
    except Exception:
        pass

    # Fallback to bundled research file
    fallback = os.path.join(RESEARCH_DIR, "damodaran_betas.json")
    if os.path.exists(fallback):
        with open(fallback, "r") as f:
            raw = json.load(f)
        return _normalize_damodaran(raw)

    return {}


def _normalize_damodaran(raw: dict | list) -> dict:
    """Normalize damodaran data to {industry: {fields...}} dict."""
    # Handle list-of-dicts format from research agent
    industries = raw.get("industries", raw) if isinstance(raw, dict) else raw
    if isinstance(industries, list):
        result = {}
        for entry in industries:
            if isinstance(entry, dict) and "industry" in entry:
                name = entry["industry"]
                result[name] = {
                    "n_firms": entry.get("num_firms", 0),
                    "levered_beta": entry.get("levered_beta", 1.0),
                    "unlevered_beta": entry.get("unlevered_beta", 1.0),
                    "de_ratio": entry.get("de_ratio_pct", 0) / 100.0,
                    "eff_tax_rate": entry.get("tax_rate_pct", 0) / 100.0,
                }
        return result
    elif isinstance(industries, dict):
        # Already in dict format
        result = {}
        for name, data in industries.items():
            if isinstance(data, dict):
                result[name] = data
        return result
    return {}


def _parse_damodaran_betas_html() -> dict:
    """Fetch and parse the Damodaran Betas HTML table."""
    url = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html"
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")

    result = {}
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all("td")
            if len(cells) >= 6:
                industry = " ".join(cells[0].get_text(strip=True).split())
                if not industry or industry.lower() == "industry name":
                    continue
                try:
                    # Damodaran column order:
                    # [0] Industry  [1] #Firms  [2] Levered Beta
                    # [3] D/E Ratio  [4] Tax Rate  [5] Unlevered Beta
                    # [6] Cash/Firm Value  [7] Unlevered Beta (cash-adjusted)
                    result[industry] = {
                        "n_firms": _safe_int(cells[1].get_text(strip=True)),
                        "levered_beta": _safe_float(cells[2].get_text(strip=True)),
                        "de_ratio": _safe_float(cells[3].get_text(strip=True)) / 100.0,
                        "eff_tax_rate": _safe_float(cells[4].get_text(strip=True)) / 100.0,
                        "unlevered_beta": _safe_float(cells[5].get_text(strip=True)),
                    }
                except (ValueError, IndexError):
                    continue

    return result


def _safe_float(s: str) -> float:
    s = s.replace("%", "").replace(",", "").strip()
    if not s or s == "NA":
        return 0.0
    return float(s)


def _safe_int(s: str) -> int:
    s = s.replace(",", "").strip()
    if not s or s == "NA":
        return 0
    return int(float(s))


def get_country_erp(country: str) -> float:
    """Look up country equity risk premium from bundled JSON."""
    path = os.path.join(RESEARCH_DIR, "country_erp.json")
    if not os.path.exists(path):
        return 0.0
    with open(path, "r") as f:
        raw = json.load(f)

    # Handle nested list format: raw["countries"] = [{country, equity_risk_premium}, ...]
    countries = raw.get("countries", raw.get("data", []))
    if isinstance(countries, list):
        for entry in countries:
            if isinstance(entry, dict):
                name = entry.get("country", "")
                if name.lower() == country.lower():
                    return float(entry.get("equity_risk_premium", entry.get("total_erp", 0.0)))
        return 0.0

    # Dict format: {country_name: {erp, ...}}
    if isinstance(countries, dict):
        for k, v in countries.items():
            if k.lower() == country.lower():
                if isinstance(v, dict):
                    return float(v.get("equity_risk_premium", v.get("total_erp", 0.0)))
                return float(v)

    return 0.0


# ── Industry mapping ────────────────────────────────────────────────────────

# Manual overrides for common tickers
TICKER_INDUSTRY_OVERRIDES = {
    "AAPL": "Computers/Peripherals",
    "MSFT": "Software (System & Application)",
    "GOOGL": "Software (Internet)",
    "GOOG": "Software (Internet)",
    "META": "Software (Internet)",
    "AMZN": "Retail (Online)",
    "NVDA": "Semiconductor",
    "AMD": "Semiconductor",
    "TSM": "Semiconductor",
    "ASML": "Semiconductor Equip",
    "TSLA": "Auto & Truck",
    "JPM": "Banks (Money Center)",
    "BAC": "Banks (Money Center)",
    "GS": "Brokerage & Investment Banking",
    "XOM": "Oil/Gas (Integrated)",
    "CVX": "Oil/Gas (Integrated)",
    "JNJ": "Drugs (Pharmaceutical)",
    "PFE": "Drugs (Pharmaceutical)",
    "UNH": "Healthcare Information and Technology",
    "PG": "Household Products",
    "KO": "Beverage (Soft)",
    "WMT": "Retail (Grocery and Food)",
    "HD": "Retail (Building Supply)",
    "DIS": "Entertainment",
    "NFLX": "Entertainment",
    "V": "Financial Svcs. (Non-bank & Insurance)",
    "MA": "Financial Svcs. (Non-bank & Insurance)",
    "BRK-B": "Insurance (General)",
    "GLD": "Precious Metals",
    "SPY": "Diversified",
    "VTI": "Diversified",
    "AVGO": "Semiconductor",
    "INTC": "Semiconductor",
    "CRM": "Software (System & Application)",
    "ORCL": "Software (System & Application)",
    "COST": "Retail (Grocery and Food)",
    "LLY": "Drugs (Pharmaceutical)",
    "ABBV": "Drugs (Pharmaceutical)",
    "MRK": "Drugs (Pharmaceutical)",
    "T": "Telecom (Wireless)",
    "VZ": "Telecom (Wireless)",
    "NEE": "Power",
    "LIN": "Chemical (Diversified)",
    "RTX": "Aerospace/Defense",
    "BA": "Aerospace/Defense",
    "CAT": "Machinery",
    "DE": "Machinery",
    "MMM": "Diversified",
}


def map_ticker_to_damodaran(ticker: str, yf_info: dict) -> str:
    """Map a ticker to Damodaran industry name via overrides + fuzzy matching.

    Works for large/mid/small cap — uses yfinance sector/industry strings
    for any ticker not in the manual override list.
    """
    # Check manual overrides first
    if ticker.upper() in TICKER_INDUSTRY_OVERRIDES:
        return TICKER_INDUSTRY_OVERRIDES[ticker.upper()]

    # Get yfinance industry/sector
    yf_industry = yf_info.get("industry", "")
    yf_sector = yf_info.get("sector", "")

    # Load Damodaran industries
    damodaran = fetch_damodaran_betas()
    if not damodaran:
        return "Diversified"

    industries = list(damodaran.keys())

    # yfinance industry → Damodaran industry keyword mapping
    yf_to_damodaran = {
        # Technology
        "Software - Application": "Software (System & Application)",
        "Software - Infrastructure": "Software (System & Application)",
        "Semiconductors": "Semiconductor",
        "Semiconductor Equipment & Materials": "Semiconductor Equip",
        "Electronic Components": "Electronics (General)",
        "Consumer Electronics": "Electronics (Consumer & Office)",
        "Information Technology Services": "Computer Services",
        "Internet Content & Information": "Software (Internet)",
        "Internet Retail": "Retail (Online)",
        "Electronic Gaming & Multimedia": "Software (Entertainment)",
        "Scientific & Technical Instruments": "Electronics (General)",
        "Communication Equipment": "Telecom. Equipment",
        "Computer Hardware": "Computers/Peripherals",
        # Healthcare
        "Drug Manufacturers - General": "Drugs (Pharmaceutical)",
        "Drug Manufacturers - Specialty & Generic": "Drugs (Pharmaceutical)",
        "Biotechnology": "Drugs (Biotechnology)",
        "Medical Devices": "Healthcare Products",
        "Medical Instruments & Supplies": "Healthcare Products",
        "Health Information Services": "Heathcare Information and Technology",
        "Medical Distribution": "Healthcare Support Services",
        "Diagnostics & Research": "Healthcare Products",
        "Healthcare Plans": "Healthcare Support Services",
        "Medical Care Facilities": "Hospitals/Healthcare Facilities",
        # Financial Services
        "Banks - Diversified": "Bank (Money Center)",
        "Banks - Regional": "Banks (Regional)",
        "Capital Markets": "Brokerage & Investment Banking",
        "Financial Data & Stock Exchanges": "Financial Svcs. (Non-bank & Insurance)",
        "Insurance - Diversified": "Insurance (General)",
        "Insurance - Life": "Insurance (Life)",
        "Insurance - Property & Casualty": "Insurance (Prop/Cas.)",
        "Insurance Brokers": "Insurance (General)",
        "Asset Management": "Investments & Asset Management",
        "Credit Services": "Financial Svcs. (Non-bank & Insurance)",
        "Financial Conglomerates": "Financial Svcs. (Non-bank & Insurance)",
        "Mortgage Finance": "Bank (Money Center)",
        # Consumer
        "Specialty Retail": "Retail (Special Lines)",
        "Home Improvement Retail": "Retail (Building Supply)",
        "Apparel Retail": "Retail (Special Lines)",
        "Footwear & Accessories": "Shoe",
        "Apparel Manufacturing": "Apparel",
        "Luxury Goods": "Apparel",
        "Restaurants": "Restaurant/Dining",
        "Packaged Foods": "Food Processing",
        "Household & Personal Products": "Household Products",
        "Beverages - Non-Alcoholic": "Beverage (Soft)",
        "Beverages - Alcoholic": "Beverage (Alcoholic)",
        "Discount Stores": "Retail (General)",
        "Department Stores": "Retail (General)",
        "Grocery Stores": "Retail (Grocery and Food)",
        "Auto Manufacturers": "Auto & Truck",
        "Auto Parts": "Auto Parts",
        "Residential Construction": "Homebuilding",
        "Gambling": "Hotel/Gaming",
        "Lodging": "Hotel/Gaming",
        "Leisure": "Recreation",
        "Resorts & Casinos": "Hotel/Gaming",
        "Tobacco": "Tobacco",
        # Industrials
        "Specialty Industrial Machinery": "Machinery",
        "Farm & Heavy Construction Machinery": "Machinery",
        "Industrial Distribution": "Retail (Distributors)",
        "Aerospace & Defense": "Aerospace/Defense",
        "Airlines": "Air Transport",
        "Railroads": "Transportation (Railroads)",
        "Trucking": "Trucking",
        "Building Products & Equipment": "Building Materials",
        "Construction": "Engineering/Construction",
        "Engineering & Construction": "Engineering/Construction",
        "Waste Management": "Environmental & Waste Services",
        "Electrical Equipment & Parts": "Electrical Equipment",
        "Conglomerates": "Diversified",
        "Staffing & Employment Services": "Business & Consumer Services",
        "Consulting Services": "Business & Consumer Services",
        # Energy
        "Oil & Gas Integrated": "Oil/Gas (Integrated)",
        "Oil & Gas E&P": "Oil/Gas (Production and Exploration)",
        "Oil & Gas Midstream": "Oil/Gas Distribution",
        "Oil & Gas Equipment & Services": "Oilfield Svcs/Equip.",
        "Oil & Gas Refining & Marketing": "Oil/Gas Distribution",
        "Thermal Coal": "Coal & Related Energy",
        "Uranium": "Power",
        # Materials
        "Specialty Chemicals": "Chemical (Specialty)",
        "Chemicals": "Chemical (Diversified)",
        "Steel": "Steel",
        "Gold": "Precious Metals",
        "Other Precious Metals & Mining": "Precious Metals",
        "Industrial Metals & Minerals": "Metals & Mining",
        "Copper": "Metals & Mining",
        "Aluminum": "Metals & Mining",
        "Paper & Paper Products": "Paper/Forest Products",
        "Lumber & Wood Production": "Paper/Forest Products",
        # Utilities / Real Estate / Comms
        "Utilities - Regulated Electric": "Utility (General)",
        "Utilities - Regulated Water": "Utility (Water)",
        "Utilities - Diversified": "Utility (General)",
        "Utilities - Renewable": "Green & Renewable Energy",
        "REIT - Residential": "R.E.I.T.",
        "REIT - Industrial": "R.E.I.T.",
        "REIT - Retail": "Retail (REITs)",
        "REIT - Office": "R.E.I.T.",
        "REIT - Diversified": "R.E.I.T.",
        "REIT - Healthcare Facilities": "R.E.I.T.",
        "REIT - Specialty": "R.E.I.T.",
        "Real Estate Services": "Real Estate (Operations & Services)",
        "Real Estate - Development": "Real Estate (Development)",
        "Telecom Services": "Telecom. Services",
        "Entertainment": "Entertainment",
        "Advertising Agencies": "Advertising",
        "Broadcasting": "Broadcasting",
        "Publishing": "Publishing & Newspapers",
        "Education & Training Services": "Education",
        "Solar": "Green & Renewable Energy",
        "Packaging & Containers": "Packaging & Container",
        "Farm Products": "Farming/Agriculture",
    }

    # Direct yfinance industry match
    if yf_industry in yf_to_damodaran:
        return yf_to_damodaran[yf_industry]

    # yfinance sector → Damodaran keyword mapping for broader fuzzy matching
    sector_hints = {
        "Technology": ["Software", "Semiconductor", "Computer", "Electronics"],
        "Healthcare": ["Drugs", "Healthcare", "Hospitals", "Medical"],
        "Financial Services": ["Banks", "Insurance", "Financial", "Brokerage"],
        "Financials": ["Banks", "Insurance", "Financial", "Brokerage"],
        "Consumer Cyclical": ["Retail", "Auto", "Homebuilding", "Restaurant", "Apparel"],
        "Consumer Defensive": ["Beverage", "Food", "Household", "Tobacco"],
        "Energy": ["Oil/Gas", "Coal", "Power"],
        "Industrials": ["Machinery", "Aerospace", "Transportation", "Engineering"],
        "Communication Services": ["Telecom", "Entertainment", "Publishing"],
        "Utilities": ["Power", "Utility"],
        "Real Estate": ["REIT", "Real Estate"],
        "Basic Materials": ["Chemical", "Metals", "Mining", "Paper"],
    }

    # Try exact + fuzzy match on industry name first
    best_match = None
    best_score = 0.0

    search_terms = [yf_industry, yf_sector]

    # Add sector hints
    if yf_sector in sector_hints:
        search_terms.extend(sector_hints[yf_sector])

    for term in search_terms:
        if not term:
            continue
        term_lower = term.lower()
        for ind in industries:
            ind_lower = ind.lower()
            # Exact substring match
            if term_lower in ind_lower or ind_lower in term_lower:
                score = 0.8 + SequenceMatcher(None, term_lower, ind_lower).ratio() * 0.2
            else:
                score = SequenceMatcher(None, term_lower, ind_lower).ratio()

            # Boost if multiple word overlap
            term_words = set(term_lower.split())
            ind_words = set(ind_lower.replace("/", " ").replace("(", " ").replace(")", " ").split())
            word_overlap = len(term_words & ind_words)
            if word_overlap >= 2:
                score += 0.3
            elif word_overlap >= 1:
                score += 0.1

            if score > best_score:
                best_score = score
                best_match = ind

    if best_match and best_score > 0.35:
        return best_match

    return "Diversified"


# ── Orchestrator ────────────────────────────────────────────────────────────

def fetch_all_data(
    tickers: list[str],
    lookback_years: int = 2,
) -> dict:
    """Fetch all data needed for analysis. Returns prices, fundamentals, damodaran, warnings."""
    warnings = []
    period = f"{lookback_years}y"

    # Fetch prices (batch)
    try:
        prices = fetch_prices(tickers, period)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch prices: {e}")

    # Check which tickers actually have data
    valid_tickers = [t for t in tickers if t in prices.columns and prices[t].notna().sum() > 20]
    missing = set(tickers) - set(valid_tickers)
    if missing:
        warnings.append(f"No price data for: {', '.join(missing)}")
        prices = prices[valid_tickers]

    # Fetch fundamentals per ticker
    fundamentals = {}
    for t in valid_tickers:
        try:
            fundamentals[t] = fetch_fundamentals(t)
        except Exception as e:
            warnings.append(f"Failed to fetch fundamentals for {t}: {e}")
            fundamentals[t] = {}

    # Industry mappings
    industry_map = {}
    for t in valid_tickers:
        industry_map[t] = map_ticker_to_damodaran(t, fundamentals.get(t, {}))

    # Damodaran data
    damodaran = fetch_damodaran_betas()

    # Compute returns
    returns = prices.pct_change().dropna()

    return {
        "prices": prices,
        "returns": returns,
        "fundamentals": fundamentals,
        "industry_map": industry_map,
        "damodaran": damodaran,
        "valid_tickers": valid_tickers,
        "warnings": warnings,
    }

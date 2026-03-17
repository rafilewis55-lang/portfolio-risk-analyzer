// Portfolio Risk Analyzer — Frontend App

const FACTOR_LABELS = {
    interest_rate_risk: "Interest Rate Risk",
    china_revenue_risk: "China Revenue Risk",
    geopolitical_country_risk: "Geopolitical/Country Risk",
    currency_risk: "Currency Risk",
    regulatory_policy_risk: "Regulatory/Policy Risk",
    leverage_credit_risk: "Leverage/Credit Risk",
    earnings_cyclicality: "Earnings Cyclicality",
    sector_concentration: "Sector Concentration",
    supply_chain_concentration: "Supply Chain Concentration",
    esg_energy_transition_risk: "ESG/Energy Transition Risk",
};

const METRIC_TOOLTIPS = {
    risk_grade: "Letter grade (A-F) summarizing overall portfolio risk. A = low risk, F = very high risk. Based on the average of all 10 factor scores, weighted by your allocation.",
    hhi: "Herfindahl-Hirschman Index: sum of squared portfolio weights. Ranges from 1/N (perfectly equal) to 1.0 (single stock). Below 0.15 = well distributed, above 0.25 = concentrated.",
    n_eff: "Effective Number of Bets: how many truly independent risk sources your portfolio has, based on eigenvalue decomposition of the correlation matrix. A portfolio of 10 highly correlated stocks might only have N_eff of 2-3.",
    diversification_ratio: "Ratio of weighted-average individual volatilities to portfolio volatility. Always >= 1.0. Higher = more diversification benefit from combining holdings. DR of 1.0 means zero diversification benefit (perfect correlation).",
    portfolio_volatility: "Annualized standard deviation of portfolio returns, calculated from the covariance matrix and your weights. Represents the expected range of annual returns (~68% of outcomes fall within +/- this value).",
    distance_to_diversification: "How far the portfolio is from being well-diversified, on a 0-1 scale. 0.0 = fully diversified (N_eff meets benchmark of 30), 1.0 = single stock. Based on N_eff relative to an ideal benchmark.",
};

const FACTOR_TOOLTIPS = {
    interest_rate_risk: "Sensitivity to interest rate changes. High-duration assets (REITs, utilities, long-dated growth) score higher. Banks score high because rate moves directly affect net interest margins.",
    china_revenue_risk: "Estimated revenue exposure to China. Semiconductors, electronics, and luxury goods score highest (7-9). Domestic-focused services score lowest (1-3).",
    geopolitical_country_risk: "Exposure to emerging/frontier market instability, trade conflicts, and country-specific political risk. Based on Damodaran country equity risk premiums.",
    currency_risk: "Percentage of revenue earned in foreign currencies. Companies with high international sales face exchange rate volatility that can swing earnings.",
    regulatory_policy_risk: "Vulnerability to government regulation, antitrust action, or policy changes. Banks, healthcare, Big Tech, and energy face the most regulatory scrutiny.",
    leverage_credit_risk: "Derived from Damodaran D/E ratios. Higher leverage = more sensitivity to credit conditions and refinancing risk. Financial firms and utilities tend to score highest.",
    earnings_cyclicality: "Derived from Damodaran standard deviation of operating income. Measures how much earnings swing with economic cycles. Semiconductors, autos, and commodities are most cyclical.",
    sector_concentration: "Risk of GICS sector overlap in your portfolio. Multiple holdings in the same sector amplify sector-specific shocks (e.g., all-tech portfolios during a tech correction).",
    supply_chain_concentration: "Dependency on concentrated supply chains, particularly Taiwan/TSMC for semiconductors. Disruption risk from geopolitical events, natural disasters, or factory shutdowns.",
    esg_energy_transition_risk: "Exposure to fossil fuel dependency, carbon regulation, and energy transition costs. Oil/gas and coal score highest. Clean energy and software score lowest.",
};

function infoIcon(tooltipText) {
    return `<span class="info-icon">i<span class="tooltip">${tooltipText}</span></span>`;
}

let analysisData = null;

// Initialize with example portfolio
document.addEventListener("DOMContentLoaded", () => {
    const examples = [
        { ticker: "AAPL", weight: 20 },
        { ticker: "MSFT", weight: 20 },
        { ticker: "NVDA", weight: 20 },
        { ticker: "JPM", weight: 20 },
        { ticker: "XOM", weight: 20 },
    ];
    examples.forEach(e => addRow(e.ticker, e.weight));
    updateWeightStatus();
});

function addRow(ticker = "", weight = "") {
    const tbody = document.getElementById("holdingsBody");
    const row = document.createElement("tr");
    row.innerHTML = `
        <td><input type="text" class="ticker-input" placeholder="e.g. AAPL"
            value="${ticker}" oninput="updateWeightStatus()"></td>
        <td><input type="number" class="weight-input" placeholder="25"
            value="${weight}" min="0" max="100" step="0.1" oninput="updateWeightStatus()"></td>
        <td><button class="btn btn-danger" onclick="removeRow(this)">Remove</button></td>
    `;
    tbody.appendChild(row);
    updateWeightStatus();
}

function removeRow(btn) {
    btn.closest("tr").remove();
    updateWeightStatus();
}

function getHoldings() {
    const rows = document.querySelectorAll("#holdingsBody tr");
    const holdings = [];
    rows.forEach(row => {
        const ticker = row.querySelector(".ticker-input").value.trim().toUpperCase();
        const weight = parseFloat(row.querySelector(".weight-input").value) || 0;
        if (ticker && weight > 0) {
            holdings.push({ ticker, weight });
        }
    });
    return holdings;
}

function updateWeightStatus() {
    const holdings = getHoldings();
    const total = holdings.reduce((sum, h) => sum + h.weight, 0);
    const statusEl = document.getElementById("weightStatus");
    const btn = document.getElementById("analyzeBtn");

    if (holdings.length === 0) {
        statusEl.textContent = "Add at least one holding";
        statusEl.className = "weight-status weight-bad";
        btn.disabled = true;
    } else if (Math.abs(total - 100) > 0.5) {
        statusEl.textContent = `Weight sum: ${total.toFixed(1)}% (must equal 100%)`;
        statusEl.className = "weight-status weight-bad";
        btn.disabled = true;
    } else {
        statusEl.textContent = `Weight sum: ${total.toFixed(1)}%`;
        statusEl.className = "weight-status weight-ok";
        btn.disabled = false;
    }
}

async function analyze() {
    const holdings = getHoldings();
    if (holdings.length === 0) return;

    const tickers = holdings.map(h => h.ticker);
    const weights = holdings.map(h => h.weight / 100);

    document.getElementById("inputSection").style.display = "none";
    document.getElementById("loadingSection").style.display = "block";
    document.getElementById("resultsSection").classList.remove("active");
    document.getElementById("warningsSection").style.display = "none";

    try {
        const resp = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tickers, weights }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || "Analysis failed");
        }

        analysisData = await resp.json();
        renderResults(analysisData);
    } catch (err) {
        alert("Error: " + err.message);
        document.getElementById("inputSection").style.display = "block";
    } finally {
        document.getElementById("loadingSection").style.display = "none";
    }
}

function renderResults(data) {
    // Show warnings
    if (data.warnings && data.warnings.length > 0) {
        const wEl = document.getElementById("warningsSection");
        wEl.innerHTML = data.warnings.map(w => `<div>${w}</div>`).join("");
        wEl.style.display = "block";
    }

    renderScorecard(data);
    renderHeatmap(data);
    renderCorrelation(data);
    renderOverlaps(data);
    renderNarrative(data);

    document.getElementById("resultsSection").classList.add("active");
}

function renderScorecard(data) {
    const m = data.portfolio_metrics;
    const rf = data.risk_factors;
    const grid = document.getElementById("scorecardGrid");

    const grade = rf.risk_grade || "C";
    const gradeClass = `grade-${grade}`;

    grid.innerHTML = `
        <div class="metric-card">
            <div class="grade-badge ${gradeClass}">${grade}</div>
            <div class="label">Overall Risk Grade ${infoIcon(METRIC_TOOLTIPS.risk_grade)}</div>
            <div class="interpretation">Score: ${(rf.overall_score || 0).toFixed(1)}/10</div>
        </div>
        <div class="metric-card">
            <div class="value">${(m.hhi || 0).toFixed(4)}</div>
            <div class="label">HHI ${infoIcon(METRIC_TOOLTIPS.hhi)}</div>
            <div class="interpretation">${hhi_interp(m.hhi)}</div>
        </div>
        <div class="metric-card">
            <div class="value">${(m.n_eff || 0).toFixed(2)}</div>
            <div class="label">N<sub>eff</sub> (Effective Bets) ${infoIcon(METRIC_TOOLTIPS.n_eff)}</div>
            <div class="interpretation">of ${data.tickers.length} holdings</div>
        </div>
        <div class="metric-card">
            <div class="value">${(m.diversification_ratio || 0).toFixed(2)}</div>
            <div class="label">Diversification Ratio ${infoIcon(METRIC_TOOLTIPS.diversification_ratio)}</div>
            <div class="interpretation">${dr_interp(m.diversification_ratio)}</div>
        </div>
        <div class="metric-card">
            <div class="value">${((m.portfolio_volatility || 0) * 100).toFixed(1)}%</div>
            <div class="label">Portfolio Volatility (Ann.) ${infoIcon(METRIC_TOOLTIPS.portfolio_volatility)}</div>
        </div>
        <div class="metric-card">
            <div class="value">${(m.distance_to_diversification || 0).toFixed(2)}</div>
            <div class="label">Distance to Diversification ${infoIcon(METRIC_TOOLTIPS.distance_to_diversification)}</div>
            <div class="interpretation">${dist_interp(m.distance_to_diversification)}</div>
        </div>
    `;
}

function hhi_interp(hhi) {
    if (hhi >= 0.5) return "Highly concentrated";
    if (hhi >= 0.25) return "Moderately concentrated";
    if (hhi >= 0.15) return "Unconcentrated";
    return "Well distributed";
}

function dr_interp(dr) {
    if (dr >= 1.4) return "Strong benefit";
    if (dr >= 1.15) return "Moderate benefit";
    return "Limited benefit";
}

function dist_interp(d) {
    if (d <= 0.3) return "Close to diversified";
    if (d <= 0.6) return "Room to improve";
    return "Far from diversified";
}

function renderHeatmap(data) {
    const container = document.getElementById("heatmapContainer");
    const tickers = data.tickers;
    const perHolding = data.risk_factors.per_holding || {};
    const weighted = data.risk_factors.portfolio_weighted || {};
    const benchmark = data.risk_factors.benchmark || {};

    let html = '<table class="heatmap-table"><thead><tr><th>Factor</th>';
    tickers.forEach(t => html += `<th>${t}</th>`);
    html += '<th>Portfolio</th><th>S&P 500</th></tr></thead><tbody>';

    for (const [factor, label] of Object.entries(FACTOR_LABELS)) {
        const tip = FACTOR_TOOLTIPS[factor] || "";
        html += `<tr><td><div class="factor-label-cell">${label} ${tip ? infoIcon(tip) : ""}</div></td>`;
        tickers.forEach(t => {
            const score = (perHolding[t] || {})[factor] || 5;
            html += `<td class="score-${score}">${score}</td>`;
        });
        const pw = (weighted[factor] || 5).toFixed(1);
        const bm = benchmark[factor] || 5;
        html += `<td style="font-weight:700">${pw}</td>`;
        html += `<td>${bm}</td>`;
        html += '</tr>';
    }

    html += '</tbody></table>';
    container.innerHTML = html;
}

function renderCorrelation(data) {
    const container = document.getElementById("corrContainer");
    const tickers = data.tickers;
    const corr = data.portfolio_metrics.correlation_matrix || {};

    let html = '<table class="corr-table"><thead><tr><th></th>';
    tickers.forEach(t => html += `<th>${t}</th>`);
    html += '</tr></thead><tbody>';

    tickers.forEach(t1 => {
        html += `<tr><td style="background:var(--db-blue);color:white;font-weight:600">${t1}</td>`;
        tickers.forEach(t2 => {
            const val = (corr[t1] || {})[t2] || 0;
            const color = corrColor(val);
            html += `<td style="background:${color}">${val.toFixed(2)}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function corrColor(val) {
    // Green (negative) → White (0) → Red (positive)
    if (val >= 0) {
        const intensity = Math.min(val, 1);
        const r = 255;
        const g = Math.round(255 - intensity * 130);
        const b = Math.round(255 - intensity * 130);
        return `rgb(${r},${g},${b})`;
    } else {
        const intensity = Math.min(-val, 1);
        const r = Math.round(255 - intensity * 130);
        const g = 255;
        const b = Math.round(255 - intensity * 130);
        return `rgb(${r},${g},${b})`;
    }
}

function renderOverlaps(data) {
    const container = document.getElementById("overlapCards");
    const overlaps = data.overlaps || [];

    if (overlaps.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);font-style:italic">No significant risk overlaps detected.</p>';
        return;
    }

    container.innerHTML = overlaps.map(o => {
        const tip = FACTOR_TOOLTIPS[o.factor] || "";
        return `
        <div class="overlap-card ${o.severity}">
            <div class="overlap-severity">${o.severity}</div>
            <div class="overlap-info">
                <div class="factor-name">${o.factor_label} ${tip ? infoIcon(tip) : ""}</div>
                <div class="tickers">${o.tickers.join(", ")}</div>
            </div>
            <div class="overlap-stats">
                <div>Weight: ${(o.combined_weight * 100).toFixed(1)}%</div>
                <div>Avg Score: ${o.avg_score.toFixed(1)}/10</div>
            </div>
        </div>`;
    }).join("");
}

function renderNarrative(data) {
    const container = document.getElementById("narrativeText");
    const narrative = data.narrative || "No narrative generated.";

    // Convert markdown-like formatting to HTML
    const paragraphs = narrative.split("\n\n").filter(p => p.trim());
    container.innerHTML = paragraphs.map(p => {
        // Bold
        p = p.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Bullet points
        if (p.includes("  - ")) {
            const lines = p.split("\n").map(l => {
                l = l.trim();
                if (l.startsWith("- ")) {
                    return `<li>${l.substring(2)}</li>`;
                }
                return l;
            });
            return `<ul>${lines.join("")}</ul>`;
        }
        return `<p>${p}</p>`;
    }).join("");
}

async function downloadExcel() {
    if (!analysisData) return;

    const holdings = getHoldingsFromAnalysis();
    try {
        const resp = await fetch("/api/analyze/excel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(holdings),
        });
        const blob = await resp.blob();
        downloadBlob(blob, "portfolio_risk_analysis.xlsx");
    } catch (err) {
        alert("Download failed: " + err.message);
    }
}

async function downloadPDF() {
    if (!analysisData) return;

    const holdings = getHoldingsFromAnalysis();
    try {
        const resp = await fetch("/api/analyze/pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(holdings),
        });
        const blob = await resp.blob();
        downloadBlob(blob, "portfolio_risk_analysis.pdf");
    } catch (err) {
        alert("Download failed: " + err.message);
    }
}

function getHoldingsFromAnalysis() {
    if (!analysisData) return {};
    return {
        tickers: analysisData.tickers,
        weights: analysisData.tickers.map(t => analysisData.weights[t]),
    };
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function resetView() {
    document.getElementById("inputSection").style.display = "block";
    document.getElementById("resultsSection").classList.remove("active");
    document.getElementById("warningsSection").style.display = "none";
    analysisData = null;
}


// ── File Upload ────────────────────────────────────────────────────────────

let uploadedHoldings = [];

function switchInputTab(tab) {
    document.querySelectorAll('.input-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.input-tab-content').forEach(t => t.classList.remove('active'));

    if (tab === 'manual') {
        document.querySelectorAll('.input-tab')[0].classList.add('active');
        document.getElementById('manualTab').classList.add('active');
    } else {
        document.querySelectorAll('.input-tab')[1].classList.add('active');
        document.getElementById('uploadTab').classList.add('active');
    }
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) processFile(file);
}

async function processFile(file) {
    const errorEl = document.getElementById('uploadError');
    const previewEl = document.getElementById('uploadPreview');
    const areaEl = document.getElementById('uploadArea');
    errorEl.style.display = 'none';
    previewEl.style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/parse-portfolio', {
            method: 'POST',
            body: formData,
        });

        const data = await resp.json();

        if (!resp.ok || data.error) {
            errorEl.textContent = data.error || 'Failed to parse file';
            errorEl.style.display = 'block';
            return;
        }

        uploadedHoldings = data.holdings;
        renderUploadPreview(data.holdings, data.filename);
        areaEl.style.display = 'none';
        previewEl.style.display = 'block';

    } catch (err) {
        errorEl.textContent = 'Error uploading file: ' + err.message;
        errorEl.style.display = 'block';
    }
}

function renderUploadPreview(holdings, filename) {
    document.getElementById('uploadFileName').textContent = filename + ` (${holdings.length} holdings found)`;

    const tbody = document.getElementById('uploadBody');
    tbody.innerHTML = '';

    let total = 0;
    holdings.forEach((h, i) => {
        total += h.weight;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align:center;color:var(--text-muted);font-size:0.8rem">${i + 1}</td>
            <td><strong>${h.ticker}</strong></td>
            <td>${h.weight}%</td>
        `;
        tbody.appendChild(tr);
    });

    const statusEl = document.getElementById('uploadWeightStatus');
    const btn = document.getElementById('uploadAnalyzeBtn');

    if (Math.abs(total - 100) > 0.5) {
        statusEl.textContent = `Weight sum: ${total.toFixed(1)}% (must equal 100%)`;
        statusEl.className = 'weight-status weight-bad';
        btn.disabled = true;
    } else {
        statusEl.textContent = `Weight sum: ${total.toFixed(1)}%`;
        statusEl.className = 'weight-status weight-ok';
        btn.disabled = false;
    }
}

function clearUpload() {
    uploadedHoldings = [];
    document.getElementById('uploadPreview').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'flex';
    document.getElementById('uploadError').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

function loadUploadToManual() {
    // Clear existing manual rows
    document.getElementById('holdingsBody').innerHTML = '';

    // Add uploaded holdings to manual entry
    uploadedHoldings.forEach(h => addRow(h.ticker, h.weight));
    updateWeightStatus();

    // Switch to manual tab
    switchInputTab('manual');
    clearUpload();
}

async function analyzeUpload() {
    if (uploadedHoldings.length === 0) return;

    const tickers = uploadedHoldings.map(h => h.ticker);
    const weights = uploadedHoldings.map(h => h.weight / 100);

    document.getElementById('inputSection').style.display = 'none';
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('resultsSection').classList.remove('active');
    document.getElementById('warningsSection').style.display = 'none';

    try {
        const resp = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers, weights }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.error || 'Analysis failed');
        }

        analysisData = await resp.json();
        renderResults(analysisData);
    } catch (err) {
        alert('Error: ' + err.message);
        document.getElementById('inputSection').style.display = 'block';
    } finally {
        document.getElementById('loadingSection').style.display = 'none';
    }
}

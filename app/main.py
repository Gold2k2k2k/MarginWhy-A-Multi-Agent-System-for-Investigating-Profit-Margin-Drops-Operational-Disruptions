import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from .agents.orchestrator import MarginWhyOrchestrator

app = FastAPI(
    title="MarginWhy API & Executive Dashboard",
    description="Multi-Agent Root-Cause Investigation for Retail Profit Drops & Operational Disruptions",
    version="1.0.0"
)

# In-memory orchestrator instance for stateful interactive inspection
orchestrator = MarginWhyOrchestrator(sample_mode=True)


class RunRequest(BaseModel):
    query: Optional[str] = None
    scenario_file: Optional[str] = None
    sample_mode: Optional[bool] = True


@app.get("/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "HEALTHY",
        "system": "MarginWhy",
        "version": "1.0.0",
        "hmem_status": "READY",
        "track": "Track 02: The Agent That Can Explain Why",
        "model": os.getenv("NVIDIA_MODEL_NAME", "nvidia/nemotron-3-super-120b-a12b"),
        "sample_mode": os.getenv("SAMPLE_MODE", "true").lower() == "true",
        "records_in_memory": len(orchestrator.hmem.records),
        "trust_ledger_mutations": len(orchestrator.hmem.trust_ledger)
    }


@app.get("/api/scenarios")
def list_scenarios() -> List[Dict[str, Any]]:
    samples_dir = Path(__file__).resolve().parent.parent / "data" / "samples"
    scenarios = []
    if samples_dir.exists():
        for f in sorted(samples_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    scenarios.append({
                        "id": data.get("scenario_id", f.stem),
                        "file": f.name,
                        "filename": f.name,
                        "title": data.get("title", f.stem),
                        "description": data.get("query", ""),
                        "query": data.get("query", ""),
                        "category": data.get("category", "General"),
                        "margin_drop_pct": data.get("reported_margin_drop_pct", 0.0)
                    })
            except Exception:
                continue
    return scenarios


@app.get("/api/trace")
def get_trace_log(limit: int = 50) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    log_file = Path(__file__).resolve().parent.parent / "logs" / "trace.jsonl"
    if not log_file.exists():
        return []
    events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    return events[-limit:]


@app.get("/api/hmem")
def get_hmem_state() -> Dict[str, Any]:
    carryover = orchestrator.hmem.build_markovian_carryover()
    return {
        "carryover": carryover,
        "trust_ledger_count": len(orchestrator.hmem.trust_ledger),
        "recent_ledger": orchestrator.hmem.trust_ledger[-10:],
        "all_records": [r.to_dict() for r in orchestrator.hmem.records.values()]
    }


@app.post("/run")
def run_investigation(req: RunRequest) -> Dict[str, Any]:
    scenario = req.scenario_file
    query = req.query

    # Validate scenario_file against directory traversal
    if scenario:
        if ".." in scenario or "/" in scenario or "\\" in scenario:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scenario_file '{scenario}': path traversal is not permitted."
            )

    # If scenario not specified, infer from query keywords if query is present
    if not scenario and query:
        q_lower = query.lower()
        if "apparel" in q_lower:
            scenario = "scenario_2_apparel_returns.json"
        elif "shipping" in q_lower or "freight" in q_lower or "logistics" in q_lower:
            scenario = "scenario_3_shipping_delay.json"
        else:
            scenario = "scenario_1_electronics_q3.json"
    elif not scenario:
        scenario = "scenario_1_electronics_q3.json"

    # Configure sample mode if provided
    if req.sample_mode is not None:
        orchestrator.sample_mode = req.sample_mode
        if req.sample_mode:
            os.environ["SAMPLE_MODE"] = "true"
        else:
            os.environ["SAMPLE_MODE"] = "false"

    # Load query from scenario if query not explicitly provided
    if not query:
        sample_path = Path(__file__).resolve().parent.parent / "data" / "samples" / scenario
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
                query = bundle.get("query", "Investigate profit margin anomaly")
        else:
            query = "Why did net profit margin for Electronics drop 18.5% in Q3?"

    res = orchestrator.run_investigation(query=query, scenario_file=scenario)
    return {
        "status": "SUCCESS",
        "query": res["query"],
        "scenario_file": res["scenario_file"],
        "turns": res["turns_executed"],
        "turns_executed": res["turns_executed"],
        "approved_claims": res["approved_claims"],
        "report": res["report_markdown"],
        "report_markdown": res["report_markdown"],
        "hmem_state": res["hmem_state"],
        "trust_ledger": res["trust_ledger"],
        "trace_events": res["trace_events"][-10:]
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Delivers the Executive Multi-Agent Root-Cause Diagnostic Dashboard."""
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MarginWhy — Executive Multi-Agent Root-Cause Dashboard</title>
  <meta name="description" content="Non-linear multi-agent adversarial critic system for root-cause profit margin drop investigation.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #060913;
      --bg-surface: #0d1224;
      --bg-surface-elevated: #151c36;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.25);
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.2);
      --warning: #f59e0b;
      --danger: #f43f5e;
      --danger-glow: rgba(244, 63, 94, 0.2);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --nvidia-green: #76b900;
      --zetaris-blue: #0080ff;
      --meterless-purple: #a855f7;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      line-height: 1.6;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
        radial-gradient(circle at 85% 25%, rgba(168, 85, 247, 0.10) 0%, transparent 45%),
        radial-gradient(circle at 50% 85%, rgba(16, 185, 129, 0.08) 0%, transparent 50%);
      background-attachment: fixed;
    }

    /* Top Navigation */
    header {
      border-bottom: 1px solid var(--border-subtle);
      background: rgba(13, 18, 36, 0.75);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 50;
      padding: 1rem 2rem;
    }

    .nav-container {
      max-width: 1440px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), var(--meterless-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.15rem;
      box-shadow: 0 4px 14px var(--primary-glow);
    }

    .brand-title {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .brand-tag {
      font-size: 0.72rem;
      text-transform: uppercase;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      background: rgba(99, 102, 241, 0.18);
      border: 1px solid rgba(99, 102, 241, 0.35);
      color: #c7d2fe;
      font-weight: 600;
      letter-spacing: 0.05em;
    }

    .badges {
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .badge {
      font-size: 0.75rem;
      padding: 0.3rem 0.65rem;
      border-radius: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      gap: 0.4rem;
      font-weight: 500;
    }

    .badge.nvidia { border-color: rgba(118, 185, 0, 0.4); color: #d9f99d; }
    .badge.zetaris { border-color: rgba(0, 128, 255, 0.4); color: #93c5fd; }
    .badge.meterless { border-color: rgba(168, 85, 247, 0.4); color: #e9d5ff; }

    /* Main Container */
    main {
      max-width: 1440px;
      margin: 2rem auto;
      padding: 0 2rem;
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 2rem;
    }

    /* Control Panel (Left Column) */
    .panel {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .panel-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: #f1f5f9;
    }

    .form-group {
      margin-bottom: 1.25rem;
    }

    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 0.45rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    select, textarea, input {
      width: 100%;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 0.75rem 1rem;
      color: var(--text-main);
      font-size: 0.88rem;
      font-family: inherit;
      transition: all 0.2s ease;
    }

    select:focus, textarea:focus, input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--primary-glow);
    }

    textarea {
      resize: vertical;
      min-height: 95px;
    }

    .btn-run {
      width: 100%;
      background: linear-gradient(135deg, var(--primary), #4338ca);
      color: #ffffff;
      border: none;
      border-radius: 10px;
      padding: 0.9rem 1.5rem;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.6rem;
      box-shadow: 0 4px 18px var(--primary-glow);
      transition: all 0.25s ease;
    }

    .btn-run:hover {
      background: linear-gradient(135deg, #4f46e5, #3730a3);
      transform: translateY(-2px);
      box-shadow: 0 6px 24px var(--primary-glow);
    }

    .btn-run:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }

    /* Memory / Engine Stats */
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      margin-top: 1.25rem;
    }

    .stat-card {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 0.85rem;
      text-align: center;
    }

    .stat-value {
      font-size: 1.35rem;
      font-weight: 700;
      color: #ffffff;
      font-family: 'JetBrains Mono', monospace;
    }

    .stat-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-top: 0.2rem;
    }

    /* Right Column: Execution Stage & Results */
    .stage-section {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    /* Multi-Agent Loop Stepper */
    .loop-stepper {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }

    .agent-step {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 1.15rem;
      position: relative;
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .agent-step.active {
      border-color: var(--primary);
      box-shadow: 0 4px 20px var(--primary-glow);
    }

    .agent-step.blocked {
      border-color: var(--danger);
      background: linear-gradient(180deg, rgba(244, 63, 94, 0.08) 0%, var(--bg-surface) 100%);
    }

    .agent-step.approved {
      border-color: var(--success);
      background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--bg-surface) 100%);
    }

    .agent-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: var(--bg-surface-elevated);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
      margin-bottom: 0.65rem;
    }

    .agent-name {
      font-size: 0.88rem;
      font-weight: 700;
      color: #ffffff;
    }

    .agent-role {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }

    .agent-status-tag {
      margin-top: 0.75rem;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 5px;
      display: inline-block;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .status-standby { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; }
    .status-running { background: rgba(99, 102, 241, 0.25); color: #a5b4fc; }
    .status-blocked { background: rgba(244, 63, 94, 0.25); color: #fda4af; }
    .status-verified { background: rgba(16, 185, 129, 0.25); color: #6ee7b7; }

    /* Results Tabs */
    .tabs-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .tabs-header {
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: rgba(13, 18, 36, 0.5);
      padding: 0 1.5rem;
    }

    .tab-btn {
      padding: 1rem 1.25rem;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s ease;
    }

    .tab-btn:hover {
      color: var(--text-main);
    }

    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }

    .tab-content {
      padding: 1.5rem;
      min-height: 400px;
    }

    /* Report View */
    .markdown-body {
      font-size: 0.92rem;
      color: #e2e8f0;
    }

    .markdown-body h1 {
      font-size: 1.35rem;
      margin-bottom: 0.75rem;
      color: #ffffff;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 0.5rem;
    }

    .markdown-body h2 {
      font-size: 1.1rem;
      margin-top: 1.5rem;
      margin-bottom: 0.5rem;
      color: #a5b4fc;
    }

    .markdown-body h3 {
      font-size: 0.95rem;
      margin-top: 1rem;
      margin-bottom: 0.4rem;
      color: #f1f5f9;
    }

    .markdown-body p {
      margin-bottom: 0.85rem;
      color: #cbd5e1;
    }

    .markdown-body blockquote {
      border-left: 3px solid var(--success);
      padding: 0.75rem 1rem;
      background: rgba(16, 185, 129, 0.08);
      border-radius: 0 8px 8px 0;
      margin-bottom: 1rem;
      font-style: italic;
      color: #d1fae5;
    }

    .markdown-body ul {
      margin-left: 1.25rem;
      margin-bottom: 1rem;
    }

    .markdown-body li {
      margin-bottom: 0.4rem;
    }

    .markdown-body code {
      background: var(--bg-surface-elevated);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      color: #e0e7ff;
    }

    /* Trace Log Stream */
    .trace-list {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
    }

    .trace-item {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 0.85rem 1.15rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .trace-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .trace-agent {
      font-weight: 700;
      color: #818cf8;
    }

    .trace-event {
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 700;
    }

    .ev-blocked { background: rgba(244, 63, 94, 0.2); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.35); }
    .ev-approved { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.35); }
    .ev-plan { background: rgba(99, 102, 241, 0.2); color: #6366f1; border: 1px solid rgba(99, 102, 241, 0.35); }
    .ev-query { background: rgba(0, 128, 255, 0.2); color: #0080ff; border: 1px solid rgba(0, 128, 255, 0.35); }

    .trace-body {
      color: #cbd5e1;
      font-size: 0.8rem;
    }

    /* Trust Ledger Table */
    .table-responsive {
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }

    th {
      text-align: left;
      padding: 0.75rem;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.72rem;
    }

    td {
      padding: 0.75rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: #e2e8f0;
      font-family: 'JetBrains Mono', monospace;
    }

    /* Pulse animation */
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .pulse {
      animation: pulse 1.5s infinite;
    }
  </style>
</head>
<body>

  <!-- Top Header Navigation -->
  <header>
    <div class="nav-container">
      <div class="brand">
        <div class="brand-logo">MW</div>
        <div>
          <div class="brand-title">MarginWhy</div>
          <div style="font-size: 0.72rem; color: var(--text-muted);">Root-Cause Anomaly Investigation System</div>
        </div>
        <span class="brand-tag">Track 02 — The Agent That Can Explain Why</span>
      </div>
      <div class="badges">
        <div class="badge nvidia"><span>●</span> NVIDIA Nemotron-3 Super 120B</div>
        <div class="badge zetaris"><span>●</span> Zetaris Lightning SQL</div>
        <div class="badge meterless"><span>●</span> Meterless H-MEM</div>
      </div>
    </div>
  </header>

  <!-- Main Grid Workspace -->
  <main>
    <!-- Left Column: Controls & Parameters -->
    <div class="panel">
      <div class="panel-title">
        <span>Investigation Control</span>
        <span style="font-size: 0.75rem; color: var(--success);">Online / Ready</span>
      </div>

      <div class="form-group">
        <label for="scenarioSelect">Benchmark Dataset Scenario</label>
        <select id="scenarioSelect" onchange="onScenarioChange()">
          <option value="scenario_1_electronics_q3.json">Scenario 1: Electronics Q3 Profit Margin Drop (-18.5%)</option>
          <option value="scenario_2_apparel_returns.json">Scenario 2: Apparel Fall-Winter Catalog Slump (-14.2%)</option>
          <option value="scenario_3_shipping_delay.json">Scenario 3: Suburban Freight Cost Overrun (+22.0%)</option>
        </select>
      </div>

      <div class="form-group">
        <label for="queryInput">Business Question / Prompt</label>
        <textarea id="queryInput" placeholder="Enter inquiry...">Why did net profit margin for Electronics drop 18.5% in Q3?</textarea>
      </div>

      <button id="btnRun" class="btn-run" onclick="triggerInvestigation()">
        <span id="btnIcon">⚡</span>
        <span id="btnText">Launch Adversarial Investigation</span>
      </button>

      <div class="stats-grid">
        <div class="stat-card">
          <div id="statTurns" class="stat-value">2</div>
          <div class="stat-label">Critic Turns</div>
        </div>
        <div class="stat-card">
          <div id="statConfidence" class="stat-value" style="color: var(--success);">91%</div>
          <div class="stat-label">Causal Confidence</div>
        </div>
        <div class="stat-card">
          <div id="statMemoryTiers" class="stat-value">3 Tiers</div>
          <div class="stat-label">H-MEM Active</div>
        </div>
        <div class="stat-card">
          <div id="statLedgerMutations" class="stat-value">14</div>
          <div class="stat-label">Trust Ledger Events</div>
        </div>
      </div>

      <div style="margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border-subtle);">
        <label>Primary Sponsors Integration</label>
        <p style="font-size: 0.75rem; color: var(--text-dim); line-height: 1.4;">
          Queries execute against Zetaris AI Data Harness (TPCDS_DB & NY_TAXI). Hypotheses and branch rejections are permanently recorded into Meterless H-MEM living knowledge graph.
        </p>
      </div>
    </div>

    <!-- Right Column: Multi-Agent Debate & Executive Diagnosis -->
    <div class="stage-section">

      <!-- 4-Agent Stepper Pipeline -->
      <div class="loop-stepper">
        <div id="agentPlanner" class="agent-step approved">
          <div class="agent-icon" style="color: #818cf8;">🧠</div>
          <div class="agent-name">HypothesisPlanner</div>
          <div class="agent-role">Markovian Carryover & Branching</div>
          <div id="tagPlanner" class="agent-status-tag status-verified">Turn 2: H2_H3 Planned</div>
        </div>

        <div id="agentRetriever" class="agent-step approved">
          <div class="agent-icon" style="color: #60a5fa;">⚡</div>
          <div class="agent-name">ZetarisRetriever</div>
          <div class="agent-role">Lightning SQL + Timeout Guard</div>
          <div id="tagRetriever" class="agent-status-tag status-verified">SQL Verified (5 rows)</div>
        </div>

        <div id="agentCritic" class="agent-step approved">
          <div class="agent-icon" style="color: #34d399;">🛡️</div>
          <div class="agent-name">SkepticalCritic</div>
          <div class="agent-role">NVIDIA Nemotron-3 Super 120B</div>
          <div id="tagCritic" class="agent-status-tag status-verified">Score: 0.91 (Approved)</div>
        </div>

        <div id="agentWriter" class="agent-step approved">
          <div class="agent-icon" style="color: #f472b6;">📄</div>
          <div class="agent-name">ActionReportWriter</div>
          <div class="agent-role">Synthesis & Mitigation Roadmap</div>
          <div id="tagWriter" class="agent-status-tag status-verified">Report Ready</div>
        </div>
      </div>

      <!-- Results & Details Tabs -->
      <div class="tabs-card">
        <div class="tabs-header">
          <button id="tabBtnReport" class="tab-btn active" onclick="switchTab('report')">
            <span>📄</span> Executive Root-Cause Report
          </button>
          <button id="tabBtnTrace" class="tab-btn" onclick="switchTab('trace')">
            <span>📡</span> Live Audit Trace Log
          </button>
          <button id="tabBtnHMem" class="tab-btn" onclick="switchTab('hmem')">
            <span>🧠</span> H-MEM Living Knowledge Graph
          </button>
        </div>

        <div class="tab-content">
          <!-- Tab 1: Executive Diagnosis Report -->
          <div id="tabReport" class="markdown-body">
            <h1>Executive Root-Cause Diagnostic Report: Profit Margin Anomaly</h1>
            <p><strong>Business Inquiry:</strong> <code>Why did net profit margin for Electronics drop 18.5% in Q3?</code></p>
            <p><strong>Primary Track:</strong> Track 02 — The Agent That Can Explain Why | <strong>Auditing Model:</strong> <code>nvidia/nemotron-3-super-120b-a12b</code></p>
            
            <h2>1. Executive Summary & Verified Root Cause</h2>
            <blockquote>
              Cross-silo evidence confirms Northeast Distribution Center (warehouse_sk=1) inventory collapsed by 84% (down to 64-120 units vs baseline of 1,500 units). Urban delivery congestion documented in NY_TAXI (trip duration up 34% to 49.8 mins) triggered 2,410 customer order cancellations and forced $39.50/unit expedited freight courier surcharges. Combined financial impact explains 17.8% of the 18.5% net margin drop.
            </blockquote>

            <h2>2. Evidence Cross-Examination & Refuted Hypotheses</h2>
            <ul>
              <li><strong>H1 [Confidence: 0.42 - REFUTED]:</strong> National return rate in <code>TPCDS_DB.web_returns</code> increased by only 1.2% year-over-year ($103,400 total return volume), which mathematically accounts for less than 1.1% of the observed $1.85M (18.5%) margin contraction. Critic issued <code>CLAIM_BLOCKED</code> and forced orthogonal cross-silo branching.</li>
              <li><strong>H2_H3_COMBINED [Confidence: 0.91 - APPROVED]:</strong> Verified correlation between <code>TPCDS_DB.inventory</code> stockouts and <code>NY_TAXI.trip_data</code> urban arterial congestion spikes.</li>
            </ul>

            <h2>3. Prioritized Operational Mitigations</h2>
            <ul>
              <li><strong>Immediate (0-30 Days):</strong> Re-index safety stock buffer thresholds across Northeast regional hubs and cap emergency courier dispatch surge rates.</li>
              <li><strong>Strategic (30-90 Days):</strong> Ingest municipal traffic feeds into automated fulfillment logic to prioritize off-peak dispatch windows.</li>
            </ul>

            <h2>4. Caveats & Data Limitations</h2>
            <p>Timeframe bounds restricted to available historical quarterly periods. Exogenous promotional matching was unobserved in accessible relational schemas.</p>
          </div>

          <!-- Tab 2: Audit Trace Stream -->
          <div id="tabTrace" style="display: none;">
            <div id="traceContainer" class="trace-list">
              <!-- Loaded via JavaScript -->
            </div>
          </div>

          <!-- Tab 3: H-MEM Living Knowledge Graph & Ledger -->
          <div id="tabHMem" style="display: none;">
            <h3 style="font-size: 0.95rem; margin-bottom: 0.75rem; color: #a5b4fc;">Meterless H-MEM Trust Ledger & Lineage Audit Trail</h3>
            <div class="table-responsive">
              <table id="ledgerTable">
                <thead>
                  <tr>
                    <th>Timestamp (UTC)</th>
                    <th>Action</th>
                    <th>Record ID</th>
                    <th>Audit Details</th>
                  </tr>
                </thead>
                <tbody id="ledgerBody">
                  <!-- Loaded via JavaScript -->
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>

    </div>
  </main>

  <script>
    const scenarios = {
      "scenario_1_electronics_q3.json": "Why did net profit margin for Electronics drop 18.5% in Q3?",
      "scenario_2_apparel_returns.json": "Why did Fall-Winter apparel net revenue decline by 14.2% across catalog channels?",
      "scenario_3_shipping_delay.json": "Why did suburban retail logistics freight costs exceed budget by 22%?"
    };

    function onScenarioChange() {
      const select = document.getElementById("scenarioSelect");
      const query = scenarios[select.value] || "";
      document.getElementById("queryInput").value = query;
    }

    function switchTab(tabName) {
      document.getElementById("tabReport").style.display = tabName === 'report' ? 'block' : 'none';
      document.getElementById("tabTrace").style.display = tabName === 'trace' ? 'block' : 'none';
      document.getElementById("tabHMem").style.display = tabName === 'hmem' ? 'block' : 'none';

      document.getElementById("tabBtnReport").classList.toggle('active', tabName === 'report');
      document.getElementById("tabBtnTrace").classList.toggle('active', tabName === 'trace');
      document.getElementById("tabBtnHMem").classList.toggle('active', tabName === 'hmem');

      if (tabName === 'trace') loadTrace();
      if (tabName === 'hmem') loadHMem();
    }

    async function loadTrace() {
      try {
        const resp = await fetch("/api/trace");
        const events = await resp.json();
        const container = document.getElementById("traceContainer");
        container.innerHTML = "";
        
        events.forEach(e => {
          let badgeClass = "ev-plan";
          if (e.event === "CLAIM_BLOCKED") badgeClass = "ev-blocked";
          else if (e.event === "APPROVED_CLAIM") badgeClass = "ev-approved";
          else if (e.event === "ZETARIS_QUERY_EXECUTED") badgeClass = "ev-query";

          const item = document.createElement("div");
          item.className = "trace-item";
          item.innerHTML = `
            <div class="trace-header">
              <span class="trace-agent">${e.agent || "System"}</span>
              <span class="trace-event ${badgeClass}">${e.event || "EVENT"}</span>
            </div>
            <div class="trace-body">
              ${e.sql_query ? `<div><strong>SQL:</strong> <code>${escapeHtml(e.sql_query)}</code></div>` : ""}
              ${e.reasoning ? `<div><strong>Reasoning:</strong> ${escapeHtml(e.reasoning)}</div>` : ""}
              ${e.confidence_score !== undefined ? `<div><strong>Confidence:</strong> ${(e.confidence_score * 100).toFixed(1)}%</div>` : ""}
            </div>
          `;
          container.appendChild(item);
        });
      } catch (err) {
        console.error("Error loading trace:", err);
      }
    }

    async function loadHMem() {
      try {
        const resp = await fetch("/api/hmem");
        const data = await resp.json();
        const tbody = document.getElementById("ledgerBody");
        tbody.innerHTML = "";

        const ledger = data.recent_ledger || [];
        ledger.forEach(item => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td style="color: #94a3b8;">${item.timestamp.split(".")[0].replace("T", " ")}</td>
            <td><strong style="color: #818cf8;">${item.action}</strong></td>
            <td><code>${item.record_id}</code></td>
            <td style="color: #cbd5e1; font-size: 0.78rem;">${JSON.stringify(item.details)}</td>
          `;
          tbody.appendChild(tr);
        });
      } catch (err) {
        console.error("Error loading H-MEM:", err);
      }
    }

    async function triggerInvestigation() {
      const btn = document.getElementById("btnRun");
      const btnText = document.getElementById("btnText");
      const btnIcon = document.getElementById("btnIcon");
      const scenario = document.getElementById("scenarioSelect").value;
      const query = document.getElementById("queryInput").value;

      btn.disabled = true;
      btnIcon.textContent = "⏳";
      btnText.textContent = "Auditing Hypotheses Across Silos...";

      try {
        const resp = await fetch("/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, scenario_file: scenario })
        });
        const res = await resp.json();

        // Update stats
        document.getElementById("statTurns").textContent = res.turns_executed;
        const claim = (res.approved_claims || [])[0] || {};
        const conf = claim.confidence_score ? `${(claim.confidence_score * 100).toFixed(0)}%` : "91%";
        document.getElementById("statConfidence").textContent = conf;

        // Render report
        renderMarkdown(res.report_markdown);

        // Switch to report tab
        switchTab('report');
      } catch (err) {
        alert("Investigation error: " + err);
      } finally {
        btn.disabled = false;
        btnIcon.textContent = "⚡";
        btnText.textContent = "Launch Adversarial Investigation";
      }
    }

    function renderMarkdown(md) {
      // Basic markdown converter for clean executive presentation
      let html = md
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`([^`]+)`/gim, '<code>$1</code>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/gim, '<br>');
      
      document.getElementById("tabReport").innerHTML = html;
    }

    function escapeHtml(text) {
      return text ? text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : "";
    }
  </script>
</body>
</html>
"""

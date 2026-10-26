"""Interactive Strategic Slide Deck Generator for MarginWhy.

Fulfills Hackathon Section 3.2 Slide Deck Requirements:
1. Problem & Target Users (Retail Operations & Merchandising Lead, $1.85M Margin Contraction)
2. Solution (Non-Linear Multi-Agent Adversarial System)
3. Agent Workflow & Iterative Architecture (Planner -> Retriever -> Critic -> Synthesizer)
4. Technical Stack (FastAPI, H-MEM, Zetaris Lightning SQL, NVIDIA Nemotron, Nightshift)
5. How Zetaris & Meterless were used (Zetaris AI Data Harness & Meterless H-MEM + Markovian Carryover)
6. What was unique about sponsor technology usage (SkepticalCritic Arbitration, Trust Ledger, String Coercion)
7. Product Visuals (Executive Command Console, SVG Waterfall Bridge, What-If Recovery Simulator)
8. Future Enhancements & Production Roadmap (Real-time telemetry, automated PO, Monte Carlo simulation)
"""

SLIDES_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MarginWhy — Executive Hackathon Presentation Deck</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #020617;
      --bg-surface: #0b1120;
      --bg-card: #0f172a;
      --bg-elevated: #1e293b;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-strong: rgba(255, 255, 255, 0.16);
      --primary: #6366f1;
      --primary-glow: rgba(99, 102, 241, 0.35);
      --info: #38bdf8;
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
      --purple: #c084fc;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      overflow: hidden;
      height: 100vh;
      width: 100vw;
      display: flex;
      flex-direction: column;
      user-select: none;
    }

    /* TOP BAR */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.85rem 2rem;
      background: rgba(11, 17, 32, 0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-subtle);
      z-index: 50;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .brand-logo {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: linear-gradient(135deg, var(--primary), var(--purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 0.95rem;
      color: #fff;
    }

    .brand-title {
      font-size: 1.15rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .brand-pill {
      font-size: 0.68rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      background: rgba(99, 102, 241, 0.18);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #c7d2fe;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .nav-btn {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s;
    }

    .nav-btn:hover {
      border-color: var(--primary);
      background: var(--bg-elevated);
      transform: translateY(-1px);
    }

    /* SLIDE CONTAINER */
    .deck-container {
      flex: 1;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }

    .slide {
      position: absolute;
      width: min(1200px, 92vw);
      height: min(680px, 80vh);
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 18px;
      padding: 2.75rem 3.25rem;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05);
      opacity: 0;
      pointer-events: none;
      transform: scale(0.96) translateX(40px);
      transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .slide.active {
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateX(0);
      z-index: 10;
    }

    .slide.previous {
      opacity: 0;
      pointer-events: none;
      transform: scale(0.96) translateX(-40px);
    }

    /* SLIDE HEADER & TYPOGRAPHY */
    .slide-tag {
      font-size: 0.72rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--info);
      margin-bottom: 0.4rem;
      display: flex;
      align-items: center;
      gap: 0.45rem;
    }

    .slide-title {
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      color: #ffffff;
      line-height: 1.2;
      margin-bottom: 0.65rem;
    }

    .slide-subtitle {
      font-size: 0.95rem;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 1.75rem;
    }

    /* SLIDE CONTENT GRIDS */
    .slide-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.25rem;
    }

    .grid-4 {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 1.25rem 1.4rem;
      display: flex;
      flex-direction: column;
      transition: all 0.2s;
    }

    .card:hover {
      border-color: var(--border-strong);
      transform: translateY(-2px);
    }

    .card-title {
      font-size: 1rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 0.45rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .card-text {
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.55;
    }

    .metric-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.85rem;
      font-weight: 800;
      color: #4ade80;
      margin: 0.5rem 0 0.25rem;
    }

    .metric-badge.danger { color: #f87171; }
    .metric-badge.info { color: #38bdf8; }
    .metric-badge.purple { color: #c084fc; }

    /* CODE BOX */
    .code-box {
      background: #020617;
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.74rem;
      color: #cbd5e1;
      overflow-x: auto;
      line-height: 1.5;
    }

    /* FOOTER CONTROLS */
    footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.85rem 2.5rem;
      background: rgba(11, 17, 32, 0.95);
      border-top: 1px solid var(--border-subtle);
      z-index: 50;
    }

    .progress-bar-container {
      flex: 1;
      max-width: 480px;
      height: 4px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 2px;
      margin: 0 1.5rem;
      overflow: hidden;
    }

    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--primary), var(--info));
      width: 12.5%;
      transition: width 0.3s ease;
    }

    .controls {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }

    .ctrl-btn {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
    }

    .ctrl-btn:hover {
      border-color: var(--primary);
      background: var(--bg-elevated);
      color: #fff;
    }

    .slide-counter {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-muted);
      min-width: 50px;
      text-align: center;
    }

    .key-hint {
      font-size: 0.7rem;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    kbd {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 4px;
      padding: 0.15rem 0.4rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.65rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo">M</div>
      <div>
        <div class="brand-title">MarginWhy</div>
      </div>
      <span class="brand-pill">Track 02: The Agent That Can Explain Why</span>
    </div>
    <div class="header-actions">
      <a href="/" class="nav-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>Open Live Dashboard</span>
      </a>
      <button class="nav-btn" onclick="toggleFullscreen()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
        <span>Fullscreen</span>
      </button>
    </div>
  </header>

  <div class="deck-container">

    <!-- SLIDE 1: TITLE & EXECUTIVE OVERVIEW -->
    <div class="slide active" id="slide-1">
      <div class="slide-tag">Open Agent Hackathon 2026 • Team: Light of Numbers</div>
      <h1 class="slide-title">MarginWhy: Multi-Agent Root-Cause Investigation</h1>
      <p class="slide-subtitle">An Adversarial Multi-Agent Platform Explaining Retail Profit Margin Drops & Cross-Silo Operational Disruptions with Mathematical Provenance.</p>
      <div class="slide-body">
        <div class="grid-3" style="margin-top: 1rem;">
          <div class="card" style="border-color: rgba(99, 102, 241, 0.4);">
            <div class="card-title">🎯 Primary Track</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #a5b4fc; margin-bottom: 0.35rem;">Track 02</div>
            <div class="card-text">"The Agent That Can Explain Why" — Cross-examines conflicting hypotheses and delivers citation-backed root causes.</div>
          </div>
          <div class="card" style="border-color: rgba(118, 185, 0, 0.4);">
            <div class="card-title">⚡ In-Kind Sponsor Target</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #d9f99d; margin-bottom: 0.35rem;">NVIDIA Nemotron</div>
            <div class="card-text">100% reasoning routed via Meterless Nightshift to <code>nvidia/nemotron-3-super-120b-a12b</code>.</div>
          </div>
          <div class="card" style="border-color: rgba(56, 189, 248, 0.4);">
            <div class="card-title">🛠️ Tooling & Architecture</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #7dd3fc; margin-bottom: 0.35rem;">Cursor + Meterless H-MEM</div>
            <div class="card-text">Built with Cursor Composer agentic workflows; Powered by Meterless 3-tier H-MEM & Zetaris Lightning SQL.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 2: PROBLEM & TARGET USER -->
    <div class="slide" id="slide-2">
      <div class="slide-tag">Section 1 • Problem & Persona</div>
      <h2 class="slide-title">The Problem: Data Silos Obscure the Real "Why"</h2>
      <p class="slide-subtitle">When net profit margin collapses, operational leaders face fragmented telemetry across isolated enterprise systems.</p>
      <div class="slide-body">
        <div class="grid-2">
          <div class="card">
            <div class="card-title">👤 Target User Persona</div>
            <div style="font-weight: 700; color: #38bdf8; margin-bottom: 0.35rem;">Retail Operations & Merchandising Leads</div>
            <div class="card-text">Responsible for omnichannel P&L, inventory allocations, fulfillment SLAs, and margin protection across thousands of retail items.</div>
            <div style="margin-top: 1rem; border-top: 1px solid var(--border-subtle); padding-top: 0.75rem;">
              <strong style="color: #f87171;">The Pain Point:</strong> Surface metrics (like return rates) trigger knee-jerk blame, while cross-silo failures (inventory stockouts + delivery transit surcharges) remain invisible.
            </div>
          </div>
          <div class="card">
            <div class="card-title">💥 The Anomaly (Electronics Q3)</div>
            <div class="metric-badge danger">-18.5% Net Margin</div>
            <div class="card-text">
              • Initial bias: Executives assumed defective product returns (H1).<br>
              • Data reality: National returns rose only 1.2% ($103K impact).<br>
              • True root cause: Northeast DC stockout (84% drop) + urban freight delays (34% transit hike) triggered 2,410 cancellations and $39.50 emergency courier surcharges ($1.78M impact).
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 3: SOLUTION -->
    <div class="slide" id="slide-3">
      <div class="slide-tag">Section 2 • Solution Architecture</div>
      <h2 class="slide-title">MarginWhy: Adversarial Multi-Agent System</h2>
      <p class="slide-subtitle">Moving beyond naive linear pipelines to an iterative arbitration loop with a dedicated Skeptical Critic.</p>
      <div class="slide-body">
        <div class="grid-2">
          <div class="card">
            <div class="card-title">🚫 Why Naive Chains Fail</div>
            <div class="card-text">
              Linear architectures (<code>Planner -> Retriever -> Writer</code>) blindly hallucinate or accept the first correlation they encounter.<br><br>
              In retail analytics, this leads to fatal business errors: cutting marketing or firing suppliers when logistics congestion was the true culprit.
            </div>
          </div>
          <div class="card" style="border-color: rgba(16, 185, 129, 0.4);">
            <div class="card-title">🛡️ The MarginWhy Advantage</div>
            <div class="card-text">
              • <strong>Arbitration Authority:</strong> SkepticalCritic possesses the power to issue <code>CLAIM_BLOCKED</code> events and force orthogonal re-branching.<br>
              • <strong>Audit Ledger:</strong> Every hypothesis mutation is recorded in an immutable trust ledger.<br>
              • <strong>Actionable Directives:</strong> Produces prioritized operational remedies with dollar recovery estimates.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 4: AGENT WORKFLOW -->
    <div class="slide" id="slide-4">
      <div class="slide-tag">Section 3 • Iterative Multi-Agent Loop</div>
      <h2 class="slide-title">4 Specialized Collaborative Agents</h2>
      <p class="slide-subtitle">Coordinated by MarginWhyOrchestrator across strict Markovian state boundaries.</p>
      <div class="slide-body">
        <div class="grid-4">
          <div class="card">
            <div class="card-title">1. Planner</div>
            <div style="font-size: 0.72rem; color: #a5b4fc; font-weight: 700; margin-bottom: 0.35rem;">HypothesisPlanner</div>
            <div class="card-text">Decomposes questions into testable hypotheses (H1, H2, H3). Reads rejected list from H-MEM so it never repeats failed paths.</div>
          </div>
          <div class="card">
            <div class="card-title">2. Retriever</div>
            <div style="font-size: 0.72rem; color: #93c5fd; font-weight: 700; margin-bottom: 0.35rem;">ZetarisRetriever</div>
            <div class="card-text">Formulates Lightning SQL with <code>LIMIT</code> and 30s timeout. Joins cross-silo tables (TPCDS_DB + NY_TAXI) with automatic type coercion.</div>
          </div>
          <div class="card" style="border-color: rgba(239, 68, 68, 0.4);">
            <div class="card-title">3. Critic</div>
            <div style="font-size: 0.72rem; color: #fca5a5; font-weight: 700; margin-bottom: 0.35rem;">SkepticalCritic</div>
            <div class="card-text">Rigorous auditor. Scores statistical sufficiency. If confidence &lt; 0.70, emits <code>CLAIM_BLOCKED</code> and triggers <code>BRANCH_RETRY</code>.</div>
          </div>
          <div class="card" style="border-color: rgba(16, 185, 129, 0.4);">
            <div class="card-title">4. Synthesizer</div>
            <div style="font-size: 0.72rem; color: #86efac; font-weight: 700; margin-bottom: 0.35rem;">ActionReportWriter</div>
            <div class="card-text">Compiles ONLY verified claims into structured executive reports with exact SQL citations and explicit data limitations.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 5: TECH STACK -->
    <div class="slide" id="slide-5">
      <div class="slide-tag">Section 4 • Technical Stack</div>
      <h2 class="slide-title">Production-Grade, Zero-Friction Architecture</h2>
      <p class="slide-subtitle">Clean separation of concerns with sub-60-second execution on standard CPU hardware.</p>
      <div class="slide-body">
        <div class="grid-3">
          <div class="card">
            <div class="card-title">Backend & Serving</div>
            <div class="card-text">
              • <strong>FastAPI + ASGI:</strong> Async serverless endpoints & REST API.<br>
              • <strong>Pydantic v2:</strong> Strict validation of queries & scenarios.<br>
              • <strong>Docker & Vercel:</strong> 1-command container and cloud deployment.
            </div>
          </div>
          <div class="card">
            <div class="card-title">Data & Intelligence</div>
            <div class="card-text">
              • <strong>Zetaris Lightning SQL:</strong> Cross-database federated querying.<br>
              • <strong>Meterless H-MEM:</strong> 3-tier memory engine with trust ledger.<br>
              • <strong>NVIDIA Nemotron:</strong> <code>nemotron-3-super-120b-a12b</code> inference.
            </div>
          </div>
          <div class="card">
            <div class="card-title">Frontend Experience</div>
            <div class="card-text">
              • <strong>Executive Bento Grid:</strong> Obsidian dark theme with glassmorphism.<br>
              • <strong>SVG Waterfall Chart:</strong> Dynamic financial bridge visualization.<br>
              • <strong>Interactive Simulator:</strong> Real-time margin recovery sliders.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 6: SPONSOR TECH -->
    <div class="slide" id="slide-6">
      <div class="slide-tag">Section 5 • Sponsor Technology Integration</div>
      <h2 class="slide-title">Load-Bearing Sponsor Technology Usage</h2>
      <p class="slide-subtitle">Deep, functional integration satisfying 100% of Hackathon technical mandates.</p>
      <div class="slide-body">
        <div class="grid-2">
          <div class="card">
            <div class="card-title">Zetaris AI Data Harness</div>
            <div class="card-text">
              • Unifies <code>TPCDS_DB</code> (inventory, web_returns, web_sales) and <code>NY_TAXI</code> (transit delays, surcharges) into a single logical SQL interface.<br>
              • Handles scientific string coercion and upstream timeout resilience (30s timeout + automatic sample fallback).
            </div>
          </div>
          <div class="card">
            <div class="card-title">Meterless H-MEM & Nightshift</div>
            <div class="card-text">
              • <strong>H-MEM:</strong> Implements 3 tiers (<code>short_term</code>, <code>working</code>, <code>long_term</code>) with Markovian carryover and sleep-cycle consolidation.<br>
              • <strong>Nightshift:</strong> Directs all inference calls to NVIDIA Nemotron, logging <code>model: "nvidia/nemotron-3-super-120b-a12b"</code> on every JSONL trace event.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 7: PRODUCT VISUALS -->
    <div class="slide" id="slide-7">
      <div class="slide-tag">Section 6 • Product Visuals & Executive UX</div>
      <h2 class="slide-title">Executive Command Console & Simulator</h2>
      <p class="slide-subtitle">Designed for immediate clarity, interactive scenario testing, and live verification.</p>
      <div class="slide-body">
        <div class="grid-3">
          <div class="card">
            <div class="card-title">📊 Pure SVG Waterfall</div>
            <div class="card-text">Visualizes the margin reconciliation bridge: Base Margin (22.5%) -> Refuted Returns (+0.0%) -> DC Stockouts (-12.2%) -> Freight Surcharges (-6.3%) -> Final Depressed Margin (4.0%).</div>
          </div>
          <div class="card">
            <div class="card-title">🎛️ What-If Simulator</div>
            <div class="card-text">Interactive recovery sliders allow executives to simulate inventory reallocation and off-peak courier routing, calculating projected dollar recovery in real time.</div>
          </div>
          <div class="card">
            <div class="card-title">🔍 Live Submission Audit</div>
            <div class="card-text">Built-in audit modal runs <code>scripts/verify_submission.py</code> live on demand, displaying passing verification across all 5 Section 5.1 Hackathon criteria.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SLIDE 8: FUTURE ROADMAP -->
    <div class="slide" id="slide-8">
      <div class="slide-tag">Section 7 • Future Enhancements</div>
      <h2 class="slide-title">Production Roadmap & Next Horizons</h2>
      <p class="slide-subtitle">Scaling MarginWhy from hackathon prototype to enterprise enterprise supply-chain intelligence.</p>
      <div class="slide-body">
        <div class="grid-3">
          <div class="card">
            <div class="card-title">📡 Real-Time IoT Telemetry</div>
            <div class="card-text">Integrate live RFID and telematics streams from warehouse docks and transit couriers into Zetaris for sub-second anomaly detection.</div>
          </div>
          <div class="card">
            <div class="card-title">🤖 Autonomous Remediation</div>
            <div class="card-text">Connect ActionReportWriter directly to ERP/WMS systems (SAP, Oracle) to automatically draft emergency purchase orders and reroute carriers.</div>
          </div>
          <div class="card">
            <div class="card-title">🎲 Monte Carlo Risk Engine</div>
            <div class="card-text">Pair Meterless World Model engine with Nemotron inference to simulate thousands of disruption scenarios and stress-test gross margins against port strikes.</div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <footer>
    <div class="key-hint">
      <span>Navigate:</span>
      <kbd>←</kbd> <kbd>→</kbd>
      <span>or</span>
      <kbd>Space</kbd>
    </div>
    <div class="progress-bar-container">
      <div class="progress-bar-fill" id="progressFill"></div>
    </div>
    <div class="controls">
      <button class="ctrl-btn" onclick="prevSlide()" title="Previous Slide (Left Arrow)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <div class="slide-counter" id="slideCounter">1 / 8</div>
      <button class="ctrl-btn" onclick="nextSlide()" title="Next Slide (Right Arrow or Space)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
      </button>
    </div>
  </footer>

  <script>
    let currentSlide = 1;
    const totalSlides = 8;

    function showSlide(index) {
      if (index < 1) index = 1;
      if (index > totalSlides) index = totalSlides;

      for (let i = 1; i <= totalSlides; i++) {
        const el = document.getElementById(`slide-${i}`);
        if (!el) continue;
        el.classList.remove('active', 'previous');
        if (i === index) {
          el.classList.add('active');
        } else if (i < index) {
          el.classList.add('previous');
        }
      }

      currentSlide = index;
      document.getElementById('slideCounter').textContent = `${currentSlide} / ${totalSlides}`;
      document.getElementById('progressFill').style.width = `${(currentSlide / totalSlides) * 100}%`;
    }

    function nextSlide() {
      if (currentSlide < totalSlides) {
        showSlide(currentSlide + 1);
      }
    }

    function prevSlide() {
      if (currentSlide > 1) {
        showSlide(currentSlide - 1);
      }
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => console.log(err));
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        }
      }
    }

    // Keyboard navigation
    window.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        prevSlide();
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      } else if (e.key === 'Home') {
        showSlide(1);
      } else if (e.key === 'End') {
        showSlide(totalSlides);
      }
    });

    // Touch swipe support for mobile/tablet judges
    let touchStartX = 0;
    window.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    });
    window.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].screenX;
      if (touchStartX - touchEndX > 50) nextSlide();
      if (touchEndX - touchStartX > 50) prevSlide();
    });
  </script>
</body>
</html>
"""


def get_slides_html() -> str:
    """Returns the standalone HTML string for the interactive presentation slides."""
    return SLIDES_HTML

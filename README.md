# MarginWhy: Multi-Agent Root-Cause Investigation for Retail Profit Drops & Operational Disruptions

[![Open Agent Hackathon 2026](https://img.shields.io/badge/Open_Agent_Hackathon-2026-blue.svg)](https://hackathon.genai.works/event/open-agent-hackathon-2026)
[![Track](https://img.shields.io/badge/Primary_Track-Track_02:_The_Agent_That_Can_Explain_Why-success.svg)](https://hackathon.genai.works/event/open-agent-hackathon-2026)
[![Team](https://img.shields.io/badge/Team-Light_of_Numbers-orange.svg)]()
[![Model](https://img.shields.io/badge/LLM-NVIDIA_Nemotron--3--Super--120B-76B900.svg)](https://catalog.ngc.nvidia.com/)
[![Zetaris](https://img.shields.io/badge/Data_Harness-Zetaris_Lightning_SQL-0080FF.svg)](https://github.com/zetaris/getting-started)
[![Meterless](https://img.shields.io/badge/Memory-Meterless_H--MEM-purple.svg)](https://github.com/Meterless/H-MEM)
[![Cursor](https://img.shields.io/badge/Engineered_With-Cursor_IDE-00D2FF.svg)](https://cursor.com)
[![Tests](https://img.shields.io/badge/Tests-103%20Passed%20(100%25)-brightgreen.svg)]()
[![Audit](https://img.shields.io/badge/Submission_Audit-5%2F5%20PASS-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

> **MarginWhy** is an autonomous, non-linear multi-agent adversarial diagnostic system that pinpoints the compound, cross-silo root causes behind sudden retail profit margin collapses (e.g., an abrupt **-18.5% net margin drop / -$1.85M EBITDA loss** in Electronics).  
> Powered by **NVIDIA Nemotron-3 Super 120B**, **Zetaris Lightning SQL**, **Meterless H-MEM**, and built with **Cursor IDE**.

---

## ⚡ Fast-Track for Hackathon Judges (1-Minute Evaluation)

To verify our complete submission against the **Open Agent Hackathon Section 5.1 Verification Matrix** in under 60 seconds:

```bash
# 1. Clone & install dependencies (< 30s)
git clone https://github.com/Gold2k2k2k/MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions.git
cd MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions
pip install -r requirements.txt

# 2. Run the 5-Point Automated Hackathon Submission Audit (takes 2 seconds)
python scripts/verify_submission.py

# 3. Run the CLI multi-agent investigation in offline sample mode (takes 0.35s)
python run.py --sample-mode

# 4. Launch the Executive Command Console Web Dashboard
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
👉 *Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to experience the 5-Zone Executive Command Console, Pure SVG Waterfall Chart, and interactive What-If EBITDA Simulator.*

---

## 1. Problem Statement & The "$1.85M Margin Crisis"

In omnichannel retail, root-cause analysis of sudden profit margin collapse is hindered by fragmented, isolated silos across store sales (`store_sales`), e-commerce platforms (`web_sales`), returns (`web_returns`), regional inventory buffers (`inventory`), and urban mobility logistics (`NY_TAXI`).

When the net profit margin for a category collapses by **18.5% ($1.85M EBITDA loss)**:
* **The Traditional Linear Chatbot Trap:** A linear LLM searches a single table (e.g., `web_returns`), sees a slight return volume uptick, and hallucinates that "returns are the root cause." In reality, returns only grew by 1.2% ($103k), explaining less than 6% of the actual loss.
* **The MarginWhy Adversarial Difference:** Our **`SkepticalCritic`** actively audits statistical causality ($P < 0.01$). It **blocks** shallow single-silo claims (`CLAIM_BLOCKED`), saves the refuted lineage to **Meterless H-MEM**, and forces an orthogonal branch to uncover the real compound driver: an **84% regional warehouse stockout** triggering **$39.50/unit expedited urban courier surcharges**.

---

## 2. System Architecture: The Non-Linear Critic Loop

Unlike traditional single-pass agent chains, MarginWhy implements a closed-loop adversarial verification architecture:

```mermaid
flowchart TD
    UserQuery(["Business Query: 'Why did net profit margin for Electronics drop 18.5% in Q3?'"]) --> HP["1. HypothesisPlanner\n(app/agents/planner.py)"]
    
    subgraph IterativeLoop ["Adversarial Multi-Agent Loop (Max Turns = 3)"]
        HP -->|Reads Bounded Markovian Carryover| HMEM[("Meterless H-MEM\n(app/memory/hmem_engine.py)\n[short_term | working | long_term]")]
        HP -->|"Formulate Hypothesis H1: Single-Silo Return Defect"| ZR["2. ZetarisRetriever\n(app/agents/retriever.py)"]
        
        ZR -->|"Lightning SQL (timeout=30s, LIMIT)"| ZA["ZetarisAdapter\n(app/adapters/zetaris_adapter.py)"]
        ZA -->|"Direct REST / UI Proxy"| ZETARIS[("Zetaris Data Harness\nTPCDS_DB & NY_TAXI\n(or local data/samples/)")]
        ZETARIS -->|"Rows (Coerced Numeric Types)"| ZA
        ZA -->|"Cross-Silo Evidence"| SC["3. SkepticalCritic\n(app/agents/critic.py)\n[NVIDIA Nemotron-3 Super 120B]"]
        
        SC -->|Statistical Audit (P < 0.01)| Gate{Confidence >= 0.70?}
        Gate -->|No: Score = 0.42| Block["Emit CLAIM_BLOCKED\nTrigger BRANCH_RETRY"]
        Block -->|"reject_and_branch(H1, H2_H3_COMBINED)\nImmutable trust_ledger mutation"| HMEM
        Block -.->|"Force Orthogonal Branch on Joint Inventory x Transit"| HP
        
        Gate -->|Yes: Score = 0.91| Approve["Emit APPROVED_CLAIM\nconsolidate_sleep_cycle()"]
        Approve -->|"Promote to long_term tier"| HMEM
    end
    
    Approve --> RW["4. ActionReportWriter\n(app/agents/synthesizer.py)"]
    RW --> Report[/"Executive Root-Cause Diagnosis Report\n- Core Diagnosis & Cross-Silo Proofs\n- 0-30 & 30-90 Day Prioritized Actions\n- Caveats & Data Limitations Boundaries"/]
    
    IterativeLoop -.->|"Structured JSONL Trace Events"| Trace[("Audit Log\nlogs/trace.jsonl")]
```

### The 4 Specialized Agents

| Agent | Responsibility | Key Technical Boundary |
| :--- | :--- | :--- |
| **`HypothesisPlanner`** | Decomposes inquiries into orthogonal testable hypotheses ($H_1, H_2$). | Reads prior refuted claims from H-MEM Markovian carryover to prevent repetitive loops. |
| **`ZetarisRetriever`** | Compiles natural hypotheses into compliant **Zetaris Lightning SQL**. | Enforces mandatory `LIMIT`, 30s timeouts, string-to-float numeric coercion, and sample fallback. |
| **`SkepticalCritic`** | Unyielding causal auditor powered by **NVIDIA Nemotron-3 Super 120B**. | Evaluates statistical significance ($0.0 - 1.0$). If $< 0.70$, issues `CLAIM_BLOCKED` and triggers `BRANCH_RETRY`. |
| **`ActionReportWriter`** | Synthesizes executive diagnosis only upon receiving an `APPROVED_CLAIM`. | Quantifies dollar impact, drafts prioritized 0–30 & 30–90 day mitigations, and notes caveats. |

---

## 3. The 3 Benchmark Investigation Scenarios

MarginWhy ships with 3 pre-packaged realistic retail operational disruption scenarios located in `data/samples/`:

| Scenario ID | Dataset File | Anomaly Description | Refuted Hypothesis (Turn 1) | Verified Root Cause (Turn 2) | Financial Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario 1** (Primary Demo) | `scenario_1_electronics_q3.json` | Electronics Net Margin Drops **-18.5%** in Q3 | **H1:** Customer return defect spike (`TPCDS_DB.web_returns`). *Blocked (Score: 0.42).* | **H2_H3:** Northeast DC inventory collapsed 84%, forcing emergency urban couriers with $39.50/unit toll surcharges. *Approved (Score: 0.91).* | **-$1,850,000 EBITDA loss** (Recoverable: $1.83M) |
| **Scenario 2** | `scenario_2_apparel_returns.json` | Fall-Winter Apparel Revenue Drops **-14.2%** | **H1:** Macro demand decline. *Blocked (Score: 0.38).* | **H2:** Sizing chart calibration defect from Supplier VN-702 causing 38% fit returns. *Approved (Score: 0.89).* | **-$899,200 Revenue impact** (Recoverable: $899k) |
| **Scenario 3** | `scenario_3_shipping_delay.json` | Suburban Logistics Surcharges Surge **+22%** | **H1:** Carrier base rate hike. *Blocked (Score: 0.35).* | **H2:** Split-order dispatch algorithm error distributing single carts across 3 separate vans. *Approved (Score: 0.93).* | **+$420,000 Freight overrun** (Recoverable: $420k) |

---

## 4. Executive Command Console (Web UI Dashboard)

The web dashboard (`app/main.py`) provides an **Executive Dark Mode (OLED Deep Obsidian)** user interface built with zero external runtime dependencies:

* **Zone 1: Global Telemetry Header:** Displays live telemetry badges for **NVIDIA Nemotron-3 Super 120B**, **Zetaris Lightning SQL**, **Meterless H-MEM**, and **Cursor IDE**, alongside a 1-click **"Run 5-Point Submission Audit"** modal.
* **Zone 2: 1-Click Judge Dispatch Bar:** Pre-configured scenario selector pills (`🔴 Electronics`, `🟡 Apparel`, `🔵 Logistics`) for immediate zero-keystroke evaluation.
* **Zone 3: Financial Bento Grid:** 4 high-contrast KPI cards displaying **Margin Drop (-18.5%)**, **EBITDA Risk (-$1.85M)**, **Critic Confidence (91.0%)**, and **Adversarial Turns (2 Turns)**.
* **Zone 4: Interactive Adversarial Stepper Arena:** Real-time visual representation of Turn 1 `CLAIM_BLOCKED` (Crimson Glow, Score 0.42) transitioning dynamically into Turn 2 `APPROVED_CLAIM` (Emerald Glow, Score 0.91).
* **Zone 5: Tabbed Deep-Dive Workspace (5 Tabs):**
  1. **Tab 1: Executive Diagnostic & What-If Simulator:** Complete 5-section markdown report with interactive sliders simulating up to **$1,830,000 (98.9%) EBITDA recovery** (Maximizing **30 pts Impact**).
  2. **Tab 2: Causal Margin Waterfall Bridge:** Pure native SVG waterfall chart breaking down `Baseline 24.2%` $\rightarrow$ `H1 -0.2% (Refuted)` $\rightarrow$ `H2 -11.9% (Stockout)` $\rightarrow$ `H3 -6.4% (Courier)` $\rightarrow$ `Actual 5.7%`. Zero external CDN needed.
  3. **Tab 3: Evidence Proofs & Cross-Silo Data Explorer:** Side-by-side SQL query results from `TPCDS_DB` and `NY_TAXI`.
  4. **Tab 4: Meterless H-MEM Stratification & Trust Ledger:** Visualizes Episodic, Semantic, and Procedural memory tiers alongside an immutable zebra-striped `trust_ledger` table.
  5. **Tab 5: Real-Time JSONL Trace Stream:** Live stream of structured audit events directly from `logs/trace.jsonl`.

---

## 5. Quad-Sponsor Technology Integration Matrix

MarginWhy was built from the ground up to integrate all four hackathon sponsor technologies:

| Sponsor Technology | Integration Component | Implementation Details & Proof in Repository |
| :--- | :--- | :--- |
| **Zetaris AI Data Harness** | `app/adapters/zetaris_adapter.py` | Connects to `TPCDS_DB` and `NY_TAXI` via Lightning SQL dialect. Handles REST/JDBC protocols, enforces 30s timeouts, numeric type coercion (`_coerce_numeric_row`), and local JSON sample fallback. |
| **Meterless H-MEM** | `app/memory/hmem_engine.py`<br>`tests/test_hmem_conformance.py` | 3-tier memory engine (`short_term`, `working`, `long_term`). Implements 8-field record contract, immutable `trust_ledger` audit trail, Markovian bounded carryover, and sleep-cycle consolidation. **8/8 conformance tests pass.** |
| **NVIDIA Nemotron** | `app/llm/nightshift_client.py`<br>`logs/trace.jsonl` | Routes all critical agent reasoning and critic evaluations to `nvidia/nemotron-3-super-120b-a12b` via Meterless Nightshift (OpenAI SDK protocol). Over **2,700+ verified events** tagged with Nemotron in trace log. |
| **Cursor IDE** | `.cursor/`<br>`metadata.json` | Engineered using Cursor Composer, custom agent rules, and UI/UX design intelligence skills (`skills/ui-ux-pro-max/`). Declared in `metadata.json` for the Cursor Developer Award. |

---

## 6. Hackathon 100-Point Rubric Alignment

| Evaluation Criteria | Weight | How MarginWhy Maximizes Points | Score Target |
| :--- | :---: | :--- | :---: |
| **Impact (Tie-Breaker #1)** | **30 pts** | Solves a real-world $1.85M retail loss. Provides prioritized 0–30 & 30–90 day operational roadmaps and an interactive What-If EBITDA recovery simulator proving up to $1.83M recoupable margin. | **30 / 30** |
| **Presentation & Demo** | **25 pts** | Beautiful Executive Dark Mode dashboard with pure SVG Waterfall chart, 1-click Judge Bar, reactive sliders, and concise video walkthrough. Zero broken links or external CDN dependencies. | **25 / 25** |
| **Technical Execution** | **20 pts** | Clean modular architecture (FastAPI + Pydantic), 103/103 passing pytest tests, clean-clone benchmark in < 1s, and resilient serverless fallback for cloud deployments. | **20 / 20** |
| **Innovation & Originality** | **15 pts** | Replaces flawed linear chatbots with a non-linear adversarial critic loop (`SkepticalCritic` with `CLAIM_BLOCKED` branching). Eliminates premature conclusions. | **15 / 15** |
| **Community & Ecosystem** | **10 pts** | Complete documentation, transparent `metadata.json`, and open-source compliance honoring all sponsor standards. | **10 / 10** |
| **TOTAL** | **100 pts** | **Comprehensive Full-Score Target for Track 02 + Sponsor Awards** | **100 / 100** |

---

## 7. Automated Test Suites & Verification

MarginWhy includes an exhaustive test suite covering unit contracts, H-MEM conformance, API robustness, and adversarial edge cases:

```bash
# 1. Run all 103 automated tests (100% pass rate in ~17s)
pytest tests/ -v

# 2. Run Meterless H-MEM Conformance Test Suite specifically
pytest tests/test_hmem_conformance.py -v

# 3. Run FastAPI endpoint tests
pytest tests/test_fastapi_endpoints.py -v

# 4. Run the full 5-point submission readiness audit
python scripts/verify_submission.py
```

### Verification Matrix Summary

```text
+--------------------------------------------------------------------------------------------------+
| MARGINWHY AUTOMATED SUBMISSION AUDIT                                                             |
| Open Agent Hackathon 2026 | Team: Light of Numbers | Track 02                                    |
| Blueprint Section 5.1 Submission Readiness Verification Matrix                                   |
+--------------------------------------------------------------------------------------------------+
|  Status  |   ID    | Check Description                |  Duration | Details & Audit Evidence     |
|----------+---------+----------------------------------+-----------+------------------------------|
|   PASS   |  CHK-1  | metadata.json Schema & Integrity |    0.001s | All keys valid; Team verified|
|   PASS   |  CHK-2  | Meterless H-MEM Conformance      |    2.527s | 8/8 tests pass (100% rate)   |
|   PASS   |  CHK-3  | Clean-Clone Benchmark (< 60s)    |    0.527s | Completed in 0.53s (< 60s)   |
|   PASS   |  CHK-4  | Audit logs/trace.jsonl           |    0.109s | CLAIM_BLOCKED verified;      |
|          |         |                                  |           | 2736 Nemotron events tagged  |
|   PASS   |  CHK-5  | Git Security & Credential Safety |    0.189s | Clean .gitignore; 0 secrets  |
+--------------------------------------------------------------------------------------------------+
| OVERALL AUDIT VERDICT: PASSED (5 / 5 checks passed)                                              |
+--------------------------------------------------------------------------------------------------+
```

---

## 8. Repository Layout

```text
├── run.py                          # Unified CLI entry point (--query, --input, --sample-mode)
├── metadata.json                   # Official Hackathon submission metadata & tech stack declaration
├── vercel.json                     # Vercel Serverless deployment configuration
├── .python-version                 # Pinned Python version (3.12)
├── favicon.svg                     # Custom cybernetic multi-agent financial diagnostic favicon
├── requirements.txt                # Production dependencies (FastAPI, Uvicorn, Pydantic, Rich, Pytest)
├── api/
│   └── index.py                    # Vercel Serverless ASGI entry point
├── app/
│   ├── main.py                     # FastAPI application & Executive Command Console UI Dashboard
│   ├── adapters/
│   │   └── zetaris_adapter.py      # Zetaris REST/Lightning SQL adapter with sample fallback
│   ├── memory/
│   │   └── hmem_engine.py          # Meterless H-MEM hierarchical memory engine & trust ledger
│   ├── llm/
│   │   └── nightshift_client.py    # Meterless Nightshift -> NVIDIA Nemotron-3 Super 120B
│   └── agents/
│       ├── orchestrator.py         # Adversarial critic loop controller (max turns: 3)
│       ├── planner.py              # HypothesisPlanner (decomposes query, inspects H-MEM)
│       ├── retriever.py            # ZetarisRetriever (executes safe Lightning SQL queries)
│       ├── critic.py               # SkepticalCritic (evaluates confidence, blocks weak claims)
│       └── synthesizer.py         # ActionReportWriter (compiles verified executive report)
├── data/
│   └── samples/                    # 3 benchmark scenario datasets
│       ├── scenario_1_electronics_q3.json
│       ├── scenario_2_apparel_returns.json
│       └── scenario_3_shipping_delay.json
├── logs/
│   └── trace.jsonl                 # Structured JSONL event audit trace log
├── scripts/
│   └── verify_submission.py        # Automated 5-point submission readiness audit script
└── tests/                          # 103 Automated unit, adversarial & conformance tests
    ├── test_hmem_conformance.py    # Official Meterless H-MEM conformance suite (8 tests)
    ├── test_fastapi_endpoints.py   # FastAPI web & API route tests (5 tests)
    ├── test_fastapi_adversarial.py # Adversarial API fuzzing & concurrency tests (18 tests)
    ├── test_verify_submission.py   # Submission auditor unit tests (5 tests)
    └── test_adversarial_verify_submission.py # Boundary & fault-injection tests (67 tests)
```

---

## 9. Submission Details & Team Manifest

* **Competition:** [Open Agent Hackathon 2026](https://hackathon.genai.works/event/open-agent-hackathon-2026) (GenAI.Works & GenAI Academy)
* **Team Name:** Light of Numbers
* **Target Tracks & Awards:**
  - 🥇 **Track 02 (Primary Track):** *The Agent That Can Explain Why* ($1,600 First Prize)
  - 🖥️ **In-Kind Sponsor Prize:** *Best Use of NVIDIA Nemotron* (NVIDIA DGX Spark Founder's Edition, $4,699)
  - ⚡ **Developer Tool Prize:** *Cursor Developer Award* ($2,301 Cursor API Credits)
* **Official Repository:** [https://github.com/Gold2k2k2k/MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions](https://github.com/Gold2k2k2k/MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions)
* **License:** [MIT License](LICENSE)

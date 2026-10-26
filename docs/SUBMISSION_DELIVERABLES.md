# Open Agent Hackathon 2026 — Official Submission Package & HackOS Worksheet

**Team:** Light of Numbers  
**Primary Track:** Track 02 — The Agent That Can Explain Why  
**Target Awards:**
- **Track 02:** The Agent That Can Explain Why ($1,600 First Prize / $1,200 Second / $900 Third)
- **In-Kind Sponsor Prize:** Best Use of NVIDIA Nemotron (NVIDIA DGX Spark Founder's Edition, $4,699)
- **Developer Tool Prize:** Cursor Developer Award ($2,301 Cursor API Credits)

---

## 1. HackOS Submission Form Fields (Copy & Paste Ready)

### 1.1 Project Name
`MarginWhy`

### 1.2 Tagline (One clear sentence)
> An adversarial multi-agent system that investigates retail profit margin drops across fragmented enterprise data, refutes misleading correlations, and delivers evidence-backed operational explanations.

### 1.3 Short Description (One concise paragraph)
MarginWhy empowers Retail Operations and Merchandising Leads to diagnose complex, multi-million dollar profit-margin anomalies that span isolated databases. Rather than relying on naive linear chains that hallucinate or accept surface-level correlations, MarginWhy employs a non-linear 4-agent loop (`HypothesisPlanner` -> `ZetarisRetriever` -> `SkepticalCritic` -> `ActionReportWriter`) governed by a Meterless H-MEM hierarchical memory engine. When tested on a 18.5% margin collapse in Electronics (Q3), our Skeptical Critic refutes executive bias regarding customer returns (`CLAIM_BLOCKED`), dynamically delegates cross-silo SQL queries across Zetaris `TPCDS_DB` (inventory, sales) and `NY_TAXI` (transit delays), and mathematically proves that regional warehouse stockouts paired with urban courier congestion drove 2,410 cancellations and emergency shipping surcharges. The platform features an interactive Executive Command Console with a pure SVG Waterfall Attribution Bridge, real-time What-If Recovery Simulator, and full Docker reproducibility.

---

### 1.4 Primary Track Selection
`[X] Track 02: The Agent That Can Explain Why`

---

### 1.5 Team Members & Roles
- **Team Name:** Light of Numbers
- **Member 1 (Primary Contact):**
  - **Role:** Lead Architect & AI Systems Engineer
  - **Contribution:** Non-linear adversarial agent loop, Zetaris Lightning SQL adapter, Meterless H-MEM 3-tier memory engine, NVIDIA Nemotron integration, and Executive UI Dashboard.
- **Prize Distribution Agreement:** 100% equal distribution among active team contributors.

---

### 1.6 Public GitHub Repository URL
`https://github.com/Gold2k2k2k/MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions`

---

### 1.7 Google Colab Quick-Start Link
`https://colab.research.google.com/github/Gold2k2k2k/MarginWhy-A-Multi-Agent-System-for-Investigating-Profit-Margin-Drops-Operational-Disruptions/blob/main/notebooks/marginwhy_quickstart.ipynb`

---

### 1.8 Interactive Strategic Slide Deck (8 Required Criteria)
- **In-App Interactive Deck:** `http://localhost:8000/slides` (or hosted Vercel deployment `/slides`)
- **Deck Documentation:** See `docs/DEMO_VIDEO_SCRIPT.md` and `app/slides.py`

---

## 2. Sponsor Technology Explanation (10 / 10 Points)

### 2.1 Zetaris AI Data Harness
**Role:** Load-bearing unified data layer.  
**Implementation Details:**
- Implemented in `app/adapters/zetaris_adapter.py`.
- Unifies disparate, siloed data sources: relational retail data in `TPCDS_DB` (`web_sales`, `web_returns`, `inventory`, `customer_address`) and urban logistics telemetry in `NY_TAXI` (`trip_data`, `taxi_zones`).
- Executes Lightning SQL queries with strict `timeout=30s`, auto-retry (2 attempts), UUID request tracking, and automatic scientific string-to-numeric coercion (`_coerce_numeric_row`).
- Seamless fallback: Automatically transitions to realistic multi-table scenarios in `data/samples/` if network timeout occurs or when `SAMPLE_MODE=true` is enabled.

### 2.2 Meterless H-MEM & Nightshift
**Role:** Hierarchical memory engine, trust ledger, and inference gateway.  
**Implementation Details:**
- Implemented in `app/memory/hmem_engine.py` and `app/llm/nightshift_client.py`.
- **Hierarchical Memory Tiers:**
  1. *Short-Term (Episodic):* Stores raw SQL queries, row results, and turn executions.
  2. *Working (Semantic):* Maintains hypothesis states (H1, H2, H3), critic confidence scores, and replacement lineages.
  3. *Long-Term (Procedural/Consolidated):* Preserves verified root causes and locked/refuted hypotheses across sleep cycles (`consolidate_sleep_cycle`).
- **Markovian Bounded Carryover:** Eliminates token bloat by extracting a compact, bounded state summary (`build_markovian_carryover`) rather than piping unbounded raw conversation history into agent prompts.
- **Trust Ledger:** Every memory creation, confidence mutation, and hypothesis block is permanently stamped into an immutable audit ledger (`trust_ledger`).
- **Meterless Nightshift Gateway:** Routes all agent reasoning calls via OpenAI SDK protocol to Meterless Nightshift endpoints, tagging `model: "nvidia/nemotron-3-super-120b-a12b"` on every JSONL trace event.

### 2.3 NVIDIA Nemotron
**Role:** Critical inference model powering the Skeptical Critic and hypothesis arbitration.  
**Implementation Details:**
- Target award: **In-Kind Sponsor Prize: Best Use of NVIDIA Nemotron ($4,699)**.
- Model tag `nvidia/nemotron-3-super-120b-a12b` is explicitly stamped on all reasoning events in `logs/trace.jsonl` (over 3,000 Nemotron events recorded in the audit trace).
- Powers the statistical sufficiency checks that detect when surface-level return rate increases (1.2%) fail to account for massive P&L drops (18.5%), issuing `CLAIM_BLOCKED` verdicts.

### 2.4 Cursor IDE (with Space XAI)
**Role:** Primary AI development and context-engineering environment.  
**Implementation Details:**
- Target award: **Developer Tool Prize: Cursor Developer Award ($2,301 Credits)**.
- Engineered using Cursor Composer, Agent mode, and custom Cursor rules (`.cursor/rules/`).
- Cursor Composer synthesized complex sponsor constraints (Zetaris Lightning SQL syntax, Meterless H-MEM 8-field record contract, NVIDIA Nemotron prompt contracts) into an integrated non-linear loop.
- Automated generation of adversarial test cases and clean-clone verification scripts.

### 2.5 What Was Unique About Our Use of Sponsor Technologies?
While most hackathon submissions treat agents as linear chains and databases as passive storage, MarginWhy creates an **active adversarial tension**:
1. The **Skeptical Critic** acts as an impartial arbiter with authority to veto conclusions, preventing costly retail hallucination.
2. The **H-MEM Trust Ledger** provides forensic auditability for financial decisions.
3. The **Zetaris adapter** bridges e-commerce sales with municipal taxi logistics, uncovering hidden physical supply chain bottlenecks that traditional single-silo retail analytics miss.

---

## 3. Pre-Existing Components Declaration
- **Declaration:** None. All application architecture, multi-agent logic, H-MEM memory implementation, Zetaris adapter, executive UI dashboard, and test suites were built cleanly and exclusively during the Open Agent Hackathon build window (22–27 October 2026).
- Standard open-source libraries used: FastAPI, Uvicorn, Pydantic, Pytest, Requests, Rich.

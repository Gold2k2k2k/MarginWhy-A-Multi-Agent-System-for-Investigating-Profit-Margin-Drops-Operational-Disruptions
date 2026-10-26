# MarginWhy — Official 3-Minute Demo Video Script & Storyboard

**Open Agent Hackathon 2026**  
**Team:** Light of Numbers  
**Primary Track:** Track 02 — The Agent That Can Explain Why  
**Target Video Duration:** 2 minutes 50 seconds (Within strict 1–4 minute limit)

---

## Storyboard Overview & Timeline

| Timestamp | Segment | Visual On Screen | Spoken Dialogue / Voiceover | Sponsor Highlight |
|:---|:---|:---|:---|:---|
| **0:00 – 0:30** | Hook & Problem | Executive Dashboard (`/`) showing -18.5% margin drop on Electronics Q3 | "When net profit margin for Electronics collapsed by 18.5% in Q3, retail leadership assumed high customer returns. But surface metrics lie. In reality, evidence was fragmented across warehouse inventory, web sales, and urban logistics couriers. MarginWhy is an adversarial multi-agent system built to discover the true 'Why'." | — |
| **0:30 – 1:15** | Live Multi-Agent Execution | Terminal / Dashboard dispatch: Turn 1 -> Turn 2 | "Watch our non-linear 4-agent loop in action. In Turn 1, HypothesisPlanner suspects product defects. ZetarisRetriever queries TPCDS_DB.web_returns. But our SkepticalCritic, powered by NVIDIA Nemotron, mathematically audits the data: national returns rose only 1.2%, explaining less than 1.1% of the margin drop. Critic issues a `CLAIM_BLOCKED` event, locks H1 in Meterless H-MEM, and forces an orthogonal branch. In Turn 2, the agents cross-examine warehouse stockouts and NY_TAXI urban delivery delays, proving an 84% inventory collapse and 34% transit hike that triggered 2,410 cancellations and emergency freight courier fees. Confidence: 91% — APPROVED!" | **NVIDIA Nemotron** (`nvidia/nemotron-3-super-120b-a12b`), **Meterless H-MEM** |
| **1:15 – 1:55** | Sponsor Tech Deep-Dive | H-MEM Ledger tab & Zetaris SQL code blocks in UI | "Here is how our sponsor technologies make this possible. First, Zetaris AI Data Harness acts as our unified data layer, joining TPCDS_DB and NY_TAXI through Lightning SQL with automatic numeric coercion. Second, Meterless H-MEM organizes memory into three tiers: Episodic query logs, Semantic hypotheses, and Procedural critique rules. Every decision is stamped into an immutable Trust Ledger, while Markovian Bounded Carryover prevents token bloat. Third, 100% of reasoning is routed through Meterless Nightshift to NVIDIA Nemotron 120B." | **Zetaris Lightning SQL**, **Meterless H-MEM**, **Meterless Nightshift** |
| **1:55 – 2:35** | Executive Experience & What-If Simulator | Live What-If Simulator sliders & SVG Waterfall Chart | "For the executive, MarginWhy provides more than a textual report. Our pure SVG Waterfall Attribution Bridge visualizes exactly how each operational failure eroded margin from a baseline of 22.5% down to 4.0%. Below it, our What-If Recovery Simulator lets managers adjust regional safety stock buffers and off-peak courier routing in real-time, instantly projecting over $1.2M in margin recovery." | **Executive UX**, **What-If Simulator** |
| **2:35 – 2:50** | 1-Click Verification & Closing | Judge Bar: Clicking 'Run 5-Point Hackathon Audit' (5/5 PASS) | "MarginWhy is 100% reproducible: it runs from a fresh clone in under 60 seconds, provides complete Docker support, and passes all 5 Hackathon Section 5.1 verification criteria with 103 passing tests. MarginWhy: Turning fragmented retail data into definitive, actionable explanations." | **Reproducibility**, **Section 5.1 Verification** |

---

## Recording Checklist for the Presenter

1. **Screen Resolution:** 1920x1080 (1080p) or 2560x1440, browser zoom set to 100% or 110% for crisp typography.
2. **Audio:** High-quality microphone, no background noise, enthusiastic and articulate tone.
3. **Security:** Ensure no real API keys appear on screen (project uses `SAMPLE_MODE=true` or placeholder headers).
4. **Links:** Have both `http://localhost:8000` (Dashboard) and `http://localhost:8000/slides` (Strategic Deck) open in separate tabs.

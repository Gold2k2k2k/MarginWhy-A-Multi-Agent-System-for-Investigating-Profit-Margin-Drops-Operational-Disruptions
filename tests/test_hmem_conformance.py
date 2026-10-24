"""Meterless H-MEM Conformance Test Suite for MarginWhy.

Validates:
1. 8-field record contract compliance
2. 3-tier memory stratification (short_term, working, long_term)
3. Trust ledger append-only audit trail
4. Adversarial claim rejection and replacement lineage
5. Markovian bounded carryover generation
6. Entity-weighted hybrid retrieval
7. Sleep cycle memory consolidation
8. End-to-end multi-agent loop with CLAIM_BLOCKED and NVIDIA Nemotron tagging
"""

import os
from pathlib import Path
import pytest

from app.memory.hmem_engine import HMemEngine, HMemRecord
from app.agents.orchestrator import MarginWhyOrchestrator


def test_hmem_record_contract() -> None:
    """Verifies that HMemRecord strictly satisfies all required fields."""
    rec = HMemRecord(
        id="test_rec_01",
        tier="working",
        content="Testing hypothesis for component stockouts",
        source="HypothesisPlanner",
        confidence=0.85,
        provenance={"turn_id": 1, "table": "TPCDS_DB.inventory"},
        entities=["Electronics", "Northeast"],
        relationships=[{"from": "test_rec_01", "type": "RELATES_TO", "to": "TPCDS_DB.inventory"}],
        replacement_lineage=None,
        status="ACTIVE"
    )

    d = rec.to_dict()
    assert d["id"] == "test_rec_01"
    assert d["tier"] == "working"
    assert d["confidence"] == 0.85
    assert "Electronics" in d["entities"]
    assert d["status"] == "ACTIVE"
    assert len(d["relationships"]) == 1


def test_hmem_3_tier_stratification() -> None:
    """Verifies distinct tier storage and retrieval across short_term, working, and long_term."""
    engine = HMemEngine()

    r_short = HMemRecord(
        id="sql_01",
        tier="short_term",
        content="SELECT * FROM TPCDS_DB.web_returns",
        source="ZetarisRetriever",
        confidence=1.0,
        provenance={"latency_ms": 120}
    )
    r_working = HMemRecord(
        id="H1",
        tier="working",
        content="Product return defect hypothesis",
        source="HypothesisPlanner",
        confidence=0.5,
        provenance={"turn": 1}
    )
    r_long = HMemRecord(
        id="rule_01",
        tier="long_term",
        content="Electronics margin drop threshold is 15%",
        source="SystemConfig",
        confidence=0.99,
        provenance={"domain": "RetailOps"}
    )

    engine.mine(r_short)
    engine.mine(r_working)
    engine.mine(r_long)

    assert len(engine.records) == 3
    assert engine.records["sql_01"].tier == "short_term"
    assert engine.records["H1"].tier == "working"
    assert engine.records["rule_01"].tier == "long_term"


def test_hmem_trust_ledger_immutability() -> None:
    """Verifies that all mutations generate audit events in trust_ledger with valid timestamps."""
    engine = HMemEngine()
    r = HMemRecord(
        id="H1",
        tier="working",
        content="Initial claim",
        source="HypothesisPlanner",
        confidence=0.5,
        provenance={}
    )
    engine.mine(r)

    assert len(engine.trust_ledger) == 1
    event = engine.trust_ledger[0]
    assert event["action"] == "MINE"
    assert event["record_id"] == "H1"
    assert "timestamp" in event
    assert "Z" in event["timestamp"] or "+00:00" in event["timestamp"]


def test_hmem_rejection_branching_and_lineage() -> None:
    """Verifies that reject_and_branch correctly updates status, confidence, and records lineage."""
    engine = HMemEngine()
    r = HMemRecord(
        id="H1",
        tier="working",
        content="Product defect returns caused 18.5% margin drop",
        source="HypothesisPlanner",
        confidence=0.5,
        provenance={}
    )
    engine.mine(r)

    reason = "Return rate increased only 1.2%, insufficient to explain 18.5% drop."
    engine.reject_and_branch(
        rejected_id="H1",
        new_id="H2_H3_COMBINED",
        reason=reason,
        critic_confidence=0.42
    )

    rec = engine.records["H1"]
    assert rec.status == "REJECTED"
    assert rec.confidence == 0.42
    assert rec.replacement_lineage is not None
    assert rec.replacement_lineage["superseded_id"] == "H1"
    assert rec.replacement_lineage["replaced_by"] == "H2_H3_COMBINED"
    assert rec.replacement_lineage["reason"] == reason

    # Check rejected hypotheses accessor
    assert "H1" in engine.get_rejected_hypotheses()

    # Check audit ledger
    lineage_events = [e for e in engine.trust_ledger if e["action"] == "CLAIM_BLOCKED_LINEAGE"]
    assert len(lineage_events) == 1
    assert lineage_events[0]["record_id"] == "H1"


def test_hmem_markovian_carryover() -> None:
    """Verifies that Markovian carryover produces compact summaries without raw transcript bloat."""
    engine = HMemEngine()

    r1 = HMemRecord(
        id="H1",
        tier="working",
        content="Old hypothesis",
        source="HypothesisPlanner",
        confidence=0.4,
        provenance={}
    )
    engine.mine(r1)
    engine.reject_and_branch("H1", "H2", "Statistical insufficiency", 0.4)

    r2 = HMemRecord(
        id="H2",
        tier="working",
        content="Verified root cause",
        source="SkepticalCritic",
        confidence=0.92,
        provenance={"tables": ["inventory", "trip_data"]}
    )
    engine.mine(r2)

    carryover = engine.build_markovian_carryover()
    assert "rejected_hypotheses" in carryover
    assert len(carryover["rejected_hypotheses"]) == 1
    assert carryover["rejected_hypotheses"][0]["id"] == "H1"

    assert "approved_claims" in carryover
    assert len(carryover["approved_claims"]) == 1
    assert carryover["approved_claims"][0]["id"] == "H2"
    assert carryover["approved_claims"][0]["confidence"] == 0.92


def test_hmem_hybrid_retrieval() -> None:
    """Verifies hybrid retrieval ranking and exclusion of rejected records by default."""
    engine = HMemEngine()

    r1 = HMemRecord(
        id="H1",
        tier="working",
        content="Rejected claim",
        source="Planner",
        confidence=0.4,
        provenance={},
        entities=["Electronics", "Q3"]
    )
    engine.mine(r1)
    engine.reject_and_branch("H1", "H2", "Refuted", 0.4)

    r2 = HMemRecord(
        id="H2",
        tier="working",
        content="Active verified claim",
        source="Critic",
        confidence=0.95,
        provenance={},
        entities=["Electronics", "Warehouse"]
    )
    engine.mine(r2)

    results = engine.retrieve_hybrid(query_entities=["Electronics"], min_confidence=0.5)
    assert len(results) == 1
    assert results[0].id == "H2"

    # If include_rejected=True, both should be retrievable with lower min_confidence
    all_results = engine.retrieve_hybrid(query_entities=["Electronics"], min_confidence=0.0, include_rejected=True)
    assert len(all_results) == 2


def test_hmem_sleep_cycle_consolidation() -> None:
    """Verifies that consolidate_sleep_cycle promotes verified working memories to long_term."""
    engine = HMemEngine()

    r1 = HMemRecord(
        id="H_VERIFIED",
        tier="working",
        content="Strong validated finding",
        source="Critic",
        confidence=0.88,
        provenance={},
        status="ACTIVE"
    )
    r2 = HMemRecord(
        id="H_WEAK",
        tier="working",
        content="Weak unconfirmed finding",
        source="Planner",
        confidence=0.62,
        provenance={},
        status="ACTIVE"
    )
    engine.mine(r1)
    engine.mine(r2)

    promoted = engine.consolidate_sleep_cycle()
    assert promoted == 1
    assert engine.records["H_VERIFIED"].tier == "long_term"
    assert engine.records["H_VERIFIED"].status == "CONSOLIDATED"
    assert engine.records["H_WEAK"].tier == "working"
    assert engine.records["H_WEAK"].status == "ACTIVE"


def test_full_critic_loop_end_to_end(tmp_path: Path) -> None:
    """Verifies end-to-end execution of MarginWhy adversarial critic loop in sample mode."""
    trace_file = tmp_path / "test_trace.jsonl"
    orchestrator = MarginWhyOrchestrator(
        trace_log_path=str(trace_file),
        sample_mode=True
    )

    query = "Why did net profit margin for Electronics drop 18.5% in Q3?"
    result = orchestrator.run_investigation(query=query, scenario_file="scenario_1_electronics_q3.json")

    assert result["turns_executed"] == 2
    assert len(result["approved_claims"]) == 1
    assert result["approved_claims"][0]["confidence_score"] >= 0.70

    # Verify structured events
    events = result["trace_events"]
    event_names = [e.get("event") for e in events]
    assert "PLAN_GENERATED" in event_names
    assert "ZETARIS_QUERY_EXECUTED" in event_names
    assert "CLAIM_BLOCKED" in event_names
    assert "APPROVED_CLAIM" in event_names
    assert "REPORT_SYNTHESIZED" in event_names

    # Verify NVIDIA Nemotron model tagging
    critic_events = [e for e in events if e.get("agent") in ("SkepticalCritic", "HypothesisPlanner")]
    for ce in critic_events:
        assert "nemotron" in str(ce.get("model", "")).lower()

    # Verify report contains key sections
    report = result["report_markdown"]
    assert "Executive Summary & Core Diagnosis" in report
    assert "Evidence Cross-Examination & Refuted Hypotheses" in report
    assert "Prioritized Operational Mitigations" in report
    assert "Caveats & Data Limitations" in report

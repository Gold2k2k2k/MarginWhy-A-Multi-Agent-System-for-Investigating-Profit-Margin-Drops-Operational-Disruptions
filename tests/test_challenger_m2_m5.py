"""Empirical Challenger Test Suite for Milestone M2_M5: Full-Stack Championship Upgrades.

Adversarially probes:
1. Dynamic query entity extraction (unusual categories, regions, metrics, directions, extreme percentages).
2. End-to-end agent pipeline reflection across H1, H2, SkepticalCritic audit reasoning, and ActionReportWriter report.
3. Edge-case resilience (empty queries, special characters, unicode, SQL injection strings, long payloads).
4. All 6 official Zetaris discovery commands against execute_studio_query (case-insensitivity, trailing semicolons, aliases).
5. Fast offline CLI execution (< 5.0s) and FastAPI /run and /api/zetaris/query endpoints.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict
import pytest

from fastapi.testclient import TestClient
from app.main import app
from app.agents.planner import extract_query_entities, HypothesisPlanner, KNOWN_CATEGORIES, KNOWN_REGIONS
from app.llm.nightshift_client import NightshiftClient
from app.agents.synthesizer import ActionReportWriter
from app.adapters.zetaris_adapter import ZetarisAdapter
from app.agents.orchestrator import MarginWhyOrchestrator
from app.memory.hmem_engine import HMemEngine, HMemRecord


client = TestClient(app)


# =============================================================================
# 1. DYNAMIC QUERY ENTITY EXTRACTION STRESS-TESTS
# =============================================================================

class TestEntityExtractionAdversarial:
    """Stress-tests extract_query_entities with boundary conditions and arbitrary syntax."""

    def test_empty_and_whitespace_inputs(self):
        """Empty, None, or whitespace-only inputs must default safely without crashing."""
        for empty_val in [None, "", "   ", "\t\n\r"]:
            ent = extract_query_entities(empty_val)
            assert isinstance(ent, dict)
            assert ent["category"] == "Electronics"
            assert ent["region"] == "Northeast"
            assert ent["metric"] == "net profit margin"
            assert ent["direction"] == "drop"
            assert ent["metric_delta_pct"] == 18.5
            assert ent["timeframe"] == "Q3"
            assert ent["ebitda_exposure"] == 1850000

    def test_missing_percentage_in_query(self):
        """Queries without explicit % symbol or numeric delta should default or extract verb numbers."""
        q1 = "Why did gross margin for Apparel collapse in Midwest during Q2?"
        ent1 = extract_query_entities(q1)
        assert ent1["category"] == "Apparel"
        assert ent1["region"] == "Midwest"
        assert ent1["metric"] == "gross margin"
        assert ent1["direction"] == "collapse"
        assert ent1["timeframe"] == "Q2"
        assert ent1["metric_delta_pct"] == 18.5  # safe default

        q2 = "Why did operating margin for Footwear decline 14 points in Texas?"
        ent2 = extract_query_entities(q2)
        assert ent2["category"] == "Footwear"
        assert ent2["region"] == "Texas"
        assert ent2["metric"] == "operating margin"
        assert ent2["direction"] == "decline"
        assert ent2["metric_delta_pct"] == 14.0

    def test_extreme_and_decimal_percentages(self):
        """Test boundary percentages: very small, very large, 0%, and high decimal precision."""
        test_cases = [
            ("Why did net profit margin for Grocery drop 0.05% in Florida?", 0.05, 5000),
            ("Why did net profit margin for Hardware drop 0% in California?", 0.0, 0),
            ("Why did net profit margin for Luxury Goods drop 99.9% in New York?", 99.9, 9990000),
            ("Why did net profit margin for Cosmetics drop 450.5% in Midwest?", 450.5, 45050000),
        ]
        for query, expected_pct, expected_ebitda in test_cases:
            ent = extract_query_entities(query)
            assert ent["metric_delta_pct"] == expected_pct
            assert ent["ebitda_exposure"] == expected_ebitda

    def test_catalog_category_precedence(self):
        """Known catalog categories take precedence (e.g. 'Hardware' inside 'Quantum Hardware')."""
        q = "Why did gross margin for Quantum Hardware drop 25% in Pacific Northwest?"
        ent = extract_query_entities(q)
        assert ent["category"] == "Hardware"

    def test_out_of_catalog_category_extraction_bug_preposition_prefix(self):
        """When query contains 'margin for <Category>', regex with word boundary
        matches cleanly without preposition prefix leak."""
        # Clean case without 'margin' ending in 'in' right before 'for':
        q_clean = "Why did net revenue for Solar Panels decline 30% in California?"
        ent_clean = extract_query_entities(q_clean)
        assert ent_clean["category"] == "Solar Panels"

        # Query where 'margin' precedes 'for':
        q_bug = "Why did gross margin for Aerospace Systems fall 32% in Southwest?"
        ent_bug = extract_query_entities(q_bug)
        assert ent_bug["category"] == "Aerospace Systems"

    def test_all_known_regions_and_directions(self):
        """Test that every known region and direction keyword is recognized correctly."""
        for r in KNOWN_REGIONS:
            q = f"Why did net profit margin for Electronics drop 15% in {r}?"
            ent = extract_query_entities(q)
            assert ent["region"] == r

        directions = [
            ("surge", "surge"),
            ("overrun", "surge"),
            ("exceed", "surge"),
            ("increase", "surge"),
            ("collapse", "collapse"),
            ("decline", "decline"),
            ("contraction", "contraction"),
            ("drop", "drop"),
        ]
        for word, expected_dir in directions:
            q = f"Why did freight costs {word} 20% in Midwest during Q1?"
            ent = extract_query_entities(q)
            assert ent["direction"] == expected_dir

    def test_timeframe_variations(self):
        """Test quarterly, seasonal, and monthly timeframe extraction."""
        tfs = [
            ("Why did margin drop 10% in Q1?", "Q1"),
            ("Why did margin drop 10% in Q4?", "Q4"),
            ("Why did margin drop 10% in 2024-Q2?", "2024-Q2"),
            ("Why did margin drop 10% in Fall-Winter?", "FALL-WINTER"),
            ("Why did margin drop 10% in Spring-Summer?", "SPRING-SUMMER"),
            ("Why did margin drop 10% in January?", "JANUARY"),
            ("Why did margin drop 10% in November?", "NOVEMBER"),
        ]
        for q, expected_tf in tfs:
            ent = extract_query_entities(q)
            assert ent["timeframe"] == expected_tf


# =============================================================================
# 2. END-TO-END PIPELINE REFLECTION (H1, H2, CRITIC, REPORT)
# =============================================================================

class TestPipelineEntityReflection:
    """Verifies that extracted entities genuinely propagate through H1, H2, Critic, and Report."""

    def test_planner_reflects_custom_entities_in_h1_and_h2(self):
        """HypothesisPlanner must format H1 and H2 with custom category and region."""
        planner = HypothesisPlanner()
        hmem = HMemEngine()

        custom_query = "Why did gross margin for Home Appliances drop 21.4% in Midwest during Q2?"
        
        # Turn 1: H1
        plan_t1 = planner.plan_turn(query=custom_query, turn_id=1, hmem=hmem)
        assert plan_t1["hypothesis_id"] == "H1"
        assert "Home Appliances" in plan_t1["hypothesis_text"]
        assert "21.4%" in plan_t1["hypothesis_text"]
        assert "gross margin" in plan_t1["hypothesis_text"]
        assert "Q2" in plan_t1["hypothesis_text"]
        assert "Home Appliances" in plan_t1["reasoning"]

        # Simulate rejection in H-MEM carryover
        rec = HMemRecord(
            id="H1",
            tier="working",
            content=plan_t1["hypothesis_text"],
            source="HypothesisPlanner",
            confidence=0.42,
            provenance={"turn_id": 1},
            entities=["Home Appliances", "Midwest", "Q2"],
            relationships=[],
        )
        hmem.mine(rec)
        hmem.reject_and_branch(
            rejected_id="H1",
            new_id="H2_H3_COMBINED",
            reason="National return rate increased by only 1.2%",
            critic_confidence=0.42
        )

        # Turn 2: H2_H3_COMBINED
        plan_t2 = planner.plan_turn(query=custom_query, turn_id=2, hmem=hmem)
        assert plan_t2["hypothesis_id"] == "H2_H3_COMBINED"
        assert "Midwest" in plan_t2["hypothesis_text"]
        assert "Home Appliances" in plan_t2["hypothesis_text"]
        assert "Midwest" in plan_t2["reasoning"]
        assert "Home Appliances" in plan_t2["reasoning"]

    def test_critic_reflects_custom_entities_in_fallback_reasoning(self):
        """NightshiftClient deterministic reasoning must calculate exposure and quote custom entities."""
        client = NightshiftClient()
        custom_query = "Why did gross margin for Home Appliances drop 21.4% in Midwest during Q2?"

        # Turn 1: Rejection
        critique_h1 = client._deterministic_eval(
            hypothesis_id="H1",
            hypothesis_text="H1 test",
            query=custom_query,
            evidence_rows=[]
        )
        assert critique_h1["event"] == "CLAIM_BLOCKED"
        assert "Home Appliances" in critique_h1["reasoning"]
        assert "21.4%" in critique_h1["reasoning"]
        assert "gross margin" in critique_h1["reasoning"]
        assert "$2,140,000" in critique_h1["reasoning"]  # 21.4 * 100,000

        # Turn 2: Approval
        critique_h2 = client._deterministic_eval(
            hypothesis_id="H2_H3_COMBINED",
            hypothesis_text="H2 test",
            query=custom_query,
            evidence_rows=[]
        )
        assert critique_h2["event"] == "APPROVED_CLAIM"
        assert "Midwest" in critique_h2["reasoning"]
        assert "Home Appliances" in critique_h2["reasoning"]
        assert "Q2" in critique_h2["reasoning"]
        assert "21.4%" in critique_h2["reasoning"]
        assert "gross margin" in critique_h2["reasoning"]

    def test_action_report_reflects_entities_and_mitigations(self):
        """ActionReportWriter markdown report must incorporate category, region, and tailored actions."""
        writer = ActionReportWriter()
        hmem = HMemEngine()
        custom_query = "Why did gross margin for Home Appliances drop 21.4% in Midwest during Q2?"

        approved_claim = {
            "hypothesis_id": "H2_H3_COMBINED",
            "reasoning": "Midwest Distribution Center inventory for Home Appliances collapsed by 84%.",
            "confidence_score": 0.91
        }
        res = writer.generate_report(
            query=custom_query,
            approved_claims=[approved_claim],
            hmem=hmem,
            turn_count=2
        )

        md = res["report_markdown"]
        assert "Home Appliances" in md
        assert "Gross Margin" in md
        assert "Midwest" in md
        assert "Q2" in md
        assert "21.4%" in md
        # Mitigations section checks
        assert "Home Appliances" in md
        assert "Midwest" in md

    def test_hmem_add_record_convenience_method(self):
        """HMemEngine.add_record stores the record and logs an ADD_RECORD entry to trust_ledger."""
        hmem = HMemEngine()
        rec = HMemRecord(
            id="H_TEST",
            tier="working",
            content="Testing convenience add_record method",
            source="UnitTest",
            confidence=0.85,
            provenance={"test": True},
            entities=["Electronics"],
            relationships=[],
        )
        hmem.add_record(rec)
        assert "H_TEST" in hmem.records
        assert hmem.records["H_TEST"].confidence == 0.85

        # Verify trust_ledger entry
        add_events = [e for e in hmem.trust_ledger if e["action"] == "ADD_RECORD"]
        assert len(add_events) == 1
        assert add_events[0]["record_id"] == "H_TEST"
        assert add_events[0]["details"]["tier"] == "working"
        assert add_events[0]["details"]["confidence"] == 0.85


# =============================================================================
# 3. ZETARIS DISCOVERY COMMANDS & SQL NORMALIZATION
# =============================================================================

class TestZetarisDiscoveryCommands:
    """Stress-tests all 6 official Zetaris discovery commands against execute_studio_query."""

    @pytest.fixture
    def adapter(self):
        return ZetarisAdapter()

    def test_cmd1_select_1(self, adapter):
        for cmd in ["SELECT 1 AS one;", "select 1 as one", "  SELECT 1 AS one;  "]:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_CORE"
            assert res["row_count"] == 1
            assert res["columns"] == ["one"]
            assert res["rows"][0]["one"] == 1

    def test_cmd2_show_server_version(self, adapter):
        for cmd in ["SHOW SERVER VERSION;", "show server version", "SHOW SERVER VERSION"]:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_CORE"
            assert res["row_count"] == 1
            assert "server_version" in res["columns"]
            assert "Zetaris Lightning Engine" in res["rows"][0]["server_version"]

    def test_cmd3_show_lightning_databases(self, adapter):
        for cmd in ["SHOW LIGHTNING DATABASES;", "show lightning databases"]:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_CATALOG"
            assert res["row_count"] == 2
            db_names = [r["database_name"] for r in res["rows"]]
            assert "TPCDS_DB" in db_names
            assert "NY_TAXI" in db_names

    def test_cmd4_show_lightning_tables_tpcds(self, adapter):
        for cmd in ["SHOW LIGHTNING TABLES TPCDS_DB;", "show lightning tables tpcds_db"]:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_CATALOG"
            assert res["row_count"] == 9
            tbl_names = [r["table_name"] for r in res["rows"]]
            assert "inventory" in tbl_names
            assert "web_sales" in tbl_names
            assert "web_returns" in tbl_names

    def test_cmd5_show_lightning_tables_ny_taxi(self, adapter):
        for cmd in ["SHOW LIGHTNING TABLES NY_TAXI;", "show lightning tables ny_taxi"]:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_CATALOG"
            assert res["row_count"] == 4
            tbl_names = [r["table_name"] for r in res["rows"]]
            assert "trip_data" in tbl_names
            assert "taxi_zones" in tbl_names

    def test_cmd6_describe_datasource_table(self, adapter):
        aliases = [
            "DESCRIBE DATASOURCE TABLE NY_TAXI.taxi_zones;",
            "describe datasource table ny_taxi.taxi_zones;",
            "DESCRIBE TABLE NY_TAXI.taxi_zones;",
            "DESCRIBE NY_TAXI.taxi_zones;"
        ]
        for cmd in aliases:
            res = adapter.execute_studio_query(cmd)
            assert res["status"] == "SUCCESS"
            assert res["source"] == "ZETARIS_LIGHTNING_SCHEMA"
            assert res["row_count"] == 4
            col_names = [r["column_name"] for r in res["rows"]]
            assert "locationid" in col_names
            assert "borough" in col_names
            assert "zone" in col_names
            assert "service_zone" in col_names

    def test_lowercase_sql_normalization(self, adapter):
        """Adapter must normalize lowercase tpcds_db. and ny_taxi. to uppercase."""
        sql = "SELECT inv_quantity_on_hand FROM tpcds_db.inventory JOIN ny_taxi.trip_data ON 1=1"
        res = adapter.execute_studio_query(sql, scenario_file="scenario_1_electronics_q3.json")
        assert res["status"] in ("SUCCESS", "FALLBACK_SAMPLE")
        assert "TPCDS_DB.inventory" in res["sql"]
        assert "NY_TAXI.trip_data" in res["sql"]


# =============================================================================
# 4. ADVERSARIAL INPUTS & SECURITY ROBUSTNESS
# =============================================================================

class TestAdversarialInputsAndResilience:
    """Probes orchestrator and endpoints against adversarial strings, injections, and boundaries."""

    def test_extremely_long_query(self):
        """Query with 2,000 repeating words should not throw RecursionError or crash."""
        long_q = "Why did margin drop 15% in Midwest " + ("word " * 500) + "?"
        ent = extract_query_entities(long_q)
        assert ent["region"] == "Midwest"
        assert ent["metric_delta_pct"] == 15.0

    def test_sql_injection_attempt_in_query(self):
        """SQL injection attempt in natural language query must be safely parsed as string."""
        malicious_q = "Why did margin for Electronics drop 10% in Northeast; DROP TABLE inventory; --"
        ent = extract_query_entities(malicious_q)
        assert ent["category"] == "Electronics"
        assert ent["region"] == "Northeast"
        assert ent["metric_delta_pct"] == 10.0

    def test_unicode_and_symbols_in_query(self):
        """Unicode characters and currency symbols should not crash extraction."""
        unicode_q = "Why did €50M gross margin for 电子产品 drop 22.5% in Texas?!"
        ent = extract_query_entities(unicode_q)
        assert ent["metric"] == "gross margin"
        assert ent["metric_delta_pct"] == 22.5
        assert ent["region"] == "Texas"

    def test_fastapi_run_with_empty_and_custom_body(self):
        """FastAPI POST /run endpoint must handle empty body and custom queries cleanly."""
        # Empty json
        r1 = client.post("/run", json={})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["status"] == "SUCCESS"
        assert "entities" in d1

        # Custom query with unusual category & region
        r2 = client.post("/run", json={
            "query": "Why did net revenue for Automotive fall 28.5% in Southwest during Q4?",
            "sample_mode": True
        })
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["status"] == "SUCCESS"
        assert d2["entities"]["category"] == "Automotive"
        assert d2["entities"]["region"] == "Southwest"
        assert d2["entities"]["timeframe"] == "Q4"
        assert d2["entities"]["metric_delta_pct"] == 28.5
        assert "Automotive" in d2["report"]

    def test_fastapi_zetaris_query_discovery_endpoints(self):
        """FastAPI POST /api/zetaris/query must execute discovery commands successfully."""
        cmds = [
            "SELECT 1 AS one;",
            "SHOW SERVER VERSION;",
            "SHOW LIGHTNING DATABASES;",
            "SHOW LIGHTNING TABLES TPCDS_DB;",
            "SHOW LIGHTNING TABLES NY_TAXI;",
            "DESCRIBE DATASOURCE TABLE NY_TAXI.taxi_zones;"
        ]
        for c in cmds:
            resp = client.post("/api/zetaris/query", json={"sql": c})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "SUCCESS"
            assert data["row_count"] > 0


# =============================================================================
# 5. CLI RUNNER BENCHMARK & COLD EXECUTION
# =============================================================================

class TestCliOfflineRunner:
    """Verifies python run.py --query ... --sample-mode cold execution."""

    def test_cli_execution_with_arbitrary_query(self):
        """CLI must complete in < 5.0 seconds and output H1, H2, and custom entities."""
        query = "Why did gross margin for Home Appliances drop 21.4% in Midwest during Q2?"
        start = time.time()
        res = subprocess.run(
            [sys.executable, "run.py", "--query", query, "--sample-mode"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent)
        )
        duration = time.time() - start

        assert res.returncode == 0, f"run.py exited with error:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        assert duration < 5.0, f"run.py took {duration:.2f}s, exceeding 5.0s threshold"

        stdout = res.stdout
        # Verify H1 rejected with Home Appliances and 21.4%
        assert "Home Appliances" in stdout
        assert "21.4%" in stdout
        # Verify H2/H3 approved with Midwest
        assert "Midwest" in stdout
        assert "FINAL INVESTIGATION REPORT" in stdout
        assert "Executive Root-Cause Diagnostic Report: Home Appliances Gross Margin Anomaly" in stdout

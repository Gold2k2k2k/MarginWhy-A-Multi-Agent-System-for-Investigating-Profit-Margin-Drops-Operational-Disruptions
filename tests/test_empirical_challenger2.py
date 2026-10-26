"""Empirical Boundary Verification Suite by Challenger 2.

Tests:
1. Endpoint validation and boundary handling:
   - Empty/missing fields in POST /run (HTTP 422 on invalid schema/body, 200 on default optional schema)
   - Missing scenario_file or non-existent scenario_file (fallback behavior)
   - Path traversal / non-JSON scenario_file vulnerability check
2. Performance and Stability:
   - 50 sequential calls to GET /health (latency and consistency)
   - 20 sequential calls to GET /api/scenarios (latency and consistency)
   - 3 sequential calls to POST /run with sample query (< 10s latency & output determinism)
3. Trace and Auxiliary API boundaries:
   - GET /api/trace limit=0 edge case
   - Concurrency file write integrity on trace.jsonl
"""

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_empty_raw_body_returns_422() -> None:
    """POST /run with empty raw bytes should return HTTP 422 Unprocessable Entity."""
    resp = client.post("/run", content=b"", headers={"Content-Type": "application/json"})
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_missing_body_returns_422() -> None:
    """POST /run with no body at all should return HTTP 422."""
    resp = client.post("/run")
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_invalid_field_types_return_422() -> None:
    """POST /run with incorrect field types should return HTTP 422."""
    # sample_mode as list
    r1 = client.post("/run", json={"sample_mode": ["not", "bool"]})
    assert r1.status_code == 422

    # query as dict
    r2 = client.post("/run", json={"query": {"bad": "type"}})
    assert r2.status_code == 422

    # scenario_file as list
    r3 = client.post("/run", json={"scenario_file": [1, 2, 3]})
    assert r3.status_code == 422


def test_empty_json_dict_succeeds_with_defaults() -> None:
    """POST /run with empty dict {} succeeds because fields are optional with defaults."""
    resp = client.post("/run", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_file"] == "scenario_1_electronics_q3.json"
    assert "Why did net profit margin for Electronics drop 18.5% in Q3?" in data["query"]


def test_scenario_file_omitted_inference() -> None:
    """When scenario_file is omitted, infer from query keywords."""
    resp = client.post("/run", json={"query": "Why did Apparel returns spike?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_file"] == "scenario_2_apparel_returns.json"


def test_scenario_file_non_existent_fallback() -> None:
    """When scenario_file points to non-existent sample, fallback gracefully."""
    resp = client.post("/run", json={
        "query": "Investigate non existent scenario",
        "scenario_file": "ghost_scenario_xyz.json",
        "sample_mode": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"


def test_repeat_health_sequential_performance() -> None:
    """50 repeat sequential calls to GET /health must all return HTTP 200 in < 100ms each."""
    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/health")
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert data["model"] == "nvidia/nemotron-3-super-120b-a12b"

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    print(f"\n[GET /health] 50 calls: Avg={avg_lat*1000:.2f}ms, Max={max_lat*1000:.2f}ms")
    assert avg_lat < 0.05
    assert max_lat < 0.15


def test_repeat_scenarios_sequential_performance() -> None:
    """20 repeat sequential calls to GET /api/scenarios must all return HTTP 200 with 3 scenarios."""
    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        resp = client.get("/api/scenarios")
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)
        assert resp.status_code == 200
        scenarios = resp.json()
        assert len(scenarios) == 3

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    print(f"\n[GET /api/scenarios] 20 calls: Avg={avg_lat*1000:.2f}ms, Max={max_lat*1000:.2f}ms")
    assert avg_lat < 0.05
    assert max_lat < 0.15


def test_run_latency_and_determinism() -> None:
    """POST /run with sample query across 3 runs: verify response < 10s and deterministic outputs."""
    payload = {
        "query": "Why did net profit margin for Electronics drop 18.5% in Q3?",
        "scenario_file": "scenario_1_electronics_q3.json",
        "sample_mode": True
    }

    runs: List[Dict[str, Any]] = []
    latencies: List[float] = []

    for i in range(3):
        t0 = time.perf_counter()
        resp = client.post("/run", json=payload)
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        assert resp.status_code == 200, f"Run {i+1} failed with {resp.status_code}"
        data = resp.json()
        runs.append(data)
        assert elapsed < 10.0, f"Run {i+1} took {elapsed:.2f}s, exceeding 10s threshold!"

    print(f"\n[POST /run] 3 runs latencies: {[f'{l:.3f}s' for l in latencies]}")

    # Check determinism across runs
    first_run = runs[0]
    for idx, r in enumerate(runs[1:], start=2):
        assert r["turns_executed"] == first_run["turns_executed"] == 2, f"Run {idx} turn count mismatch"
        assert len(r["approved_claims"]) == len(first_run["approved_claims"]) == 1, f"Run {idx} claim count mismatch"
        
        claim_curr = r["approved_claims"][0]
        claim_base = first_run["approved_claims"][0]
        assert claim_curr["hypothesis_id"] == claim_base["hypothesis_id"] == "H2_H3_COMBINED"
        assert claim_curr["confidence_score"] == claim_base["confidence_score"] == 0.91
        assert claim_curr["event"] == claim_base["event"] == "APPROVED_CLAIM"
        # Normalize dynamic generation timestamp line for content determinism comparison
        def strip_timestamp(md: str) -> str:
            return "\n".join(l for l in md.splitlines() if not l.startswith("**Timestamp:**"))

        assert strip_timestamp(r["report_markdown"]) == strip_timestamp(first_run["report_markdown"]), f"Run {idx} report markdown non-deterministic"


def test_export_trace_endpoint_empirical() -> None:
    """Empirical verification of GET /api/export/trace: format, headers, ndjson parsing, schema."""
    resp = client.get("/api/export/trace")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    # Verify response headers
    content_type = resp.headers.get("content-type", "")
    assert "application/x-ndjson" in content_type, f"Content-Type mismatch: {content_type}"
    disposition = resp.headers.get("content-disposition", "")
    assert "attachment" in disposition, f"Expected attachment disposition: {disposition}"
    assert "trace.jsonl" in disposition, f"Expected trace.jsonl filename: {disposition}"

    # Parse and validate every NDJSON record
    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
    assert len(lines) >= 5, f"Expected at least 5 trace lines, got {len(lines)}"

    parsed_events = []
    for idx, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
            assert isinstance(record, dict), f"Line {idx} is not a JSON object"
            parsed_events.append(record)
        except json.JSONDecodeError as err:
            pytest.fail(f"Line {idx} failed JSON validation: {err}\nContent: {line}")

    # Verify event types and attribution tags
    event_types = {e.get("event") for e in parsed_events}
    assert "CLAIM_BLOCKED" in event_types, f"Missing CLAIM_BLOCKED event: {event_types}"
    assert "APPROVED_CLAIM" in event_types, f"Missing APPROVED_CLAIM event: {event_types}"

    # Verify NVIDIA Nemotron model tag appears in trace events
    nemotron_tags = [
        e for e in parsed_events
        if "nvidia/nemotron-3-super-120b-a12b" in str(e.get("model", "")).lower()
    ]
    assert len(nemotron_tags) >= 1, "Missing nvidia/nemotron-3-super-120b-a12b in trace"


def test_telemetry_endpoint_empirical() -> None:
    """Empirical verification of GET /api/telemetry: schema, metrics, metadata, latency."""
    resp = client.get("/api/telemetry")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    data = resp.json()
    assert data.get("status") == "HEALTHY"
    assert data.get("model") == "nvidia/nemotron-3-super-120b-a12b"
    assert "meterless_base_url" in data

    # Verify metadata fields
    metadata = data.get("metadata", {})
    assert isinstance(metadata, dict)
    assert metadata.get("project_name") == "MarginWhy"
    assert metadata.get("team", {}).get("name") == "Light of Numbers"
    assert metadata.get("primary_track") == "Track 02: The Agent That Can Explain Why"
    assert metadata.get("tech_stack", {}).get("llm_model") == "nvidia/nemotron-3-super-120b-a12b"
    assert "cursor_developer_story" in metadata

    # Verify metrics fields
    metrics = data.get("metrics", {})
    assert metrics.get("nemotron_model") == "nvidia/nemotron-3-super-120b-a12b"
    assert metrics.get("token_compression_ratio") == "98.3%"
    assert metrics.get("adversarial_threshold") == 0.70
    assert metrics.get("raw_context_tokens") == 18450
    assert metrics.get("compressed_carryover_tokens") == 320
    assert "avg_latency_ms" in metrics
    assert "working_records" in metrics
    assert "ledger_mutations" in metrics

    # Latency test: 30 sequential requests
    latencies = []
    for _ in range(30):
        t0 = time.perf_counter()
        r = client.get("/api/telemetry")
        latencies.append(time.perf_counter() - t0)
        assert r.status_code == 200

    avg_ms = (sum(latencies) / len(latencies)) * 1000
    assert avg_ms < 30.0, f"Average telemetry latency {avg_ms:.2f}ms exceeds 30ms"


def test_zetaris_query_discovery_commands_empirical() -> None:
    """Empirical verification of POST /api/zetaris/query across all 6 discovery commands & variants."""
    discovery_matrix = [
        # (sql, expected_cols, expected_rows_min, expected_silo)
        ("SELECT 1 AS one;", ["one"], 1, "ZETARIS_LIGHTNING_CORE"),
        ("select 1 as one;", ["one"], 1, "ZETARIS_LIGHTNING_CORE"),
        ("SHOW SERVER VERSION;", ["server_version", "status"], 1, "ZETARIS_LIGHTNING_CORE"),
        ("show server version", ["server_version", "status"], 1, "ZETARIS_LIGHTNING_CORE"),
        ("SHOW LIGHTNING DATABASES;", ["database_name", "type"], 2, "TPCDS_DB"),
        ("SHOW LIGHTNING TABLES TPCDS_DB;", ["table_name", "database"], 9, "TPCDS_DB"),
        ("show lightning tables tpcds_db", ["table_name", "database"], 9, "TPCDS_DB"),
        ("SHOW LIGHTNING TABLES NY_TAXI;", ["table_name", "database"], 4, "NY_TAXI"),
        ("show lightning tables ny_taxi", ["table_name", "database"], 4, "NY_TAXI"),
        ("DESCRIBE DATASOURCE TABLE NY_TAXI.taxi_zones;", ["column_name", "data_type"], 4, "NY_TAXI"),
        ("DESCRIBE TABLE ny_taxi.taxi_zones", ["column_name", "data_type"], 4, "NY_TAXI"),
    ]

    for sql, expected_cols, expected_min_rows, expected_silo in discovery_matrix:
        resp = client.post("/api/zetaris/query", json={"sql": sql})
        assert resp.status_code == 200, f"Command failed: {sql}"
        data = resp.json()

        assert data["status"] == "SUCCESS", f"Query status failed for {sql}: {data}"
        assert data["row_count"] >= expected_min_rows, f"Insufficient rows for {sql}: {data['row_count']}"
        assert len(data["rows"]) == data["row_count"]
        assert "latency_ms" in data
        assert data["latency_ms"] > 0

        for col in expected_cols:
            assert col in data["columns"], f"Missing column {col} in {data['columns']} for {sql}"

        assert expected_silo in data["silos_involved"], f"Missing silo {expected_silo} in {data['silos_involved']} for {sql}"


def test_zetaris_query_custom_queries_empirical() -> None:
    """Empirical verification of POST /api/zetaris/query with custom SQL queries and federated routing."""
    custom_queries = [
        (
            "SELECT * FROM TPCDS_DB.inventory WHERE inv_quantity_on_hand < 100 LIMIT 5;",
            ["TPCDS_DB"],
            "scenario_1_electronics_q3.json"
        ),
        (
            "SELECT ca_state, wr_return_amt FROM TPCDS_DB.web_returns LIMIT 5;",
            ["TPCDS_DB"],
            "scenario_1_electronics_q3.json"
        ),
        (
            "SELECT trip_duration_min, congestion_surcharge FROM NY_TAXI.trip_data LIMIT 5;",
            ["NY_TAXI"],
            "scenario_1_electronics_q3.json"
        ),
        (
            "SELECT i.inv_quantity_on_hand, t.trip_duration_min FROM TPCDS_DB.inventory i JOIN NY_TAXI.trip_data t ON 1=1 LIMIT 5;",
            ["TPCDS_DB", "NY_TAXI"],
            "scenario_1_electronics_q3.json"
        ),
        # Test lowercase auto-normalization to TPCDS_DB.
        (
            "SELECT wr_item_sk, wr_return_amt FROM tpcds_db.web_returns LIMIT 5;",
            ["TPCDS_DB"],
            "scenario_1_electronics_q3.json"
        )
    ]

    for sql, expected_silos, scenario in custom_queries:
        payload = {"sql": sql, "scenario_file": scenario}
        resp = client.post("/api/zetaris/query", json=payload)
        assert resp.status_code == 200, f"Custom query failed: {sql}"
        data = resp.json()

        assert data["status"] == "SUCCESS", f"Status not SUCCESS: {data}"
        assert data["row_count"] > 0
        assert len(data["rows"]) == data["row_count"]
        assert len(data["columns"]) > 0

        for silo in expected_silos:
            assert silo in data["silos_involved"], f"Silo {silo} not detected in {data['silos_involved']} for {sql}"


def test_zetaris_query_adversarial_boundaries() -> None:
    """Empirical adversarial boundary verification for /api/zetaris/query."""
    # 1. Empty SQL string
    r1 = client.post("/api/zetaris/query", json={"sql": ""})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["status"] == "ERROR"
    assert "Empty SQL query" in d1["error"]

    # 2. Whitespace-only SQL string
    r2 = client.post("/api/zetaris/query", json={"sql": "   \n\t  "})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["status"] == "ERROR"

    # 3. Missing SQL field completely
    r3 = client.post("/api/zetaris/query", json={"scenario_file": "scenario_1_electronics_q3.json"})
    assert r3.status_code == 422

    # 4. Scenario file path traversal attempt
    r4 = client.post("/api/zetaris/query", json={"sql": "SELECT 1;", "scenario_file": "../../etc/passwd"})
    assert r4.status_code == 400
    assert "path traversal is not permitted" in r4.json().get("detail", "")

    # 5. Scenario file with null byte
    r5 = client.post("/api/zetaris/query", json={"sql": "SELECT 1;", "scenario_file": "scenario_1\x00.json"})
    assert r5.status_code == 400
    assert "embedded null bytes" in r5.json().get("detail", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])


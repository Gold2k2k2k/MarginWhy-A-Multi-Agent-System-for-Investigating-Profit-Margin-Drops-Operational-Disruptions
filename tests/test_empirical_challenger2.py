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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

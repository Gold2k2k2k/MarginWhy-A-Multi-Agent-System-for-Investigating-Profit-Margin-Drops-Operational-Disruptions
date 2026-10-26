"""Adversarial and Empirical Stress Test Suite for FastAPI Application (app/main.py).

Tests:
1. Malformed payload edge cases:
   - Missing fields, None fields, empty strings.
   - Invalid JSON types (int/list where str expected).
   - Broken JSON syntax.
   - Empty body with JSON header.
2. Non-existent and boundary scenario files:
   - Non-existent filename.
   - Path traversal attempt (../../).
   - Empty scenario string.
3. Auxiliary endpoints edge cases:
   - /health consistency and latency across rapid repeated calls.
   - /api/scenarios repeated calls.
   - /api/trace with limit=-1, limit=0, limit=999999, limit='invalid'.
   - /api/hmem state sanity.
4. Concurrency & Sequential Integrity:
   - Sequential runs with alternating scenarios (Apparel, Shipping, Electronics).
   - Multi-threaded concurrent execution to test H-MEM dictionary iteration safety
     and trace log file atomicity.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ============================================================================
# 1. Malformed Payload Tests
# ============================================================================

def test_malformed_empty_json_body(client: TestClient) -> None:
    """POST /run with empty JSON object {} should succeed with defaults."""
    resp = client.post("/run", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "query" in data
    assert "report" in data


def test_malformed_empty_string_query(client: TestClient) -> None:
    """POST /run with empty string query should gracefully fallback to default query."""
    resp = client.post("/run", json={"query": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert len(data["query"]) > 0


def test_malformed_none_fields(client: TestClient) -> None:
    """POST /run with explicit None values for query and scenario_file."""
    resp = client.post("/run", json={"query": None, "scenario_file": None, "sample_mode": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"


def test_malformed_invalid_sample_mode_type(client: TestClient) -> None:
    """POST /run with invalid boolean type for sample_mode should return HTTP 422."""
    resp = client.post("/run", json={"query": "test query", "sample_mode": "not_a_boolean_12345"})
    assert resp.status_code == 422


def test_malformed_invalid_query_type(client: TestClient) -> None:
    """POST /run with non-string query (e.g. list or nested dict) should return HTTP 422."""
    resp = client.post("/run", json={"query": ["invalid", "query", "list"]})
    assert resp.status_code == 422

    resp2 = client.post("/run", json={"query": {"nested": "dict"}})
    assert resp2.status_code == 422


def test_malformed_invalid_scenario_file_type(client: TestClient) -> None:
    """POST /run with non-string scenario_file (e.g. list) should return HTTP 422."""
    resp = client.post("/run", json={"scenario_file": [1, 2, 3]})
    assert resp.status_code == 422


def test_malformed_syntax_raw_bytes(client: TestClient) -> None:
    """POST /run with completely broken JSON syntax should return HTTP 422 or 400, not 500."""
    resp = client.post(
        "/run",
        content=b"{broken: json, missing quotes",
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code in (400, 422)


def test_malformed_empty_raw_body(client: TestClient) -> None:
    """POST /run with empty raw body and Content-Type application/json should return HTTP 422."""
    resp = client.post(
        "/run",
        content=b"",
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 422


def test_malformed_extra_unexpected_fields(client: TestClient) -> None:
    """POST /run with extra ignored fields should succeed gracefully."""
    resp = client.post(
        "/run",
        json={
            "query": "Why did net profit margin for Electronics drop 18.5% in Q3?",
            "unexpected_token": "ignore_me",
            "injection_attempt": "'; DROP TABLE test;--"
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCESS"


# ============================================================================
# 2. Non-existent and Boundary Scenario Files
# ============================================================================

def test_nonexistent_scenario_file(client: TestClient) -> None:
    """POST /run with non-existent scenario file should execute gracefully or handle cleanly without server crash."""
    resp = client.post(
        "/run",
        json={
            "query": "Why did net profit margin for Electronics drop 18.5% in Q3?",
            "scenario_file": "non_existent_scenario_999.json",
            "sample_mode": True
        }
    )
    # Server should not crash with unhandled 500; should succeed with fallback or graceful status
    assert resp.status_code in (200, 400, 404, 422)
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] == "SUCCESS"


def test_path_traversal_scenario_file(client: TestClient) -> None:
    """POST /run with path traversal string in scenario_file should not leak or crash server."""
    resp = client.post(
        "/run",
        json={
            "query": "Why did net profit margin for Electronics drop 18.5% in Q3?",
            "scenario_file": "../../../../../windows/system32/calc.exe",
            "sample_mode": True
        }
    )
    assert resp.status_code in (200, 400, 403, 404, 422)


def test_empty_scenario_file_string(client: TestClient) -> None:
    """POST /run with empty string scenario_file should fall back to query keyword inference or default."""
    resp = client.post(
        "/run",
        json={
            "query": "Why did net profit margin for Apparel drop in Q3?",
            "scenario_file": "",
            "sample_mode": True
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "apparel" in data["scenario_file"].lower()


# ============================================================================
# 3. Auxiliary Endpoints Robustness & Performance
# ============================================================================

def test_health_rapid_repeated_calls(client: TestClient) -> None:
    """GET /health must respond in < 100ms and return identical system metadata across 30 repeated calls."""
    latencies = []
    for _ in range(30):
        t0 = time.perf_counter()
        resp = client.get("/health")
        latencies.append(time.perf_counter() - t0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert data["system"] == "MarginWhy"
        assert data["model"] == "nvidia/nemotron-3-super-120b-a12b"

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    assert avg_latency < 0.05, f"Average /health latency too high: {avg_latency:.4f}s"
    assert max_latency < 0.20, f"Max /health latency too high: {max_latency:.4f}s"


def test_scenarios_repeated_calls(client: TestClient) -> None:
    """GET /api/scenarios must consistently return the 3 packaged scenarios."""
    for _ in range(10):
        resp = client.get("/api/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()
        assert len(scenarios) >= 3
        filenames = {s["filename"] for s in scenarios}
        assert "scenario_1_electronics_q3.json" in filenames
        assert "scenario_2_apparel_returns.json" in filenames
        assert "scenario_3_shipping_delay.json" in filenames


def test_trace_endpoint_edge_cases(client: TestClient) -> None:
    """GET /api/trace with various limit parameter values."""
    # Negative limit
    resp_neg = client.get("/api/trace?limit=-5")
    assert resp_neg.status_code == 200
    assert isinstance(resp_neg.json(), list)

    # Zero limit
    resp_zero = client.get("/api/trace?limit=0")
    assert resp_zero.status_code == 200
    assert resp_zero.json() == []

    # Extremely large limit
    resp_huge = client.get("/api/trace?limit=1000000")
    assert resp_huge.status_code == 200
    assert isinstance(resp_huge.json(), list)

    # Invalid non-integer limit
    resp_inv = client.get("/api/trace?limit=not_an_int")
    assert resp_inv.status_code == 422


def test_hmem_endpoint_structure(client: TestClient) -> None:
    """GET /api/hmem must return valid H-MEM state dictionary."""
    resp = client.get("/api/hmem")
    assert resp.status_code == 200
    data = resp.json()
    assert "carryover" in data
    assert "trust_ledger_count" in data
    assert "recent_ledger" in data
    assert "all_records" in data
    assert isinstance(data["all_records"], list)


# ============================================================================
# 4. Sequential and Concurrency Stress Testing
# ============================================================================

def test_sequential_cross_scenario_runs(client: TestClient) -> None:
    """Executing sequential runs across different business scenarios.
    
    Verifies that the orchestrator correctly processes different domains
    without corrupting report synthesis.
    """
    scenarios = [
        ("scenario_1_electronics_q3.json", "Why did net profit margin for Electronics drop 18.5% in Q3?"),
        ("scenario_2_apparel_returns.json", "Why did catalog profit margin for Apparel drop 12.3%?"),
        ("scenario_3_shipping_delay.json", "Why did Northeast shipping logistics costs surge 24%?")
    ]

    for scenario_file, query in scenarios:
        resp = client.post("/run", json={"scenario_file": scenario_file, "query": query, "sample_mode": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["scenario_file"] == scenario_file
        assert "report" in data
        assert len(data["approved_claims"]) >= 1


def test_concurrent_run_requests_thread_safety(client: TestClient) -> None:
    """Empirical Stress Test: Send concurrent requests across 4 worker threads.
    
    Tests:
    1. Does the server survive concurrent execution without unhandled 500 errors?
    2. Does dictionary iteration inside H-MEM raise RuntimeError?
    3. Are trace log lines in logs/trace.jsonl cleanly serialized without corrupted JSON?
    """
    trace_path = Path(__file__).resolve().parent.parent / "logs" / "trace.jsonl"
    
    # Record starting line count of trace log
    initial_lines = 0
    if trace_path.exists():
        with open(trace_path, "r", encoding="utf-8") as f:
            initial_lines = sum(1 for line in f if line.strip())

    queries = [
        {"query": "Why did net profit margin for Electronics drop 18.5% in Q3?", "scenario_file": "scenario_1_electronics_q3.json"},
        {"query": "Why did catalog profit margin for Apparel drop 12.3%?", "scenario_file": "scenario_2_apparel_returns.json"},
        {"query": "Why did Northeast shipping logistics costs surge 24%?", "scenario_file": "scenario_3_shipping_delay.json"},
        {"query": "Why did net profit margin for Electronics drop 18.5% in Q3?", "scenario_file": "scenario_1_electronics_q3.json"},
    ]

    def make_request(payload: dict) -> dict:
        t0 = time.perf_counter()
        resp = client.post("/run", json={**payload, "sample_mode": True})
        elapsed = time.perf_counter() - t0
        return {
            "status_code": resp.status_code,
            "elapsed": elapsed,
            "body": resp.json() if resp.status_code == 200 else resp.text
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(make_request, q) for q in queries]
        results = [f.result() for f in futures]

    # Verify all responses
    for idx, r in enumerate(results):
        assert r["status_code"] == 200, f"Concurrent request {idx} failed with {r['status_code']}: {r['body']}"
        assert r["body"]["status"] == "SUCCESS"

    # Audit trace log file atomicity: every line written during the test must be valid JSON
    assert trace_path.exists()
    corrupted_lines = []
    with open(trace_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                json.loads(line_str)
            except Exception as e:
                corrupted_lines.append((line_no, line_str, str(e)))

    assert len(corrupted_lines) == 0, f"Found corrupted JSON lines in trace.jsonl: {corrupted_lines}"


# ============================================================================
# 5. Post-Merge Endpoints Adversarial & Traversal Security
# ============================================================================

def test_export_markdown_path_traversal_rejected(client: TestClient) -> None:
    """GET /api/export/markdown with path traversal must return HTTP 400."""
    resp = client.get("/api/export/markdown?scenario_file=../../secret.txt")
    assert resp.status_code == 400
    assert "path traversal is not permitted" in resp.json()["detail"]

    resp2 = client.get("/api/export/markdown?scenario_file=..\\..\\secret.txt")
    assert resp2.status_code == 400


def test_export_markdown_sanitized_attachment_header(client: TestClient) -> None:
    """GET /api/export/markdown ensures filename header has no special characters or injection."""
    resp = client.get("/api/export/markdown?scenario_file=scenario_1_electronics_q3.json")
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    assert 'filename="MarginWhy_Executive_Report_scenario_1_electronics_q3.md"' in cd


def test_zetaris_query_path_traversal_rejected(client: TestClient) -> None:
    """POST /api/zetaris/query with path traversal in scenario_file must return HTTP 400."""
    resp = client.post("/api/zetaris/query", json={
        "sql": "SELECT 1;",
        "scenario_file": "../../secret.txt"
    })
    assert resp.status_code == 400
    assert "path traversal is not permitted" in resp.json()["detail"]


def test_scenarios_cache_refresh(client: TestClient) -> None:
    """GET /api/scenarios?refresh=true forces scenario cache reload."""
    resp = client.get("/api/scenarios?refresh=true")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3


def test_export_markdown_windows_drive_and_null_byte_rejected(client: TestClient) -> None:
    """GET /api/export/markdown rejects Windows drive letter paths and null bytes with HTTP 400."""
    resp_drive = client.get("/api/export/markdown?scenario_file=C:secret.txt")
    assert resp_drive.status_code == 400
    assert "path traversal is not permitted" in resp_drive.json()["detail"]

    resp_null = client.get("/api/export/markdown?scenario_file=test%00abc")
    assert resp_null.status_code == 400
    assert "null bytes" in resp_null.json()["detail"]


def test_zetaris_query_windows_drive_and_null_byte_rejected(client: TestClient) -> None:
    """POST /api/zetaris/query rejects Windows drive letter paths and null bytes with HTTP 400."""
    resp_drive = client.post("/api/zetaris/query", json={
        "sql": "SELECT 1;",
        "scenario_file": "C:secret.txt"
    })
    assert resp_drive.status_code == 400
    assert "path traversal is not permitted" in resp_drive.json()["detail"]

    resp_null = client.post("/api/zetaris/query", json={
        "sql": "SELECT 1;",
        "scenario_file": "test\x00abc"
    })
    assert resp_null.status_code == 400
    assert "null bytes" in resp_null.json()["detail"]


def test_run_investigation_windows_drive_and_null_byte_rejected(client: TestClient) -> None:
    """POST /run rejects Windows drive letters, null bytes, and traversal in scenario_file with HTTP 400."""
    resp_drive = client.post("/run", json={"scenario_file": "C:secret.txt"})
    assert resp_drive.status_code == 400
    assert "path traversal is not permitted" in resp_drive.json()["detail"]

    resp_null = client.post("/run", json={"scenario_file": "test\x00abc"})
    assert resp_null.status_code == 400
    assert "null bytes" in resp_null.json()["detail"]


def test_run_investigation_input_nested_traversal_rejected(client: TestClient) -> None:
    """POST /run rejects traversal and invalid types supplied within the nested input dictionary."""
    resp_nested = client.post("/run", json={
        "input": {"scenario_file": "C:secret.txt"}
    })
    assert resp_nested.status_code == 400
    assert "path traversal is not permitted" in resp_nested.json()["detail"]

    resp_invalid_type = client.post("/run", json={
        "input": {"scenario_file": [1, 2, 3]}
    })
    assert resp_invalid_type.status_code == 400
    assert "must be a string" in resp_invalid_type.json()["detail"]


def test_run_investigation_nested_query_and_sample_mode_type_validation(client: TestClient) -> None:
    """POST /run rejects invalid types for query in input and sample_mode in options with HTTP 400."""
    # query as list in input
    resp_query_list = client.post("/run", json={"input": {"query": [1, 2, 3]}})
    assert resp_query_list.status_code == 400
    assert "Invalid query: must be a string." in resp_query_list.json()["detail"]

    # query as dict in input
    resp_query_dict = client.post("/run", json={"input": {"query": {"bad": "type"}}})
    assert resp_query_dict.status_code == 400
    assert "Invalid query: must be a string." in resp_query_dict.json()["detail"]

    # sample_mode as string in options
    resp_sample_str = client.post("/run", json={"options": {"sample_mode": "not_bool"}})
    assert resp_sample_str.status_code == 400
    assert "Invalid sample_mode: must be a boolean." in resp_sample_str.json()["detail"]

    # sample_mode as list in options
    resp_sample_list = client.post("/run", json={"options": {"sample_mode": [True, False]}})
    assert resp_sample_list.status_code == 400
    assert "Invalid sample_mode: must be a boolean." in resp_sample_list.json()["detail"]


def test_run_investigation_nested_run_id_type_validation(client: TestClient) -> None:
    """POST /run rejects non-string run_id in input with HTTP 400."""
    resp_run_id_list = client.post("/run", json={"input": {"run_id": [1, 2, 3]}})
    assert resp_run_id_list.status_code == 400
    assert "Invalid run_id: must be a string." in resp_run_id_list.json()["detail"]

    resp_run_id_dict = client.post("/run", json={"input": {"run_id": {"nested": "id"}}})
    assert resp_run_id_dict.status_code == 400
    assert "Invalid run_id: must be a string." in resp_run_id_dict.json()["detail"]



"""FastAPI Endpoints and Web UI Conformance Tests for MarginWhy.

Validates:
1. GET /health returns HTTP 200, status HEALTHY, and model nvidia/nemotron-3-super-120b-a12b.
2. GET /api/scenarios returns HTTP 200 with at least 3 packaged sample scenarios.
3. POST /run executes end-to-end investigation and returns synthesized investigation report.
4. GET / delivers the full Executive Multi-Agent Root-Cause Diagnostic Dashboard HTML.
5. GET /api/trace and GET /api/hmem return valid state and audit telemetry.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing TestClient instance."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Confirms GET /health returns HTTP 200, status HEALTHY, and model tag nvidia/nemotron-3-super-120b-a12b."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["system"] == "MarginWhy"
    assert data["model"] == "nvidia/nemotron-3-super-120b-a12b"
    assert data.get("version") == "1.0.0"
    assert data.get("hmem_status") == "READY"
    assert "records_in_memory" in data
    assert "trust_ledger_mutations" in data


def test_scenarios_endpoint(client: TestClient) -> None:
    """Confirms GET /api/scenarios returns HTTP 200 and at least 3 sample scenarios with complete metadata."""
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3

    # Check key attributes on each scenario
    filenames = [s.get("filename") or s.get("file") for s in scenarios]
    assert "scenario_1_electronics_q3.json" in filenames
    assert "scenario_2_apparel_returns.json" in filenames
    assert "scenario_3_shipping_delay.json" in filenames

    for s in scenarios:
        assert "title" in s
        assert "query" in s or "description" in s
        assert "category" in s
        assert "margin_drop_pct" in s


def test_run_investigation_endpoint(client: TestClient) -> None:
    """Confirms POST /run executes an investigation via API and returns synthesized report and audit trail."""
    payload = {
        "query": "Why did net profit margin for Electronics drop 18.5% in Q3?",
        "sample_mode": True
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    result = response.json()

    assert result["status"] == "SUCCESS"
    assert "report" in result or "report_markdown" in result
    report = result.get("report") or result.get("report_markdown")
    assert len(report) > 100
    assert "Executive Summary & Core Diagnosis" in report
    assert "Evidence Cross-Examination" in report

    assert result["turns_executed"] >= 1
    assert len(result["approved_claims"]) >= 1
    assert result["approved_claims"][0]["confidence_score"] >= 0.70

    # Ensure H-MEM state and trace events returned
    assert "hmem_state" in result
    assert "trust_ledger" in result
    assert "trace_events" in result
    assert len(result["trace_events"]) > 0


def test_web_ui_dashboard_endpoint(client: TestClient) -> None:
    """Confirms GET / delivers the diagnostic dashboard HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html_content = response.text
    assert "<!DOCTYPE html>" in html_content
    assert "<title>MarginWhy — Executive Multi-Agent Root-Cause Dashboard</title>" in html_content
    assert "scenarioSelect" in html_content
    assert "btnRun" in html_content
    assert "tabReport" in html_content
    assert "tabTrace" in html_content
    assert "tabHMem" in html_content


def test_auxiliary_api_endpoints(client: TestClient) -> None:
    """Confirms /api/trace and /api/hmem endpoints return valid structure."""
    trace_resp = client.get("/api/trace?limit=10")
    assert trace_resp.status_code == 200
    assert isinstance(trace_resp.json(), list)

    hmem_resp = client.get("/api/hmem")
    assert hmem_resp.status_code == 200
    hmem_data = hmem_resp.json()
    assert "carryover" in hmem_data
    assert "trust_ledger_count" in hmem_data
    assert "recent_ledger" in hmem_data
    assert "all_records" in hmem_data


def test_slides_endpoint(client: TestClient) -> None:
    """Confirms GET /slides delivers the strategic 8-slide presentation deck HTML."""
    response = client.get("/slides")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "<title>MarginWhy — Executive Hackathon Presentation Deck</title>" in html
    assert 'id="slide-1"' in html
    assert 'id="slide-8"' in html
    assert "Track 02" in html
    assert "NVIDIA Nemotron" in html
    assert "Zetaris" in html
    assert "Meterless H-MEM" in html
    assert "slideCounter" in html


def test_run_investigation_technical_execution_format(client: TestClient) -> None:
    """Confirms POST /run accepts the nested input/options contract from technical execution requirements."""
    payload = {
        "run_id": "test-hackathon-audit-001",
        "input": {
            "query": "Why did net profit margin for Electronics drop 18.5% in Q3?"
        },
        "options": {
            "sample_mode": True
        }
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["run_id"] == "test-hackathon-audit-001"
    assert "execution_time_seconds" in data
    assert "output" in data
    assert "summary" in data["output"]
    assert "recommendations" in data["output"]
    assert len(data["output"]["recommendations"]) >= 1
    assert "agents" in data
    assert len(data["agents"]) == 4
    agent_names = [a["name"] for a in data["agents"]]
    assert "HypothesisPlanner" in agent_names
    assert "ZetarisRetriever" in agent_names
    assert "SkepticalCritic" in agent_names
    assert "ActionReportWriter" in agent_names


def test_zetaris_schema_endpoint(client: TestClient) -> None:
    """Confirms GET /api/zetaris/schema returns the dual-silo catalog for TPCDS_DB and NY_TAXI."""
    response = client.get("/api/zetaris/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONNECTED"
    assert "TPCDS_DB" in data["federated_silos"]
    assert "NY_TAXI" in data["federated_silos"]
    assert "databases" in data
    assert "TPCDS_DB" in data["databases"]
    assert "NY_TAXI" in data["databases"]

    tpcds_tables = data["databases"]["TPCDS_DB"]["tables"]
    assert "inventory" in tpcds_tables
    assert "web_returns" in tpcds_tables
    assert "item" in tpcds_tables

    ny_tables = data["databases"]["NY_TAXI"]["tables"]
    assert "trip_data" in ny_tables
    assert "taxi_zones" in ny_tables


def test_zetaris_query_endpoint(client: TestClient) -> None:
    """Confirms POST /api/zetaris/query executes federated query with latency telemetry and coerced rows."""
    payload = {
        "sql": "SELECT ca_state, COUNT(*) AS return_cnt, SUM(wr_return_amt) AS total_return_amt FROM TPCDS_DB.web_returns GROUP BY ca_state LIMIT 5;",
        "scenario_file": "scenario_1_electronics_q3.json"
    }
    response = client.post("/api/zetaris/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["row_count"] > 0
    assert "latency_ms" in data
    assert data["latency_ms"] > 0.0
    assert "columns" in data
    assert "rows" in data
    assert len(data["rows"]) == data["row_count"]
    assert "silos_involved" in data


def test_export_markdown_endpoint(client: TestClient) -> None:
    """Confirms GET /api/export/markdown returns downloadable markdown document with attachment header."""
    response = client.get("/api/export/markdown?scenario_file=scenario_1_electronics_q3.json")
    assert response.status_code == 200
    assert "text/markdown" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "MarginWhy_Executive_Report" in response.headers.get("content-disposition", "")
    assert len(response.text) > 100
    assert "Executive Summary" in response.text


def test_dashboard_has_studio_and_hmem_bento(client: TestClient) -> None:
    """Confirms GET / includes the new Zetaris SQL Studio and Meterless H-MEM Inspector components."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "tabStudio" in html
    assert "btnRunStudio" in html
    assert "studioSqlInput" in html
    assert "studioCatalogTree" in html
    assert "hmemCarryoverTokens" in html
    assert "hmemLedgerCountBadge" in html
    assert "tierShortTermList" in html
    assert "tierWorkingList" in html
    assert "tierLongTermList" in html
    assert "downloadReportMarkdown" in html


def test_audit_endpoint(client: TestClient) -> None:
    """Confirms GET /api/audit and POST /api/audit trigger verify_submission and return 100% PASS."""
    for method in [client.get, client.post]:
        response = method("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASSED"
        assert data["all_passed"] is True
        assert data["total_checks"] == 5
        assert data["passed_checks"] == 5
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 5
        chk_ids = [r["id"] for r in data["results"]]
        assert "CHK-1" in chk_ids
        assert "CHK-5" in chk_ids


def test_favicon_endpoints(client: TestClient) -> None:
    """Confirms /favicon.ico and /favicon.svg deliver SVG icon with HTTP 200."""
    for path in ["/favicon.ico", "/favicon.svg"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers.get("content-type", "")
        assert "<svg" in response.text


def test_run_investigation_custom_entities(client: TestClient) -> None:
    """Confirms POST /run extracts structured query entities and reflects them in the report and response."""
    payload = {
        "query": "Why did gross margin for Home Appliances drop 21.4% in Midwest during Q2?",
        "sample_mode": True
    }
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "entities" in data
    entities = data["entities"]
    assert entities.get("category") == "Home Appliances"
    assert entities.get("region") == "Midwest"
    assert entities.get("timeframe") == "Q2"
    assert entities.get("metric_delta_pct") == 21.4
    assert entities.get("metric") == "gross margin"

    # Verify synthesized report dynamically injects extracted domain entities
    report = data.get("report") or data.get("report_markdown", "")
    assert "Home Appliances" in report
    assert "Midwest" in report


def test_zetaris_discovery_commands(client: TestClient) -> None:
    """Confirms all 6 official discovery SQL commands return valid schema and row telemetry."""
    discovery_queries = [
        ("SELECT 1 AS one;", ["one"]),
        ("SHOW SERVER VERSION;", ["server_version", "status"]),
        ("SHOW LIGHTNING DATABASES;", ["database_name", "type"]),
        ("SHOW LIGHTNING TABLES TPCDS_DB;", ["table_name", "database"]),
        ("SHOW LIGHTNING TABLES NY_TAXI;", ["table_name", "database"]),
        ("DESCRIBE DATASOURCE TABLE NY_TAXI.taxi_zones;", ["column_name", "data_type"])
    ]

    for sql, expected_cols in discovery_queries:
        payload = {"sql": sql, "scenario_file": "scenario_1_electronics_q3.json"}
        resp = client.post("/api/zetaris/query", json=payload)
        assert resp.status_code == 200, f"Query failed: {sql}"
        res = resp.json()
        assert res["status"] == "SUCCESS", f"Expected SUCCESS for {sql}"
        assert res["row_count"] > 0, f"Expected non-empty rows for {sql}"
        for col in expected_cols:
            assert col in res["columns"], f"Expected column {col} in {res['columns']} for {sql}"


def test_export_trace_endpoint(client: TestClient) -> None:
    """Confirms GET /api/export/trace streams trace.jsonl as a downloadable attachment."""
    response = client.get("/api/export/trace")
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "trace.jsonl" in response.headers.get("content-disposition", "")
    assert len(response.text) > 0


def test_telemetry_endpoint(client: TestClient) -> None:
    """Confirms GET /api/telemetry serves project metadata, model configurations, and token compression metrics."""
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "model" in data
    assert "meterless_base_url" in data
    assert "metadata" in data
    assert "metrics" in data
    assert data["metrics"]["token_compression_ratio"] == "98.3%"
    assert data["metrics"]["adversarial_threshold"] == 0.70



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

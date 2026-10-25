"""Unit tests for scripts/verify_submission.py (Milestone 2).

Validates that SubmissionAuditor methods correctly inspect repo metadata,
trace logs, git security, and execute without error.
"""

import json
from pathlib import Path
import pytest
from scripts.verify_submission import SubmissionAuditor, REPO_ROOT


@pytest.fixture
def auditor():
    return SubmissionAuditor(verbose=False, timeout_sec=60)


def test_metadata_schema_verification(auditor):
    passed, details = auditor.check_metadata()
    assert passed is True, f"Metadata check failed: {details}"
    assert "Light of Numbers" in details
    assert "Track 02" in details
    assert "nvidia/nemotron-3-super-120b-a12b" in details


def test_trace_log_verification(auditor):
    passed, details = auditor.check_trace_log()
    assert passed is True, f"Trace log check failed: {details}"
    assert "CLAIM_BLOCKED" in details
    assert "Nemotron" in details


def test_git_security_verification(auditor):
    passed, details = auditor.check_git_security()
    assert passed is True, f"Git security check failed: {details}"
    assert ".gitignore" in details
    assert ".env.example" in details


def test_auditor_run_all_fast(auditor):
    # Test execution with benchmark skipped for fast regression
    all_passed = auditor.run_all(target_check="all", skip_benchmark=True, skip_tests=True)
    assert all_passed is True
    assert len(auditor.results) == 5
    for r in auditor.results:
        assert r["passed"] is True
        assert r["status"] == "PASS"


def test_auditor_json_serialization(auditor):
    auditor.run_all(target_check="metadata", skip_benchmark=True, skip_tests=True)
    json_str = auditor.to_json(True)
    parsed = json.loads(json_str)
    assert parsed["all_passed"] is True
    assert parsed["project_name"] == "MarginWhy"
    assert parsed["team"] == "Light of Numbers"
    assert len(parsed["checks"]) == 1
    assert parsed["checks"][0]["id"] == "CHK-1"

"""Unit tests for scripts/verify_submission.py (Milestone 2).

Validates that SubmissionAuditor methods correctly inspect repo metadata,
trace logs, git security, and execute without error.
"""

import json
from pathlib import Path
import pytest
from scripts.verify_submission import SubmissionAuditor, REPO_ROOT
import scripts.verify_submission as vs_mod


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


def test_git_security_vercel_env_flag(auditor, monkeypatch):
    """Verify CHK-5 passes when VERCEL=1 environment variable is set."""
    monkeypatch.setenv("VERCEL", "1")
    passed, details = auditor.check_git_security()
    assert passed is True, f"Git security check failed with VERCEL=1: {details}"
    assert ".gitignore" in details
    assert ".env.example" in details
    assert "VERCEL=1" in details


def test_git_security_serverless_missing_gitignore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify CHK-5 passes in serverless mode even when .gitignore is omitted by packager."""
    (tmp_path / "metadata.json").write_text(
        json.dumps({"project_name": "MarginWhy", "team": {"name": "Light of Numbers"}}),
        encoding="utf-8",
    )
    (tmp_path / ".env.example").write_text(
        "SAMPLE_MODE=true\nZETARIS_API_KEY=dummy\nMETERLESS_API_KEY=dummy\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("VERCEL", "1")

    auditor = SubmissionAuditor(verbose=False)
    passed, details = auditor.check_git_security()
    assert passed is True, f"Serverless git security failed without .gitignore: {details}"
    assert ".gitignore" in details
    assert ".env.example" in details
    assert "zero live .env secrets bundled" in details


def test_git_security_serverless_detects_live_env_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify CHK-5 detects and blocks live secrets in .env even in serverless environments."""
    (tmp_path / "metadata.json").write_text(
        json.dumps({"project_name": "MarginWhy"}),
        encoding="utf-8",
    )
    (tmp_path / ".env.example").write_text(
        "SAMPLE_MODE=true\nZETARIS_API_KEY=dummy\nMETERLESS_API_KEY=dummy\n",
        encoding="utf-8",
    )
    # Leaked live production secret key in .env
    (tmp_path / ".env").write_text(
        "SAMPLE_MODE=false\nZETARIS_API_KEY=sk-testliveapikeysecretwith32charsminimumlength123\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("VERCEL", "1")

    auditor = SubmissionAuditor(verbose=False)
    passed, details = auditor.check_git_security()
    assert passed is False
    assert "CRITICAL SECURITY ALERT: Live .env containing sensitive secrets" in details


def test_git_security_headless_repo_non_git_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify clean headless bundle without .git passes cleanly without git code 128 error."""
    (tmp_path / "metadata.json").write_text(
        json.dumps({"project_name": "MarginWhy"}),
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text(".env\n*.pyc\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "SAMPLE_MODE=true\nZETARIS_API_KEY=dummy\nMETERLESS_API_KEY=dummy\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)

    auditor = SubmissionAuditor(verbose=False)
    passed, details = auditor.check_git_security()
    assert passed is True, f"Headless non-git check failed: {details}"
    assert ".gitignore" in details
    assert ".env.example" in details


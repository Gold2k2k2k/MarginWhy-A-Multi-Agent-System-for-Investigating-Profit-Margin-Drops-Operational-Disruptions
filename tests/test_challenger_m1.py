"""Empirical Challenger Test Suite for Milestone 1: CHK-5 Audit Serverless Fix.

Stress-tests SubmissionAuditor.check_git_security() and check_trace_log()
under adversarial edge cases, including:
- Simulated Vercel serverless environment (VERCEL=1, VERCEL=true, AWS_LAMBDA)
- Headless deployments (omitted .git folder)
- Missing .gitignore in serverless vs non-serverless mode
- Present .gitignore in serverless missing .env ignore rule
- Live secret leakage detection (.env with sk-, AKIA, ghp_, nvapi-) in all modes
- Benign .env without secrets
- Missing .env file (standard clean bundle)
- .env.example corruption or live secrets in template
- Serverless trace log fallback to /tmp/logs/trace.jsonl
- Live FastAPI /api/audit endpoint behavior under serverless and corrupted states
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict
import pytest

from fastapi.testclient import TestClient
from scripts.verify_submission import REPO_ROOT, SubmissionAuditor
import scripts.verify_submission as vs_mod
from app.main import app, run_submission_audit


# =============================================================================
# Helper Fixture
# =============================================================================

@pytest.fixture
def minimal_valid_bundle(tmp_path: Path):
    """Creates a minimal valid headless deployment bundle."""
    (tmp_path / "metadata.json").write_text(
        json.dumps({
            "project_name": "MarginWhy",
            "team": {"name": "Light of Numbers"},
            "primary_track": "Track 02",
        }),
        encoding="utf-8",
    )
    (tmp_path / ".env.example").write_text(
        "SAMPLE_MODE=true\nZETARIS_API_KEY=dummy\nMETERLESS_API_KEY=dummy\n",
        encoding="utf-8",
    )
    return tmp_path


# =============================================================================
# 1. SERVERLESS DETECTION & FLAG TESTING
# =============================================================================

class TestServerlessDetectionFlags:
    """Tests various environment variable flags for serverless detection."""

    @pytest.mark.parametrize("env_val", ["1", "true", "True"])
    def test_vercel_truthy_flags_pass_without_gitignore(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch, env_val: str
    ):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", env_val)
        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True
        assert "serverless bundle (.gitignore excluded)" in details

    @pytest.mark.parametrize("env_val", ["0", "false", "False", ""])
    def test_vercel_falsy_flags_require_gitignore(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch, env_val: str
    ):
        # When .git is present or not serverless, falsy VERCEL flag should not trigger Vercel bypass
        (minimal_valid_bundle / ".git").mkdir()
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", env_val)
        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert ".gitignore file not found in repository root" in details

    def test_aws_lambda_flag_activates_serverless_mode(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.delenv("VERCEL", raising=False)
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "marginwhy-backend")
        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True
        assert "serverless bundle (.gitignore excluded)" in details


# =============================================================================
# 2. HEADLESS DEPLOYMENT (NO .git DIRECTORY)
# =============================================================================

class TestHeadlessDeployment:
    """Stress-tests behavior when .git directory is completely absent."""

    def test_headless_with_metadata_passes_without_git(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.delenv("VERCEL", raising=False)
        monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
        assert not (minimal_valid_bundle / ".git").exists()
        assert (minimal_valid_bundle / "metadata.json").exists()

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True
        assert "zero live .env secrets bundled" in details

    def test_corrupted_git_dir_returncode_128_handled_cleanly(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Simulate a .git directory that triggers fatal returncode 128 from git CLI
        (minimal_valid_bundle / ".git").mkdir()
        (minimal_valid_bundle / ".gitignore").write_text(".env\n", encoding="utf-8")
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)

        def mock_subprocess_run(cmd, *args, **kwargs):
            if cmd[0] == "git":
                return subprocess.CompletedProcess(
                    args=cmd, returncode=128, stdout="", stderr="fatal: not a git repository"
                )
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True
        assert "filesystem .gitignore confirmed" in details


# =============================================================================
# 3. .gitignore IN SERVERLESS VS NON-SERVERLESS
# =============================================================================

class TestGitignoreLogic:
    """Adversarial tests on .gitignore presence, absence, and contents."""

    def test_non_serverless_missing_gitignore_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".env.example").write_text(
            "SAMPLE_MODE=true\nZETARIS_API_KEY=dummy\nMETERLESS_API_KEY=dummy\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        monkeypatch.delenv("VERCEL", raising=False)
        monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert ".gitignore file not found in repository root" in details

    def test_serverless_with_gitignore_missing_env_rule_fails(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Even in serverless mode, if a .gitignore is present, it MUST ignore .env
        (minimal_valid_bundle / ".gitignore").write_text("*.log\nnode_modules/\n", encoding="utf-8")
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert ".gitignore does not explicitly contain '.env' ignore rule" in details

    def test_serverless_with_gitignore_having_env_rule_passes(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (minimal_valid_bundle / ".gitignore").write_text(".env\n*.pyc\n", encoding="utf-8")
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True
        assert ".gitignore excludes .env" in details


# =============================================================================
# 4. LIVE SECRET DETECTION IN .env
# =============================================================================

class TestLiveSecretDetection:
    """Stress-tests secret pattern detection in .env across various regexes and modes."""

    @pytest.mark.parametrize(
        "secret_value",
        [
            "sk-abc1234567890123456789012345678901234",
            "AKIAIOSFODNN7EXAMPLE",
            "ghp_123456789012345678901234567890123456",
            "nvapi-32characterminimumstringwithdashes_and_numbers1234",
        ],
    )
    def test_serverless_blocks_various_live_secret_patterns(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch, secret_value: str
    ):
        (minimal_valid_bundle / ".env").write_text(
            f"SAMPLE_MODE=false\nAPI_KEY={secret_value}\n", encoding="utf-8"
        )
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert "CRITICAL SECURITY ALERT: Live .env containing sensitive secrets" in details

    def test_serverless_allows_benign_env_file(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # A .env file with non-secret configurations must be allowed
        (minimal_valid_bundle / ".env").write_text(
            "SAMPLE_MODE=true\nZETARIS_API_KEY=mock-zetaris-key\nMETERLESS_API_KEY=mock-meterless-key\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is True


# =============================================================================
# 5. .env.example ROBUSTNESS
# =============================================================================

class TestEnvExampleRobustness:
    """Tests .env.example validation."""

    def test_missing_env_example_rejected_in_serverless(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch
    ):
        (minimal_valid_bundle / ".env.example").unlink()
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert ".env.example file not found in repository root" in details

    @pytest.mark.parametrize("missing_key", ["SAMPLE_MODE", "ZETARIS_API_KEY", "METERLESS_API_KEY"])
    def test_env_example_missing_single_key(
        self, minimal_valid_bundle: Path, monkeypatch: pytest.MonkeyPatch, missing_key: str
    ):
        keys = ["SAMPLE_MODE", "ZETARIS_API_KEY", "METERLESS_API_KEY"]
        remaining = [k for k in keys if k != missing_key]
        content = "\n".join(f"{k}=placeholder" for k in remaining) + "\n"
        (minimal_valid_bundle / ".env.example").write_text(content, encoding="utf-8")
        monkeypatch.setattr(vs_mod, "REPO_ROOT", minimal_valid_bundle)
        monkeypatch.setenv("VERCEL", "1")

        auditor = SubmissionAuditor()
        passed, details = auditor.check_git_security()
        assert passed is False
        assert f".env.example is missing template keys: ['{missing_key}']" in details


# =============================================================================
# 6. SERVERLESS TRACE LOG /tmp FALLBACK
# =============================================================================

class TestServerlessTraceLogFallback:
    """Tests check_trace_log() fallback to /tmp/logs/trace.jsonl."""

    def test_serverless_trace_fallback_to_tmp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Setup bundle without repo trace log
        (tmp_path / "metadata.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        monkeypatch.setenv("VERCEL", "1")

        # Setup valid trace log in /tmp/logs/trace.jsonl
        tmp_log_dir = Path("/tmp") / "logs"
        tmp_log_dir.mkdir(parents=True, exist_ok=True)
        tmp_trace_file = tmp_log_dir / "trace.jsonl"
        valid_events = [
            {"event": "CLAIM_BLOCKED", "status": "BRANCH_RETRY"},
            {"event": "APPROVED_CLAIM", "status": "VERIFIED"},
            {"event": "INFERENCE", "model": "nvidia/nemotron-3-super-120b-a12b"},
        ]
        tmp_trace_file.write_text(
            "\n".join(json.dumps(e) for e in valid_events) + "\n",
            encoding="utf-8",
        )

        try:
            auditor = SubmissionAuditor()
            passed, details = auditor.check_trace_log()
            assert passed is True
            assert "CLAIM_BLOCKED -> BRANCH_RETRY verified" in details
            assert "Nemotron events tagged" in details
        finally:
            if tmp_trace_file.exists():
                tmp_trace_file.unlink()


# =============================================================================
# 7. LIVE FASTAPI /api/audit ENDPOINT VERIFICATION
# =============================================================================

class TestLiveApiAuditEndpoint:
    """Verifies that the /api/audit endpoint behaves consistently."""

    def test_api_audit_local_returns_5_of_5_pass(self):
        client = TestClient(app)
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASSED"
        assert data["all_passed"] is True
        assert data["total_checks"] == 5
        assert data["passed_checks"] == 5
        chk5 = next(c for c in data["results"] if c["id"] == "CHK-5")
        assert chk5["passed"] is True
        assert chk5["status"] == "PASS"

    def test_api_audit_with_vercel_env_flag(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("VERCEL", "1")
        client = TestClient(app)
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASSED"
        assert data["all_passed"] is True
        assert data["passed_checks"] == 5
        chk5 = next(c for c in data["results"] if c["id"] == "CHK-5")
        assert "VERCEL=1" in chk5["details"]

    def test_direct_run_submission_audit_function(self):
        result = run_submission_audit()
        assert result["status"] == "PASSED"
        assert result["all_passed"] is True
        assert result["total_checks"] == 5
        assert result["passed_checks"] == 5

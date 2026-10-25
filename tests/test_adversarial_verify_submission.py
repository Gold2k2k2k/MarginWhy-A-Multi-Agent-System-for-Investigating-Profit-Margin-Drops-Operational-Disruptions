"""Adversarial stress-testing suite for scripts/verify_submission.py.

Empirical verification of error handling, negative test cases, edge cases,
CLI invocation, and exit code propagation for Open Agent Hackathon 2026.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict
import pytest

from scripts.verify_submission import REPO_ROOT, SubmissionAuditor
import scripts.verify_submission as vs_mod


# Base valid metadata fixture
@pytest.fixture
def valid_metadata() -> Dict[str, Any]:
    with open(REPO_ROOT / "metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)


# Base valid trace line fixtures
@pytest.fixture
def valid_trace_events() -> list[Dict[str, Any]]:
    events = []
    with open(REPO_ROOT / "logs" / "trace.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                try:
                    rec = json.loads(line_str)
                    if isinstance(rec, dict):
                        events.append(rec)
                except json.JSONDecodeError:
                    pass
    return events


# =============================================================================
# 1. METADATA.JSON ADVERSARIAL TESTS
# =============================================================================

class TestMetadataAdversarial:
    def test_missing_metadata_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "metadata.json not found" in msg

    def test_invalid_json_syntax(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text("{ unclosed json: ", encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "Failed to parse metadata.json" in msg

    def test_root_is_not_dict(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text('["not", "a", "dict"]', encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "root must be a JSON object" in msg

    @pytest.mark.parametrize(
        "missing_key",
        [
            "project_name",
            "hackathon",
            "primary_track",
            "target_awards",
            "team",
            "tech_stack",
            "cursor_developer_story",
            "execution",
        ],
    )
    def test_missing_required_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict, missing_key: str
    ):
        data = dict(valid_metadata)
        del data[missing_key]
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert f"Missing required top-level schema keys: ['{missing_key}']" in msg

    def test_wrong_project_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["project_name"] = "OtherProject"
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "project_name must be 'MarginWhy'" in msg

    def test_wrong_team_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["team"] = {"name": "Wrong Team"}
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "team.name must be 'Light of Numbers'" in msg

    def test_team_not_a_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["team"] = "Light of Numbers"
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "team.name must be 'Light of Numbers'" in msg

    def test_wrong_primary_track(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["primary_track"] = "Track 01: Fast Agents"
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "primary_track must indicate Track 02" in msg

    def test_wrong_llm_model(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["tech_stack"] = {"llm_model": "gpt-4o"}
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "tech_stack.llm_model must be 'nvidia/nemotron-3-super-120b-a12b'" in msg

    def test_insufficient_target_awards(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["target_awards"] = ["Track 02"]
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "target_awards must contain at least 3 target tracks/awards" in msg

    def test_empty_cursor_story(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["cursor_developer_story"] = {"description": ""}
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "cursor_developer_story must contain a non-empty description" in msg

    def test_missing_execution_commands(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_metadata: dict
    ):
        data = dict(valid_metadata)
        data["execution"] = {"cli_command": "python run.py"}  # missing test_command
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / "metadata.json").write_text(json.dumps(data), encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_metadata()
        assert passed is False
        assert "execution must define cli_command and test_command" in msg


# =============================================================================
# 2. H-MEM CONFORMANCE TEST ADVERSARIAL TESTS
# =============================================================================

class TestHMemConformanceAdversarial:
    def test_missing_conformance_test_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_hmem_tests()
        assert passed is False
        assert "Conformance test file not found" in msg

    def test_pytest_timeout(self, monkeypatch: pytest.MonkeyPatch):
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=45.0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_hmem_tests()
        assert passed is False
        assert "timed out after 45.0s" in msg

    def test_pytest_failure_detected(self, monkeypatch: pytest.MonkeyPatch):
        fake_proc = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout="FAILED tests/test_hmem_conformance.py::test_fail\n1 failed, 7 passed in 1.2s",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_hmem_tests()
        assert passed is False
        assert "pytest returned non-zero exit code 1" in msg

    def test_pytest_error_detected(self, monkeypatch: pytest.MonkeyPatch):
        fake_proc = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=1,
            stdout="ERROR tests/test_hmem_conformance.py\n1 error in 0.5s",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_hmem_tests()
        assert passed is False
        assert "pytest returned non-zero exit code 1" in msg

    def test_insufficient_passed_tests_detected(self, monkeypatch: pytest.MonkeyPatch):
        fake_proc = subprocess.CompletedProcess(
            args=["pytest"],
            returncode=0,
            stdout="5 passed in 2.0s",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_hmem_tests()
        assert passed is False
        assert "Expected at least 8 conformance tests to pass, found: 5" in msg


# =============================================================================
# 3. BENCHMARK (RUN.PY) ADVERSARIAL TESTS
# =============================================================================

class TestBenchmarkAdversarial:
    def test_missing_run_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_benchmark()
        assert passed is False
        assert "run.py not found" in msg

    def test_benchmark_timeout_expired(self, monkeypatch: pytest.MonkeyPatch):
        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=60.0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor(timeout_sec=60)
        passed, msg = auditor.check_benchmark()
        assert passed is False
        assert "timed out after 60s" in msg

    def test_benchmark_error_exit_code(self, monkeypatch: pytest.MonkeyPatch):
        fake_proc = subprocess.CompletedProcess(
            args=["python", "run.py"],
            returncode=1,
            stdout="",
            stderr="Traceback (most recent call last)...",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_benchmark()
        assert passed is False
        assert "run.py exited with error code 1" in msg

    def test_benchmark_empty_output(self, monkeypatch: pytest.MonkeyPatch):
        fake_proc = subprocess.CompletedProcess(
            args=["python", "run.py"],
            returncode=0,
            stdout="   \n  ",
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_benchmark()
        assert passed is False
        assert "run.py output was empty or unexpectedly truncated" in msg

    @pytest.mark.parametrize(
        "missing_marker",
        [
            "MarginWhy Multi-Agent Investigation Initiated",
            "FINAL INVESTIGATION REPORT",
            "Executive Summary & Core Diagnosis",
        ],
    )
    def test_benchmark_missing_report_marker(
        self, monkeypatch: pytest.MonkeyPatch, missing_marker: str
    ):
        full_markers = [
            "MarginWhy Multi-Agent Investigation Initiated",
            "FINAL INVESTIGATION REPORT",
            "Executive Summary & Core Diagnosis",
        ]
        kept = [m for m in full_markers if m != missing_marker]
        stdout_text = "Detailed output padding text " * 20 + "\n" + "\n".join(kept)
        fake_proc = subprocess.CompletedProcess(
            args=["python", "run.py"],
            returncode=0,
            stdout=stdout_text,
            stderr="",
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake_proc)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_benchmark()
        assert passed is False
        assert f"Report output missing required section marker: '{missing_marker}'" in msg


# =============================================================================
# 4. TRACE LOG (LOGS/TRACE.JSONL) ADVERSARIAL TESTS
# =============================================================================

class TestTraceLogAdversarial:
    def test_missing_trace_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "logs/trace.jsonl not found" in msg

    def test_empty_trace_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "trace.jsonl").write_text("\n\n   \n", encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "logs/trace.jsonl is empty" in msg

    def test_malformed_json_lines_resilience(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_trace_events: list
    ):
        """Auditor should skip corrupted lines and still validate valid events."""
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)

        lines = ["{ corrupted JSON line: missing bracket\n"]
        for evt in valid_trace_events:
            lines.append(json.dumps(evt) + "\n")

        (logs_dir / "trace.jsonl").write_text("".join(lines), encoding="utf-8")
        auditor = SubmissionAuditor(verbose=True)
        passed, msg = auditor.check_trace_log()
        assert passed is True
        assert "CLAIM_BLOCKED -> BRANCH_RETRY verified" in msg

    def test_missing_claim_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_trace_events: list
    ):
        filtered = [e for e in valid_trace_events if e.get("event") != "CLAIM_BLOCKED"]
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "trace.jsonl").write_text(
            "\n".join(json.dumps(e) for e in filtered), encoding="utf-8"
        )
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "Missing required 'CLAIM_BLOCKED' event with status 'BRANCH_RETRY'" in msg

    def test_wrong_status_for_claim_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_trace_events: list
    ):
        mutated = []
        for e in valid_trace_events:
            rec = dict(e)
            if rec.get("event") == "CLAIM_BLOCKED":
                rec["status"] = "DROPPED"  # not BRANCH_RETRY
            mutated.append(rec)
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "trace.jsonl").write_text(
            "\n".join(json.dumps(e) for e in mutated), encoding="utf-8"
        )
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "Missing required 'CLAIM_BLOCKED' event with status 'BRANCH_RETRY'" in msg

    def test_missing_nemotron_model(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_trace_events: list
    ):
        mutated = []
        for e in valid_trace_events:
            rec = dict(e)
            if "nemotron" in str(rec.get("model", "")).lower():
                rec["model"] = "openai/gpt-4o"
            mutated.append(rec)
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "trace.jsonl").write_text(
            "\n".join(json.dumps(e) for e in mutated), encoding="utf-8"
        )
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "Missing 'nvidia/nemotron-3-super-120b-a12b' model attribution tag" in msg

    def test_missing_approved_claim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_trace_events: list
    ):
        filtered = [e for e in valid_trace_events if e.get("event") != "APPROVED_CLAIM"]
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "trace.jsonl").write_text(
            "\n".join(json.dumps(e) for e in filtered), encoding="utf-8"
        )
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_trace_log()
        assert passed is False
        assert "Missing required 'APPROVED_CLAIM' event with status 'VERIFIED'" in msg


# =============================================================================
# 5. GIT SECURITY ADVERSARIAL TESTS
# =============================================================================

class TestGitSecurityAdversarial:
    def test_missing_gitignore(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert ".gitignore file not found" in msg

    def test_gitignore_lacking_env_rule(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert ".gitignore does not explicitly contain '.env' ignore rule" in msg

    def test_git_check_ignore_fails(self, monkeypatch: pytest.MonkeyPatch):
        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "check-ignore"]:
                return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert "git check-ignore indicates .env is NOT ignored" in msg

    def test_env_tracked_in_git_index(self, monkeypatch: pytest.MonkeyPatch):
        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".env\n", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".gitignore:1:.env\n", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert "CRITICAL SECURITY ALERT: .env is currently tracked in git index" in msg

    def test_missing_env_example(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")

        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "check-ignore"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".gitignore:1:.env\n", stderr="")
            if cmd[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert ".env.example file not found" in msg

    def test_env_example_missing_template_keys(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        # Missing METERLESS_API_KEY
        (tmp_path / ".env.example").write_text("SAMPLE_MODE=true\nZETARIS_API_KEY=foo\n", encoding="utf-8")

        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "check-ignore"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".gitignore:1:.env\n", stderr="")
            if cmd[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert ".env.example is missing template keys: ['METERLESS_API_KEY']" in msg

    @pytest.mark.parametrize(
        "leaked_key",
        [
            "sk-1234567890123456789012345678901234",
            "AKIAIOSFODNN7EXAMPLE",
            "ghp_123456789012345678901234567890123456",
            "nvapi-1234567890123456789012345678901234",
        ],
    )
    def test_env_example_contains_leaked_secret(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, leaked_key: str
    ):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        content = (
            f"SAMPLE_MODE=true\nZETARIS_API_KEY={leaked_key}\nMETERLESS_API_KEY=test\n"
        )
        (tmp_path / ".env.example").write_text(content, encoding="utf-8")

        def fake_run(cmd, *a, **kw):
            if cmd[:2] == ["git", "check-ignore"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".gitignore:1:.env\n", stderr="")
            if cmd[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert "CRITICAL: .env.example appears to contain a live production secret key!" in msg

    def test_local_env_file_staged_in_git(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(vs_mod, "REPO_ROOT", tmp_path)
        (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
        (tmp_path / ".env.example").write_text(
            "SAMPLE_MODE=true\nZETARIS_API_KEY=test\nMETERLESS_API_KEY=test\n", encoding="utf-8"
        )
        (tmp_path / ".env").write_text("SECRET=leaked\n", encoding="utf-8")

        def fake_run(cmd, *a, **kw):
            if cmd[:3] == ["git", "status", "--porcelain"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="M  .env\n", stderr="")
            if cmd[:2] == ["git", "check-ignore"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=".gitignore:1:.env\n", stderr="")
            if cmd[:2] == ["git", "ls-files"]:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        auditor = SubmissionAuditor()
        passed, msg = auditor.check_git_security()
        assert passed is False
        assert "CRITICAL: .env file is staged or tracked in git status" in msg


# =============================================================================
# 6. RUNNER ORCHESTRATION & CLI INTEGRATION ADVERSARIAL TESTS
# =============================================================================

class TestRunnerOrchestrationAndCLI:
    def test_run_all_detects_single_check_failure(self):
        auditor = SubmissionAuditor()
        # Deliberately mock Check 1 to fail
        auditor.check_metadata = lambda: (False, "Injected metadata fault")
        all_passed = auditor.run_all(skip_benchmark=True, skip_tests=True)
        assert all_passed is False
        assert auditor.results[0]["status"] == "FAIL"
        assert auditor.results[0]["details"] == "Injected metadata fault"
        # Remaining checks still ran
        assert len(auditor.results) == 5

    def test_run_all_handles_check_exception_gracefully(self):
        auditor = SubmissionAuditor()
        def crash():
            raise RuntimeError("Simulated crash")
        auditor.check_metadata = crash
        all_passed = auditor.run_all(skip_benchmark=True, skip_tests=True)
        assert all_passed is False
        assert auditor.results[0]["status"] == "FAIL"
        assert "Unhandled exception during check execution: Simulated crash" in auditor.results[0]["details"]

    def test_target_check_by_id_and_name(self):
        auditor = SubmissionAuditor()
        # By ID
        assert auditor.run_all(target_check="CHK-1", skip_benchmark=True, skip_tests=True) is True
        assert len(auditor.results) == 1
        assert auditor.results[0]["id"] == "CHK-1"

        # By name
        assert auditor.run_all(target_check="git", skip_benchmark=True, skip_tests=True) is True
        assert len(auditor.results) == 1
        assert auditor.results[0]["id"] == "CHK-5"

    def test_unknown_target_check(self):
        auditor = SubmissionAuditor()
        assert auditor.run_all(target_check="non_existent") is False
        assert len(auditor.results) == 0

    def test_cli_execution_from_repo_root(self):
        proc = subprocess.run(
            [sys.executable, "scripts/verify_submission.py", "--quick"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert "OVERALL AUDIT VERDICT: PASSED" in proc.stdout

    def test_cli_execution_from_scripts_dir(self):
        """Must correctly locate REPO_ROOT even when run from scripts/ directory."""
        proc = subprocess.run(
            [sys.executable, "verify_submission.py", "--quick"],
            cwd=str(REPO_ROOT / "scripts"),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        assert "OVERALL AUDIT VERDICT: PASSED" in proc.stdout

    def test_cli_json_mode(self):
        proc = subprocess.run(
            [sys.executable, "scripts/verify_submission.py", "--check", "metadata", "--json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert data["all_passed"] is True
        assert data["project_name"] == "MarginWhy"
        assert len(data["checks"]) == 1
        assert data["checks"][0]["id"] == "CHK-1"

    def test_cli_invalid_argument_causes_exit_2(self):
        proc = subprocess.run(
            [sys.executable, "scripts/verify_submission.py", "--check", "invalid_choice"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2
        assert "invalid choice" in proc.stderr

    def test_cli_failure_exit_code_propagation(self, tmp_path: Path):
        """CLI must exit with code 1 when any check fails."""
        # Create a runner script invoking verify_submission in an environment with missing metadata
        test_script = (
            "import sys\n"
            "from scripts.verify_submission import SubmissionAuditor, main\n"
            "import scripts.verify_submission as vs\n"
            "from pathlib import Path\n"
            f"vs.REPO_ROOT = Path(r'{tmp_path}')\n"
            "sys.exit(main())\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", test_script, "--quick"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1
        assert "OVERALL AUDIT VERDICT: FAILED" in proc.stdout

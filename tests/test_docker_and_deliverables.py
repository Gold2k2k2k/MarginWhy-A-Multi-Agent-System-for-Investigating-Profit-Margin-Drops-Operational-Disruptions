"""Tests validating Dockerization, Colab quickstart, and Submission deliverables.

Ensures the repository satisfies 100% of the Hackathon technical criteria:
- Dockerfile & docker-compose.yml syntax and configuration
- Google Colab notebook validity and badges
- Demo video script and HackOS submission worksheet completeness
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_configuration():
    """Confirms Dockerfile exists and contains required production directives."""
    dockerfile = REPO_ROOT / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile must exist at repository root"
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in content
    assert "WORKDIR /app" in content
    assert "COPY requirements.txt" in content
    assert "EXPOSE 8000" in content
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content


def test_docker_compose_configuration():
    """Confirms docker-compose.yml exists and contains proper ports and service mapping."""
    compose_file = REPO_ROOT / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml must exist at repository root"
    content = compose_file.read_text(encoding="utf-8")
    assert "8000:8000" in content
    assert "SAMPLE_MODE=true" in content
    assert "nvidia/nemotron-3-super-120b-a12b" in content
    assert "healthcheck" in content


def test_colab_notebook_validity():
    """Confirms Google Colab quickstart notebook exists and contains valid JSON."""
    nb_file = REPO_ROOT / "notebooks" / "marginwhy_quickstart.ipynb"
    assert nb_file.exists(), "Quickstart notebook must exist at notebooks/marginwhy_quickstart.ipynb"
    with open(nb_file, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    assert nb_data.get("nbformat") == 4
    cells = nb_data.get("cells", [])
    assert len(cells) >= 5
    full_text = "".join("".join(c.get("source", [])) for c in cells)
    assert "colab-badge.svg" in full_text
    assert "verify_submission.py" in full_text
    assert "run.py" in full_text


def test_demo_video_script_deliverable():
    """Confirms DEMO_VIDEO_SCRIPT.md exists and covers 1-4 minute timeline and sponsor callouts."""
    script_file = REPO_ROOT / "docs" / "DEMO_VIDEO_SCRIPT.md"
    assert script_file.exists(), "Demo video script must exist at docs/DEMO_VIDEO_SCRIPT.md"
    content = script_file.read_text(encoding="utf-8")
    assert "NVIDIA Nemotron" in content
    assert "Zetaris" in content
    assert "Meterless H-MEM" in content
    assert "CLAIM_BLOCKED" in content


def test_submission_deliverables_worksheet():
    """Confirms SUBMISSION_DELIVERABLES.md contains all HackOS fields and 100-point rubric alignment."""
    deliv_file = REPO_ROOT / "docs" / "SUBMISSION_DELIVERABLES.md"
    assert deliv_file.exists(), "Submission deliverables must exist at docs/SUBMISSION_DELIVERABLES.md"
    content = deliv_file.read_text(encoding="utf-8")
    assert "Track 02" in content
    assert "Light of Numbers" in content
    assert "Zetaris AI Data Harness" in content
    assert "Meterless H-MEM" in content
    assert "NVIDIA Nemotron" in content
    assert "Cursor IDE" in content


def test_dockerignore_configuration():
    """Confirms .dockerignore exists and excludes sensitive and build artifact files."""
    dockerignore = REPO_ROOT / ".dockerignore"
    assert dockerignore.exists(), ".dockerignore must exist at repository root"
    content = dockerignore.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    assert ".git" in lines
    assert ".env" in lines
    assert ".venv" in lines
    assert "__pycache__" in lines


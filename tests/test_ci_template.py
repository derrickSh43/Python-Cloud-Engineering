"""Runs the gate script from the CI template (ci/github-actions/changegate-gate.yml) locally against the
reference implementation, so the template can't silently break. Needs bash (Linux, macOS, Git Bash)."""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "01-cloud-change-control"
TEMPLATE = PROJECT / "ci" / "github-actions" / "changegate-gate.yml"
PLANS = "projects/01-cloud-change-control/sample_data/plans/"


def step_script(name):
    """The `run: |` block of the step called `name` (enough YAML parsing for this one file)."""
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "- name: %s" % name)
    run = next(i for i in range(start, len(lines)) if lines[i].strip() == "run: |")
    indent = len(lines[run + 1]) - len(lines[run + 1].lstrip())
    body = []
    for line in lines[run + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) < indent:
            break
        body.append(line[indent:])
    return "\n".join(body).strip() + "\n"


def test_template_has_no_hard_coded_secrets_and_uses_variables():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "${{ secrets.CHANGEGATE_HMAC_KEY }}" in text
    for var in ("CHANGEGATE_PACKAGE", "CHANGEGATE_CONFIG", "CHANGEGATE_PLANS"):
        assert "vars.%s" % var in text
    assert "permissions:" in text and "contents: read" in text


bash = shutil.which("bash")


@pytest.mark.skipif(bash is None, reason="bash not available")
@pytest.mark.parametrize("plans, expected", [
    (PLANS + "aws_safe.json " + PLANS + "gcp_safe.json", 0),
    (PLANS + "aws_safe.json " + PLANS + "aws_risky.json", 1),
    (PLANS + "aws_db_replace.json", 2),
])
def test_gate_script(tmp_path, plans, expected):
    work = tmp_path / "repo"
    shutil.copytree(PROJECT, work / "projects" / "01-cloud-change-control",
                    ignore=shutil.ignore_patterns("workspace", "__pycache__", "*.egg-info"))
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    shim = shim_dir / "changegate"
    python = Path(sys.executable).as_posix()
    shim.write_text('#!/usr/bin/env bash\nexec "%s" -m changegate "$@"\n' % python, encoding="utf-8", newline="\n")
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
    script = tmp_path / "gate.sh"
    script.write_text(step_script("Gate every plan"), encoding="utf-8", newline="\n")
    summary = tmp_path / "summary.md"
    env = dict(os.environ,
               PYTHONPATH=str(work / "projects" / "01-cloud-change-control" / "reference"),
               CHANGEGATE_CONFIG="projects/01-cloud-change-control/sample_data/changegate.example.toml",
               CHANGEGATE_PLANS=plans, GITHUB_STEP_SUMMARY=summary.as_posix())
    env.pop("CHANGEGATE_HMAC_KEY", None)
    env["PATH"] = str(shim_dir) + os.pathsep + env["PATH"]
    result = subprocess.run([bash, script.as_posix()], cwd=str(work), env=env, capture_output=True, text=True,
                            timeout=120)
    assert result.returncode == expected, result.stdout + result.stderr
    assert summary.read_text(encoding="utf-8").count("## Cloud ChangeGate") == len(plans.split())

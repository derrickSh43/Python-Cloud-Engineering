"""End-to-end tests of the command-line tool, including the full approval workflow."""

import json
import shutil

import pytest

from changegate import cli


@pytest.fixture
def workdir(tmp_path, samples, example_config_path, monkeypatch):
    """A scratch directory with the sample plans and the example config (audit log goes here too)."""
    shutil.copytree(samples, tmp_path / "plans")
    shutil.copy(example_config_path, tmp_path / "changegate.toml")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CHANGEGATE_CONFIG", raising=False)
    monkeypatch.delenv("CHANGEGATE_AUTHOR", raising=False)
    return tmp_path


@pytest.mark.parametrize("plan, code", [
    ("aws_safe.json", cli.EXIT_OK), ("aws_db_replace.json", cli.EXIT_NEEDS_APPROVAL),
    ("aws_risky.json", cli.EXIT_BLOCKED), ("gcp_risky.json", cli.EXIT_BLOCKED),
])
def test_evaluate_exit_codes(workdir, plan, code, capsys):
    assert cli.main(["evaluate", "plans/" + plan]) == code
    assert "decision:" in capsys.readouterr().out


def test_evaluate_json_and_markdown(workdir, capsys):
    cli.main(["evaluate", "plans/gcp_risky.json", "--format", "json", "--output", "report.json"])
    data = json.loads(capsys.readouterr().out)
    assert data["decision"] == "block" and data["outcome"] == "BLOCKED"
    assert json.loads((workdir / "report.json").read_text())["risk"] == "CRITICAL"
    cli.main(["evaluate", "plans/aws_db_replace.json", "--format", "markdown"])
    assert "## Cloud ChangeGate: APPROVAL REQUIRED" in capsys.readouterr().out


def test_full_approval_workflow(workdir, key_env, capsys):
    plan = "plans/aws_db_replace.json"   # HIGH risk: needs 2 approvals
    assert cli.main(["verify", plan, "--author", "dave"]) == cli.EXIT_NEEDS_APPROVAL
    assert cli.main(["approve", plan, "--approver", "alice", "--comment", "maintenance window"]) == cli.EXIT_OK
    assert cli.main(["verify", plan, "--author", "dave"]) == cli.EXIT_NEEDS_APPROVAL
    # the author can't approve their own change
    assert cli.main(["approve", plan, "--approver", "dave"]) == cli.EXIT_OK
    assert cli.main(["verify", plan, "--author", "dave"]) == cli.EXIT_NEEDS_APPROVAL
    assert cli.main(["approve", plan, "--approver", "bob"]) == cli.EXIT_OK
    capsys.readouterr()
    assert cli.main(["verify", plan, "--author", "dave"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "decision:  APPROVED" in out and "dave: authors cannot approve their own change" in out
    # every step was audited and the chain is intact
    assert cli.main(["audit", "verify"]) == cli.EXIT_OK
    assert "audit log OK" in capsys.readouterr().out
    events = [json.loads(l)["event"] for l in (workdir / "changegate-audit.jsonl").read_text().splitlines()]
    assert events.count("approve") == 3 and events.count("verify") == 4


def test_approvals_do_not_transfer_to_a_modified_plan(workdir, key_env):
    plan = workdir / "plans" / "aws_db_replace.json"
    for who in ("alice", "bob"):
        cli.main(["approve", str(plan), "--approver", who])
    assert cli.main(["verify", str(plan), "--author", "dave"]) == cli.EXIT_OK
    plan.write_text(plan.read_text().replace("16.1", "16.2"))   # someone edits the plan after approval
    assert cli.main(["verify", str(plan), "--author", "dave"]) == cli.EXIT_NEEDS_APPROVAL


def test_approve_refuses_allowed_and_blocked(workdir, key_env, capsys):
    assert cli.main(["approve", "plans/aws_safe.json", "--approver", "alice"]) == cli.EXIT_OK
    assert "Nothing to approve" in capsys.readouterr().out
    assert cli.main(["approve", "plans/aws_risky.json", "--approver", "alice"]) == cli.EXIT_BLOCKED
    assert not (workdir / "approvals").exists()


def test_missing_key_is_an_error(workdir, monkeypatch, capsys):
    monkeypatch.delenv("CHANGEGATE_HMAC_KEY", raising=False)
    assert cli.main(["approve", "plans/aws_db_replace.json", "--approver", "alice"]) == cli.EXIT_ERROR
    assert "CHANGEGATE_HMAC_KEY" in capsys.readouterr().err
    assert cli.main(["verify", "plans/aws_db_replace.json"]) == cli.EXIT_NEEDS_APPROVAL
    assert "CHANGEGATE_HMAC_KEY" in capsys.readouterr().out


def test_tampered_audit_log_fails(workdir):
    cli.main(["evaluate", "plans/aws_safe.json"])
    cli.main(["evaluate", "plans/gcp_safe.json"])
    log = workdir / "changegate-audit.jsonl"
    log.write_text(log.read_text().replace('"decision": "allow"', '"decision": "block"', 1))
    assert cli.main(["audit", "verify"]) == cli.EXIT_BLOCKED


def test_errors_use_exit_code_3(workdir, capsys):
    assert cli.main(["evaluate", "plans/nope.json"]) == cli.EXIT_ERROR
    (workdir / "bad.toml").write_text("[risk]\napproval_at = 'severe'\n")
    assert cli.main(["--config", "bad.toml", "evaluate", "plans/aws_safe.json"]) == cli.EXIT_ERROR
    with pytest.raises(SystemExit) as exc:
        cli.main(["evaluate"])          # missing argument: usage error, not "needs approval"
    assert exc.value.code == cli.EXIT_ERROR


def test_no_audit_flag_and_policies_and_hash(workdir, capsys):
    cli.main(["evaluate", "plans/aws_safe.json", "--no-audit"])
    assert not (workdir / "changegate-audit.jsonl").exists()
    capsys.readouterr()
    assert cli.main(["policies"]) == cli.EXIT_OK
    assert "AWS-SG-OPEN-INGRESS" in capsys.readouterr().out
    assert cli.main(["hash", "plans/aws_safe.json"]) == cli.EXIT_OK
    assert len(capsys.readouterr().out.strip()) == 64


def test_audit_show(workdir, capsys):
    cli.main(["evaluate", "plans/aws_safe.json"])
    capsys.readouterr()
    cli.main(["audit", "show", "--tail", "1"])
    assert json.loads(capsys.readouterr().out)["event"] == "evaluate"

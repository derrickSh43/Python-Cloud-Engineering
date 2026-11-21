from changegate import evaluator, report
from changegate.approvals import ApprovalCheck
from changegate.config import load_config
from support import EXAMPLE_CONFIG, sample


def evaluate(name):
    return evaluator.evaluate_file(sample(name), load_config(EXAMPLE_CONFIG))


def test_final_outcome():
    """final_outcome reflects the decision and, for approvals, the check"""
    replace = evaluate("aws_db_replace.json")
    assert report.final_outcome(replace, None) == "APPROVAL REQUIRED"
    assert report.final_outcome(replace, ApprovalCheck(True, 2, ("a", "b"), ())) == "APPROVED"
    assert report.final_outcome(replace, ApprovalCheck(False, 2, ("a",), ())) == "APPROVAL REQUIRED"
    assert report.final_outcome(evaluate("aws_risky.json"), None) == "BLOCKED"
    assert report.final_outcome(evaluate("aws_safe.json"), ApprovalCheck(True, 0, (), ())) == "ALLOW"


def test_header_lines():
    """the text report starts with the plan, changes, risk and decision"""
    result = evaluate("aws_db_replace.json")
    lines = report.render_text(result).splitlines()
    assert lines[0] == "Cloud ChangeGate"
    assert lines[1] == "  plan:      sha256 " + result.plan_sha256
    assert lines[2] == "  changes:   1 create, 1 replace"
    assert lines[3] == "  risk:      HIGH"
    assert lines[4] == "  decision:  APPROVAL REQUIRED"
    assert lines[5].startswith("             - ")


def test_findings_section():
    """each finding shows severity, policy, address, message and fix"""
    text = report.render_text(evaluate("aws_db_replace.json"))
    assert "Findings (1):" in text
    assert "  [HIGH    ] CG-DESTROY-STATEFUL  aws_db_instance.orders" in text
    assert "             fix: Confirm backups" in text
    assert text.endswith("\n")
    assert "Findings" not in report.render_text(evaluate("aws_safe.json"))


def test_approvals_section():
    """with a check, approvals and problems are listed"""
    check = ApprovalCheck(False, 2, ("alice",), ("bob: expired at 2026-01-01T00:00:00Z",))
    text = report.render_text(evaluate("aws_db_replace.json"), check)
    assert "Approvals: 1 of 2 required" in text
    assert "  ok   alice" in text and "  --   bob: expired" in text
    assert "Approvals" not in report.render_text(evaluate("aws_safe.json"), ApprovalCheck(True, 0, (), ()))

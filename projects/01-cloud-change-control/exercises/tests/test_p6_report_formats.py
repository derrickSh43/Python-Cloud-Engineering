import json

from changegate import evaluator, report
from changegate.approvals import ApprovalCheck
from changegate.config import load_config
from support import EXAMPLE_CONFIG, sample


def evaluate(name):
    return evaluator.evaluate_file(sample(name), load_config(EXAMPLE_CONFIG))


def test_json_report():
    """the JSON report is the evaluation plus outcome (and approvals when given)"""
    result = evaluate("gcp_risky.json")
    text = report.render_json(result)
    assert text.endswith("\n")
    data = json.loads(text)
    assert data["outcome"] == "BLOCKED" and data["risk"] == "CRITICAL" and "approvals" not in data
    with_check = json.loads(report.render_json(evaluate("aws_db_replace.json"), ApprovalCheck(True, 2, ("a", "b"), ())))
    assert with_check["outcome"] == "APPROVED" and with_check["approvals"]["approved_by"] == ["a", "b"]


def test_markdown_header():
    """the Markdown report starts with a heading and a summary table"""
    result = evaluate("aws_db_replace.json")
    md = report.render_markdown(result)
    assert md.startswith("## Cloud ChangeGate: APPROVAL REQUIRED\n")
    assert "| Risk | **HIGH** |" in md
    assert "| Plan SHA-256 | `%s` |" % result.plan_sha256 in md
    assert md.endswith("\n")


def test_markdown_findings_table():
    """findings appear in a table with code-formatted policy and resource"""
    md = report.render_markdown(evaluate("aws_db_replace.json"))
    assert "### Findings" in md and "| Severity | Policy | Resource | Problem | Fix |" in md
    assert "| HIGH | `CG-DESTROY-STATEFUL` | `aws_db_instance.orders` |" in md
    assert "### Findings" not in report.render_markdown(evaluate("aws_safe.json"))


def test_markdown_escapes_pipes():
    """a | inside a message can't break the table"""
    check = ApprovalCheck(False, 2, ("alice",), ("bob | mallory: not in the configured approvers list",))
    md = report.render_markdown(evaluate("aws_db_replace.json"), check)
    assert "### Approvals (1 of 2)" in md and "- approved by **alice**" in md
    assert "bob \\| mallory" in md

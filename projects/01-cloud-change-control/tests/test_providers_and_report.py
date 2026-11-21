import json

from changegate import evaluator, providers, report
from changegate.approvals import ApprovalCheck
from changegate.config import load_config


def test_provider_lookup():
    assert providers.provider_key("registry.terraform.io/hashicorp/aws") == "aws"
    assert providers.cloud_for("registry.terraform.io/hashicorp/google-beta") == "gcp"
    assert providers.cloud_for("registry.terraform.io/hashicorp/azurerm") == "other"
    assert "aws_db_instance" in providers.all_stateful_types()
    assert "google_sql_database_instance" in providers.all_stateful_types()


def test_registering_a_new_provider():
    providers.register(providers.Provider("examplecloud", "example", ("labels",), frozenset({"examplecloud_db"})))
    assert providers.cloud_for("registry.terraform.io/acme/examplecloud") == "example"
    assert "examplecloud_db" in providers.all_stateful_types()


def test_reports(samples, example_config_path):
    result = evaluator.evaluate_file(samples / "aws_db_replace.json", load_config(example_config_path))
    check = ApprovalCheck(False, 2, ("alice",), ("1 of 2 required approval(s) for HIGH risk",))
    text = report.render_text(result, check)
    assert "APPROVAL REQUIRED" in text and "ok   alice" in text and "CG-DESTROY-STATEFUL" in text
    data = json.loads(report.render_json(result, check))
    assert data["approvals"]["approved_by"] == ["alice"]
    md = report.render_markdown(result, check)
    assert md.startswith("## Cloud ChangeGate") and "| HIGH |" in md
    satisfied = ApprovalCheck(True, 2, ("alice", "bob"), ())
    assert report.final_outcome(result, satisfied) == "APPROVED"

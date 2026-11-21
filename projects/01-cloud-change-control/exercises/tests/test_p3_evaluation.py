import dataclasses
import json

from changegate.models import Action, Decision, Evaluation, Finding, ResourceChange, Severity


def change(address, action):
    t = address.split(".")[0]
    return ResourceChange(address, t, address.split(".")[1], "aws", "aws", action)


def sample_evaluation():
    changes = (change("aws_s3_bucket.a", Action.CREATE), change("aws_s3_bucket.b", Action.CREATE),
               change("aws_db_instance.c", Action.DELETE))
    findings = (Finding("CG-DESTROY-STATEFUL", Severity.HIGH, "aws_db_instance.c", "deleted", "backup"),)
    return Evaluation("f" * 64, changes, findings, Severity.HIGH, Decision.REQUIRE_APPROVAL, ("why",))


def test_fields():
    """Evaluation is a frozen dataclass with six fields in order"""
    assert dataclasses.is_dataclass(Evaluation)
    assert [f.name for f in dataclasses.fields(Evaluation)] == [
        "plan_sha256", "changes", "findings", "risk", "decision", "reasons"]


def test_action_counts():
    """action_counts counts changes by action value"""
    assert sample_evaluation().action_counts == {"create": 2, "delete": 1}


def test_to_dict():
    """to_dict produces the documented JSON-ready structure"""
    data = sample_evaluation().to_dict()
    assert data["plan_sha256"] == "f" * 64
    assert data["risk"] == "HIGH" and data["decision"] == "require_approval"
    assert data["reasons"] == ["why"]
    assert data["summary"] == {"resources": 3, "actions": {"create": 2, "delete": 1}, "findings": 1}
    assert data["findings"][0]["severity"] == "HIGH"
    assert data["changes"][2] == {"address": "aws_db_instance.c", "type": "aws_db_instance", "cloud": "aws",
                                  "action": "delete"}
    json.dumps(data)

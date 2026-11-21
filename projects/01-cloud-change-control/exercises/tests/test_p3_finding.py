import dataclasses
import json

from changegate.models import Finding, Severity
from support import raises


def test_fields_and_default():
    """Finding has five fields; remediation defaults to ''"""
    assert dataclasses.is_dataclass(Finding), "decorate the class with @dataclass(frozen=True)"
    assert [f.name for f in dataclasses.fields(Finding)] == ["policy_id", "severity", "address", "message", "remediation"]
    finding = Finding("AWS-X", Severity.HIGH, "aws_s3_bucket.a", "bad")
    assert finding.remediation == ""


def test_frozen_and_comparable():
    """Findings are frozen and equal when their fields are equal"""
    a = Finding("AWS-X", Severity.HIGH, "r.a", "bad", "fix it")
    assert a == Finding("AWS-X", Severity.HIGH, "r.a", "bad", "fix it")
    raises(dataclasses.FrozenInstanceError, setattr, a, "message", "changed")


def test_to_dict():
    """to_dict returns plain JSON-ready data with the severity name as text"""
    data = Finding("GCP-Y", Severity.CRITICAL, "google_x.y", "open", "close it").to_dict()
    assert data == {"policy_id": "GCP-Y", "severity": "CRITICAL", "address": "google_x.y", "message": "open",
                    "remediation": "close it"}
    json.dumps(data)

import json
from datetime import datetime, timedelta, timezone

from changegate import approvals as ap
from changegate.models import Severity
from support import raises

UTC = timezone.utc
ISSUED = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)


def approval(**overrides):
    values = dict(plan_sha256="a" * 64, approver="alice", risk=Severity.HIGH, issued_at=ISSUED,
                  expires_at=ISSUED + timedelta(hours=24), comment="window", signature="sig")
    values.update(overrides)
    return ap.Approval(**values)


def test_iso():
    """_iso formats UTC with a Z suffix and converts other timezones to UTC"""
    assert ap._iso(ISSUED) == "2026-03-01T12:00:00Z"
    plus_two = datetime(2026, 3, 1, 14, 0, 30, 999, tzinfo=timezone(timedelta(hours=2)))
    assert ap._iso(plus_two) == "2026-03-01T12:00:30Z"


def test_iso_rejects_naive():
    """naive datetimes (no timezone) are refused"""
    raises(ap.ApprovalError, ap._iso, datetime(2026, 3, 1, 12, 0))


def test_parse_time():
    """_parse_time accepts Z and offsets, refuses naive and garbage"""
    assert ap._parse_time("2026-03-01T12:00:00Z", "issued_at") == ISSUED
    assert ap._parse_time("2026-03-01T14:00:00+02:00", "issued_at") == ISSUED
    assert "timezone" in str(raises(ap.ApprovalError, ap._parse_time, "2026-03-01T12:00:00", "issued_at"))
    assert "ISO-8601" in str(raises(ap.ApprovalError, ap._parse_time, "yesterday", "issued_at"))


def test_payload_and_to_dict():
    """payload holds the signed fields; to_dict adds the signature"""
    payload = approval().payload()
    assert payload == {"version": 1, "plan_sha256": "a" * 64, "approver": "alice", "risk": "HIGH",
                       "issued_at": "2026-03-01T12:00:00Z", "expires_at": "2026-03-02T12:00:00Z", "comment": "window"}
    assert approval().to_dict() == {**payload, "signature": "sig"}


def test_from_dict_roundtrip():
    """from_dict(to_dict()) gives back an equal Approval"""
    original = approval()
    restored = ap.Approval.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original and restored.signature == "sig"
    data = original.to_dict()
    del data["comment"]
    assert ap.Approval.from_dict(data).comment == ""


def test_from_dict_errors():
    """bad input raises ApprovalError with a clear reason"""
    good = approval().to_dict()
    raises(ap.ApprovalError, ap.Approval.from_dict, ["not", "a", "dict"])
    missing = {k: v for k, v in good.items() if k != "signature"}
    assert str(raises(ap.ApprovalError, ap.Approval.from_dict, missing)).startswith("approval is missing:")
    assert "unsupported" in str(raises(ap.ApprovalError, ap.Approval.from_dict, {**good, "version": 2}))
    raises(ap.ApprovalError, ap.Approval.from_dict, {**good, "risk": "severe"})

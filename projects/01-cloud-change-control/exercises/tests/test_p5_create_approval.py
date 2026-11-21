from datetime import datetime, timedelta, timezone

from changegate import approvals as ap
from changegate.models import Severity
from support import raises

KEY = b"k" * 32
NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


def test_creates_signed_approval():
    """create_approval returns a signed approval issued now, expiring after ttl_hours"""
    approval = ap.create_approval("a" * 64, " alice ", Severity.HIGH, KEY, ttl_hours=4, comment="ok", now=NOW)
    assert approval.approver == "alice"
    assert approval.issued_at == NOW and approval.expires_at == NOW + timedelta(hours=4)
    assert approval.risk is Severity.HIGH and approval.comment == "ok"
    assert ap.signature_valid(approval, KEY)


def test_default_now_is_utc():
    """without `now`, the current UTC time is used"""
    approval = ap.create_approval("b" * 64, "bob", Severity.MEDIUM, KEY, ttl_hours=1)
    assert approval.issued_at.tzinfo is not None
    assert abs((approval.issued_at - datetime.now(timezone.utc)).total_seconds()) < 60


def test_validation():
    """bad hashes, blank approvers and non-positive TTLs are refused"""
    for bad_hash in ("short", "A" * 64, "g" * 64):
        raises(ap.ApprovalError, ap.create_approval, bad_hash, "alice", Severity.HIGH, KEY, 1, now=NOW)
    raises(ap.ApprovalError, ap.create_approval, "a" * 64, "   ", Severity.HIGH, KEY, 1, now=NOW)
    raises(ap.ApprovalError, ap.create_approval, "a" * 64, "alice", Severity.HIGH, KEY, 0, now=NOW)

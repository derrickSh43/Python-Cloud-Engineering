import hashlib
import hmac
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from changegate import approvals as ap
from changegate.canonical import canonical_bytes
from changegate.models import Severity
from support import raises

KEY = b"k" * 32
ISSUED = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
UNSIGNED = ap.Approval("a" * 64, "alice", Severity.HIGH, ISSUED, ISSUED + timedelta(hours=1))


def test_load_key():
    """load_key reads the variable and returns bytes"""
    assert ap.load_key("MY_KEY", {"MY_KEY": "x" * 32}) == b"x" * 32


def test_load_key_errors():
    """missing/empty keys say 'not set'; short keys say 'too short'"""
    assert "not set" in str(raises(ap.ApprovalError, ap.load_key, "MY_KEY", {}))
    assert "not set" in str(raises(ap.ApprovalError, ap.load_key, "MY_KEY", {"MY_KEY": ""}))
    assert "too short" in str(raises(ap.ApprovalError, ap.load_key, "MY_KEY", {"MY_KEY": "short"}))


def test_compute_signature():
    """the signature is HMAC-SHA256 of the canonical payload"""
    expected = hmac.new(KEY, canonical_bytes(UNSIGNED.payload()), hashlib.sha256).hexdigest()
    assert ap.compute_signature(UNSIGNED, KEY) == expected


def test_sign_returns_a_copy():
    """sign returns a new Approval with the signature set"""
    signed = ap.sign(UNSIGNED, KEY)
    assert signed is not UNSIGNED and UNSIGNED.signature == ""
    assert signed.signature == ap.compute_signature(UNSIGNED, KEY)


def test_signature_valid():
    """a signed approval verifies with the right key only"""
    signed = ap.sign(UNSIGNED, KEY)
    assert ap.signature_valid(signed, KEY) is True
    assert ap.signature_valid(signed, b"z" * 32) is False


def test_any_edit_invalidates():
    """changing the approver, risk, expiry or plan breaks the signature"""
    signed = ap.sign(UNSIGNED, KEY)
    for edited in (replace(signed, approver="mallory"), replace(signed, risk=Severity.CRITICAL),
                   replace(signed, expires_at=signed.expires_at + timedelta(days=30)),
                   replace(signed, plan_sha256="b" * 64)):
        assert not ap.signature_valid(edited, KEY)

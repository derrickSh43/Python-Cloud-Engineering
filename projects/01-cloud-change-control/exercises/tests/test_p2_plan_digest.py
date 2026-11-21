import hashlib

from changegate.plan_parser import plan_digest


def test_returns_hex_string():
    """plan_digest returns a 64-character lowercase hex string"""
    digest = plan_digest(b"{}")
    assert isinstance(digest, str), "expected a str, got %s" % type(digest).__name__
    assert len(digest) == 64, "a SHA-256 hex digest has 64 characters, got %d" % len(digest)
    assert digest == digest.lower()


def test_matches_sha256():
    """plan_digest is the SHA-256 of exactly the bytes given"""
    raw = b'{"format_version": "1.2"}'
    assert plan_digest(raw) == hashlib.sha256(raw).hexdigest()


def test_one_byte_changes_everything():
    """changing a single byte gives a different digest"""
    assert plan_digest(b"plan-a") != plan_digest(b"plan-b")
    assert plan_digest(b"same") == plan_digest(b"same")

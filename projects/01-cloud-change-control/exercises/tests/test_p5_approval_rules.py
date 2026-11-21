from datetime import datetime, timedelta, timezone

from changegate import approvals as ap
from changegate.config import ApprovalConfig
from changegate.models import Decision, Evaluation, Severity

KEY = b"k" * 32
NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
PLAN = "a" * 64
CFG = ApprovalConfig(approvers=("alice", "bob"))
EVALUATION = Evaluation(PLAN, (), (), Severity.HIGH, Decision.REQUIRE_APPROVAL, ())


def approve(who="alice", risk=Severity.HIGH, plan=PLAN, issued=NOW, ttl=24, key=KEY):
    return ap.create_approval(plan, who, risk, key, ttl_hours=ttl, now=issued)


def problem(approval, author=None, cfg=CFG, now=NOW):
    return ap.approval_problem(approval, EVALUATION, cfg, KEY, author, now)


def test_valid_approval():
    """a correct approval has no problem (None)"""
    assert problem(approve()) is None
    assert problem(approve("ALICE")) is None, "approver names are compared case-insensitively"


def test_each_rule():
    """each broken rule is reported with the approver's name first"""
    cases = [
        (approve(key=b"x" * 32), {}, "signature is invalid"),
        (approve(plan="b" * 64), {}, "different plan"),
        (approve(issued=NOW + timedelta(hours=1)), {}, "issued in the future"),
        (approve(issued=NOW - timedelta(hours=2), ttl=1), {}, "expired"),
        (approve(issued=NOW - timedelta(hours=30), ttl=48), {}, "older than"),
        (approve(), {"author": "Alice"}, "own change"),
        (approve("mallory"), {}, "not in the configured approvers"),
        (approve(risk=Severity.MEDIUM), {}, "but the plan is now HIGH"),
    ]
    for approval, kwargs, expected in cases:
        result = problem(approval, **kwargs)
        assert result is not None and expected in result, "expected %r, got %r" % (expected, result)
        assert result.startswith(approval.approver + ": "), result


def test_signature_checked_first():
    """a forged approval is rejected for its signature before anything else is believed"""
    forged = approve("mallory", plan="b" * 64, key=b"x" * 32)
    assert "signature" in problem(forged)


def test_small_clock_skew_allowed():
    """an approval issued a minute 'in the future' (clock skew) is fine"""
    assert problem(approve(issued=NOW + timedelta(minutes=1))) is None


def test_self_approval_setting():
    """allow_self_approval lets authors approve their own change"""
    cfg = ApprovalConfig(approvers=("alice",), allow_self_approval=True)
    assert problem(approve(), author="alice", cfg=cfg) is None

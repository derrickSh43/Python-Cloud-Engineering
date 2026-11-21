import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from changegate import approvals as ap
from changegate.config import ApprovalConfig
from changegate.models import Decision, Evaluation, Severity

KEY = b"k" * 32
NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
PLAN = "a" * 64
CFG = ApprovalConfig(approvers=("alice", "bob", "carol"))


def evaluation(level=Severity.HIGH, decision=Decision.REQUIRE_APPROVAL, plan=PLAN):
    return Evaluation(plan, (), (), level, decision, ())


def approve(who, level=Severity.HIGH, plan=PLAN, now=NOW, ttl=24, key=KEY):
    return ap.create_approval(plan, who, level, key, ttl_hours=ttl, now=now)


def test_load_key(monkeypatch):
    assert ap.load_key("K", {"K": "x" * 32}) == b"x" * 32
    with pytest.raises(ap.ApprovalError, match="not set"):
        ap.load_key("K", {})
    with pytest.raises(ap.ApprovalError, match="too short"):
        ap.load_key("K", {"K": "short"})


def test_sign_and_verify_roundtrip():
    approval = approve("alice")
    assert ap.signature_valid(approval, KEY)
    assert not ap.signature_valid(approval, b"z" * 32)
    restored = ap.Approval.from_dict(json.loads(json.dumps(approval.to_dict())))
    assert restored == approval and ap.signature_valid(restored, KEY)


def test_any_edit_breaks_signature():
    approval = approve("alice")
    for changed in (replace(approval, approver="mallory"), replace(approval, risk=Severity.CRITICAL),
                    replace(approval, expires_at=approval.expires_at + timedelta(days=30)),
                    replace(approval, plan_sha256="b" * 64)):
        assert not ap.signature_valid(changed, KEY)


def test_create_validates_input():
    with pytest.raises(ap.ApprovalError):
        ap.create_approval("not-a-hash", "alice", Severity.HIGH, KEY, 1, now=NOW)
    with pytest.raises(ap.ApprovalError):
        ap.create_approval(PLAN, "  ", Severity.HIGH, KEY, 1, now=NOW)
    with pytest.raises(ap.ApprovalError):
        ap.create_approval(PLAN, "alice", Severity.HIGH, KEY, 0, now=NOW)


def test_two_approvals_satisfy_high_risk():
    check = ap.check_approvals(evaluation(), [approve("alice"), approve("bob")], CFG, KEY, author="dave", now=NOW)
    assert check.satisfied and check.required == 2 and set(check.approved_by) == {"alice", "bob"}


def test_one_approval_is_not_enough_for_high():
    check = ap.check_approvals(evaluation(), [approve("alice")], CFG, KEY, now=NOW)
    assert not check.satisfied and any("1 of 2" in p for p in check.problems)


def test_duplicate_approver_counts_once():
    check = ap.check_approvals(evaluation(), [approve("alice"), approve("ALICE")], CFG, KEY, now=NOW)
    assert not check.satisfied and any("duplicate" in p for p in check.problems)


@pytest.mark.parametrize("approval_kwargs, check_kwargs, message", [
    ({"key": b"x" * 32}, {}, "signature"),
    ({"plan": "b" * 64}, {}, "different plan"),
    ({"now": NOW + timedelta(hours=1)}, {}, "future"),
    ({"now": NOW - timedelta(hours=2), "ttl": 1}, {}, "expired"),
    ({"now": NOW - timedelta(hours=30), "ttl": 48}, {}, "older than"),
    ({"level": Severity.MEDIUM}, {}, "now HIGH"),
    ({}, {"author": "Alice"}, "own change"),
])
def test_invalid_approvals(approval_kwargs, check_kwargs, message):
    check = ap.check_approvals(evaluation(), [approve("alice", **approval_kwargs), approve("bob")], CFG, KEY,
                               now=NOW, **check_kwargs)
    assert not check.satisfied
    assert any(message in p for p in check.problems), check.problems


def test_unlisted_approver():
    check = ap.check_approvals(evaluation(Severity.MEDIUM), [approve("mallory", Severity.MEDIUM)], CFG, KEY, now=NOW)
    assert not check.satisfied and any("not in the configured approvers" in p for p in check.problems)


def test_self_approval_when_allowed():
    cfg = replace(CFG, allow_self_approval=True)
    check = ap.check_approvals(evaluation(Severity.MEDIUM), [approve("alice", Severity.MEDIUM)], cfg, KEY,
                               author="alice", now=NOW)
    assert check.satisfied


def test_allow_and_block_ignore_approvals():
    assert ap.check_approvals(evaluation(Severity.LOW, Decision.ALLOW), [], CFG, None).satisfied
    blocked = ap.check_approvals(evaluation(Severity.CRITICAL, Decision.BLOCK),
                                 [approve("alice", Severity.CRITICAL), approve("bob", Severity.CRITICAL)], CFG, KEY, now=NOW)
    assert not blocked.satisfied and "blocked" in blocked.problems[0]


def test_no_approvers_configured():
    check = ap.check_approvals(evaluation(), [approve("alice")], ApprovalConfig(), KEY, now=NOW)
    assert not check.satisfied and "no approvers" in check.problems[0]


def test_write_and_load_files(tmp_path):
    path = ap.write_approval(approve("alice"), tmp_path)
    assert path.name.startswith(PLAN[:12])
    (tmp_path / "garbage.json").write_text("{nope")
    (tmp_path / "incomplete.json").write_text('{"version": 1}')
    found, problems = ap.load_approvals([tmp_path, tmp_path / "missing.json"])
    assert [a.approver for a in found] == ["alice"]
    assert len(problems) == 3


def test_from_dict_rejects_naive_timestamps():
    data = approve("alice").to_dict()
    data["issued_at"] = "2026-03-01T12:00:00"
    with pytest.raises(ap.ApprovalError, match="timezone"):
        ap.Approval.from_dict(data)

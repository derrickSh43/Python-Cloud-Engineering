from datetime import datetime, timezone

from changegate import approvals as ap
from changegate.config import ApprovalConfig
from changegate.models import Decision, Evaluation, Severity

KEY = b"k" * 32
NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
PLAN = "a" * 64
CFG = ApprovalConfig(approvers=("alice", "bob", "carol"))


def evaluation(risk=Severity.HIGH, decision=Decision.REQUIRE_APPROVAL):
    return Evaluation(PLAN, (), (), risk, decision, ())


def approve(who, risk=Severity.HIGH):
    return ap.create_approval(PLAN, who, risk, KEY, ttl_hours=24, now=NOW)


def test_allow_needs_nothing():
    """an allowed plan is satisfied with zero approvals"""
    check = ap.check_approvals(evaluation(Severity.LOW, Decision.ALLOW), [], CFG, None)
    assert check == ap.ApprovalCheck(True, 0, (), ())


def test_block_cannot_be_approved():
    """a blocked plan is never satisfied"""
    check = ap.check_approvals(evaluation(Severity.CRITICAL, Decision.BLOCK),
                               [approve("alice", Severity.CRITICAL), approve("bob", Severity.CRITICAL)], CFG, KEY, now=NOW)
    assert not check.satisfied and "blocked" in check.problems[0]


def test_two_approvers_for_high():
    """HIGH risk needs two distinct approvers"""
    check = ap.check_approvals(evaluation(), [approve("alice"), approve("bob")], CFG, KEY, author="dave", now=NOW)
    assert check.satisfied and check.required == 2 and check.approved_by == ("alice", "bob")


def test_not_enough():
    """one approval for HIGH is reported as '1 of 2'"""
    check = ap.check_approvals(evaluation(), [approve("alice")], CFG, KEY, now=NOW)
    assert not check.satisfied
    assert check.problems[-1] == "1 of 2 required approval(s) for HIGH risk", check.problems


def test_duplicates_count_once():
    """the same person approving twice counts once"""
    check = ap.check_approvals(evaluation(), [approve("alice"), approve("Alice")], CFG, KEY, now=NOW)
    assert not check.satisfied and check.approved_by == ("alice",)
    assert any("duplicate" in p for p in check.problems)


def test_invalid_approvals_listed():
    """invalid approvals are explained but not counted"""
    check = ap.check_approvals(evaluation(Severity.MEDIUM), [approve("mallory", Severity.MEDIUM),
                                                             approve("carol", Severity.MEDIUM)], CFG, KEY, now=NOW)
    assert check.satisfied and check.approved_by == ("carol",)
    assert any("mallory" in p for p in check.problems)


def test_missing_configuration():
    """no approvers configured, or no key, can't be satisfied"""
    no_approvers = ap.check_approvals(evaluation(), [approve("alice")], ApprovalConfig(), KEY, now=NOW)
    assert not no_approvers.satisfied and "no approvers" in no_approvers.problems[0]
    no_key = ap.check_approvals(evaluation(), [approve("alice")], CFG, None, now=NOW)
    assert not no_key.satisfied and "no signing key" in no_key.problems[0]

from changegate.config import RiskConfig
from changegate.models import Decision, Finding, Severity
from changegate.risk import classify, decide
from support import make_change


def finding(level):
    return Finding("TEST", level, "x.y", "msg")


def test_no_changes():
    """no state changes and no findings is LOW: 'the plan makes no changes'"""
    level, reasons = classify([make_change("aws_s3_bucket", {}, action="no-op", before={})], [])
    assert level is Severity.LOW and reasons == ["the plan makes no changes"]


def test_highest_finding_wins():
    """risk is the highest finding severity, explained in the first reason"""
    level, reasons = classify([make_change("aws_s3_bucket", {})],
                              [finding(Severity.MEDIUM), finding(Severity.HIGH), finding(Severity.HIGH)])
    assert level is Severity.HIGH
    assert reasons[0] == "3 finding(s); highest severity HIGH (2 at that level)", reasons


def test_no_findings():
    """changes without findings are LOW"""
    level, reasons = classify([make_change("aws_s3_bucket", {}, name="a"), make_change("aws_s3_bucket", {}, name="b")], [])
    assert level is Severity.LOW and reasons == ["no policy findings across 2 change(s)"]


def test_destructive_escalation():
    """reaching the destructive threshold raises risk one level; 0 disables it"""
    deletes = [make_change("aws_instance", action="delete", before={}, name="n%d" % i) for i in range(3)]
    level, reasons = classify(deletes, [], RiskConfig(destructive_escalation_threshold=3))
    assert level is Severity.MEDIUM and "destructive" in reasons[-1]
    assert classify(deletes[:2], [], RiskConfig(destructive_escalation_threshold=3))[0] is Severity.LOW
    assert classify(deletes, [], RiskConfig(destructive_escalation_threshold=0))[0] is Severity.LOW
    critical = classify(deletes, [finding(Severity.CRITICAL)], RiskConfig(destructive_escalation_threshold=3))
    assert critical[0] is Severity.CRITICAL and len(critical[1]) == 1


def test_default_decisions():
    """defaults: LOW allow, MEDIUM/HIGH approval, CRITICAL block"""
    assert decide(Severity.LOW)[0] is Decision.ALLOW
    assert decide(Severity.MEDIUM)[0] is Decision.REQUIRE_APPROVAL
    assert decide(Severity.HIGH)[0] is Decision.REQUIRE_APPROVAL
    decision, why = decide(Severity.CRITICAL)
    assert decision is Decision.BLOCK and "block" in why


def test_custom_thresholds():
    """thresholds come from config; block_at None never blocks"""
    cfg = RiskConfig(approval_at=Severity.HIGH, block_at=None)
    assert decide(Severity.MEDIUM, cfg)[0] is Decision.ALLOW
    assert decide(Severity.CRITICAL, cfg)[0] is Decision.REQUIRE_APPROVAL

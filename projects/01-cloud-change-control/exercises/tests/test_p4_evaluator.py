from changegate import evaluator
from changegate.config import load_config
from changegate.models import Decision, Evaluation, Severity
from support import EXAMPLE_CONFIG, sample

EXPECTED = {
    "aws_safe.json": (Severity.LOW, Decision.ALLOW),
    "gcp_safe.json": (Severity.LOW, Decision.ALLOW),
    "missing_tags.json": (Severity.LOW, Decision.ALLOW),
    "gcp_bucket_acls.json": (Severity.MEDIUM, Decision.REQUIRE_APPROVAL),
    "multi_cloud_teardown.json": (Severity.MEDIUM, Decision.REQUIRE_APPROVAL),
    "aws_db_replace.json": (Severity.HIGH, Decision.REQUIRE_APPROVAL),
    "aws_risky.json": (Severity.CRITICAL, Decision.BLOCK),
    "gcp_risky.json": (Severity.CRITICAL, Decision.BLOCK),
}


def test_every_sample_plan():
    """every sample plan gets the expected risk and decision"""
    cfg = load_config(EXAMPLE_CONFIG)
    for name, (risk, decision) in EXPECTED.items():
        result = evaluator.evaluate_file(sample(name), cfg)
        assert isinstance(result, Evaluation)
        assert (result.risk, result.decision) == (risk, decision), "%s: got %s / %s" % (name, result.risk, result.decision)


def test_findings_sorted():
    """findings are sorted most severe first, then by address"""
    result = evaluator.evaluate_file(sample("aws_risky.json"), load_config(EXAMPLE_CONFIG))
    keys = [(-f.severity, f.address, f.policy_id) for f in result.findings]
    assert keys == sorted(keys)
    assert result.findings[0].policy_id == "AWS-IAM-WILDCARD"


def test_tuples_and_reasons():
    """changes/findings are tuples; reasons end with the decision's explanation"""
    result = evaluator.evaluate_file(sample("aws_db_replace.json"))
    assert isinstance(result.changes, tuple) and isinstance(result.findings, tuple)
    assert "approval threshold" in result.reasons[-1]
    assert len(result.plan_sha256) == 64


def test_custom_policies():
    """an explicit (empty) policy list is respected"""
    result = evaluator.evaluate_bytes(sample("aws_risky.json").read_bytes(), policies=[])
    assert result.findings == () and result.decision is Decision.ALLOW

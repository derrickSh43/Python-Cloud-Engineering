import pytest

from changegate import evaluator, risk
from changegate.config import RiskConfig, load_config
from changegate.models import Decision, Finding, Severity


def finding(level):
    return Finding("TEST", level, "x.y", "msg")


def test_no_changes_is_low(make_change):
    level, reasons = risk.classify([make_change("aws_s3_bucket", {}, action="no-op", before={})], [])
    assert level is Severity.LOW and "no changes" in reasons[0]


def test_risk_is_max_finding(make_change):
    changes = [make_change("aws_s3_bucket", {})]
    level, _ = risk.classify(changes, [finding(Severity.MEDIUM), finding(Severity.HIGH), finding(Severity.LOW)])
    assert level is Severity.HIGH


def test_destructive_escalation(make_change):
    deletes = [make_change("aws_instance", action="delete", before={}, name="n%d" % n) for n in range(5)]
    level, reasons = risk.classify(deletes, [], RiskConfig(destructive_escalation_threshold=5))
    assert level is Severity.MEDIUM and any("destructive" in r for r in reasons)
    level, _ = risk.classify(deletes[:4], [], RiskConfig(destructive_escalation_threshold=5))
    assert level is Severity.LOW
    level, _ = risk.classify(deletes, [], RiskConfig(destructive_escalation_threshold=0))
    assert level is Severity.LOW


@pytest.mark.parametrize("level, expected", [
    (Severity.LOW, Decision.ALLOW), (Severity.MEDIUM, Decision.REQUIRE_APPROVAL),
    (Severity.HIGH, Decision.REQUIRE_APPROVAL), (Severity.CRITICAL, Decision.BLOCK),
])
def test_default_decisions(level, expected):
    assert risk.decide(level)[0] is expected


def test_custom_thresholds():
    cfg = RiskConfig(approval_at=Severity.HIGH, block_at=None)
    assert risk.decide(Severity.MEDIUM, cfg)[0] is Decision.ALLOW
    assert risk.decide(Severity.CRITICAL, cfg)[0] is Decision.REQUIRE_APPROVAL


# Expected outcome for every sample plan with the example config. This is the contract the
# learner's finished ChangeGate must meet too.
EXPECTED = {
    "aws_safe.json": (Severity.LOW, Decision.ALLOW, set()),
    "gcp_safe.json": (Severity.LOW, Decision.ALLOW, set()),
    "no_changes.json": (Severity.LOW, Decision.ALLOW, set()),
    "missing_tags.json": (Severity.LOW, Decision.ALLOW, {"CG-REQUIRED-TAGS"}),
    "gcp_bucket_acls.json": (Severity.MEDIUM, Decision.REQUIRE_APPROVAL, {"GCP-GCS-UNIFORM-ACCESS"}),
    "multi_cloud_teardown.json": (Severity.MEDIUM, Decision.REQUIRE_APPROVAL, set()),
    "aws_db_replace.json": (Severity.HIGH, Decision.REQUIRE_APPROVAL, {"CG-DESTROY-STATEFUL"}),
    "aws_risky.json": (Severity.CRITICAL, Decision.BLOCK, {
        "AWS-IAM-WILDCARD", "AWS-RDS-PUBLIC", "AWS-STORAGE-UNENCRYPTED", "AWS-S3-PUBLIC-ACL",
        "AWS-S3-PUBLIC-ACCESS-BLOCK", "AWS-SG-OPEN-INGRESS"}),
    "gcp_risky.json": (Severity.CRITICAL, Decision.BLOCK, {
        "GCP-FIREWALL-OPEN-INGRESS", "GCP-IAM-PRIMITIVE-ROLE", "GCP-SQL-PUBLIC-NETWORK", "GCP-GCS-PUBLIC-IAM",
        "GCP-GCS-UNIFORM-ACCESS"}),
}


def test_every_sample_has_an_expectation(samples):
    assert {p.name for p in samples.glob("*.json")} == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_sample_outcomes(samples, example_config_path, name):
    expected_risk, expected_decision, expected_policies = EXPECTED[name]
    result = evaluator.evaluate_file(samples / name, load_config(example_config_path))
    assert result.risk is expected_risk
    assert result.decision is expected_decision
    assert {f.policy_id for f in result.findings} == expected_policies
    assert len(result.plan_sha256) == 64


def test_findings_sorted_most_severe_first(samples, example_config_path):
    result = evaluator.evaluate_file(samples / "aws_risky.json", load_config(example_config_path))
    levels = [f.severity for f in result.findings]
    assert levels == sorted(levels, reverse=True)


def test_evaluation_to_dict(samples):
    data = evaluator.evaluate_file(samples / "aws_db_replace.json").to_dict()
    assert data["decision"] == "require_approval" and data["risk"] == "HIGH"
    assert data["summary"]["actions"] == {"replace": 1, "create": 1}

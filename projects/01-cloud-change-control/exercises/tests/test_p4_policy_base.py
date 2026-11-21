from changegate.models import Action, Finding, Severity
from changegate.policies.base import Policy
from support import make_change


class BucketPolicy(Policy):
    id = "TEST-BUCKET"
    title = "test"
    severity = Severity.MEDIUM
    resource_types = frozenset({"aws_s3_bucket"})

    def check(self, change):
        yield self.finding(change, "found it")


class AnyTypePolicy(BucketPolicy):
    id = "TEST-ANY"
    resource_types = frozenset()


def test_applies_to_matching_type():
    """applies_to is True for a listed resource type with a create/update/replace"""
    policy = BucketPolicy()
    assert policy.applies_to(make_change("aws_s3_bucket", {}))
    assert policy.applies_to(make_change("aws_s3_bucket", {}, action="replace", before={}))
    assert not policy.applies_to(make_change("aws_instance", {}))


def test_applies_to_respects_actions():
    """deletes, reads and no-ops are skipped by default"""
    policy = BucketPolicy()
    assert not policy.applies_to(make_change("aws_s3_bucket", action="delete", before={}))
    assert not policy.applies_to(make_change("aws_s3_bucket", {}, action="no-op", before={}))


def test_empty_resource_types_means_all():
    """an empty resource_types matches every type"""
    assert AnyTypePolicy().applies_to(make_change("google_compute_instance", {}))


def test_finding_fields():
    """finding() fills in the policy id and the change address"""
    change = make_change("aws_s3_bucket", {}, name="logs")
    finding = BucketPolicy().finding(change, "msg", "fix")
    assert finding == Finding("TEST-BUCKET", Severity.MEDIUM, "aws_s3_bucket.logs", "msg", "fix")


def test_finding_severity_argument():
    """a severity passed to finding() is used..."""
    change = make_change("aws_s3_bucket", {})
    assert BucketPolicy().finding(change, "m", severity=Severity.CRITICAL).severity is Severity.CRITICAL


def test_config_override_always_wins():
    """...unless config overrode the policy's severity"""
    change = make_change("aws_s3_bucket", {})
    policy = BucketPolicy(severity=Severity.LOW)
    assert policy.finding(change, "m", severity=Severity.CRITICAL).severity is Severity.LOW
    assert policy.finding(change, "m").severity is Severity.LOW
    assert Action.CREATE in policy.actions

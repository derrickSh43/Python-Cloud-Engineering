import types

from changegate.models import Severity
from changegate.policies.base import Policy, run_policies
from support import make_change


class Flags(Policy):
    id = "TEST-FLAG"
    title = "t"
    severity = Severity.LOW
    resource_types = frozenset({"aws_s3_bucket"})

    def check(self, change):
        yield self.finding(change, "flagged")


class Twice(Flags):
    id = "TEST-TWICE"
    resource_types = frozenset()

    def check(self, change):
        yield self.finding(change, "one")
        yield self.finding(change, "two")


class Broken(Flags):
    id = "TEST-BROKEN"

    def check(self, change):
        raise RuntimeError("boom")
        yield  # pragma: no cover


def test_is_a_generator():
    """run_policies is a generator"""
    assert isinstance(run_policies([], []), types.GeneratorType), "use yield / yield from"


def test_runs_matching_policies_in_order():
    """findings come change by change, policy by policy, only where applies_to is True"""
    changes = [make_change("aws_s3_bucket", {}, name="a"), make_change("aws_instance", {}, name="b")]
    found = [(f.address, f.message) for f in run_policies(iter([Flags(), Twice()]), changes)]
    assert found == [("aws_s3_bucket.a", "flagged"), ("aws_s3_bucket.a", "one"), ("aws_s3_bucket.a", "two"),
                     ("aws_instance.b", "one"), ("aws_instance.b", "two")], found


def test_crashing_policy_fails_closed():
    """a policy that raises produces a CRITICAL finding and the others still run"""
    found = list(run_policies([Broken(), Flags()], [make_change("aws_s3_bucket", {})]))
    assert len(found) == 2
    crash = found[0]
    assert crash.policy_id == "TEST-BROKEN" and crash.severity is Severity.CRITICAL
    assert "RuntimeError" in crash.message and "boom" in crash.message, crash.message
    assert found[1].message == "flagged"

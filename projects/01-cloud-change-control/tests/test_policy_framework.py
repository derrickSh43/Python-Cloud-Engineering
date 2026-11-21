import sys
import textwrap

import pytest

from changegate.config import PolicyConfig
from changegate.models import Severity
from changegate.policies import Policy, PolicyLoadError, load_policies, register, registered, run_policies


def ids(policies):
    return {p.id for p in policies}


def test_builtin_policies_cover_both_clouds():
    loaded = ids(load_policies())
    assert {"CG-DESTROY-STATEFUL", "CG-REQUIRED-TAGS"} <= loaded
    assert any(i.startswith("AWS-") for i in loaded) and any(i.startswith("GCP-") for i in loaded)


def test_disable_and_override():
    policies = load_policies(PolicyConfig(disabled=frozenset({"AWS-RDS-PUBLIC"}),
                                          severity_overrides={"GCP-GCS-UNIFORM-ACCESS": Severity.HIGH}))
    assert "AWS-RDS-PUBLIC" not in ids(policies)
    uniform = next(p for p in policies if p.id == "GCP-GCS-UNIFORM-ACCESS")
    assert uniform.level is Severity.HIGH


def test_override_wins_over_per_finding_severity(make_change):
    policies = load_policies(PolicyConfig(severity_overrides={"AWS-IAM-WILDCARD": Severity.MEDIUM}))
    change = make_change("aws_iam_policy", {"policy": '{"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]}'})
    findings = [f for f in run_policies(policies, [change]) if f.policy_id == "AWS-IAM-WILDCARD"]
    assert findings and all(f.severity is Severity.MEDIUM for f in findings)


@pytest.mark.parametrize("field", ["disabled", "severity_overrides", "settings"])
def test_unknown_policy_ids_are_rejected(field):
    value = {"NOPE-1": Severity.LOW} if field == "severity_overrides" else (
        {"NOPE-1": {}} if field == "settings" else frozenset({"NOPE-1"}))
    with pytest.raises(PolicyLoadError, match="NOPE-1"):
        load_policies(PolicyConfig(**{field: value}))


def test_unknown_policy_setting_rejected():
    with pytest.raises(PolicyLoadError, match="unknown setting"):
        load_policies(PolicyConfig(settings={"CG-REQUIRED-TAGS": {"requird": ["owner"]}}))


def test_extra_module_is_loaded(tmp_path, monkeypatch, make_change):
    (tmp_path / "acme_policies.py").write_text(textwrap.dedent('''
        from changegate.models import Severity
        from changegate.policies import Policy, register

        @register
        class NoLargeInstances(Policy):
            id = "ACME-NO-LARGE"
            title = "No large instances"
            severity = Severity.MEDIUM
            resource_types = frozenset({"aws_instance"})

            def check(self, change):
                if str(change.attributes.get("instance_type", "")).endswith("xlarge"):
                    yield self.finding(change, "too big")
    '''))
    monkeypatch.syspath_prepend(str(tmp_path))
    policies = load_policies(PolicyConfig(extra_modules=("acme_policies",)))
    assert "ACME-NO-LARGE" in ids(policies)
    findings = list(run_policies(policies, [make_change("aws_instance", {"instance_type": "m5.4xlarge"})]))
    assert [f.policy_id for f in findings] == ["ACME-NO-LARGE"]
    sys.modules.pop("acme_policies", None)


def test_missing_extra_module():
    with pytest.raises(PolicyLoadError, match="cannot import"):
        load_policies(PolicyConfig(extra_modules=("does_not_exist_anywhere",)))


def test_duplicate_id_rejected():
    class First(Policy):
        id = "TEST-DUP"
        title = "t"
        severity = Severity.LOW

        def check(self, change):
            return []

    register(First)

    class Second(First):
        pass

    with pytest.raises(PolicyLoadError, match="duplicate"):
        register(Second)
    registered()  # registry still usable


def test_crashing_policy_fails_closed(make_change):
    class Broken(Policy):
        id = "TEST-BROKEN"
        title = "broken"
        severity = Severity.LOW

        def check(self, change):
            raise RuntimeError("boom")

    findings = list(run_policies([Broken()], [make_change("aws_s3_bucket", {})]))
    assert len(findings) == 1 and findings[0].severity is Severity.CRITICAL and "boom" in findings[0].message


def test_policies_skip_no_op_and_reads(make_change):
    policies = load_policies()
    risky = {"acl": "public-read-write"}
    assert list(run_policies(policies, [make_change("aws_s3_bucket_acl", risky, action="no-op", before=risky)])) == []

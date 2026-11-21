from changegate.config import PolicyConfig
from changegate.models import Severity
from changegate.policies.base import Policy, PolicyLoadError, load_policies, register, registered
from support import raises


def test_register_returns_the_class():
    """@register returns the class and records it by id"""
    class Sample(Policy):
        id = "TEST-REG-1"
        title = "t"
        severity = Severity.LOW

        def check(self, change):
            return []

    assert register(Sample) is Sample, "a decorator must return the class"
    assert registered()["TEST-REG-1"] is Sample


def test_register_requires_attributes():
    """a class without id/title/severity is rejected"""
    class NoId(Policy):
        title = "t"
        severity = Severity.LOW

        def check(self, change):
            return []

    raises(PolicyLoadError, register, NoId)


def test_duplicate_ids():
    """two different classes can't share an id"""
    class First(Policy):
        id = "TEST-DUP"
        title = "t"
        severity = Severity.LOW

        def check(self, change):
            return []

    class Second(First):
        pass

    register(First)
    register(First)  # registering the same class again is fine
    error = raises(PolicyLoadError, register, Second)
    assert "duplicate" in str(error)


def test_load_builtin_policies_sorted():
    """load_policies imports the built-in modules and returns instances sorted by id"""
    ids = [p.id for p in load_policies()]
    assert "AWS-SG-OPEN-INGRESS" in ids and "GCP-FIREWALL-OPEN-INGRESS" in ids and "CG-DESTROY-STATEFUL" in ids
    builtin = [i for i in ids if not i.startswith("TEST-")]
    assert builtin == sorted(builtin)
    assert all(isinstance(p, Policy) for p in load_policies())


def test_disable_override_and_settings():
    """config can disable a policy, override its severity and pass settings"""
    policies = load_policies(PolicyConfig(disabled=frozenset({"AWS-RDS-PUBLIC"}),
                                          severity_overrides={"GCP-GCS-UNIFORM-ACCESS": Severity.HIGH},
                                          settings={"CG-REQUIRED-TAGS": {"required": ["owner"]}}))
    by_id = {p.id: p for p in policies}
    assert "AWS-RDS-PUBLIC" not in by_id
    assert by_id["GCP-GCS-UNIFORM-ACCESS"].level is Severity.HIGH
    assert by_id["CG-REQUIRED-TAGS"].settings["required"] == ["owner"]


def test_unknown_ids_rejected():
    """mentioning an unknown policy id in config is an error naming it"""
    error = raises(PolicyLoadError, load_policies, PolicyConfig(disabled=frozenset({"NOPE-42"})))
    assert "NOPE-42" in str(error)
    raises(PolicyLoadError, load_policies, PolicyConfig(severity_overrides={"NOPE-43": Severity.LOW}))
    raises(PolicyLoadError, load_policies, PolicyConfig(settings={"NOPE-44": {}}))

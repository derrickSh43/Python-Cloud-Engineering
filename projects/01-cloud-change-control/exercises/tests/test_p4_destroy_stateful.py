from changegate.models import Severity
from changegate.policies.common import DestroyStatefulResource
from support import make_change


def run(policy, change):
    return list(policy.check(change)) if policy.applies_to(change) else []


def test_stateful_types():
    """stateful_types combines providers, extra_types and ignore_types"""
    types = DestroyStatefulResource().stateful_types()
    assert isinstance(types, frozenset)
    assert "aws_db_instance" in types and "google_storage_bucket" in types
    custom = DestroyStatefulResource({"extra_types": ["aws_instance"], "ignore_types": ["aws_s3_bucket"]})
    assert "aws_instance" in custom.stateful_types() and "aws_s3_bucket" not in custom.stateful_types()


def test_delete_database():
    """deleting a database gives a HIGH finding saying it will be deleted"""
    found = run(DestroyStatefulResource(), make_change("aws_db_instance", action="delete", before={}))
    assert len(found) == 1
    assert found[0].severity is Severity.HIGH
    assert found[0].message == "aws_db_instance holds data and will be deleted"
    assert "backup" in found[0].remediation.lower()


def test_replace_database():
    """replacing a database says 'destroyed and re-created (replaced)'"""
    found = run(DestroyStatefulResource(), make_change("google_sql_database_instance", {}, action="replace", before={}))
    assert [f.message for f in found] == [
        "google_sql_database_instance holds data and will be destroyed and re-created (replaced)"]


def test_ignores_stateless_and_non_destructive():
    """stateless deletes and updates of stateful resources are fine"""
    assert run(DestroyStatefulResource(), make_change("aws_instance", action="delete", before={})) == []
    assert run(DestroyStatefulResource(), make_change("aws_db_instance", {}, action="update", before={})) == []

import pytest

from changegate.config import PolicyConfig
from changegate.models import Severity
from changegate.policies import load_policies, run_policies


def findings(policies, change, policy_id):
    return [f for f in run_policies(policies, [change]) if f.policy_id == policy_id]


@pytest.mark.parametrize("resource_type, action, count", [
    ("aws_db_instance", "delete", 1), ("aws_db_instance", "replace", 1), ("aws_db_instance", "update", 0),
    ("google_sql_database_instance", "delete", 1), ("google_storage_bucket", "replace", 1),
    ("aws_instance", "delete", 0), ("google_compute_instance", "delete", 0),
])
def test_destroy_stateful(make_change, resource_type, action, count):
    attrs = {"name": "x"}
    change = make_change(resource_type, None if action == "delete" else attrs, action=action, before=attrs)
    got = findings(load_policies(), change, "CG-DESTROY-STATEFUL")
    assert len(got) == count
    if count:
        assert got[0].severity is Severity.HIGH


def test_destroy_stateful_settings(make_change):
    policies = load_policies(PolicyConfig(settings={"CG-DESTROY-STATEFUL": {
        "extra_types": ["aws_instance"], "ignore_types": ["aws_s3_bucket"]}}))
    assert findings(policies, make_change("aws_instance", action="delete", before={}), "CG-DESTROY-STATEFUL")
    assert not findings(policies, make_change("aws_s3_bucket", action="delete", before={}), "CG-DESTROY-STATEFUL")


@pytest.fixture
def tag_policies():
    return load_policies(PolicyConfig(settings={"CG-REQUIRED-TAGS": {"required": ["owner", "environment"]}}))


def test_required_tags_off_by_default(make_change):
    assert not findings(load_policies(), make_change("aws_s3_bucket", {"tags": {}}), "CG-REQUIRED-TAGS")


def test_required_tags_aws(tag_policies, make_change):
    got = findings(tag_policies, make_change("aws_s3_bucket", {"tags": {"owner": "x"}, "tags_all": {"owner": "x"}}),
                   "CG-REQUIRED-TAGS")
    assert len(got) == 1 and "environment" in got[0].message and "owner" not in got[0].message
    # provider default_tags show up in tags_all, which wins
    ok = make_change("aws_s3_bucket", {"tags": {}, "tags_all": {"owner": "x", "environment": "dev"}})
    assert not findings(tag_policies, ok, "CG-REQUIRED-TAGS")


def test_required_labels_gcp(tag_policies, make_change):
    got = findings(tag_policies, make_change("google_storage_bucket", {"labels": None}), "CG-REQUIRED-TAGS")
    assert len(got) == 1 and "labels" in got[0].message


def test_required_tags_skips_untaggable_and_unknown(tag_policies, make_change):
    assert not findings(tag_policies, make_change("aws_s3_bucket_acl", {"acl": "private"}), "CG-REQUIRED-TAGS")
    unknown = make_change("aws_s3_bucket", {"tags_all": None}, unknown={"tags_all": True})
    assert not findings(tag_policies, unknown, "CG-REQUIRED-TAGS")

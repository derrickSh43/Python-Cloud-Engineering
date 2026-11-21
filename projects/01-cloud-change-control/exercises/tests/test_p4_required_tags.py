from changegate.policies.common import RequiredTags
from support import make_change, messages

REQUIRED = {"required": ["owner", "environment"]}


def run(policy, change):
    return list(policy.check(change)) if policy.applies_to(change) else []


def test_inactive_by_default():
    """with no required keys configured nothing is reported"""
    assert run(RequiredTags(), make_change("aws_s3_bucket", {"tags": {}})) == []


def test_aws_missing_tag():
    """missing AWS tags are listed in configured order"""
    change = make_change("aws_s3_bucket", {"tags": {"owner": "x"}, "tags_all": {"owner": "x"}})
    assert messages(run(RequiredTags(REQUIRED), change)) == ["missing required tags_all: environment"]


def test_tags_all_wins_over_tags():
    """tags_all (which includes provider default tags) is checked first"""
    change = make_change("aws_s3_bucket", {"tags": {}, "tags_all": {"owner": "x", "environment": "dev"}})
    assert run(RequiredTags(REQUIRED), change) == []


def test_gcp_labels_and_null():
    """GCP uses labels; a null value counts as no labels"""
    assert messages(run(RequiredTags(REQUIRED), make_change("google_storage_bucket", {"labels": None}))) == [
        "missing required labels: owner, environment"]


def test_untaggable_and_unknown():
    """resources without tags, unknown tag values and unknown providers are skipped"""
    assert run(RequiredTags(REQUIRED), make_change("aws_s3_bucket_acl", {"acl": "private"})) == []
    assert run(RequiredTags(REQUIRED), make_change("aws_s3_bucket", {"tags_all": None, "tags": {}},
                                                   unknown={"tags_all": True})) == []
    from changegate.plan_parser import parse_change
    other = parse_change({"address": "azurerm_rg.x", "type": "azurerm_rg", "provider_name": "hashicorp/azurerm",
                          "change": {"actions": ["create"], "after": {"tags": {}}}})
    assert run(RequiredTags(REQUIRED), other) == []

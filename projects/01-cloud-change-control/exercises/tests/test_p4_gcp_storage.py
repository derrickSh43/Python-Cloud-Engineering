import json

from changegate.policies import gcp
from changegate.policies.gcp import GcsPublicIam, GcsUniformAccess
from support import make_change, messages


def run(policy, change):
    return list(policy.check(change)) if policy.applies_to(change) else []


POLICY_DATA = json.dumps({"bindings": [{"role": "roles/storage.admin", "members": ["group:ops@example.com"]},
                                       {"role": "roles/storage.objectViewer", "members": ["allUsers"]}]})


def test_members_and_roles():
    """_members and _roles read member, members and policy_data bindings"""
    change = make_change("google_storage_bucket_iam_policy", {"policy_data": POLICY_DATA})
    assert gcp._members(change) == ["group:ops@example.com", "allUsers"]
    assert gcp._roles(change) == ["roles/storage.admin", "roles/storage.objectViewer"]
    binding = make_change("google_storage_bucket_iam_binding", {"role": "roles/x", "members": ["user:a@example.com"]})
    assert gcp._members(binding) == ["user:a@example.com"] and gcp._roles(binding) == ["roles/x"]


def test_unknown_policy_data_ignored():
    """unknown policy_data contributes nothing"""
    change = make_change("google_storage_bucket_iam_policy", {"policy_data": "x"}, unknown={"policy_data": True})
    assert gcp._members(change) == []


def test_public_bucket_iam():
    """allUsers / allAuthenticatedUsers grants are reported, sorted"""
    member = make_change("google_storage_bucket_iam_member", {"member": "allUsers", "role": "roles/storage.objectViewer"})
    assert messages(run(GcsPublicIam(), member)) == ["grants access to allUsers"]
    binding = make_change("google_storage_bucket_iam_binding", {"members": ["allUsers", "allAuthenticatedUsers"]})
    assert messages(run(GcsPublicIam(), binding)) == ["grants access to allAuthenticatedUsers, allUsers"]
    acl = make_change("google_storage_bucket_access_control", {"entity": "allUsers", "role": "READER"})
    assert len(run(GcsPublicIam(), acl)) == 1
    private = make_change("google_storage_bucket_iam_member", {"member": "user:a@example.com"})
    assert run(GcsPublicIam(), private) == []


def test_bad_policy_data():
    """invalid policy_data JSON is reported"""
    change = make_change("google_storage_bucket_iam_policy", {"policy_data": "{oops"})
    found = run(GcsPublicIam(), change)
    assert len(found) == 1 and "not valid JSON" in found[0].message


def test_uniform_access():
    """uniform access off is reported, noting whether public access prevention is enforced"""
    assert messages(run(GcsUniformAccess(), make_change("google_storage_bucket", {"uniform_bucket_level_access": False}))) == [
        "uniform_bucket_level_access = false and public access prevention is not enforced"]
    enforced = make_change("google_storage_bucket", {"uniform_bucket_level_access": False,
                                                     "public_access_prevention": "enforced"})
    assert messages(run(GcsUniformAccess(), enforced)) == ["uniform_bucket_level_access = false"]
    assert run(GcsUniformAccess(), make_change("google_storage_bucket", {"uniform_bucket_level_access": True})) == []

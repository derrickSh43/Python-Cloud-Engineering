import json

from changegate.models import Severity
from changegate.policies.gcp import IamPrimitiveOrPublicRole
from support import make_change


def run(resource_type, attrs, settings=None):
    policy = IamPrimitiveOrPublicRole(settings)
    change = make_change(resource_type, attrs)
    return [(f.severity, f.message) for f in policy.check(change)] if policy.applies_to(change) else []


def test_basic_role():
    """roles/owner and roles/editor are HIGH"""
    assert run("google_project_iam_member", {"role": "roles/owner", "member": "user:a@example.com"}) == [
        (Severity.HIGH, "grants basic role(s) roles/owner")]
    assert run("google_folder_iam_binding", {"role": "roles/editor", "members": ["group:g@example.com"]}) == [
        (Severity.HIGH, "grants basic role(s) roles/editor")]


def test_public_member_is_critical():
    """granting anything to allUsers is CRITICAL"""
    assert run("google_project_iam_member", {"role": "roles/viewer", "member": "allUsers"}) == [
        (Severity.CRITICAL, "grants a role to allUsers")]


def test_both_can_fire():
    """a policy granting owner to allAuthenticatedUsers triggers both findings"""
    data = json.dumps({"bindings": [{"role": "roles/owner", "members": ["allAuthenticatedUsers"]}]})
    found = run("google_project_iam_policy", {"policy_data": data})
    assert sorted(found) == sorted([(Severity.CRITICAL, "grants a role to allAuthenticatedUsers"),
                                    (Severity.HIGH, "grants basic role(s) roles/owner")])


def test_safe_and_configurable():
    """predefined roles are fine; primitive_roles is configurable"""
    assert run("google_project_iam_member", {"role": "roles/viewer", "member": "user:a@example.com"}) == []
    assert run("google_project_iam_member", {"role": "roles/viewer", "member": "user:a@example.com"},
               {"primitive_roles": ["roles/viewer"]}) == [(Severity.HIGH, "grants basic role(s) roles/viewer")]


def test_bad_json():
    """invalid policy_data JSON is reported"""
    found = run("google_organization_iam_policy", {"policy_data": "{"})
    assert len(found) == 1 and "not valid JSON" in found[0][1]

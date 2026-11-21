import json

import pytest

from changegate.models import Severity
from changegate.policies import load_policies, run_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def findings(policies, change, policy_id):
    return [f for f in run_policies(policies, [change]) if f.policy_id == policy_id]


@pytest.mark.parametrize("resource_type, attrs, count", [
    ("google_storage_bucket_iam_member", {"member": "allUsers", "role": "roles/storage.objectViewer"}, 1),
    ("google_storage_bucket_iam_member", {"member": "allAuthenticatedUsers"}, 1),
    ("google_storage_bucket_iam_member", {"member": "user:someone@example.com"}, 0),
    ("google_storage_bucket_iam_binding", {"members": ["group:team@example.com", "allUsers"]}, 1),
    ("google_storage_bucket_iam_policy",
     {"policy_data": json.dumps({"bindings": [{"role": "roles/storage.admin", "members": ["allUsers"]}]})}, 1),
    ("google_storage_bucket_access_control", {"entity": "allUsers", "role": "READER"}, 1),
])
def test_gcs_public_iam(policies, make_change, resource_type, attrs, count):
    assert len(findings(policies, make_change(resource_type, attrs), "GCP-GCS-PUBLIC-IAM")) == count


def test_gcs_uniform_access(policies, make_change):
    off = findings(policies, make_change("google_storage_bucket", {"uniform_bucket_level_access": False}),
                   "GCP-GCS-UNIFORM-ACCESS")
    assert len(off) == 1 and off[0].severity is Severity.MEDIUM and "not enforced" in off[0].message
    enforced = findings(policies, make_change("google_storage_bucket", {
        "uniform_bucket_level_access": False, "public_access_prevention": "enforced"}), "GCP-GCS-UNIFORM-ACCESS")
    assert len(enforced) == 1 and "not enforced" not in enforced[0].message
    assert not findings(policies, make_change("google_storage_bucket", {"uniform_bucket_level_access": True}),
                        "GCP-GCS-UNIFORM-ACCESS")


def fw(allow, source=("0.0.0.0/0",), direction="INGRESS", disabled=False):
    return {"allow": allow, "source_ranges": list(source), "direction": direction, "disabled": disabled}


@pytest.mark.parametrize("attrs, expected", [
    (fw([{"protocol": "tcp", "ports": ["22"]}]), [Severity.HIGH]),
    (fw([{"protocol": "tcp", "ports": ["443"]}]), []),
    (fw([{"protocol": "tcp", "ports": ["22"]}], source=["10.0.0.0/8"]), []),
    (fw([{"protocol": "all"}]), [Severity.CRITICAL]),
    (fw([{"protocol": "tcp", "ports": []}]), [Severity.CRITICAL]),
    (fw([{"protocol": "icmp"}]), []),
    (fw([{"protocol": "tcp", "ports": ["5000-6000"]}]), [Severity.HIGH]),   # includes 5432 and 5900
    (fw([{"protocol": "tcp", "ports": ["22"]}], direction="EGRESS"), []),
    (fw([{"protocol": "tcp", "ports": ["22"]}], disabled=True), []),
    (fw([{"protocol": "tcp", "ports": ["22", "3389"]}]), [Severity.HIGH, Severity.HIGH]),
])
def test_firewall(policies, make_change, attrs, expected):
    got = findings(policies, make_change("google_compute_firewall", attrs), "GCP-FIREWALL-OPEN-INGRESS")
    assert [f.severity for f in got] == expected


@pytest.mark.parametrize("resource_type, attrs, expected", [
    ("google_project_iam_member", {"role": "roles/owner", "member": "user:a@example.com"}, [Severity.HIGH]),
    ("google_project_iam_member", {"role": "roles/viewer", "member": "user:a@example.com"}, []),
    ("google_project_iam_member", {"role": "roles/viewer", "member": "allUsers"}, [Severity.CRITICAL]),
    ("google_folder_iam_binding", {"role": "roles/editor", "members": ["group:g@example.com"]}, [Severity.HIGH]),
    ("google_project_iam_policy", {"policy_data": json.dumps({"bindings": [
        {"role": "roles/editor", "members": ["user:a@example.com"]}]})}, [Severity.HIGH]),
])
def test_iam_primitive_roles(policies, make_change, resource_type, attrs, expected):
    got = findings(policies, make_change(resource_type, attrs), "GCP-IAM-PRIMITIVE-ROLE")
    assert sorted(f.severity for f in got) == sorted(expected)


def sql(networks, ipv4=True):
    return {"settings": [{"ip_configuration": [{"ipv4_enabled": ipv4, "authorized_networks": networks}]}]}


def test_sql_public_network(policies, make_change):
    assert findings(policies, make_change("google_sql_database_instance", sql([{"name": "all", "value": "0.0.0.0/0"}])),
                    "GCP-SQL-PUBLIC-NETWORK")
    assert not findings(policies, make_change("google_sql_database_instance",
                                              sql([{"name": "office", "value": "203.0.113.0/24"}])), "GCP-SQL-PUBLIC-NETWORK")
    assert not findings(policies, make_change("google_sql_database_instance",
                                              sql([{"value": "0.0.0.0/0"}], ipv4=False)), "GCP-SQL-PUBLIC-NETWORK")
    assert not findings(policies, make_change("google_sql_database_instance", {"settings": []}), "GCP-SQL-PUBLIC-NETWORK")

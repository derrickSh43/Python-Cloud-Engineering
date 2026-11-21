import json

import pytest

from changegate.models import Severity
from changegate.policies import load_policies, run_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def findings(policies, change, policy_id):
    return [f for f in run_policies(policies, [change]) if f.policy_id == policy_id]


def doc(*statements):
    return json.dumps({"Version": "2012-10-17", "Statement": list(statements)})


@pytest.mark.parametrize("acl, expected", [
    ("private", None), ("public-read", Severity.HIGH), ("authenticated-read", Severity.HIGH),
    ("public-read-write", Severity.CRITICAL),
])
def test_s3_acl(policies, make_change, acl, expected):
    got = findings(policies, make_change("aws_s3_bucket_acl", {"acl": acl}), "AWS-S3-PUBLIC-ACL")
    assert [f.severity for f in got] == ([expected] if expected else [])


def test_s3_public_access_block(policies, make_change):
    all_on = {f: True for f in ("block_public_acls", "block_public_policy", "ignore_public_acls",
                                "restrict_public_buckets")}
    assert not findings(policies, make_change("aws_s3_bucket_public_access_block", all_on), "AWS-S3-PUBLIC-ACCESS-BLOCK")
    got = findings(policies, make_change("aws_s3_bucket_public_access_block", {**all_on, "block_public_policy": False}),
                   "AWS-S3-PUBLIC-ACCESS-BLOCK")
    assert len(got) == 1 and "block_public_policy" in got[0].message


def test_s3_bucket_policy(policies, make_change):
    public = doc({"Sid": "Public", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": "*"})
    scoped = doc({"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"}, "Action": "s3:*"})
    conditioned = doc({"Effect": "Allow", "Principal": {"AWS": ["*"]}, "Action": "s3:GetObject",
                       "Condition": {"StringEquals": {"aws:SourceVpce": "vpce-0example"}}})
    assert len(findings(policies, make_change("aws_s3_bucket_policy", {"policy": public}), "AWS-S3-PUBLIC-POLICY")) == 1
    assert not findings(policies, make_change("aws_s3_bucket_policy", {"policy": scoped}), "AWS-S3-PUBLIC-POLICY")
    assert not findings(policies, make_change("aws_s3_bucket_policy", {"policy": conditioned}), "AWS-S3-PUBLIC-POLICY")
    unknown = make_change("aws_s3_bucket_policy", {"policy": None}, unknown={"policy": True})
    assert not findings(policies, unknown, "AWS-S3-PUBLIC-POLICY")
    broken = findings(policies, make_change("aws_s3_bucket_policy", {"policy": "{not json"}), "AWS-S3-PUBLIC-POLICY")
    assert broken and "not valid JSON" in broken[0].message


def rule(port_from, port_to, cidrs, protocol="tcp", v6=()):
    return {"from_port": port_from, "to_port": port_to, "protocol": protocol, "cidr_blocks": cidrs,
            "ipv6_cidr_blocks": list(v6)}


@pytest.mark.parametrize("ingress, expected", [
    ([rule(22, 22, ["0.0.0.0/0"])], [Severity.HIGH]),
    ([rule(22, 22, ["10.0.0.0/8"])], []),
    ([rule(443, 443, ["0.0.0.0/0"])], []),
    ([rule(0, 0, ["0.0.0.0/0"], protocol="-1")], [Severity.CRITICAL]),
    ([rule(0, 65535, ["0.0.0.0/0"])], [Severity.CRITICAL]),
    ([rule(3000, 4000, ["0.0.0.0/0"])], [Severity.HIGH]),      # range includes 3306 and 3389
    ([rule(3389, 3389, [], v6=["::/0"])], [Severity.HIGH]),
    ([rule(22, 22, ["10.0.0.0/8"]), rule(5432, 5432, ["0.0.0.0/0"])], [Severity.HIGH]),
])
def test_security_group(policies, make_change, ingress, expected):
    got = findings(policies, make_change("aws_security_group", {"ingress": ingress}), "AWS-SG-OPEN-INGRESS")
    assert [f.severity for f in got] == expected


def test_security_group_rule_variants(policies, make_change):
    sgr = make_change("aws_security_group_rule", {"type": "ingress", **rule(22, 22, ["0.0.0.0/0"])})
    egress = make_change("aws_security_group_rule", {"type": "egress", **rule(0, 0, ["0.0.0.0/0"], "-1")})
    vpc = make_change("aws_vpc_security_group_ingress_rule",
                      {"from_port": 3389, "to_port": 3389, "ip_protocol": "tcp", "cidr_ipv4": "0.0.0.0/0"})
    assert len(findings(policies, sgr, "AWS-SG-OPEN-INGRESS")) == 1
    assert not findings(policies, egress, "AWS-SG-OPEN-INGRESS")
    assert len(findings(policies, vpc, "AWS-SG-OPEN-INGRESS")) == 1


def test_sensitive_ports_are_configurable(make_change):
    from changegate.config import PolicyConfig
    custom = load_policies(PolicyConfig(settings={"AWS-SG-OPEN-INGRESS": {"sensitive_ports": [8080]}}))
    change = make_change("aws_security_group", {"ingress": [rule(8080, 8080, ["0.0.0.0/0"])]})
    assert findings(custom, change, "AWS-SG-OPEN-INGRESS")
    assert not findings(custom, make_change("aws_security_group", {"ingress": [rule(22, 22, ["0.0.0.0/0"])]}),
                        "AWS-SG-OPEN-INGRESS")


@pytest.mark.parametrize("resource_type, attrs, count", [
    ("aws_ebs_volume", {"encrypted": False}, 1),
    ("aws_ebs_volume", {"encrypted": None}, 1),
    ("aws_ebs_volume", {"encrypted": True}, 0),
    ("aws_db_instance", {"storage_encrypted": False}, 1),
    ("aws_rds_cluster", {"storage_encrypted": True}, 0),
    ("aws_instance", {"root_block_device": [{"encrypted": False}]}, 1),
    ("aws_instance", {"root_block_device": [{"encrypted": True}], "ebs_block_device": [{"encrypted": False}]}, 1),
    ("aws_instance", {"root_block_device": []}, 0),
])
def test_unencrypted_storage(policies, make_change, resource_type, attrs, count):
    assert len(findings(policies, make_change(resource_type, attrs), "AWS-STORAGE-UNENCRYPTED")) == count


def test_unencrypted_unknown_is_skipped(policies, make_change):
    change = make_change("aws_ebs_volume", {"encrypted": None}, unknown={"encrypted": True})
    assert not findings(policies, change, "AWS-STORAGE-UNENCRYPTED")


@pytest.mark.parametrize("statement, expected", [
    ({"Effect": "Allow", "Action": "*", "Resource": "*"}, [Severity.CRITICAL]),
    ({"Effect": "Allow", "Action": ["s3:*"], "Resource": "*"}, [Severity.HIGH]),
    ({"Effect": "Allow", "Action": ["s3:*"], "Resource": "arn:aws:s3:::example-bucket/*"}, []),
    ({"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "*"}, []),
    ({"Effect": "Deny", "Action": "*", "Resource": "*"}, []),
    ({"Effect": "Allow", "NotAction": "iam:*", "Resource": "*"}, [Severity.HIGH]),
])
def test_iam_wildcards(policies, make_change, statement, expected):
    change = make_change("aws_iam_role_policy", {"policy": doc(statement)})
    assert [f.severity for f in findings(policies, change, "AWS-IAM-WILDCARD")] == expected


def test_rds_public(policies, make_change):
    assert findings(policies, make_change("aws_db_instance", {"publicly_accessible": True, "storage_encrypted": True}),
                    "AWS-RDS-PUBLIC")
    assert not findings(policies, make_change("aws_db_instance", {"publicly_accessible": False}), "AWS-RDS-PUBLIC")


def test_deleting_a_risky_resource_is_not_a_config_finding(policies, make_change):
    change = make_change("aws_s3_bucket_acl", action="delete", before={"acl": "public-read"})
    assert not findings(policies, change, "AWS-S3-PUBLIC-ACL")

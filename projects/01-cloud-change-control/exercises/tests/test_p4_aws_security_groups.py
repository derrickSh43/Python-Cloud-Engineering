from changegate.models import Severity
from changegate.policies.aws import SecurityGroupOpenIngress
from support import make_change, messages


def run(change):
    policy = SecurityGroupOpenIngress()
    return list(policy.check(change)) if policy.applies_to(change) else []


def rule(low, high, cidrs, protocol="tcp", v6=()):
    return {"from_port": low, "to_port": high, "protocol": protocol, "cidr_blocks": cidrs, "ipv6_cidr_blocks": list(v6)}


def test_ssh_open_to_world():
    """SSH from 0.0.0.0/0 in an inline ingress block is HIGH and labelled by rule number"""
    change = make_change("aws_security_group", {"ingress": [rule(443, 443, ["0.0.0.0/0"]), rule(22, 22, ["0.0.0.0/0"])]})
    found = run(change)
    assert [(f.severity, f.message) for f in found] == [
        (Severity.HIGH, "ingress rule 2 exposes sensitive port(s) 22 to the internet")]


def test_private_sources_and_ipv6():
    """private sources are fine; ::/0 counts as the internet"""
    assert run(make_change("aws_security_group", {"ingress": [rule(22, 22, ["10.0.0.0/8"])]})) == []
    assert len(run(make_change("aws_security_group", {"ingress": [rule(3389, 3389, [], v6=["::/0"])]}))) == 1


def test_all_traffic():
    """protocol -1 is all traffic (CRITICAL), even with ports 0-0"""
    found = run(make_change("aws_security_group", {"ingress": [rule(0, 0, ["0.0.0.0/0"], protocol="-1")]}))
    assert [f.severity for f in found] == [Severity.CRITICAL]


def test_security_group_rule_resource():
    """aws_security_group_rule is checked only when type is ingress"""
    ingress = make_change("aws_security_group_rule", {"type": "ingress", **rule(5432, 5432, ["0.0.0.0/0"])})
    egress = make_change("aws_security_group_rule", {"type": "egress", **rule(0, 0, ["0.0.0.0/0"], "-1")})
    assert messages(run(ingress)) == ["ingress rule exposes sensitive port(s) 5432 to the internet"]
    assert run(egress) == []


def test_vpc_ingress_rule_resource():
    """aws_vpc_security_group_ingress_rule uses cidr_ipv4 and ip_protocol"""
    change = make_change("aws_vpc_security_group_ingress_rule",
                         {"from_port": None, "to_port": None, "ip_protocol": "-1", "cidr_ipv4": "0.0.0.0/0"})
    assert [f.severity for f in run(change)] == [Severity.CRITICAL]
    safe = make_change("aws_vpc_security_group_ingress_rule",
                       {"from_port": 22, "to_port": 22, "ip_protocol": "tcp", "cidr_ipv4": "10.1.0.0/16"})
    assert run(safe) == []

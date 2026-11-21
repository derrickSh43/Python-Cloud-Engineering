from changegate.models import Severity
from changegate.policies.gcp import FirewallOpenIngress, SqlPublicNetwork
from support import make_change, messages


def firewall(allow, source=("0.0.0.0/0",), **extra):
    policy = FirewallOpenIngress()
    change = make_change("google_compute_firewall", {"allow": allow, "source_ranges": list(source), **extra})
    return list(policy.check(change)) if policy.applies_to(change) else []


def test_ssh_open():
    """tcp 22 from the internet is HIGH, labelled by allow rule and protocol"""
    assert [(f.severity, f.message) for f in firewall([{"protocol": "tcp", "ports": ["22"]}])] == [
        (Severity.HIGH, "allow rule 1 (tcp) exposes sensitive port(s) 22 to the internet")]


def test_each_port_entry_checked():
    """every port entry is judged separately, including ranges"""
    found = firewall([{"protocol": "udp", "ports": ["53"]}, {"protocol": "tcp", "ports": ["443", "5000-6000"]}])
    assert messages(found) == ["allow rule 2 (tcp) exposes sensitive port(s) 5432, 5900 to the internet"]


def test_all_traffic():
    """protocol all, or tcp with no ports, is CRITICAL"""
    assert [f.severity for f in firewall([{"protocol": "all"}])] == [Severity.CRITICAL]
    assert [f.severity for f in firewall([{"protocol": "tcp", "ports": []}])] == [Severity.CRITICAL]
    assert firewall([{"protocol": "icmp"}]) == []


def test_skipped_rules():
    """private sources, egress, lower-case egress and disabled rules are skipped"""
    ssh = [{"protocol": "tcp", "ports": ["22"]}]
    assert firewall(ssh, source=["10.0.0.0/8"]) == []
    assert firewall(ssh, direction="EGRESS") == []
    assert firewall(ssh, direction="egress") == []
    assert firewall(ssh, disabled=True) == []
    assert len(firewall(ssh, direction=None)) == 1, "a missing direction means INGRESS"


def sql(networks, ipv4=True):
    return make_change("google_sql_database_instance",
                       {"settings": [{"ip_configuration": [{"ipv4_enabled": ipv4, "authorized_networks": networks}]}]})


def test_sql_public_network():
    """an authorized network of 0.0.0.0/0 is reported by name"""
    policy = SqlPublicNetwork()
    assert messages(policy.check(sql([{"name": "anywhere", "value": "0.0.0.0/0"}]))) == [
        "authorized network 'anywhere' is 0.0.0.0/0"]
    assert messages(policy.check(sql([{"value": "0.0.0.0/0"}]))) == ["authorized network '(unnamed)' is 0.0.0.0/0"]


def test_sql_safe():
    """specific ranges, disabled IPv4 and missing settings are fine"""
    policy = SqlPublicNetwork()
    assert list(policy.check(sql([{"name": "office", "value": "203.0.113.0/24"}]))) == []
    assert list(policy.check(sql([{"value": "0.0.0.0/0"}], ipv4=False))) == []
    assert list(policy.check(make_change("google_sql_database_instance", {"settings": []}))) == []

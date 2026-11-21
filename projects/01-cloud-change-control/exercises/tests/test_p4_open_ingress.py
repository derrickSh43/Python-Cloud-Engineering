from changegate.models import Severity
from changegate.policies.network import OpenIngressPolicy
from support import make_change


class Ingress(OpenIngressPolicy):
    id = "TEST-INGRESS"
    title = "t"

    def check(self, change):
        return []


CHANGE = None


def judge(all_traffic, port_range, settings=None):
    change = make_change("aws_security_group", {}, name="sg")
    return list(Ingress(settings).judge(change, "rule 1", all_traffic, port_range))


def test_all_traffic_is_critical():
    """all traffic is one CRITICAL finding"""
    found = judge(True, (22, 22))
    assert len(found) == 1 and found[0].severity is Severity.CRITICAL
    assert found[0].message == "rule 1 allows ALL ports from the internet"


def test_full_port_range_is_critical():
    """0-65535 counts as all ports"""
    assert [f.severity for f in judge(False, (0, 65535))] == [Severity.CRITICAL]


def test_sensitive_ports():
    """sensitive ports in the range are listed at HIGH"""
    found = judge(False, (3000, 4000))
    assert len(found) == 1 and found[0].severity is Severity.HIGH
    assert found[0].message == "rule 1 exposes sensitive port(s) 3306, 3389 to the internet"


def test_harmless_ports():
    """non-sensitive ports produce nothing"""
    assert judge(False, (443, 443)) == []


def test_custom_sensitive_ports():
    """sensitive_ports comes from settings"""
    assert len(judge(False, (8080, 8080), {"sensitive_ports": [8080]})) == 1
    assert judge(False, (22, 22), {"sensitive_ports": [8080]}) == []

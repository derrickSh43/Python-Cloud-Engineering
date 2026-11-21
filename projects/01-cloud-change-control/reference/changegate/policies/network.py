"""Shared base for "open to the internet on a sensitive port" policies (used by AWS and GCP).
Not registered itself - only its subclasses are."""

from __future__ import annotations

from typing import Iterable

from ..models import Finding, ResourceChange, Severity
from .base import Policy
from .helpers import covers_all_ports, range_includes_any

DEFAULT_SENSITIVE_PORTS = [22, 23, 3389, 3306, 5432, 1433, 1521, 6379, 9200, 27017, 5900]


class OpenIngressPolicy(Policy):
    """Shared logic for 'open to the internet on a sensitive port' policies."""

    severity = Severity.HIGH
    default_settings = {"sensitive_ports": DEFAULT_SENSITIVE_PORTS}

    def judge(self, change: ResourceChange, label: str, all_traffic: bool,
              port_range: tuple[int, int]) -> Iterable[Finding]:
        if all_traffic or covers_all_ports(port_range):
            yield self.finding(change, "%s allows ALL ports from the internet" % label,
                               "Restrict the source CIDR to known networks and open only the ports you need.",
                               severity=Severity.CRITICAL)
            return
        hits = range_includes_any(port_range, list(self.settings["sensitive_ports"]))
        if hits:
            yield self.finding(change, "%s exposes sensitive port(s) %s to the internet" % (
                label, ", ".join(map(str, hits))),
                "Use a bastion/SSM Session Manager or VPN, or limit the source CIDR to trusted ranges.")

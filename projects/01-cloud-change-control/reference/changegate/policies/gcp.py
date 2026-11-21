"""Google Cloud security policies."""

from __future__ import annotations

import json
from typing import Iterable

from ..models import Finding, ResourceChange, Severity
from .base import Policy, register
from .helpers import any_world, as_list, first_block, load_json_document, parse_port_range
from .network import DEFAULT_SENSITIVE_PORTS, OpenIngressPolicy

PUBLIC_MEMBERS = frozenset({"allUsers", "allAuthenticatedUsers"})


def _members(change: ResourceChange) -> list[str]:
    """Members from *_iam_member (member), *_iam_binding (members) or *_iam_policy (policy_data)."""
    attrs = change.attributes
    members = [str(m) for m in as_list(attrs.get("member")) + as_list(attrs.get("members"))]
    if attrs.get("policy_data") and not change.is_unknown("policy_data"):
        document = load_json_document(attrs["policy_data"]) or {}
        for binding in as_list(document.get("bindings")):
            members += [str(m) for m in as_list(binding.get("members"))]
    return members


def _roles(change: ResourceChange) -> list[str]:
    attrs = change.attributes
    roles = [str(r) for r in as_list(attrs.get("role"))]
    if attrs.get("policy_data") and not change.is_unknown("policy_data"):
        document = load_json_document(attrs["policy_data"]) or {}
        roles += [str(b.get("role")) for b in as_list(document.get("bindings")) if isinstance(b, dict)]
    return roles


@register
class GcsPublicIam(Policy):
    id = "GCP-GCS-PUBLIC-IAM"
    title = "Cloud Storage bucket is readable by anyone"
    severity = Severity.HIGH
    resource_types = frozenset({"google_storage_bucket_iam_member", "google_storage_bucket_iam_binding",
                                "google_storage_bucket_iam_policy", "google_storage_bucket_access_control",
                                "google_storage_default_object_access_control"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        try:
            members = _members(change) + [str(e) for e in as_list(change.attributes.get("entity"))]
        except (ValueError, json.JSONDecodeError) as e:
            yield self.finding(change, "policy_data is not valid JSON: %s" % e, "Fix the policy document.")
            return
        public = sorted(PUBLIC_MEMBERS & set(members))
        if public:
            yield self.finding(change, "grants access to %s" % ", ".join(public),
                               "Grant access to specific identities, or use signed URLs for public downloads.")


@register
class GcsUniformAccess(Policy):
    id = "GCP-GCS-UNIFORM-ACCESS"
    title = "Bucket allows per-object ACLs (uniform access disabled)"
    severity = Severity.MEDIUM
    resource_types = frozenset({"google_storage_bucket"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        attrs = change.attributes
        if attrs.get("uniform_bucket_level_access") is False:
            prevention = attrs.get("public_access_prevention")
            note = "" if prevention == "enforced" else " and public access prevention is not enforced"
            yield self.finding(change, "uniform_bucket_level_access = false%s" % note,
                               "Set uniform_bucket_level_access = true and public_access_prevention = \"enforced\".")


@register
class FirewallOpenIngress(OpenIngressPolicy):
    id = "GCP-FIREWALL-OPEN-INGRESS"
    title = "Firewall rule open to the internet on a sensitive port"
    resource_types = frozenset({"google_compute_firewall"})
    default_settings = {"sensitive_ports": DEFAULT_SENSITIVE_PORTS}

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        attrs = change.attributes
        if attrs.get("disabled") is True or str(attrs.get("direction") or "INGRESS").upper() != "INGRESS":
            return
        if not any_world(attrs.get("source_ranges")):
            return
        for n, allow in enumerate(as_list(attrs.get("allow"))):
            protocol = str(allow.get("protocol", "")).lower()
            ports = as_list(allow.get("ports"))
            label = "allow rule %d (%s)" % (n + 1, protocol or "?")
            if protocol == "all" or (protocol in ("tcp", "udp", "sctp") and not ports):
                yield from self.judge(change, label, True, (0, 65535))
                continue
            for port in ports:
                yield from self.judge(change, label, False, parse_port_range(port))


@register
class IamPrimitiveOrPublicRole(Policy):
    id = "GCP-IAM-PRIMITIVE-ROLE"
    title = "Project/folder/org IAM grants a basic role or public access"
    severity = Severity.HIGH
    resource_types = frozenset({
        "google_project_iam_member", "google_project_iam_binding", "google_project_iam_policy",
        "google_folder_iam_member", "google_folder_iam_binding", "google_folder_iam_policy",
        "google_organization_iam_member", "google_organization_iam_binding", "google_organization_iam_policy",
    })
    default_settings = {"primitive_roles": ["roles/owner", "roles/editor"]}

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        try:
            members, roles = _members(change), _roles(change)
        except (ValueError, json.JSONDecodeError) as e:
            yield self.finding(change, "policy_data is not valid JSON: %s" % e, "Fix the policy document.")
            return
        public = sorted(PUBLIC_MEMBERS & set(members))
        if public:
            yield self.finding(change, "grants a role to %s" % ", ".join(public),
                               "Never grant resource-hierarchy roles to allUsers/allAuthenticatedUsers.",
                               severity=Severity.CRITICAL)
        basic = sorted(set(roles) & set(self.settings["primitive_roles"]))
        if basic:
            yield self.finding(change, "grants basic role(s) %s" % ", ".join(basic),
                               "Use predefined or custom roles with only the permissions needed.")


@register
class SqlPublicNetwork(Policy):
    id = "GCP-SQL-PUBLIC-NETWORK"
    title = "Cloud SQL accepts connections from the whole internet"
    severity = Severity.HIGH
    resource_types = frozenset({"google_sql_database_instance"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        ip_config = first_block(first_block(change.attributes, "settings"), "ip_configuration")
        if ip_config.get("ipv4_enabled") is False:
            return
        for network in as_list(ip_config.get("authorized_networks")):
            if isinstance(network, dict) and any_world(network.get("value")):
                yield self.finding(change, "authorized network %r is %s" % (
                    network.get("name", "(unnamed)"), network.get("value")),
                    "Use private IP with the Cloud SQL Auth Proxy, or authorise only specific ranges.")

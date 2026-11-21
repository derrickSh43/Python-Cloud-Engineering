"""AWS security policies."""

from __future__ import annotations

import json
from typing import Any, Iterable

from ..models import Finding, ResourceChange, Severity
from .base import Policy, register
from .helpers import any_world, as_list, first_block, load_json_document, principal_is_public, statements
from .network import OpenIngressPolicy

@register
class S3PublicAcl(Policy):
    id = "AWS-S3-PUBLIC-ACL"
    title = "S3 bucket ACL grants public access"
    severity = Severity.HIGH
    resource_types = frozenset({"aws_s3_bucket_acl"})
    PUBLIC = {"public-read": Severity.HIGH, "authenticated-read": Severity.HIGH,
              "public-read-write": Severity.CRITICAL}

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        acl = change.attributes.get("acl")
        if acl in self.PUBLIC:
            yield self.finding(change, "bucket ACL is %r" % acl,
                               "Use acl = \"private\" and share objects with presigned URLs or CloudFront.",
                               severity=self.PUBLIC[acl])


@register
class S3PublicAccessBlock(Policy):
    id = "AWS-S3-PUBLIC-ACCESS-BLOCK"
    title = "S3 public access block is not fully enabled"
    severity = Severity.HIGH
    resource_types = frozenset({"aws_s3_bucket_public_access_block", "aws_s3_account_public_access_block"})
    FLAGS = ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        attrs = change.attributes
        off = [flag for flag in self.FLAGS if attrs.get(flag) is not True and not change.is_unknown(flag)]
        if off:
            yield self.finding(change, "public access protections disabled: %s" % ", ".join(off),
                               "Set all four public access block settings to true.")


@register
class S3PublicBucketPolicy(Policy):
    id = "AWS-S3-PUBLIC-POLICY"
    title = "S3 bucket policy allows anyone"
    severity = Severity.HIGH
    resource_types = frozenset({"aws_s3_bucket_policy"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        if change.is_unknown("policy"):
            return
        try:
            document = load_json_document(change.attributes.get("policy"))
        except (ValueError, json.JSONDecodeError) as e:
            yield self.finding(change, "bucket policy is not valid JSON: %s" % e, "Fix the policy document.")
            return
        for statement in statements(document or {}):
            if statement.get("Effect") == "Allow" and principal_is_public(statement.get("Principal")) \
                    and not statement.get("Condition"):
                yield self.finding(change, "statement %r allows Principal \"*\" with no Condition" % (
                    statement.get("Sid", "(no Sid)"),),
                    "Restrict Principal to specific accounts/roles or add a Condition (e.g. aws:SourceVpce).")


@register
class SecurityGroupOpenIngress(OpenIngressPolicy):
    id = "AWS-SG-OPEN-INGRESS"
    title = "Security group open to the internet on a sensitive port"
    resource_types = frozenset({"aws_security_group", "aws_security_group_rule",
                                "aws_vpc_security_group_ingress_rule"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        attrs = change.attributes
        if change.type == "aws_security_group":
            for n, rule in enumerate(as_list(attrs.get("ingress"))):
                yield from self._rule(change, "ingress rule %d" % (n + 1), rule,
                                      rule.get("cidr_blocks"), rule.get("ipv6_cidr_blocks"), rule.get("protocol"))
        elif change.type == "aws_security_group_rule":
            if attrs.get("type") == "ingress":
                yield from self._rule(change, "ingress rule", attrs, attrs.get("cidr_blocks"),
                                      attrs.get("ipv6_cidr_blocks"), attrs.get("protocol"))
        else:
            yield from self._rule(change, "ingress rule", attrs, attrs.get("cidr_ipv4"),
                                  attrs.get("cidr_ipv6"), attrs.get("ip_protocol"))

    def _rule(self, change: ResourceChange, label: str, rule: dict[str, Any], v4: Any, v6: Any,
              protocol: Any) -> Iterable[Finding]:
        if not (any_world(v4) or any_world(v6)):
            return
        all_traffic = str(protocol) in ("-1", "all")
        low = rule.get("from_port") if rule.get("from_port") is not None else 0
        high = rule.get("to_port") if rule.get("to_port") is not None else 65535
        yield from self.judge(change, label, all_traffic, (int(low), int(high)))


@register
class UnencryptedStorage(Policy):
    id = "AWS-STORAGE-UNENCRYPTED"
    title = "Storage is not encrypted at rest"
    severity = Severity.HIGH
    FLAGS = {"aws_ebs_volume": "encrypted", "aws_db_instance": "storage_encrypted",
             "aws_rds_cluster": "storage_encrypted", "aws_efs_file_system": "encrypted"}
    resource_types = frozenset(set(FLAGS) | {"aws_instance"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        attrs = change.attributes
        if change.type == "aws_instance":
            root = first_block(attrs, "root_block_device")
            if root and root.get("encrypted") is False:
                yield self.finding(change, "root volume is not encrypted",
                                   "Set root_block_device.encrypted = true (or enable EBS encryption by default).")
            for n, device in enumerate(as_list(attrs.get("ebs_block_device"))):
                if isinstance(device, dict) and device.get("encrypted") is False:
                    yield self.finding(change, "EBS block device %d is not encrypted" % (n + 1),
                                       "Set encrypted = true on every ebs_block_device.")
            return
        flag = self.FLAGS[change.type]
        if change.is_unknown(flag):
            return
        if attrs.get(flag) is not True:
            yield self.finding(change, "%s is %r" % (flag, attrs.get(flag)),
                               "Set %s = true (optionally with a customer-managed KMS key)." % flag)


@register
class IamWildcard(Policy):
    id = "AWS-IAM-WILDCARD"
    title = "IAM policy grants wildcard permissions"
    severity = Severity.HIGH
    resource_types = frozenset({"aws_iam_policy", "aws_iam_role_policy", "aws_iam_user_policy",
                                "aws_iam_group_policy"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        if change.is_unknown("policy"):
            return
        try:
            document = load_json_document(change.attributes.get("policy"))
        except (ValueError, json.JSONDecodeError) as e:
            yield self.finding(change, "policy is not valid JSON: %s" % e, "Fix the policy document.")
            return
        for statement in statements(document or {}):
            if statement.get("Effect") != "Allow":
                continue
            sid = statement.get("Sid", "(no Sid)")
            actions = [str(a) for a in as_list(statement.get("Action"))]
            resources = [str(r) for r in as_list(statement.get("Resource"))]
            if "NotAction" in statement:
                yield self.finding(change, "statement %r uses Allow + NotAction (allows everything else)" % sid,
                                   "List the allowed actions explicitly instead of NotAction.")
            if "*" in actions:
                yield self.finding(change, "statement %r allows every action (\"*\")" % sid,
                                   "Grant only the specific actions needed (least privilege).",
                                   severity=Severity.CRITICAL)
            elif "*" in resources:
                broad = [a for a in actions if a.endswith(":*")]
                if broad:
                    yield self.finding(change, "statement %r allows %s on every resource" % (sid, ", ".join(broad)),
                                       "Name specific actions and scope Resource to specific ARNs.")


@register
class RdsPubliclyAccessible(Policy):
    id = "AWS-RDS-PUBLIC"
    title = "Database is publicly accessible"
    severity = Severity.HIGH
    resource_types = frozenset({"aws_db_instance", "aws_rds_cluster_instance"})

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        if change.attributes.get("publicly_accessible") is True:
            yield self.finding(change, "publicly_accessible = true",
                               "Keep databases in private subnets and connect through the VPC.")

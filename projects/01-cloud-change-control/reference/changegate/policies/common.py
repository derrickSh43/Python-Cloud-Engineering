"""Policies that apply to every cloud. They ask the providers module for cloud-specific details."""

from __future__ import annotations

from typing import Iterable

from .. import providers
from ..models import Action, Finding, ResourceChange, Severity
from .base import Policy, register


@register
class DestroyStatefulResource(Policy):
    id = "CG-DESTROY-STATEFUL"
    title = "Deleting or replacing a resource that holds data"
    severity = Severity.HIGH
    actions = frozenset({Action.DELETE, Action.REPLACE})
    default_settings = {"extra_types": [], "ignore_types": []}

    def stateful_types(self) -> frozenset[str]:
        types = set(providers.all_stateful_types()) | set(self.settings["extra_types"])
        return frozenset(types - set(self.settings["ignore_types"]))

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        if change.type not in self.stateful_types():
            return
        verb = "deleted" if change.action == Action.DELETE else "destroyed and re-created (replaced)"
        yield self.finding(
            change, "%s holds data and will be %s" % (change.type, verb),
            "Confirm backups exist and the data loss is intended. For replacements, check which "
            "attribute forces a new resource and whether it can be changed in place.")


@register
class RequiredTags(Policy):
    id = "CG-REQUIRED-TAGS"
    title = "Required tags (AWS) / labels (GCP) are missing"
    severity = Severity.LOW
    default_settings = {"required": []}

    def check(self, change: ResourceChange) -> Iterable[Finding]:
        required = self.settings["required"]
        provider = providers.lookup(change.provider)
        if not required or provider is None:
            return
        attrs = change.attributes
        for attribute in provider.tag_attributes:
            if attribute not in attrs:
                continue            # this resource type doesn't support tags/labels
            if change.is_unknown(attribute):
                return              # computed at apply time; can't judge it now
            present = attrs.get(attribute) or {}
            missing = [key for key in required if key not in present]
            if missing:
                yield self.finding(change, "missing required %s: %s" % (attribute, ", ".join(missing)),
                                   "Add the missing keys to `%s` (or to provider-level defaults)." % attribute)
            return

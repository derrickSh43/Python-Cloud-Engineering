"""The Policy interface and the registry that discovers policies.

A policy is a small class: it says which resource types it cares about and yields Findings for a
single ResourceChange. Policies never see the whole plan, never do I/O, and never decide the
outcome - that keeps each one tiny and easy to test on its own.
"""

from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable, Iterator

from ..models import Action, Finding, ResourceChange, Severity

BUILTIN_MODULES = ("changegate.policies.common", "changegate.policies.aws", "changegate.policies.gcp")


class PolicyLoadError(Exception):
    pass


class Policy(ABC):
    id: ClassVar[str]
    title: ClassVar[str]
    severity: ClassVar[Severity]
    resource_types: ClassVar[frozenset[str]] = frozenset()   # empty = every type
    actions: ClassVar[frozenset[Action]] = frozenset({Action.CREATE, Action.UPDATE, Action.REPLACE})
    default_settings: ClassVar[dict[str, Any]] = {}

    def __init__(self, settings: dict[str, Any] | None = None, severity: Severity | None = None):
        unknown = set(settings or {}) - set(self.default_settings)
        if unknown:
            raise PolicyLoadError("%s: unknown setting(s) %s (allowed: %s)" % (
                self.id, ", ".join(sorted(unknown)), ", ".join(sorted(self.default_settings)) or "none"))
        self.settings = {**self.default_settings, **(settings or {})}
        self.overridden = severity is not None
        self.level = severity or type(self).severity

    def applies_to(self, change: ResourceChange) -> bool:
        if change.action not in self.actions:
            return False
        return not self.resource_types or change.type in self.resource_types

    @abstractmethod
    def check(self, change: ResourceChange) -> Iterable[Finding]:
        """Yield a Finding for every problem in this change."""

    def finding(self, change: ResourceChange, message: str, remediation: str = "",
                severity: Severity | None = None) -> Finding:
        """Build a Finding. `severity` lets one policy report different levels (e.g. CRITICAL for
        all ports open); a configured override always wins over the policy's own choice."""
        level = self.level if self.overridden else (severity or self.level)
        return Finding(self.id, level, change.address, message, remediation)


_REGISTRY: dict[str, type[Policy]] = {}


def register(cls: type[Policy]) -> type[Policy]:
    """Class decorator that makes a policy discoverable."""
    for attr in ("id", "title", "severity"):
        if not hasattr(cls, attr):
            raise PolicyLoadError("%s must define %s" % (cls.__name__, attr))
    existing = _REGISTRY.get(cls.id)
    if existing is not None and existing.__qualname__ != cls.__qualname__:
        raise PolicyLoadError("duplicate policy id %s (%s and %s)" % (cls.id, existing.__name__, cls.__name__))
    _REGISTRY[cls.id] = cls
    return cls


def registered() -> dict[str, type[Policy]]:
    return dict(_REGISTRY)


def import_modules(modules: Iterable[str]) -> None:
    for name in modules:
        try:
            importlib.import_module(name)
        except ImportError as e:
            raise PolicyLoadError("cannot import policy module %r: %s" % (name, e)) from None


def load_policies(policy_config=None) -> list[Policy]:
    """Import built-in and extra policy modules and build the enabled policies, applying config."""
    from ..config import PolicyConfig

    cfg = policy_config or PolicyConfig()
    import_modules(BUILTIN_MODULES + tuple(cfg.extra_modules))
    known = set(_REGISTRY)
    for label, ids in (("disabled", cfg.disabled), ("severity_overrides", cfg.severity_overrides),
                       ("settings", cfg.settings)):
        unknown = sorted(set(ids) - known)
        if unknown:
            raise PolicyLoadError("policies.%s mentions unknown policy id(s): %s" % (label, ", ".join(unknown)))
    policies = []
    for pid in sorted(_REGISTRY):
        if pid in cfg.disabled:
            continue
        cls = _REGISTRY[pid]
        policies.append(cls(settings=cfg.settings.get(pid), severity=cfg.severity_overrides.get(pid)))
    return policies


def run_policies(policies: Iterable[Policy], changes: Iterable[ResourceChange]) -> Iterator[Finding]:
    """Apply every policy to every change. A policy that crashes produces a CRITICAL finding:
    a gate must fail closed, never silently skip a rule."""
    policies = list(policies)
    for change in changes:
        for policy in policies:
            if not policy.applies_to(change):
                continue
            try:
                yield from policy.check(change)
            except Exception as e:  # noqa: BLE001 - deliberately broad: fail closed
                yield Finding(policy.id, Severity.CRITICAL, change.address,
                              "policy raised %s: %s" % (type(e).__name__, e),
                              "Fix the policy or the input; the change is blocked until then.")

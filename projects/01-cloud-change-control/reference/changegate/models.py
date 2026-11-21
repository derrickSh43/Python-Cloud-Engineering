"""Core data types shared by every part of ChangeGate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


# The single actions Terraform emits. A replacement is always ["delete", "create"], never "replace".
TERRAFORM_SINGLE_ACTIONS = ("create", "update", "delete", "read", "no-op")


class Action(str, Enum):
    """What Terraform will do to one resource."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REPLACE = "replace"
    READ = "read"
    NO_OP = "no-op"

    @classmethod
    def from_terraform(cls, actions: list[str] | tuple[str, ...]) -> "Action":
        """Terraform encodes actions as a list: ["create"], ["delete", "create"], ["no-op"], ..."""
        actions = tuple(actions)
        if set(actions) == {"delete", "create"}:
            return cls.REPLACE
        if len(actions) == 1 and actions[0] in TERRAFORM_SINGLE_ACTIONS:
            return cls(actions[0])
        raise ValueError("unrecognised Terraform actions: %r" % (list(actions),))

    @property
    def is_destructive(self) -> bool:
        return self in (Action.DELETE, Action.REPLACE)

    @property
    def changes_state(self) -> bool:
        return self not in (Action.READ, Action.NO_OP)


class Severity(IntEnum):
    """Ordered so severities can be compared and max()'d. Also used as the overall risk level."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value: "str | Severity") -> "Severity":
        if isinstance(value, Severity):
            return value
        try:
            return cls[str(value).strip().upper()]
        except KeyError:
            raise ValueError("unknown severity %r (use low, medium, high or critical)" % (value,)) from None

    def escalate(self, levels: int = 1) -> "Severity":
        return Severity(min(Severity.CRITICAL, self + levels))

    def __str__(self) -> str:
        return self.name


class Decision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ResourceChange:
    """One resource's planned change, simplified from Terraform's JSON."""

    address: str
    type: str
    name: str
    provider: str          # short provider key, e.g. "aws", "google", or the raw name if unknown
    cloud: str             # "aws", "gcp" or "other"
    action: Action
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    after_unknown: dict[str, Any] = field(default_factory=dict)
    module: str | None = None

    @property
    def attributes(self) -> dict[str, Any]:
        """The values that matter for policy: the new values, or the old ones for a delete."""
        if self.action == Action.DELETE:
            return self.before or {}
        return self.after or {}

    def is_unknown(self, key: str) -> bool:
        """True when Terraform can't know the value until apply (it is computed)."""
        return bool(self.after_unknown.get(key))


@dataclass(frozen=True)
class Finding:
    policy_id: str
    severity: Severity
    address: str
    message: str
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"policy_id": self.policy_id, "severity": str(self.severity), "address": self.address,
                "message": self.message, "remediation": self.remediation}


@dataclass(frozen=True)
class Evaluation:
    """The complete result of evaluating one plan."""

    plan_sha256: str
    changes: tuple[ResourceChange, ...]
    findings: tuple[Finding, ...]
    risk: Severity
    decision: Decision
    reasons: tuple[str, ...]

    @property
    def action_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for change in self.changes:
            counts[change.action.value] = counts.get(change.action.value, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_sha256": self.plan_sha256,
            "risk": str(self.risk),
            "decision": str(self.decision),
            "reasons": list(self.reasons),
            "summary": {"resources": len(self.changes), "actions": self.action_counts,
                        "findings": len(self.findings)},
            "findings": [f.to_dict() for f in self.findings],
            "changes": [{"address": c.address, "type": c.type, "cloud": c.cloud, "action": c.action.value}
                        for c in self.changes],
        }

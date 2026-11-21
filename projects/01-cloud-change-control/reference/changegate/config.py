"""Loads changegate.toml. Every environment-specific choice lives here or in environment variables -
never in code. Unknown keys are rejected so a typo can't silently weaken a rule.

Lookup order for the config file: --config argument, then $CHANGEGATE_CONFIG, then ./changegate.toml,
otherwise built-in defaults.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import Severity

CONFIG_ENV = "CHANGEGATE_CONFIG"
DEFAULT_FILENAME = "changegate.toml"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class PolicyConfig:
    disabled: frozenset[str] = frozenset()
    severity_overrides: dict[str, Severity] = field(default_factory=dict)
    settings: dict[str, dict[str, Any]] = field(default_factory=dict)
    extra_modules: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskConfig:
    approval_at: Severity = Severity.MEDIUM
    block_at: Severity | None = Severity.CRITICAL      # None = never block automatically
    destructive_escalation_threshold: int = 5          # this many deletes/replaces raise risk one level; 0 = off


@dataclass(frozen=True)
class ApprovalConfig:
    approvers: tuple[str, ...] = ()
    required: dict[Severity, int] = field(default_factory=lambda: {
        Severity.LOW: 1, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 2})
    max_age_hours: float = 24.0
    allow_self_approval: bool = False
    key_env: str = "CHANGEGATE_HMAC_KEY"

    def required_for(self, risk: Severity) -> int:
        return self.required.get(risk, max(self.required.values(), default=1))


@dataclass(frozen=True)
class AuditConfig:
    enabled: bool = True
    path: Path = Path("changegate-audit.jsonl")


@dataclass(frozen=True)
class Config:
    policies: PolicyConfig = field(default_factory=PolicyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    approvals: ApprovalConfig = field(default_factory=ApprovalConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    source: Path | None = None


# ---------------------------------------------------------------- validation helpers

def _table(data: dict[str, Any], key: str, where: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ConfigError("[%s] must be a table" % (where + "." + key if where else key))
    return value


def _reject_unknown(data: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ConfigError("unknown setting(s) in [%s]: %s (allowed: %s)" % (
            where, ", ".join(unknown), ", ".join(sorted(allowed))))


def _severity(value: Any, where: str) -> Severity:
    try:
        return Severity.parse(value)
    except ValueError as e:
        raise ConfigError("%s: %s" % (where, e)) from None


def _str_list(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ConfigError("%s must be a list of strings" % where)
    return tuple(value)


# ---------------------------------------------------------------- sections

def _policies(data: dict[str, Any]) -> PolicyConfig:
    _reject_unknown(data, {"disabled", "severity_overrides", "settings", "extra_modules"}, "policies")
    overrides = _table(data, "severity_overrides", "policies")
    settings = _table(data, "settings", "policies")
    for pid, value in settings.items():
        if not isinstance(value, dict):
            raise ConfigError("[policies.settings.%s] must be a table" % pid)
    return PolicyConfig(
        disabled=frozenset(_str_list(data.get("disabled", []), "policies.disabled")),
        severity_overrides={pid: _severity(v, "policies.severity_overrides." + pid) for pid, v in overrides.items()},
        settings={pid: dict(v) for pid, v in settings.items()},
        extra_modules=_str_list(data.get("extra_modules", []), "policies.extra_modules"),
    )


def _risk(data: dict[str, Any]) -> RiskConfig:
    _reject_unknown(data, {"approval_at", "block_at", "destructive_escalation_threshold"}, "risk")
    defaults = RiskConfig()
    approval_at = _severity(data.get("approval_at", defaults.approval_at), "risk.approval_at")
    raw_block = data.get("block_at", defaults.block_at)
    block_at = None if str(raw_block).lower() in ("never", "none") else _severity(raw_block, "risk.block_at")
    if block_at is not None and block_at < approval_at:
        raise ConfigError("risk.block_at (%s) must not be lower than risk.approval_at (%s)" % (block_at, approval_at))
    threshold = data.get("destructive_escalation_threshold", defaults.destructive_escalation_threshold)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 0:
        raise ConfigError("risk.destructive_escalation_threshold must be a whole number >= 0")
    return RiskConfig(approval_at=approval_at, block_at=block_at, destructive_escalation_threshold=threshold)


def _approvals(data: dict[str, Any]) -> ApprovalConfig:
    _reject_unknown(data, {"approvers", "required", "max_age_hours", "allow_self_approval", "key_env"}, "approvals")
    defaults = ApprovalConfig()
    required = dict(defaults.required)
    for level, count in _table(data, "required", "approvals").items():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ConfigError("approvals.required.%s must be a whole number >= 1" % level)
        required[_severity(level, "approvals.required")] = count
    max_age = data.get("max_age_hours", defaults.max_age_hours)
    if not isinstance(max_age, (int, float)) or isinstance(max_age, bool) or max_age <= 0:
        raise ConfigError("approvals.max_age_hours must be a positive number")
    allow_self = data.get("allow_self_approval", defaults.allow_self_approval)
    if not isinstance(allow_self, bool):
        raise ConfigError("approvals.allow_self_approval must be true or false")
    key_env = data.get("key_env", defaults.key_env)
    if not isinstance(key_env, str) or not key_env:
        raise ConfigError("approvals.key_env must be the NAME of an environment variable")
    approvers = tuple(a.strip() for a in _str_list(data.get("approvers", []), "approvals.approvers") if a.strip())
    return ApprovalConfig(approvers=approvers, required=required, max_age_hours=float(max_age),
                          allow_self_approval=allow_self, key_env=key_env)


def _audit(data: dict[str, Any], base: Path | None) -> AuditConfig:
    _reject_unknown(data, {"enabled", "path"}, "audit")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ConfigError("audit.enabled must be true or false")
    path = Path(data.get("path", AuditConfig().path))
    if base is not None and not path.is_absolute():
        path = base / path
    return AuditConfig(enabled=enabled, path=path)


def from_dict(data: dict[str, Any], source: Path | None = None) -> Config:
    _reject_unknown(data, {"policies", "risk", "approvals", "audit"}, "top level")
    base = source.parent if source else None
    return Config(
        policies=_policies(_table(data, "policies", "")),
        risk=_risk(_table(data, "risk", "")),
        approvals=_approvals(_table(data, "approvals", "")),
        audit=_audit(_table(data, "audit", ""), base),
        source=source,
    )


def resolve_path(explicit: str | os.PathLike | None = None, environ: dict[str, str] | None = None,
                 cwd: Path | None = None) -> Path | None:
    environ = os.environ if environ is None else environ
    if explicit:
        return Path(explicit)
    if environ.get(CONFIG_ENV):
        return Path(environ[CONFIG_ENV])
    candidate = (cwd or Path.cwd()) / DEFAULT_FILENAME
    return candidate if candidate.is_file() else None


def load_config(path: str | os.PathLike | None = None, environ: dict[str, str] | None = None) -> Config:
    resolved = resolve_path(path, environ)
    if resolved is None:
        return Config()
    try:
        with open(resolved, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError("config file not found: %s" % resolved) from None
    except tomllib.TOMLDecodeError as e:
        raise ConfigError("%s is not valid TOML: %s" % (resolved, e)) from None
    return from_dict(data, source=resolved.resolve())

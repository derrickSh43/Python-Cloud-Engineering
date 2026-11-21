"""Reads the JSON produced by `terraform show -json <planfile>` and turns it into ResourceChange objects.

Only the parts ChangeGate needs are read. Anything unexpected raises PlanError with a message a
human can act on, instead of a KeyError deep inside a policy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import providers
from .models import Action, ResourceChange

SUPPORTED_MAJOR_FORMAT = "1"


class PlanError(Exception):
    """The input is not a usable Terraform plan."""


def plan_digest(raw: bytes) -> str:
    """SHA-256 of the exact plan bytes. Approvals are tied to this value."""
    return hashlib.sha256(raw).hexdigest()


def read_plan_bytes(path: str | Path) -> bytes:
    path = Path(path)
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise PlanError("plan file not found: %s" % path) from None
    except IsADirectoryError:
        raise PlanError("expected a plan file but got a directory: %s" % path) from None


def decode_plan(raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except UnicodeDecodeError:
        raise PlanError("plan is not UTF-8 text - did you pass the binary plan instead of "
                        "`terraform show -json` output?") from None
    except json.JSONDecodeError as e:
        raise PlanError("plan is not valid JSON (line %d, column %d): %s" % (e.lineno, e.colno, e.msg)) from None
    if not isinstance(data, dict):
        raise PlanError("plan JSON must be an object at the top level")
    return data


def check_format(plan: dict[str, Any]) -> None:
    version = plan.get("format_version")
    if version is None:
        raise PlanError("missing format_version - this does not look like `terraform show -json` output")
    if str(version).split(".")[0] != SUPPORTED_MAJOR_FORMAT:
        raise PlanError("unsupported plan format_version %s (supported: %s.x)" % (version, SUPPORTED_MAJOR_FORMAT))


def parse_change(entry: dict[str, Any]) -> ResourceChange:
    try:
        address = entry["address"]
        change = entry["change"]
        actions = change["actions"]
    except (KeyError, TypeError):
        raise PlanError("resource change is missing address/change/actions: %r" % (entry,)) from None
    try:
        action = Action.from_terraform(actions)
    except ValueError as e:
        raise PlanError("%s: %s" % (address, e)) from None
    provider_name = entry.get("provider_name", "")
    return ResourceChange(
        address=address,
        type=entry.get("type", ""),
        name=entry.get("name", ""),
        provider=providers.provider_key(provider_name) if provider_name else "",
        cloud=providers.cloud_for(provider_name) if provider_name else "other",
        action=action,
        before=change.get("before"),
        after=change.get("after"),
        after_unknown=change.get("after_unknown") or {},
        module=entry.get("module_address"),
    )


def parse_plan(plan: dict[str, Any], include_data_sources: bool = False) -> list[ResourceChange]:
    """All managed-resource changes in plan order. no-op changes are kept (policies skip them)."""
    check_format(plan)
    entries = plan.get("resource_changes")
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise PlanError("resource_changes must be a list")
    changes = []
    for entry in entries:
        if not include_data_sources and isinstance(entry, dict) and entry.get("mode") == "data":
            continue
        changes.append(parse_change(entry))
    return changes


def load_plan(path: str | Path) -> tuple[bytes, dict[str, Any], list[ResourceChange]]:
    """Convenience: read a plan file and return (raw bytes, decoded JSON, changes)."""
    raw = read_plan_bytes(path)
    plan = decode_plan(raw)
    return raw, plan, parse_plan(plan)

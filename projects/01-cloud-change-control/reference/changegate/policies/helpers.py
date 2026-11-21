"""Small pure functions shared by policies: networks, ports, nested blocks and IAM documents."""

from __future__ import annotations

import ipaddress
import json
from typing import Any, Iterator

WORLD_CIDRS = frozenset({"0.0.0.0/0", "::/0"})
ALL_PORTS = (0, 65535)


def is_world(cidr: str) -> bool:
    """True for a range that covers the entire IPv4 or IPv6 internet."""
    try:
        return ipaddress.ip_network(str(cidr).strip(), strict=False).prefixlen == 0
    except ValueError:
        return False


def any_world(cidrs: Any) -> bool:
    return any(is_world(c) for c in as_list(cidrs))


def as_list(value: Any) -> list[Any]:
    """Terraform values may be null, a single value or a list. Always get a list back."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return [value]


def first_block(attrs: dict[str, Any] | None, key: str) -> dict[str, Any]:
    """Nested blocks appear as lists of objects in plan JSON (e.g. settings = [{...}]). Return the first."""
    blocks = as_list((attrs or {}).get(key))
    return blocks[0] if blocks and isinstance(blocks[0], dict) else {}


def parse_port_range(value: Any) -> tuple[int, int]:
    """'22' -> (22, 22); '8000-8080' -> (8000, 8080); 443 -> (443, 443)."""
    text = str(value).strip()
    if "-" in text:
        low, high = text.split("-", 1)
        return int(low), int(high)
    return int(text), int(text)


def range_includes_any(port_range: tuple[int, int], ports: list[int]) -> list[int]:
    low, high = port_range
    return sorted(p for p in ports if low <= p <= high)


def covers_all_ports(port_range: tuple[int, int]) -> bool:
    return port_range[0] <= ALL_PORTS[0] + 1 and port_range[1] >= ALL_PORTS[1]


def load_json_document(value: Any) -> dict[str, Any] | None:
    """IAM policies arrive as JSON strings. Returns None when the value isn't known yet."""
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        return value
    document = json.loads(value)
    if not isinstance(document, dict):
        raise ValueError("policy document must be a JSON object")
    return document


def statements(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for statement in as_list(document.get("Statement")):
        if isinstance(statement, dict):
            yield statement


def principal_is_public(principal: Any) -> bool:
    """AWS Principal of "*" or {"AWS": "*"} (or a list containing "*") means anyone."""
    if principal == "*":
        return True
    if isinstance(principal, dict):
        return any("*" in as_list(v) for v in principal.values())
    return False

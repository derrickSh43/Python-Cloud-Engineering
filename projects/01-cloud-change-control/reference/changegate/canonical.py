"""Canonical JSON: the same data always produces the same bytes, so it can be hashed and signed."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: Any) -> str:
    return hashlib.sha256(canonical_bytes(data)).hexdigest()

"""Append-only, hash-chained audit log (JSON Lines).

Every record stores the hash of the record before it. Changing, deleting or reordering any record
breaks the chain and `verify()` reports exactly where. Deleting records from the *end* can only be
detected by comparing against a head hash kept somewhere else (e.g. printed in CI logs) - see
docs/SECURITY.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canonical import sha256_hex

GENESIS_HASH = "0" * 64


class AuditError(Exception):
    pass


def record_hash(record: dict[str, Any]) -> str:
    return sha256_hex({k: v for k, v in record.items() if k != "hash"})


@dataclass(frozen=True)
class AuditVerification:
    ok: bool
    count: int
    head: str
    problems: tuple[str, ...]


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records = []
        with open(self.path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise AuditError("line %d of %s is not valid JSON: %s" % (n, self.path, e.msg)) from None
        return records

    def head(self) -> tuple[int, str]:
        records = self.records()
        if not records:
            return 0, GENESIS_HASH
        last = records[-1]
        return int(last["seq"]), str(last["hash"])

    def append(self, event: str, data: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
        seq, prev = self.head()
        moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        record = {"seq": seq + 1, "timestamp": moment.isoformat(timespec="seconds").replace("+00:00", "Z"),
                  "event": event, "data": data, "prev_hash": prev}
        record["hash"] = record_hash(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        # O_APPEND: each write goes to the end of the file, never over existing records.
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
        return record

    def verify(self, expected_head: str | None = None) -> AuditVerification:
        try:
            records = self.records()
        except AuditError as e:
            return AuditVerification(False, 0, "", (str(e),))
        problems = []
        prev = GENESIS_HASH
        for n, record in enumerate(records, 1):
            label = "record %d" % n
            if record.get("seq") != n:
                problems.append("%s: sequence number is %r, expected %d (records missing or reordered)" % (
                    label, record.get("seq"), n))
            if record.get("prev_hash") != prev:
                problems.append("%s: prev_hash does not match the previous record (chain broken)" % label)
            if record.get("hash") != record_hash(record):
                problems.append("%s: contents were modified (hash mismatch)" % label)
            prev = str(record.get("hash"))
        head = prev if records else GENESIS_HASH
        if expected_head and expected_head != head:
            problems.append("head hash %s... does not match the expected %s... (records removed from the end?)" % (
                head[:12], expected_head[:12]))
        return AuditVerification(not problems, len(records), head, tuple(problems))

import json
from datetime import datetime, timezone

from changegate.audit import GENESIS_HASH, AuditError, AuditLog, record_hash
from changegate.canonical import sha256_hex
from support import raises, temp_dir

NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


def test_record_hash_ignores_hash_field():
    """record_hash hashes everything except the 'hash' key"""
    record = {"seq": 1, "event": "x", "hash": "whatever"}
    assert record_hash(record) == sha256_hex({"seq": 1, "event": "x"})


def test_empty_log():
    """a log file that doesn't exist has no records and the genesis head"""
    with temp_dir() as tmp:
        log = AuditLog(tmp / "none.jsonl")
        assert log.records() == [] and log.head() == (0, GENESIS_HASH)


def test_append_builds_a_chain():
    """each record links to the previous record's hash"""
    with temp_dir() as tmp:
        log = AuditLog(tmp / "logs" / "audit.jsonl")
        first = log.append("evaluate", {"plan": "a"}, now=NOW)
        second = log.append("approve", {"who": "alice"}, now=NOW)
        assert first["seq"] == 1 and first["prev_hash"] == GENESIS_HASH
        assert first["timestamp"] == "2026-03-01T12:00:00Z"
        assert first["hash"] == record_hash(first)
        assert second["seq"] == 2 and second["prev_hash"] == first["hash"]
        assert log.head() == (2, second["hash"])


def test_one_json_line_per_record():
    """records are stored one JSON object per line and survive reloading"""
    with temp_dir() as tmp:
        AuditLog(tmp / "a.jsonl").append("evaluate", {"n": 1})
        AuditLog(tmp / "a.jsonl").append("evaluate", {"n": 2})
        lines = (tmp / "a.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2 and json.loads(lines[1])["data"] == {"n": 2}
        assert [r["seq"] for r in AuditLog(tmp / "a.jsonl").records()] == [1, 2]


def test_bad_line():
    """a corrupt line raises AuditError naming the line"""
    with temp_dir() as tmp:
        path = tmp / "a.jsonl"
        AuditLog(path).append("evaluate", {})
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n{broken\n")
        error = raises(AuditError, AuditLog(path).records)
        assert "line 3" in str(error) and "not valid JSON" in str(error), str(error)

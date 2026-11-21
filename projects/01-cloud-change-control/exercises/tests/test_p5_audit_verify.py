import json

from changegate.audit import GENESIS_HASH, AuditLog
from support import temp_dir


def filled(path, n=3):
    log = AuditLog(path)
    for i in range(n):
        log.append("evaluate", {"i": i})
    return log


def rewrite(log, records):
    log.path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_intact_log():
    """an untouched log verifies, reporting count and head"""
    with temp_dir() as tmp:
        log = filled(tmp / "a.jsonl")
        result = log.verify()
        assert result.ok and result.count == 3 and result.problems == ()
        assert result.head == log.records()[-1]["hash"]
        empty = AuditLog(tmp / "none.jsonl").verify()
        assert empty.ok and empty.head == GENESIS_HASH


def test_modified_record():
    """editing a record's data is detected as 'modified'"""
    with temp_dir() as tmp:
        log = filled(tmp / "a.jsonl")
        records = log.records()
        records[1]["data"]["i"] = 99
        rewrite(log, records)
        result = log.verify()
        assert not result.ok and any(p.startswith("record 2: ") and "modified" in p for p in result.problems)


def test_deleted_or_reordered():
    """removing or swapping records breaks the chain"""
    with temp_dir() as tmp:
        log = filled(tmp / "a.jsonl")
        r = log.records()
        rewrite(log, [r[0], r[2]])
        problems = log.verify().problems
        assert any("sequence" in p for p in problems) and any("chain broken" in p for p in problems)
        rewrite(log, [r[1], r[0], r[2]])
        assert not log.verify().ok


def test_truncation_with_expected_head():
    """dropping the newest records is caught only with a head hash kept elsewhere"""
    with temp_dir() as tmp:
        log = filled(tmp / "a.jsonl")
        head = log.verify().head
        rewrite(log, log.records()[:2])
        assert log.verify().ok
        result = log.verify(expected_head=head)
        assert not result.ok and "does not match the expected" in result.problems[-1]


def test_unreadable_log():
    """a corrupt file gives a failed verification, not a crash"""
    with temp_dir() as tmp:
        (tmp / "a.jsonl").write_text("{broken\n")
        result = AuditLog(tmp / "a.jsonl").verify()
        assert not result.ok and result.count == 0 and "not valid JSON" in result.problems[0]

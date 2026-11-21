import json

from changegate.audit import GENESIS_HASH, AuditLog


def filled(tmp_path, n=3):
    log = AuditLog(tmp_path / "audit.jsonl")
    for i in range(n):
        log.append("evaluate", {"i": i})
    return log


def rewrite(log, records):
    log.path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_empty_log_verifies(tmp_path):
    result = AuditLog(tmp_path / "none.jsonl").verify()
    assert result.ok and result.count == 0 and result.head == GENESIS_HASH


def test_chain_links(tmp_path):
    log = filled(tmp_path)
    records = log.records()
    assert [r["seq"] for r in records] == [1, 2, 3]
    assert records[0]["prev_hash"] == GENESIS_HASH
    assert records[1]["prev_hash"] == records[0]["hash"]
    result = log.verify()
    assert result.ok and result.count == 3 and result.head == records[-1]["hash"]


def test_modified_record_detected(tmp_path):
    log = filled(tmp_path)
    records = log.records()
    records[1]["data"]["i"] = 99
    rewrite(log, records)
    result = log.verify()
    assert not result.ok and any("record 2" in p and "modified" in p for p in result.problems)


def test_deleted_middle_record_detected(tmp_path):
    log = filled(tmp_path)
    records = log.records()
    rewrite(log, [records[0], records[2]])
    assert not log.verify().ok


def test_reordered_records_detected(tmp_path):
    log = filled(tmp_path)
    records = log.records()
    rewrite(log, [records[1], records[0], records[2]])
    assert not log.verify().ok


def test_truncation_needs_expected_head(tmp_path):
    log = filled(tmp_path)
    head = log.verify().head
    records = log.records()
    rewrite(log, records[:2])
    assert log.verify().ok                      # undetectable on its own...
    assert not log.verify(expected_head=head).ok  # ...but caught with an externally kept head


def test_invalid_json_line(tmp_path):
    log = filled(tmp_path, 1)
    with open(log.path, "a", encoding="utf-8") as f:
        f.write("{broken\n")
    result = log.verify()
    assert not result.ok and "not valid JSON" in result.problems[0]


def test_append_continues_chain_after_reload(tmp_path):
    filled(tmp_path, 2)
    log = AuditLog(tmp_path / "audit.jsonl")
    record = log.append("approve", {"who": "alice"})
    assert record["seq"] == 3 and log.verify().ok

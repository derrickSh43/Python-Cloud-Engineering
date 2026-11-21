import json
from datetime import datetime, timezone

from changegate import approvals as ap
from changegate.models import Severity
from support import temp_dir

KEY = b"k" * 32
NOW = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


def approve(who):
    return ap.create_approval("a" * 64, who, Severity.HIGH, KEY, ttl_hours=24, now=NOW)


def test_write_approval():
    """write_approval creates the folder and a predictable file name"""
    with temp_dir() as tmp:
        path = ap.write_approval(approve("alice smith"), tmp / "approvals")
        assert path.parent == tmp / "approvals"
        assert path.name == "aaaaaaaaaaaa-alice_smith.json"
        assert json.loads(path.read_text(encoding="utf-8")) == approve("alice smith").to_dict()


def test_load_from_directory_and_file():
    """load_approvals reads a directory of *.json and individual files"""
    with temp_dir() as tmp:
        ap.write_approval(approve("alice"), tmp / "a")
        single = ap.write_approval(approve("bob"), tmp / "b")
        found, problems = ap.load_approvals([tmp / "a", single])
        assert [a.approver for a in found] == ["alice", "bob"] and problems == []


def test_bad_files_are_reported_not_fatal():
    """broken files and missing paths are problems; good files still load"""
    with temp_dir() as tmp:
        ap.write_approval(approve("alice"), tmp)
        (tmp / "garbage.json").write_text("{nope")
        (tmp / "incomplete.json").write_text('{"version": 1}')
        found, problems = ap.load_approvals([tmp, tmp / "missing.json"])
        assert [a.approver for a in found] == ["alice"]
        assert len(problems) == 3, problems
        assert any("not found" in p for p in problems)
        assert any(p.startswith("garbage.json: ") for p in problems)

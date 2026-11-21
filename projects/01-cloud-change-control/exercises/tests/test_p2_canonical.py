import hashlib

from changegate.canonical import canonical_bytes, sha256_hex


def test_returns_bytes_without_spaces():
    """canonical_bytes returns compact UTF-8 bytes"""
    assert canonical_bytes({"b": 1, "a": [1, 2]}) == b'{"a":[1,2],"b":1}'


def test_key_order_does_not_matter():
    """the same data in a different key order gives identical bytes"""
    assert canonical_bytes({"x": 1, "y": {"q": 2, "p": 3}}) == canonical_bytes({"y": {"p": 3, "q": 2}, "x": 1})


def test_keeps_non_ascii():
    """non-ASCII text is kept as real characters, not \\u escapes"""
    assert canonical_bytes({"name": "café"}) == '{"name":"café"}'.encode("utf-8")


def test_sha256_hex():
    """sha256_hex is the SHA-256 of the canonical bytes"""
    data = {"approver": "alice", "risk": "HIGH"}
    assert sha256_hex(data) == hashlib.sha256(canonical_bytes(data)).hexdigest()
    assert sha256_hex({"a": 1, "b": 2}) == sha256_hex({"b": 2, "a": 1})

from changegate.plan_parser import PlanError, decode_plan
from support import raises, sample


def test_decodes_a_plan():
    """valid plan JSON becomes a dict"""
    plan = decode_plan(sample("aws_safe.json").read_bytes())
    assert isinstance(plan, dict)
    assert plan["format_version"] == "1.2"


def test_ignores_byte_order_mark():
    """a UTF-8 byte-order mark at the start is ignored (Windows editors add one)"""
    assert decode_plan(b'\xef\xbb\xbf{"a": 1}') == {"a": 1}


def test_invalid_json():
    """invalid JSON raises PlanError with the line and column"""
    error = raises(PlanError, decode_plan, b'{\n  "a": 1,\n  oops\n}')
    assert str(error).startswith("plan is not valid JSON"), "message was: %s" % error
    assert "line 3" in str(error), "include the line number (e.lineno) - message was: %s" % error


def test_not_utf8():
    """binary data raises PlanError mentioning UTF-8"""
    error = raises(PlanError, decode_plan, b"\xff\xfe\x00\x01binary")
    assert "UTF-8" in str(error), "message was: %s" % error


def test_must_be_an_object():
    """JSON that isn't an object (e.g. a list) raises PlanError"""
    error = raises(PlanError, decode_plan, b"[1, 2, 3]")
    assert "object" in str(error), "message was: %s" % error

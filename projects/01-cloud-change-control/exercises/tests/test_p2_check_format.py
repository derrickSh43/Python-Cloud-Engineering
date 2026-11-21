from changegate.plan_parser import PlanError, check_format
from support import raises


def test_supported_versions_pass():
    """format 1.x is accepted and nothing is returned"""
    assert check_format({"format_version": "1.2"}) is None
    assert check_format({"format_version": "1.0"}) is None


def test_numeric_version():
    """a version given as a number (1.2) is accepted too"""
    assert check_format({"format_version": 1.2}) is None


def test_missing_version():
    """a missing format_version raises PlanError mentioning format_version"""
    error = raises(PlanError, check_format, {"resource_changes": []})
    assert "format_version" in str(error), "message was: %s" % error


def test_unsupported_major_version():
    """format 2.0 raises PlanError('unsupported plan format_version ...')"""
    error = raises(PlanError, check_format, {"format_version": "2.0"})
    assert str(error).startswith("unsupported plan format_version"), "message was: %s" % error
    assert "2.0" in str(error)

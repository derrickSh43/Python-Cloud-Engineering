from pathlib import Path

from changegate.plan_parser import PlanError, read_plan_bytes
from support import raises, sample, temp_dir


def test_returns_exact_bytes():
    """returns the file's contents as bytes, unchanged"""
    data = read_plan_bytes(sample("aws_safe.json"))
    assert isinstance(data, bytes), "expected bytes, got %s - use read_bytes(), not read_text()" % type(data).__name__
    assert data == sample("aws_safe.json").read_bytes()


def test_accepts_a_string_path():
    """accepts a plain string as well as a Path"""
    assert read_plan_bytes(str(sample("no_changes.json"))) == sample("no_changes.json").read_bytes()


def test_missing_file():
    """a missing file raises PlanError('plan file not found: ...')"""
    with temp_dir() as tmp:
        error = raises(PlanError, read_plan_bytes, tmp / "nope.json")
    assert "plan file not found" in str(error), "message was: %s" % error
    assert "nope.json" in str(error), "the message should include the path"


def test_directory():
    """a directory raises PlanError('expected a plan file but got a directory: ...')"""
    with temp_dir() as tmp:
        error = raises(PlanError, read_plan_bytes, tmp)
    assert "directory" in str(error), "message was: %s" % error


def test_error_hides_original_traceback():
    """errors are raised `from None` so learners see one clear message"""
    with temp_dir() as tmp:
        error = raises(PlanError, read_plan_bytes, Path(tmp) / "nope.json")
    assert error.__suppress_context__, "use `raise PlanError(...) from None`"

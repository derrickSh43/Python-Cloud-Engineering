from changegate import config
from changegate.config import ConfigError
from changegate.models import Severity
from support import raises


def test_reject_unknown_accepts_known_keys():
    """_reject_unknown returns None when every key is allowed"""
    assert config._reject_unknown({"a": 1}, {"a", "b"}, "risk") is None


def test_reject_unknown_lists_sorted_keys():
    """unknown keys are reported, sorted, with the section name"""
    error = raises(ConfigError, config._reject_unknown, {"zeta": 1, "alpha": 2, "ok": 3}, {"ok"}, "risk")
    assert str(error).startswith("unknown setting(s) in [risk]: alpha, zeta"), "message was: %s" % error


def test_severity_helper():
    """_severity parses severities and turns errors into ConfigError with the location"""
    assert config._severity("high", "risk.block_at") is Severity.HIGH
    error = raises(ConfigError, config._severity, "severe", "risk.block_at")
    assert str(error).startswith("risk.block_at: "), "message was: %s" % error


def test_str_list():
    """_str_list returns a tuple of strings or raises ConfigError"""
    assert config._str_list(["a", "b"], "approvals.approvers") == ("a", "b")
    for bad in ("alice", ["a", 1], None):
        error = raises(ConfigError, config._str_list, bad, "approvals.approvers")
        assert "must be a list of strings" in str(error)


def test_used_by_from_dict():
    """a typo anywhere in a config is rejected"""
    error = raises(ConfigError, config._approvals, {"aprovers": ["x"]})
    assert "aprovers" in str(error)

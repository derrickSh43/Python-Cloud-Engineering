from changegate import config
from changegate.config import ConfigError, RiskConfig
from changegate.models import Severity
from support import raises


def test_defaults():
    """an empty [risk] table gives the RiskConfig defaults"""
    assert config._risk({}) == RiskConfig()


def test_values():
    """severities and the threshold are read"""
    cfg = config._risk({"approval_at": "high", "block_at": "critical", "destructive_escalation_threshold": 3})
    assert cfg.approval_at is Severity.HIGH and cfg.block_at is Severity.CRITICAL
    assert cfg.destructive_escalation_threshold == 3


def test_block_never():
    """block_at = 'never' or 'None' means never block"""
    assert config._risk({"block_at": "never"}).block_at is None
    assert config._risk({"block_at": "None"}).block_at is None


def test_block_below_approval_rejected():
    """block_at lower than approval_at is an error"""
    error = raises(ConfigError, config._risk, {"approval_at": "high", "block_at": "medium"})
    assert "must not be lower" in str(error)


def test_threshold_validation():
    """the threshold must be a whole number >= 0, and not true/false"""
    for bad in (-1, "5", 2.5, True):
        error = raises(ConfigError, config._risk, {"destructive_escalation_threshold": bad})
        assert ">= 0" in str(error), "%r should be rejected" % (bad,)
    assert config._risk({"destructive_escalation_threshold": 0}).destructive_escalation_threshold == 0


def test_unknown_key():
    """unknown keys in [risk] are rejected"""
    raises(ConfigError, config._risk, {"aproval_at": "high"})

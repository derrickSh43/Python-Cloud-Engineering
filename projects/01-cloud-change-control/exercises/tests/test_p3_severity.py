from changegate.models import Severity
from support import raises


def test_parse_names_any_case():
    """'high', ' Critical ' and 'LOW' parse to members"""
    assert Severity.parse("high") is Severity.HIGH
    assert Severity.parse(" Critical ") is Severity.CRITICAL
    assert Severity.parse("LOW") is Severity.LOW


def test_parse_passes_members_through():
    """a Severity passed in is returned unchanged"""
    assert Severity.parse(Severity.MEDIUM) is Severity.MEDIUM


def test_parse_unknown():
    """unknown text raises ValueError mentioning the bad value"""
    error = raises(ValueError, Severity.parse, "severe")
    assert "severe" in str(error), "message was: %s" % error


def test_escalate():
    """escalate moves up one (or more) levels"""
    assert Severity.LOW.escalate() is Severity.MEDIUM
    assert Severity.MEDIUM.escalate(2) is Severity.CRITICAL


def test_escalate_caps_at_critical():
    """escalate never goes above CRITICAL"""
    assert Severity.HIGH.escalate(5) is Severity.CRITICAL
    assert Severity.CRITICAL.escalate() is Severity.CRITICAL
    assert isinstance(Severity.HIGH.escalate(), Severity), "return a Severity, not a plain int"

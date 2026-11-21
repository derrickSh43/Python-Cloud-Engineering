import pytest

from changegate.models import Action, Decision, Severity


@pytest.mark.parametrize("actions, expected", [
    (["create"], Action.CREATE), (["update"], Action.UPDATE), (["delete"], Action.DELETE),
    (["delete", "create"], Action.REPLACE), (["create", "delete"], Action.REPLACE),
    (["read"], Action.READ), (["no-op"], Action.NO_OP),
])
def test_action_from_terraform(actions, expected):
    assert Action.from_terraform(actions) is expected


@pytest.mark.parametrize("actions", [[], ["explode"], ["create", "update"], ["replace"]])
def test_action_rejects_unknown(actions):
    with pytest.raises(ValueError):
        Action.from_terraform(actions)


def test_destructive_and_state_flags():
    assert Action.DELETE.is_destructive and Action.REPLACE.is_destructive
    assert not Action.CREATE.is_destructive
    assert not Action.NO_OP.changes_state and not Action.READ.changes_state
    assert Action.UPDATE.changes_state


def test_severity_order_and_parse():
    assert Severity.LOW < Severity.MEDIUM < Severity.HIGH < Severity.CRITICAL
    assert max([Severity.MEDIUM, Severity.CRITICAL, Severity.LOW]) is Severity.CRITICAL
    assert Severity.parse("high") is Severity.HIGH
    assert Severity.parse(" Critical ") is Severity.CRITICAL
    with pytest.raises(ValueError):
        Severity.parse("severe")


def test_severity_escalate_caps_at_critical():
    assert Severity.LOW.escalate() is Severity.MEDIUM
    assert Severity.HIGH.escalate(5) is Severity.CRITICAL
    assert str(Severity.HIGH) == "HIGH"


def test_change_attributes_use_before_for_deletes(make_change):
    deleted = make_change("aws_s3_bucket", action="delete", before={"bucket": "old"})
    assert deleted.attributes == {"bucket": "old"}
    created = make_change("aws_s3_bucket", {"bucket": "new"})
    assert created.attributes == {"bucket": "new"}


def test_decision_values():
    assert str(Decision.REQUIRE_APPROVAL) == "require_approval"

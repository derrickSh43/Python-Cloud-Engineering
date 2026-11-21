from changegate.models import Action
from support import raises


def test_single_actions():
    """['create'], ['update'], ['delete'], ['read'], ['no-op'] map to their members"""
    assert Action.from_terraform(["create"]) is Action.CREATE
    assert Action.from_terraform(["update"]) is Action.UPDATE
    assert Action.from_terraform(["delete"]) is Action.DELETE
    assert Action.from_terraform(["read"]) is Action.READ
    assert Action.from_terraform(["no-op"]) is Action.NO_OP


def test_replace_in_either_order():
    """['delete', 'create'] and ['create', 'delete'] both mean REPLACE"""
    assert Action.from_terraform(["delete", "create"]) is Action.REPLACE
    assert Action.from_terraform(("create", "delete")) is Action.REPLACE


def test_unknown_actions_raise_value_error():
    """empty, unknown or nonsense combinations raise ValueError"""
    for bad in ([], ["explode"], ["create", "update"], ["replace"]):
        raises(ValueError, Action.from_terraform, bad)


def test_is_destructive():
    """only DELETE and REPLACE are destructive"""
    assert Action.DELETE.is_destructive and Action.REPLACE.is_destructive
    for action in (Action.CREATE, Action.UPDATE, Action.READ, Action.NO_OP):
        assert not action.is_destructive, "%s should not be destructive" % action


def test_changes_state():
    """READ and NO_OP don't change anything; the others do"""
    assert not Action.READ.changes_state and not Action.NO_OP.changes_state
    for action in (Action.CREATE, Action.UPDATE, Action.DELETE, Action.REPLACE):
        assert action.changes_state, "%s changes state" % action

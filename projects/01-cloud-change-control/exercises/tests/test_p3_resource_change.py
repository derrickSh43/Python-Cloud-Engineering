import dataclasses

from changegate.models import Action, ResourceChange
from support import raises


def build(**overrides):
    values = dict(address="aws_s3_bucket.logs", type="aws_s3_bucket", name="logs", provider="aws", cloud="aws",
                  action=Action.CREATE)
    values.update(overrides)
    return ResourceChange(**values)


def test_is_a_dataclass_with_fields_in_order():
    """ResourceChange is a dataclass with the ten fields in the given order"""
    assert dataclasses.is_dataclass(ResourceChange), "decorate the class with @dataclass(frozen=True)"
    names = [f.name for f in dataclasses.fields(ResourceChange)]
    assert names == ["address", "type", "name", "provider", "cloud", "action", "before", "after",
                     "after_unknown", "module"], "fields were: %s" % names


def test_defaults():
    """before, after and module default to None; after_unknown to an empty dict"""
    change = build()
    assert change.before is None and change.after is None and change.module is None
    assert change.after_unknown == {}
    assert build().after_unknown is not build().after_unknown, "use field(default_factory=dict) for after_unknown"


def test_frozen():
    """ResourceChange is frozen: fields can't be changed after creation"""
    change = build()
    raises(dataclasses.FrozenInstanceError, setattr, change, "address", "other")


def test_attributes_uses_after():
    """attributes returns `after` for creates and updates ({} if None)"""
    assert build(after={"bucket": "new"}).attributes == {"bucket": "new"}
    assert build(action=Action.UPDATE).attributes == {}


def test_attributes_uses_before_for_delete():
    """attributes returns `before` for a delete"""
    change = build(action=Action.DELETE, before={"bucket": "old"}, after=None)
    assert change.attributes == {"bucket": "old"}
    assert build(action=Action.DELETE).attributes == {}


def test_is_unknown():
    """is_unknown is True when after_unknown marks the key"""
    change = build(after_unknown={"arn": True, "id": False})
    assert change.is_unknown("arn") is True
    assert change.is_unknown("id") is False
    assert change.is_unknown("missing") is False

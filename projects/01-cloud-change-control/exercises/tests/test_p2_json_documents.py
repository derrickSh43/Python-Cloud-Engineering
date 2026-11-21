import types

from changegate.policies.helpers import load_json_document, principal_is_public, statements
from support import raises


def test_load_document_from_string():
    """a JSON string is parsed into a dict"""
    assert load_json_document('{"Statement": []}') == {"Statement": []}


def test_load_document_unknown_values():
    """None and '' mean 'not known yet' and give None; a dict is returned as-is"""
    assert load_json_document(None) is None
    assert load_json_document("") is None
    doc = {"a": 1}
    assert load_json_document(doc) is doc


def test_load_document_rejects_non_objects():
    """JSON that isn't an object raises ValueError"""
    raises(ValueError, load_json_document, "[1, 2]")


def test_statements_is_a_generator():
    """statements() is a generator yielding each statement dict"""
    doc = {"Statement": [{"Effect": "Allow"}, "junk", {"Effect": "Deny"}]}
    result = statements(doc)
    assert isinstance(result, types.GeneratorType), "use `yield` to make statements() a generator"
    assert list(result) == [{"Effect": "Allow"}, {"Effect": "Deny"}]


def test_statements_single_or_missing():
    """a single statement dict, or no Statement key, both work"""
    assert list(statements({"Statement": {"Effect": "Allow"}})) == [{"Effect": "Allow"}]
    assert list(statements({})) == []


def test_principal_is_public():
    """'*', {'AWS': '*'} and {'AWS': ['*']} are public; specific principals are not"""
    assert principal_is_public("*")
    assert principal_is_public({"AWS": "*"})
    assert principal_is_public({"AWS": ["arn:aws:iam::123456789012:root", "*"]})
    assert not principal_is_public({"AWS": "arn:aws:iam::123456789012:root"})
    assert not principal_is_public({"Service": "ec2.amazonaws.com"})
    assert not principal_is_public(None)

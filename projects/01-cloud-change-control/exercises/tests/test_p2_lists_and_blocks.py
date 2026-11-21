from changegate.policies.helpers import as_list, first_block


def test_none_is_empty():
    """as_list(None) is []"""
    assert as_list(None) == []


def test_single_values_are_wrapped():
    """a single value becomes a one-item list (strings are single values)"""
    assert as_list("0.0.0.0/0") == ["0.0.0.0/0"]
    assert as_list(22) == [22]
    assert as_list({"a": 1}) == [{"a": 1}]


def test_collections_become_lists():
    """lists, tuples and sets become lists"""
    assert as_list([1, 2]) == [1, 2]
    assert as_list((1, 2)) == [1, 2]
    assert sorted(as_list({3, 1})) == [1, 3]
    assert isinstance(as_list((1,)), list)


def test_first_block():
    """first_block returns the first object of a nested block"""
    attrs = {"settings": [{"tier": "db-f1-micro"}, {"tier": "ignored"}]}
    assert first_block(attrs, "settings") == {"tier": "db-f1-micro"}


def test_first_block_missing_or_empty():
    """first_block returns {} for a missing key, an empty list, None attrs or a non-dict item"""
    assert first_block({}, "settings") == {}
    assert first_block({"settings": []}, "settings") == {}
    assert first_block(None, "settings") == {}
    assert first_block({"settings": ["text"]}, "settings") == {}

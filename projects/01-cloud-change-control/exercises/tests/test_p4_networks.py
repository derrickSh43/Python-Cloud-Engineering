from changegate.policies.helpers import any_world, is_world


def test_world_ranges():
    """0.0.0.0/0 and ::/0 are the whole internet"""
    assert is_world("0.0.0.0/0")
    assert is_world("::/0")


def test_sloppy_world_ranges():
    """spaces and host bits are tolerated: ' 0.0.0.0/0 ' and '1.2.3.4/0' count"""
    assert is_world(" 0.0.0.0/0 ")
    assert is_world("1.2.3.4/0")


def test_private_and_single_hosts():
    """private ranges and single hosts are not world-open"""
    for cidr in ("10.0.0.0/8", "192.168.1.0/24", "203.0.113.7/32", "0.0.0.0/1", "2001:db8::/32"):
        assert not is_world(cidr), "%s is not the whole internet" % cidr


def test_invalid_text_is_false():
    """invalid input returns False instead of raising"""
    assert is_world("not-a-cidr") is False
    assert is_world("") is False


def test_any_world():
    """any_world accepts a list or a single string"""
    assert any_world(["10.0.0.0/8", "0.0.0.0/0"])
    assert any_world("::/0")
    assert not any_world(["10.0.0.0/8"])
    assert not any_world(None)

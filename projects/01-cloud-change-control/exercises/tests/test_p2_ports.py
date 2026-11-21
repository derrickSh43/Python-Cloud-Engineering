from changegate.policies.helpers import covers_all_ports, parse_port_range, range_includes_any


def test_single_port():
    """'22' and 443 become (22, 22) and (443, 443)"""
    assert parse_port_range("22") == (22, 22)
    assert parse_port_range(443) == (443, 443)


def test_port_range():
    """'8000-8080' becomes (8000, 8080), spaces allowed"""
    assert parse_port_range("8000-8080") == (8000, 8080)
    assert parse_port_range(" 20-25 ") == (20, 25)


def test_range_includes_any():
    """range_includes_any returns the ports inside the range, sorted"""
    assert range_includes_any((3000, 4000), [5432, 3389, 22, 3306]) == [3306, 3389]
    assert range_includes_any((443, 443), [22, 3389]) == []
    assert range_includes_any((22, 22), [22]) == [22]


def test_covers_all_ports():
    """covers_all_ports is True only for 0/1 to 65535"""
    assert covers_all_ports((0, 65535))
    assert covers_all_ports((1, 65535))
    assert not covers_all_ports((0, 1024))
    assert not covers_all_ports((22, 65535))

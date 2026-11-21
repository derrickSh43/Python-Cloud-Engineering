from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p03cp", "Model and test a rule", """
    Use classes, enums, dataclasses and tests together on a small, self-contained problem.
""", [
    Q("Which tool creates an isolated place to install packages for one project?",
      "python -m venv .venv", "pip freeze", "python -m pytest", "import venv"),
    C("""
        Define:

        - `class Direction(str, Enum)` with `INGRESS = "INGRESS"` and `EGRESS = "EGRESS"`
        - a frozen dataclass `FirewallRule` with fields `name: str`, `direction: Direction`,
          `sources: tuple = ()` and `ports: tuple = ()`
        - a class method `FirewallRule.from_dict(data)` that builds one from a dict like
          `{"name": "allow-ssh", "direction": "ingress", "source_ranges": ["0.0.0.0/0"], "ports": ["22"]}`.
          The direction is case-insensitive and defaults to INGRESS when missing; sources and ports are
          stored as tuples (missing → empty tuple)
        - a property `world_open` that is True when `"0.0.0.0/0"` is among the sources
    """, '''from dataclasses import dataclass
from enum import Enum

class Direction(str, Enum):
    INGRESS = "INGRESS"
    EGRESS = "EGRESS"

@dataclass(frozen=True)
class FirewallRule:
    name: str
    direction: Direction
    sources: tuple = ()
    ports: tuple = ()

    @classmethod
    def from_dict(cls, data):
        direction = Direction(str(data.get("direction") or "INGRESS").upper())
        return cls(data["name"], direction, tuple(data.get("source_ranges") or ()), tuple(data.get("ports") or ()))

    @property
    def world_open(self):
        return "0.0.0.0/0" in self.sources''',
      check="""
        import dataclasses
        r = FirewallRule.from_dict({"name": "allow-ssh", "direction": "ingress", "source_ranges": ["0.0.0.0/0"], "ports": ["22"]})
        assert r == FirewallRule("allow-ssh", Direction.INGRESS, ("0.0.0.0/0",), ("22",)), "got %r" % (r,)
        assert r.world_open is True
        e = FirewallRule.from_dict({"name": "out", "direction": "EGRESS"})
        assert e.direction is Direction.EGRESS and e.sources == () and e.world_open is False
        assert FirewallRule.from_dict({"name": "x"}).direction is Direction.INGRESS
        try:
            r.name = "changed"
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("FirewallRule should be frozen")
      """,
      require=["@dataclass", "Enum", "@classmethod", "@property"],
      hints=["Direction(\"INGRESS\") looks a member up by value - normalise with .upper() first.",
             'from_dict: direction = Direction(str(data.get("direction") or "INGRESS").upper())',
             'return cls(data["name"], direction, tuple(data.get("source_ranges") or ()), tuple(data.get("ports") or ()))']),
    C("""
        Here's a function and two broken versions of it. Write **test functions** (pytest style:
        names starting `test_`, using plain `assert`) that pass for the correct `is_world` and would catch
        both bugs. The checker runs your tests against all three versions.

        ```
        def is_world(cidr):            # correct
            return cidr.strip() in ("0.0.0.0/0", "::/0")
        ```

        Bug 1 forgets IPv6 (`::/0`). Bug 2 forgets to strip surrounding spaces.
        Write at least two test functions.
    """, '''def is_world(cidr):
    return cidr.strip() in ("0.0.0.0/0", "::/0")

def test_ipv4_and_ipv6():
    assert is_world("0.0.0.0/0")
    assert is_world("::/0")
    assert not is_world("10.0.0.0/8")

def test_spaces_are_ignored():
    assert is_world(" 0.0.0.0/0 ")''',
      starter='def is_world(cidr):\n    return cidr.strip() in ("0.0.0.0/0", "::/0")',
      check="""
        tests = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
        assert len(tests) >= 2, "write at least two functions named test_..."
        g = globals()
        def run_all():
            for t in tests:
                t()
        run_all()  # must pass with the correct version
        for label, bad in (("forgets IPv6", lambda c: c.strip() == "0.0.0.0/0"),
                           ("forgets to strip", lambda c: c in ("0.0.0.0/0", "::/0"))):
            original = g["is_world"]
            g["is_world"] = bad
            try:
                run_all()
            except AssertionError:
                pass
            else:
                raise AssertionError("your tests didn't catch the version that " + label)
            finally:
                g["is_world"] = original
      """,
      require=["def test_", "assert"],
      hints=["Each test is a function whose name starts with test_ and that uses assert.",
             "One test should check '::/0'; another should pass a CIDR with spaces around it.",
             'def test_ipv6():\n    assert is_world("::/0")\n\ndef test_spaces():\n    assert is_world(" 0.0.0.0/0 ")']),
])

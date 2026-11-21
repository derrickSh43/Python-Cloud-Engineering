from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p03l2", "Properties and class methods", [
    T("""
        **Properties: computed attributes**

        Some values are best *calculated* from other attributes rather than stored. `@property` makes a
        method look like an attribute - no brackets when you use it:

        ```
        class Change:
            def __init__(self, actions):
                self.actions = actions

            @property
            def is_replace(self):
                return set(self.actions) == {"delete", "create"}

        Change(["delete", "create"]).is_replace    # True - no ()
        ```

        A property always reflects the current data, so it can never get out of sync.
    """),
    Ex("""
        class Change:
            def __init__(self, actions, before=None, after=None):
                self.actions = actions
                self.before = before
                self.after = after

            @property
            def is_replace(self):
                return set(self.actions) == {"delete", "create"}

            @property
            def attributes(self):
                return (self.before if self.actions == ["delete"] else self.after) or {}

        delete = Change(["delete"], before={"bucket": "old"})
        print(delete.is_replace, delete.attributes)
        print(Change(["create"]).attributes)
    """),
    T("""
        **Class methods: alternative constructors**

        A normal method works on one object (`self`). A **class method** works on the class itself - it
        receives the class as `cls`. The most common use is an alternative way to build objects, often
        named `from_something`:

        ```
        class Rule:
            def __init__(self, port, cidr):
                self.port = port
                self.cidr = cidr

            @classmethod
            def from_text(cls, text):          # "22 from 0.0.0.0/0"
                port, _, cidr = text.split()
                return cls(int(port), cidr)
        ```

        `Rule.from_text("22 from 0.0.0.0/0")` - called on the class, not an object. Using `cls(...)`
        instead of `Rule(...)` means subclasses get objects of their own type.
    """),
    Ex("""
        class Rule:
            def __init__(self, port, cidr):
                self.port = port
                self.cidr = cidr

            @classmethod
            def from_text(cls, text):
                port, _, cidr = text.split()
                return cls(int(port), cidr)

            def __repr__(self):
                return f"Rule({self.port}, {self.cidr!r})"

        print(Rule.from_text("22 from 0.0.0.0/0"))
        print([Rule.from_text(t) for t in ["443 from 0.0.0.0/0", "5432 from 10.0.0.0/8"]])
    """, note="`port, _, cidr = ...` unpacks three values; `_` is a conventional name for one you don't need."),
    T("""
        **Static methods** (`@staticmethod`) take neither `self` nor `cls` - they're plain functions that
        live in the class for organisation. You'll see them less often; a module-level function usually
        does the job just as well.
    """),
    P("""
        class Size:
            def __init__(self, gib):
                self.gib = gib

            @property
            def mib(self):
                return self.gib * 1024

            @classmethod
            def from_mib(cls, mib):
                return cls(mib // 1024)

        s = Size.from_mib(4096)
        print(s.gib, s.mib)
    """),
    Q("What does `@property` change about how a method is used?",
      "It is read like an attribute, without brackets", "It runs only once and caches the result",
      "It can be called on the class instead of an object", "It becomes private"),
    C("""
        Write a class `PortRange` with attributes `low` and `high`, plus:

        - a property `size` - how many ports, inclusive (`high - low + 1`)
        - a class method `parse(text)` that accepts `"22"` or `"8000-8080"` and returns a `PortRange`

        ```
        PortRange.parse("8000-8080").size    # 81
        PortRange.parse("22").low            # 22
        ```
    """, '''class PortRange:
    def __init__(self, low, high):
        self.low = low
        self.high = high

    @property
    def size(self):
        return self.high - self.low + 1

    @classmethod
    def parse(cls, text):
        if "-" in text:
            low, high = text.split("-")
            return cls(int(low), int(high))
        return cls(int(text), int(text))''',
      check="""
        r = PortRange.parse("8000-8080")
        assert isinstance(r, PortRange), "parse should return a PortRange"
        assert (r.low, r.high) == (8000, 8080)
        assert r.size == 81, "size should be 81 (it's a property: no brackets)"
        single = PortRange.parse("22")
        assert (single.low, single.high, single.size) == (22, 22, 1)
        assert isinstance(PortRange.__dict__["size"], property), "make size a @property"
      """,
      require=["@property", "@classmethod"],
      hints=["__init__ stores low and high. size is a method decorated with @property.",
             "parse is decorated with @classmethod and takes cls first; return cls(low, high).",
             'if "-" in text:\n    low, high = text.split("-")\n    return cls(int(low), int(high))\nreturn cls(int(text), int(text))']),
], summary="""
    - `@property` turns a method into a computed attribute read without brackets.
    - `@classmethod` methods receive the class (`cls`); use them for alternative constructors
      (`Rule.from_text(...)`), returning `cls(...)`.
    - `@staticmethod` methods take neither self nor cls.
""")

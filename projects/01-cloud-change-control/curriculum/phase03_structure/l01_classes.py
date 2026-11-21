from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p03l1", "Classes and objects", [
    T("""
        **Your own types**

        A **class** is a blueprint for a new type of value. Each value made from it is an **object** (or
        *instance*) with its own data (**attributes**) and behaviour (**methods**):

        ```
        class Rule:
            def __init__(self, port, cidr):
                self.port = port
                self.cidr = cidr

            def is_world_open(self):
                return self.cidr == "0.0.0.0/0"

        ssh = Rule(22, "0.0.0.0/0")
        ssh.port               # 22
        ssh.is_world_open()    # True
        ```

        - `__init__` runs when you create an object; it sets up the attributes.
        - `self` is the object itself. Methods receive it automatically as their first parameter.
        - Calling the class (`Rule(22, ...)`) creates an object; the arguments go to `__init__`.
    """),
    Ex("""
        class Rule:
            def __init__(self, port, cidr):
                self.port = port
                self.cidr = cidr

            def is_world_open(self):
                return self.cidr == "0.0.0.0/0"

        rules = [Rule(22, "0.0.0.0/0"), Rule(443, "0.0.0.0/0"), Rule(22, "10.0.0.0/8")]
        for rule in rules:
            print(rule.port, rule.cidr, rule.is_world_open())
    """),
    T("""
        **Why not just dictionaries?**

        `{"port": 22, "cidr": "0.0.0.0/0"}` works, but nothing stops a typo like `rule["prot"]`, and the
        logic that belongs to a rule lives somewhere else. A class keeps **data and behaviour together**,
        and a misspelled attribute fails loudly with an AttributeError.
    """),
    P("""
        class Counter:
            def __init__(self):
                self.count = 0

            def add(self, n=1):
                self.count += n

        c = Counter()
        c.add()
        c.add(5)
        print(c.count)
    """),
    T("""
        **Readable objects: __repr__**

        Printing an object shows something unhelpful like `<__main__.Rule object at 0x...>`. A `__repr__`
        method returns the text Python should show instead:

        ```
        def __repr__(self):
            return f"Rule({self.port}, {self.cidr!r})"
        ```

        `{value!r}` inside an f-string uses the value's repr - strings get quotes, which makes the output
        unambiguous. Methods with double underscores on both sides ("dunder" methods) hook into Python's
        built-in behaviour.
    """),
    Ex("""
        class Rule:
            def __init__(self, port, cidr):
                self.port = port
                self.cidr = cidr

            def __repr__(self):
                return f"Rule({self.port}, {self.cidr!r})"

        print(Rule(22, "0.0.0.0/0"))
        print([Rule(80, "10.0.0.0/8"), Rule(443, "0.0.0.0/0")])
    """),
    T("""
        **Inheritance**

        A class can **inherit** from another, getting all its attributes and methods and adding or
        overriding some. You already did this: `class PlanError(Exception)` inherits everything that makes
        an exception work.

        ```
        class Policy:
            severity = "MEDIUM"                  # a class attribute, shared by all instances
            def describe(self):
                return f"{type(self).__name__} ({self.severity})"

        class PublicBucket(Policy):
            severity = "HIGH"                    # overrides the parent's value
        ```

        ChangeGate's 14 policies all inherit from one `Policy` base class - you'll build that in Phase 4.
    """),
    Ex("""
        class Policy:
            severity = "MEDIUM"
            def describe(self):
                return f"{type(self).__name__} ({self.severity})"

        class PublicBucket(Policy):
            severity = "HIGH"

        class MissingTags(Policy):
            pass

        for policy in [PublicBucket(), MissingTags()]:
            print(policy.describe(), isinstance(policy, Policy))
    """),
    Q("Inside a method, how do you read the object's `port` attribute?", "self.port", "port", "Rule.port", "this.port"),
    C("""
        Write a class `Bucket` whose `__init__` takes `name` and `public` (a bool) and stores them as
        attributes. Add a method `label()` that returns `"<name> (PUBLIC)"` when public, otherwise just the
        name.

        ```
        Bucket("logs", False).label()    # "logs"
        Bucket("site", True).label()     # "site (PUBLIC)"
        ```
    """, 'class Bucket:\n    def __init__(self, name, public):\n        self.name = name\n        self.public = public\n\n    def label(self):\n        if self.public:\n            return f"{self.name} (PUBLIC)"\n        return self.name',
      check="""
        b = Bucket("logs", False)
        assert b.name == "logs" and b.public is False, "store name and public as attributes"
        assert b.label() == "logs", "got %r" % b.label()
        assert Bucket("site", True).label() == "site (PUBLIC)"
      """,
      require=["class Bucket", "def __init__", "self"],
      hints=["__init__(self, name, public) sets self.name = name and self.public = public.",
             "label(self) checks self.public and returns an f-string.",
             'def label(self):\n    if self.public:\n        return f"{self.name} (PUBLIC)"\n    return self.name']),
    C("""
        Write a class `Inventory` that keeps a list of resource addresses:

        - `__init__` starts with an empty list in `self.addresses`
        - `add(address)` appends an address
        - `count_type(prefix)` returns how many addresses start with `prefix + "."`

        ```
        inv = Inventory()
        inv.add("aws_instance.web"); inv.add("aws_instance.db"); inv.add("aws_s3_bucket.logs")
        inv.count_type("aws_instance")   # 2
        ```
    """, 'class Inventory:\n    def __init__(self):\n        self.addresses = []\n\n    def add(self, address):\n        self.addresses.append(address)\n\n    def count_type(self, prefix):\n        return sum(1 for a in self.addresses if a.startswith(prefix + "."))',
      check="""
        inv = Inventory()
        assert inv.addresses == [], "start with an empty list"
        for a in ("aws_instance.web", "aws_instance.db", "aws_s3_bucket.logs", "aws_instance_profile.x"):
            inv.add(a)
        assert inv.count_type("aws_instance") == 2, "got %r - remember the dot, so aws_instance_profile doesn't count" % inv.count_type("aws_instance")
        assert Inventory().addresses is not inv.addresses, "each Inventory needs its own list"
      """,
      require=["class Inventory"],
      hints=["Create the list inside __init__ (self.addresses = []) so each object has its own.",
             'count_type can loop and count addresses where a.startswith(prefix + ".").',
             'return sum(1 for a in self.addresses if a.startswith(prefix + "."))']),
], summary="""
    - `class Name:` defines a type; `Name(args)` creates an object and runs `__init__(self, args)`.
    - `self.x = ...` sets an attribute; methods are functions in the class that take `self` first.
    - `__repr__` controls how an object prints; `{value!r}` in f-strings uses repr.
    - `class Child(Parent):` inherits; class attributes are shared and can be overridden.
""")

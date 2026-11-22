from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p03l4", "Dataclasses and type hints", [
    T("""
        **Type hints**

        You can annotate what types a variable, parameter or return value should hold:

        ```
        def plan_digest(raw: bytes) -> str:
            ...

        address: str = "aws_s3_bucket.logs"
        before: dict | None = None        # a dict, or None
        changes: list[str] = []
        ```

        Python **doesn't enforce** hints at runtime - they're documentation that editors and tools
        (like mypy) check for you. `X | None` means "an X or None". You've seen hints all over the
        ChangeGate stubs; now you'll write them.
    """),
    T("""
        **Dataclasses**

        Classes that mostly hold data need a lot of repetitive code: `__init__` to store each field,
        `__repr__` to print them, `__eq__` to compare them. The `@dataclass` decorator writes all of
        that from a list of annotated fields:

        ```
        from dataclasses import dataclass

        @dataclass
        class Finding:
            policy_id: str
            severity: str
            address: str
            message: str
            remediation: str = ""         # a default makes the field optional
        ```

        Fields without defaults must come before fields with defaults.
    """),
    Ex("""
        from dataclasses import dataclass

        @dataclass
        class Finding:
            policy_id: str
            severity: str
            address: str
            message: str
            remediation: str = ""

        f = Finding("AWS-S3-PUBLIC-ACL", "HIGH", "aws_s3_bucket_acl.assets", "bucket ACL is public-read")
        print(f)
        print(f.address)
        print(f == Finding("AWS-S3-PUBLIC-ACL", "HIGH", "aws_s3_bucket_acl.assets", "bucket ACL is public-read"))
    """, note="The generated __repr__ and __eq__ come for free."),
    T("""
        **frozen=True: values that can't change**

        `@dataclass(frozen=True)` makes objects **immutable**: assigning to a field raises
        `FrozenInstanceError`. For a security tool this matters - once a finding or evaluation is created,
        nothing downstream can quietly alter it. Frozen objects can also be put in sets and used as dict keys.
    """),
    Ex("""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Finding:
            policy_id: str
            message: str

        f = Finding("CG-DESTROY-STATEFUL", "database will be deleted")
        f.message = "nothing to see here"
    """, error_ok=True),
    T("""
        **Mutable defaults: field(default_factory=...)**

        A default like `tags: dict = {}` would be **shared** by every object - a classic bug. Dataclasses
        refuse it outright. Use `field(default_factory=dict)` so each object gets a fresh one:

        ```
        from dataclasses import dataclass, field

        @dataclass(frozen=True)
        class ResourceChange:
            address: str
            after_unknown: dict = field(default_factory=dict)
        ```

        Dataclasses can have methods and properties like any class.
    """),
    Ex("""
        from dataclasses import dataclass, field, fields

        @dataclass(frozen=True)
        class Change:
            address: str
            actions: tuple = ()
            after_unknown: dict = field(default_factory=dict)

            @property
            def is_unknown_anything(self):
                return any(self.after_unknown.values())

        a = Change("aws_s3_bucket.logs", ("create",), {"arn": True})
        b = Change("aws_s3_bucket.tmp")
        print(a.is_unknown_anything, b.is_unknown_anything)
        print(b.after_unknown is Change("x").after_unknown)
        print([f.name for f in fields(Change)])
    """),
    P("""
        from dataclasses import dataclass, replace

        @dataclass(frozen=True)
        class Approval:
            approver: str
            signature: str = ""

        a = Approval("alice")
        signed = replace(a, signature="abc123")
        print(a.signature == "", signed.signature, signed.approver)
    """, explain="dataclasses.replace makes a modified COPY - the way to 'change' a frozen object. "
                 "You'll use it to sign approvals in Phase 5."),
    Q("What happens when this runs?",
      "It raises dataclasses.FrozenInstanceError", "It prints HIGH", "It prints LOW",
      "It silently ignores the assignment",
      code="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Finding:
            severity: str

        f = Finding("LOW")
        f.severity = "HIGH"
        print(f.severity)
      """, explain="A frozen dataclass refuses assignment after creation. Use dataclasses.replace for a changed copy."),
    C("""
        Define a frozen dataclass `Tagged` with fields `address: str` and `tags: dict` (default: a fresh
        empty dict for each object), and a method `missing(required)` that returns the list of keys in
        `required` that aren't in `tags`, in order.

        ```
        Tagged("aws_s3_bucket.a", {"owner": "x"}).missing(["owner", "environment"])   # ["environment"]
        ```
    """, 'from dataclasses import dataclass, field\n\n@dataclass(frozen=True)\nclass Tagged:\n    address: str\n    tags: dict = field(default_factory=dict)\n\n    def missing(self, required):\n        return [key for key in required if key not in self.tags]',
      check="""
        import dataclasses
        assert dataclasses.is_dataclass(Tagged), "use @dataclass(frozen=True)"
        t = Tagged("aws_s3_bucket.a", {"owner": "x"})
        assert t.missing(["owner", "environment"]) == ["environment"]
        assert Tagged("b.c").tags == {} and Tagged("b.c").tags is not Tagged("d.e").tags, "use field(default_factory=dict)"
        try:
            t.address = "other"
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("Tagged should be frozen")
      """,
      require=["@dataclass", "default_factory"],
      hints=["from dataclasses import dataclass, field; decorate with @dataclass(frozen=True).",
             "tags: dict = field(default_factory=dict)",
             "def missing(self, required):\n    return [key for key in required if key not in self.tags]"]),
    B("p3-resource-change", intro="Now the real thing. The starter has a placeholder `class ResourceChange` - "
                                 "replace the whole class with your dataclass."),
    B("p3-finding"),
    B("p3-evaluation", intro="The result of evaluating a whole plan. Its `to_dict()` is what the JSON report "
                            "will print in Phase 6."),
], summary="""
    - Type hints: `def f(raw: bytes) -> str`, `x: dict | None = None`, `list[str]`. Not enforced at runtime.
    - `@dataclass` generates `__init__`, `__repr__`, `__eq__` from annotated fields; defaults go last.
    - `@dataclass(frozen=True)` makes objects immutable; `dataclasses.replace(obj, field=v)` makes a modified copy.
    - Mutable defaults need `field(default_factory=dict)` (or list).
    - `dataclasses.fields(cls)` lists the fields.
""")

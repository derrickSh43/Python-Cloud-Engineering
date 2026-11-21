from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l3", "A plugin framework", [
    T("""
        **The design**

        ChangeGate has 14 policies and teams will want to add their own. Every policy should look the same
        from the outside so the engine can run them without knowing any of them by name:

        - an **id** (`AWS-SG-OPEN-INGRESS`), a **title**, a default **severity**
        - which **resource types** and **actions** it cares about
        - a `check(change)` method that **yields** findings

        A **base class** defines that shape. Each policy is a small subclass. A **registry** collects them,
        and a **decorator** adds each one to the registry automatically.
    """),
    T("""
        **Abstract base classes**

        An abstract base class (ABC) declares methods that subclasses **must** implement. Python refuses to
        create an object of a class that still has abstract methods:

        ```
        from abc import ABC, abstractmethod

        class Policy(ABC):
            @abstractmethod
            def check(self, change):
                \"\"\"Yield a Finding for every problem in this change.\"\"\"
        ```

        Forgetting to write `check` in a new policy becomes an immediate, clear error instead of a policy
        that silently never fires.
    """),
    Ex("""
        from abc import ABC, abstractmethod

        class Policy(ABC):
            @abstractmethod
            def check(self, change):
                ...

        class Forgetful(Policy):
            pass

        class Good(Policy):
            def check(self, change):
                yield "a finding"

        print(list(Good().check(None)))
        try:
            Forgetful()
        except TypeError as e:
            print("TypeError:", e)
    """),
    T("""
        **Class attributes and ClassVar**

        Values that describe the policy *as a type* - its id, title, severity, resource types - are **class
        attributes**, written in the class body. Every instance shares them, and subclasses override them.
        Instance attributes (set on `self` in `__init__`) hold per-object state like settings.

        `ClassVar[...]` in a type hint documents "this is a class attribute, not a per-instance field":

        ```
        class Policy(ABC):
            id: ClassVar[str]
            severity: ClassVar[Severity]
            resource_types: ClassVar[frozenset[str]] = frozenset()   # empty = all types
        ```

        Inside methods you read them through `self` (`self.resource_types`) - Python looks on the instance
        first, then the class.
    """),
    Ex("""
        class Policy:
            resource_types = frozenset()             # empty = every type
            def applies_to(self, resource_type):
                return not self.resource_types or resource_type in self.resource_types

        class BucketPolicy(Policy):
            resource_types = frozenset({"aws_s3_bucket", "google_storage_bucket"})

        print(Policy().applies_to("aws_instance"))
        print(BucketPolicy().applies_to("aws_instance"), BucketPolicy().applies_to("aws_s3_bucket"))
    """),
    T("""
        **Decorators**

        In Python, functions and classes are values: you can pass them around and return them. A
        **decorator** is a function that takes a function or class and returns one (usually the same). The
        `@` syntax applies it at definition time:

        ```
        _REGISTRY = {}

        def register(cls):
            _REGISTRY[cls.id] = cls
            return cls                 # without this, the class name would become None!

        @register
        class PublicBucket(Policy):    # same as: PublicBucket = register(PublicBucket)
            id = "AWS-S3-PUBLIC-ACL"
        ```

        You've already used decorators: `@property`, `@classmethod`, `@dataclass`.
    """),
    Ex("""
        _REGISTRY = {}

        def register(cls):
            _REGISTRY[cls.id] = cls
            return cls

        @register
        class A:
            id = "TEST-A"

        @register
        class B:
            id = "TEST-B"

        print(sorted(_REGISTRY), _REGISTRY["TEST-A"] is A)
    """),
    T("""
        **Importing by name and failing closed**

        Policies register themselves when their module is imported. `importlib.import_module("name")` imports
        a module from a string - which is how config can add a team's own policy module:
        `extra_modules = ["acme.policies"]`.

        Finally, the runner. Normally you catch **specific** exceptions. Here is the rare case where catching
        `Exception` broadly is right: if one policy crashes on odd data, the engine must not crash - but it
        also must not **skip the rule**. A security gate **fails closed**: a crashed policy becomes a CRITICAL
        finding, which blocks the plan until someone looks.
    """),
    Ex("""
        def run(checks, value):
            for name, check in checks:
                try:
                    yield from check(value)
                except Exception as e:
                    yield f"CRITICAL {name}: policy raised {type(e).__name__}: {e}"

        def ok(v):
            yield f"ok saw {v}"

        def broken(v):
            raise KeyError("ingress")

        print(list(run([("ok", ok), ("broken", broken), ("ok-again", ok)], "sg-1")))
    """, note="`yield from other()` re-yields everything another generator produces."),
    Q("A policy's `check` raises an exception on unusual data. What should a security gate do?",
      "Report a CRITICAL finding so the plan is blocked until someone investigates",
      "Skip that policy and carry on", "Crash the whole run with a traceback", "Treat the change as safe"),
    C("""
        Build a mini framework:

        - an abstract base class `Rule(ABC)` with an abstract method `check(value)`
        - a decorator `register(cls)` that stores the class in `RULES[cls.id]` and returns the class
        - two registered rules: `NoSpaces` (id `"NO-SPACES"`) yields `"contains spaces"` when the value has a
          space; `Lowercase` (id `"LOWERCASE"`) yields `"not lowercase"` when `value != value.lower()`
        - `run_rules(value)` returning a list of `"<id>: <message>"` for every rule (in id order)
    """, '''from abc import ABC, abstractmethod

RULES = {}

def register(cls):
    RULES[cls.id] = cls
    return cls

class Rule(ABC):
    @abstractmethod
    def check(self, value):
        ...

@register
class NoSpaces(Rule):
    id = "NO-SPACES"
    def check(self, value):
        if " " in value:
            yield "contains spaces"

@register
class Lowercase(Rule):
    id = "LOWERCASE"
    def check(self, value):
        if value != value.lower():
            yield "not lowercase"

def run_rules(value):
    return ["%s: %s" % (rid, msg) for rid in sorted(RULES) for msg in RULES[rid]().check(value)]''',
      check="""
        assert set(RULES) == {"NO-SPACES", "LOWERCASE"}, "register both rules"
        assert run_rules("My Bucket") == ["LOWERCASE: not lowercase", "NO-SPACES: contains spaces"], "got %r" % (run_rules("My Bucket"),)
        assert run_rules("logs") == []
        assert NoSpaces is not None, "register must return the class"
        try:
            Rule()
        except TypeError:
            pass
        else:
            raise AssertionError("Rule should be abstract (inherit ABC, @abstractmethod check)")
      """,
      require=["ABC", "@abstractmethod", "@register", "yield"],
      hints=["Start with RULES = {} and a register function that stores and returns cls.",
             "Each rule: @register above the class, an id class attribute, and a check generator.",
             'run_rules: ["%s: %s" % (rid, msg) for rid in sorted(RULES) for msg in RULES[rid]().check(value)]']),
    B("p4-policy-base", intro="ChangeGate's real `Policy` base class in `policies/base.py`. `__init__` is written; "
                             "you write how a policy decides whether it applies and how it builds findings."),
    B("p4-registry", intro="The decorator and the loader that builds policies from config."),
    B("p4-run-policies", intro="The engine loop - and it must fail closed."),
], summary="""
    - Abstract base class: `class Policy(ABC)` + `@abstractmethod def check(...)`; subclasses must implement it.
    - Class attributes describe the type (id, severity, resource_types); read them via `self`.
      `ClassVar[...]` documents them.
    - A decorator takes and returns a class/function: `@register` = `X = register(X)`. Always return it.
    - `importlib.import_module("pkg.mod")` imports by name. `yield from gen` re-yields another generator.
    - Fail closed: a crashing policy becomes a CRITICAL finding, never a skipped rule.
""")

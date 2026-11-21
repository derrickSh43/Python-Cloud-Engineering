from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p03l5", "Modules, packages and registries", [
    T("""
        **Modules and packages**

        Every `.py` file is a **module**. A folder of modules with an `__init__.py` file is a **package**.
        ChangeGate is a package:

        ```
        changegate/
            __init__.py         makes the folder a package (holds __version__)
            models.py           Action, Severity, ResourceChange, Finding, ...
            plan_parser.py
            providers.py
            policies/           a sub-package
                __init__.py
                base.py
                aws.py
        ```

        From outside you import with dots: `from changegate.models import Severity`,
        `import changegate.policies.aws`.
    """),
    T("""
        **Relative imports**

        Inside a package, modules import each other **relative** to their own location:

        ```
        # in changegate/plan_parser.py
        from .models import Action, ResourceChange     # . = this package
        from . import providers

        # in changegate/policies/aws.py
        from ..models import Finding, Severity        # .. = the parent package
        from .base import Policy, register            # a sibling module
        ```

        Relative imports keep a package self-contained: rename or move the folder and nothing breaks.
    """),
    T("""
        **What happens on import**

        The first time a module is imported, Python runs it **top to bottom**, then caches it - a second
        import doesn't run it again. Any code at the top level (not inside a function) runs at import
        time. That's how a registry fills itself in: module-level code calls `register(...)`.

        Code you only want when a file is run directly, not imported, goes under:

        ```
        if __name__ == "__main__":
            main()
        ```
    """),
    T("""
        **Registries**

        A **registry** is a dictionary that maps names to objects, so other code can look things up
        instead of hard-coding them:

        ```
        _REGISTRY = {}

        def register(provider):
            _REGISTRY[provider.key] = provider

        def lookup(name):
            return _REGISTRY.get(name)
        ```

        ChangeGate keeps everything cloud-specific in a provider registry. To support a new cloud later you
        register one more provider - no `if cloud == "aws"` scattered through the code. A leading
        underscore (`_REGISTRY`) signals "internal: use the functions, not the dict directly".
    """),
    Ex("""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Provider:
            key: str
            cloud: str
            tag_attributes: tuple

        _REGISTRY = {}

        def register(provider):
            _REGISTRY[provider.key] = provider

        def lookup(name):
            return _REGISTRY.get(name.rsplit("/", 1)[-1])

        register(Provider("aws", "aws", ("tags_all", "tags")))
        register(Provider("google", "gcp", ("labels",)))

        print(lookup("registry.terraform.io/hashicorp/google"))
        print(lookup("registry.terraform.io/hashicorp/azurerm"))
        print(sorted(_REGISTRY))
    """, note="`rsplit(\"/\", 1)` splits once, from the right - the last path segment is [-1]."),
    P("""
        names = {}
        def add(key, value):
            names[key] = value
        add("aws", 1)
        add("google", 2)
        add("aws", 3)
        print(names)
    """, explain="Registering the same key again replaces the earlier value."),
    T("""
        **frozenset and set union**

        A `frozenset` is an immutable set - safe to use as a default or a class attribute. To combine sets
        from many sources, start with an empty set and union each one in with `|=`:

        ```
        types = set()
        for provider in _REGISTRY.values():
            types |= provider.stateful_types
        return frozenset(types)
        ```
    """),
    Q("In `changegate/policies/gcp.py`, what does `from ..models import Finding` import from?",
      "changegate/models.py", "changegate/policies/models.py", "a models package installed with pip",
      "the current working directory"),
    C("""
        Build a tiny registry. Write `register(name, func)` that stores `func` under `name` in a module-level
        dict `CHECKS`, and `run_all(value)` that calls every registered function with `value` and returns a
        dict of `{name: result}`, in registration order.

        ```
        register("upper", str.upper)
        register("length", len)
        run_all("prod")      # {"upper": "PROD", "length": 4}
        ```
    """, 'CHECKS = {}\n\ndef register(name, func):\n    CHECKS[name] = func\n\ndef run_all(value):\n    return {name: func(value) for name, func in CHECKS.items()}',
      check="""
        CHECKS.clear()
        register("upper", str.upper)
        register("length", len)
        assert run_all("prod") == {"upper": "PROD", "length": 4}, "got %r" % (run_all("prod"),)
        assert list(run_all("x")) == ["upper", "length"], "keep registration order"
      """,
      require=["CHECKS"],
      hints=["CHECKS = {} at the top; register stores CHECKS[name] = func.",
             "Functions are values: you can store them and call them later with func(value).",
             "def run_all(value):\n    return {name: func(value) for name, func in CHECKS.items()}"]),
    B("p3-providers", intro="ChangeGate's provider registry. The `Provider` dataclass, the AWS and Google entries "
                           "and `register()` are written for you; you write the lookups."),
], summary="""
    - A module is a `.py` file; a package is a folder with `__init__.py`. Import with dots.
    - Relative imports inside a package: `from .models import X` (same package), `from ..models import X` (parent).
    - Modules run top-to-bottom once, on first import. `if __name__ == "__main__":` for script-only code.
    - Registries: a dict of name → object filled by `register()`, read by lookup functions.
    - `frozenset` is an immutable set; combine sets with `|=`.
""")

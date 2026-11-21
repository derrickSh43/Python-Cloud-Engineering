from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l7", "Functions", [
    T("""
        **Naming a piece of logic**

        A **function** is a named, reusable block of code. You've used built-in ones (`print`, `len`,
        `sorted`); now you'll write your own:

        ```
        def describe(name, region):
            print(f"{name} runs in {region}")

        describe("api", "us-east-1")
        describe("worker", "eu-west-1")
        ```

        `def`, the name, **parameters** in brackets, a colon, then an indented body. Defining a function
        doesn't run it - **calling** it with brackets does. The values passed in are **arguments**.
    """),
    Ex("""
        def describe(name, region):
            print(f"{name} runs in {region}")

        print("before")
        describe("api", "us-east-1")
        describe("worker", "eu-west-1")
    """),
    T("""
        **return hands a value back**

        `print` shows a value to a human. `return` gives a value back to the **code** that called the
        function, so it can be stored, compared or passed on. Every policy you write in ChangeGate is a
        function that returns its findings.

        ```
        def is_world_open(cidr):
            return cidr == "0.0.0.0/0"

        if is_world_open("0.0.0.0/0"):
            print("open to the internet")
        ```

        `return` ends the function immediately. A function with no `return` gives back `None`.
    """),
    Ex("""
        def monthly_cost(hourly, hours=730):
            return round(hourly * hours, 2)

        small = monthly_cost(0.0116)
        large = monthly_cost(0.1664)
        print(small, large, "difference:", round(large - small, 2))
        print(monthly_cost(0.0116, 24))
    """, note="`hours=730` is a **default**: used when the caller doesn't pass that argument."),
    P("""
        def shout(text):
            print(text.upper())

        result = shout("deploy")
        print(result)
    """, explain="shout prints DEPLOY, but it has no return statement, so result is None."),
    T("""
        **Arguments by name, and docstrings**

        Arguments can be passed by name, which makes calls self-explanatory: `monthly_cost(0.0116, hours=24)`.

        The first line of a function can be a string describing what it does - a **docstring**. Good
        docstrings say what goes in and what comes out:

        ```
        def provider_key(provider_name):
            \"\"\"'registry.terraform.io/hashicorp/aws' -> 'aws'.\"\"\"
            return provider_name.split("/")[-1]
        ```
    """),
    T("""
        **Scope**

        Variables created inside a function are **local**: they exist only while it runs and can't be
        seen outside. Pass values in as parameters and get results out with `return` - don't rely on
        variables from elsewhere. Functions that only use their inputs are easy to test, which matters a
        lot from Phase 3 onward.
    """),
    Ex("""
        def add_tag(tags, key, value):
            result = dict(tags)       # a copy, so the caller's dict isn't changed
            result[key] = value
            return result

        original = {"owner": "platform"}
        updated = add_tag(original, "environment", "prod")
        print(original)
        print(updated)
    """),
    Q("What does `def f(x): return x * 2` followed by `f(f(3))` give?", "12", "6", "9", "None"),
    C("""
        Write a function `is_sensitive(port)` that returns `True` if the port is 22, 3389 or 5432, and
        `False` otherwise.
    """, "def is_sensitive(port):\n    return port in [22, 3389, 5432]",
      check="""
        assert is_sensitive(22) is True, "is_sensitive(22) should be True"
        assert is_sensitive(3389) is True and is_sensitive(5432) is True
        assert is_sensitive(443) is False, "is_sensitive(443) should be False"
        assert is_sensitive(0) is False
      """,
      require=["def is_sensitive", "return"],
      hints=["`port in [22, 3389, 5432]` is already True or False.",
             "def is_sensitive(port):\n    return port in [22, 3389, 5432]"]),
    C("""
        Write `address(resource_type, name, module=None)` that returns the Terraform address:

        - `address("aws_s3_bucket", "logs")` → `"aws_s3_bucket.logs"`
        - `address("aws_s3_bucket", "logs", "module.storage")` → `"module.storage.aws_s3_bucket.logs"`
    """, 'def address(resource_type, name, module=None):\n    base = f"{resource_type}.{name}"\n    if module:\n        return f"{module}.{base}"\n    return base',
      check="""
        assert address("aws_s3_bucket", "logs") == "aws_s3_bucket.logs", "got %r" % address("aws_s3_bucket", "logs")
        assert address("aws_s3_bucket", "logs", "module.storage") == "module.storage.aws_s3_bucket.logs"
        assert address("google_compute_disk", "data", module=None) == "google_compute_disk.data"
      """,
      require=["def address", "return"],
      hints=["Build the base address with an f-string first.",
             "If module was given (it isn't None), put it in front with another dot.",
             'base = f"{resource_type}.{name}"\nif module:\n    return f"{module}.{base}"\nreturn base']),
    C("""
        Write `summarize(actions)` that takes a list of action strings and **returns** a string like:

        ```
        summarize(["create", "create", "delete"])   # "2 to add, 0 to change, 1 to destroy"
        ```

        `"create"` counts as add, `"update"` as change, `"delete"` as destroy. Ignore anything else.
    """, '''def summarize(actions):
    add = change = destroy = 0
    for action in actions:
        if action == "create":
            add += 1
        elif action == "update":
            change += 1
        elif action == "delete":
            destroy += 1
    return f"{add} to add, {change} to change, {destroy} to destroy"''',
      check="""
        assert summarize(["create", "create", "delete"]) == "2 to add, 0 to change, 1 to destroy", "got %r" % summarize(["create", "create", "delete"])
        assert summarize([]) == "0 to add, 0 to change, 0 to destroy"
        assert summarize(["update", "no-op", "update"]) == "0 to add, 2 to change, 0 to destroy"
      """,
      require=["def summarize", "return"],
      hints=["Keep three counters, update them in a loop, then build the string with an f-string.",
             "`add = change = destroy = 0` sets all three to 0 at once.",
             'return f"{add} to add, {change} to change, {destroy} to destroy"']),
], summary="""
    - `def name(params):` + indented body. Defining doesn't run it; `name(args)` calls it.
    - `return value` hands a result back (and ends the function). No return → `None`.
    - Defaults: `def f(x, hours=730)`. Call by name: `f(1, hours=24)`. Docstring = first-line string.
    - Variables inside a function are local. Pass data in through parameters, out through return.
""")

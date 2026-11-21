from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l8", "Reading errors and debugging", [
    T("""
        **Errors are information**

        When Python stops with an error it prints a **traceback**. Read it from the **bottom up**:

        - The **last line** says what went wrong: the error type and a message.
        - The lines above say **where**: file, line number, and the code on that line.

        Experienced engineers aren't people who don't get errors - they're people who read them carefully.
    """),
    Ex("""
        def get_owner(tags):
            return tags["owner"]

        print(get_owner({"owner": "platform"}))
        print(get_owner({"environment": "dev"}))
    """, note="The first call works. The second raises KeyError: 'owner' inside get_owner.", error_ok=True),
    T("""
        **The errors you'll meet most**

        | error | usual cause |
        |---|---|
        | `SyntaxError` | missing colon, quote or bracket |
        | `IndentationError` | inconsistent spaces at the start of lines |
        | `NameError` | a misspelled variable, or one used before it's created |
        | `TypeError` | the wrong type: `"port " + 22`, or calling a function with the wrong arguments |
        | `KeyError` | a dictionary key that doesn't exist |
        | `IndexError` | a list position that doesn't exist (`items[5]` on a 3-item list) |
        | `AttributeError` | a method the value doesn't have: `None.lower()`, or a typo like `.uper()` |
        | `ValueError` | right type, wrong value: `int("eighty")` |
    """),
    Ex("""
        tags = None
        print(tags.get("owner"))
    """, note="`None` has no methods. This happens when data you expected is missing - check for None first.",
       error_ok=True),
    Ex("""
        ports = [22, 443]
        print(ports[2])
    """, note="Positions start at 0, so a 2-item list has positions 0 and 1.", error_ok=True),
    Q("`int(\"eighty\")` raises which error?", "ValueError", "TypeError", "NameError", "KeyError",
      explain="The type (a string) is acceptable to int(), but this particular value can't be converted."),
    Q("`regoin = \"us-east-1\"` then `print(region)` raises...", "NameError", "KeyError", "SyntaxError",
      "AttributeError", explain="The variable was created with a typo, so `region` doesn't exist."),
    T("""
        **Debugging: a method, not luck**

        1. Read the last line of the error. What type? What message?
        2. Find the line it points to. What values are involved?
        3. Add a `print()` just before that line to see the actual values - they're often not what you assumed.
        4. Make one change, run again. Repeat.

        Printing values is the oldest debugging technique and still one of the best.
    """),
    P("""
        entries = [{"type": "aws_s3_bucket"}, {"name": "web"}]
        for entry in entries:
            print(entry.get("type", "unknown"))
    """, explain="The second dictionary has no 'type' key, so .get returns the default instead of raising."),
    C("""
        This code is meant to print each instance's size in upper case, but it crashes on the second
        instance because its `size` is missing (`None`). Fix it so missing sizes print `UNKNOWN`:

        ```output
        T3.MICRO
        UNKNOWN
        M5.LARGE
        ```
    """, 'instances = [{"size": "t3.micro"}, {"size": None}, {"size": "m5.large"}]\nfor instance in instances:\n    size = instance["size"]\n    if size is None:\n        print("UNKNOWN")\n    else:\n        print(size.upper())',
      starter='instances = [{"size": "t3.micro"}, {"size": None}, {"size": "m5.large"}]\nfor instance in instances:\n    size = instance["size"]\n    print(size.upper())',
      require=["None"],
      hints=["The crash is AttributeError: None has no .upper(). Check for None before calling it.",
             'if size is None:\n    print("UNKNOWN")\nelse:\n    print(size.upper())']),
    C("""
        This function should total the disk sizes, but the sizes arrive as text and it raises a
        TypeError. Fix the body so `total_size(["20", "100", "8"])` returns the number `128`.
    """, 'def total_size(sizes):\n    total = 0\n    for size in sizes:\n        total += int(size)\n    return total',
      starter='def total_size(sizes):\n    total = 0\n    for size in sizes:\n        total += size\n    return total',
      check="""
        assert total_size(["20", "100", "8"]) == 128, "got %r" % (total_size(["20", "100", "8"]),)
        assert total_size([]) == 0
      """,
      hints=["`0 + \"20\"` is the TypeError: an int plus a str.",
             "Convert each size with int(size) before adding it.",
             "total += int(size)"]),
    C("""
        One last one, putting several bugs together. Fix this code so it prints:

        ```output
        logs: 2 tags
        web: 0 tags
        ```
    """, 'resources = [{"name": "logs", "tags": {"owner": "a", "env": "b"}}, {"name": "web"}]\nfor resource in resources:\n    tags = resource.get("tags", {})\n    print(f"{resource[\'name\']}: {len(tags)} tags")',
      starter='resources = [{"name": "logs", "tags": {"owner": "a", "env": "b"}}, {"name": "web"}]\nfor resource in resources\n    tags = resource["tags"]\n    print(f"{resource[\'name\']}: {len(tags)} tags")',
      hints=["First a SyntaxError: the for line needs a colon at the end.",
             "Then a KeyError: the second resource has no 'tags'. Use resource.get(\"tags\", {}).",
             'for resource in resources:\n    tags = resource.get("tags", {})']),
], summary="""
    - Read tracebacks bottom-up: the last line is *what*, the lines above are *where*.
    - Common errors: SyntaxError, IndentationError, NameError, TypeError, KeyError, IndexError,
      AttributeError (often on `None`), ValueError.
    - Debug with a method: read the error, find the line, print the actual values, change one thing, rerun.
    - Guard against missing data: `.get(key, default)`, `if value is None:`.
""")

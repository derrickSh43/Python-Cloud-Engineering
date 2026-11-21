from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l4", "Making decisions", [
    T("""
        **Comparisons give booleans**

        | operator | meaning |
        |---|---|
        | `==` | equal (two `=` signs: one `=` assigns!) |
        | `!=` | not equal |
        | `<` `<=` `>` `>=` | ordering |
        | `in` | is contained in (`"prod" in "prod-db"` is `True`) |

        Each comparison produces `True` or `False`.
    """),
    Ex("""
        port = 22
        print(port == 22)
        print(port != 443)
        print(port < 1024)
        print("0.0.0.0/0" == "0.0.0.0/0")
        print("aws" in "registry.terraform.io/hashicorp/aws")
    """),
    T("""
        **if, elif, else**

        ```
        if port == 22:
            print("SSH")
        elif port == 3389:
            print("RDP")
        else:
            print("something else")
        ```

        - The line ends with a colon `:`.
        - The lines that belong to it are **indented** by 4 spaces. Indentation isn't decoration in
          Python - it decides which lines run.
        - Python checks each condition top to bottom and runs only the **first** block that matches.
          `else` runs when none did. `elif` and `else` are optional.
    """),
    Ex("""
        action = "delete"
        if action == "create":
            print("new resource")
        elif action == "delete":
            print("resource will be destroyed!")
        else:
            print("change in place")
        print("this line always runs - it isn't indented")
    """),
    P("""
        count = 7
        if count > 10:
            print("large")
        elif count > 5:
            print("medium")
        elif count > 0:
            print("small")
        else:
            print("none")
    """, explain="Only the first matching branch runs, even though `count > 0` is also true."),
    T("""
        **Combining conditions: and, or, not**

        - `a and b` - both must be true
        - `a or b` - at least one must be true
        - `not a` - flips True and False

        ```
        if cidr == "0.0.0.0/0" and port == 22:
            print("SSH is open to the whole internet")
        ```
    """),
    P("""
        encrypted = False
        public = True
        print(public and not encrypted)
        print(encrypted or public)
    """),
    T("""
        **Truthiness**

        `if` accepts any value, not just booleans. Empty things count as **false**: `""`, `0`, `None`,
        and (soon) empty lists and dictionaries. Everything else counts as **true**.

        ```
        tags = ""
        if not tags:
            print("no tags!")
        ```

        This is handy, but be careful: `0` is a valid port and still counts as false. When you mean
        "is this missing?", compare with `is None` instead.
    """),
    Ex("""
        from_port = 0
        if from_port:
            print("truthy")
        else:
            print("0 counts as false!")
        if from_port is not None:
            print("but it is not None - it's a real value")
    """),
    Q("Which line is a SyntaxError?",
      "if port = 22:", "if port == 22:", "if port != 22:", "if not port:",
      explain="A single `=` assigns. In a condition you need `==`."),
    C("""
        A variable `port = 3389` is given. Print:

        - `SSH` if the port is 22
        - `RDP` if it is 3389
        - `OTHER` for anything else

        Your code will be tested with several ports, so use `if / elif / else` rather than just
        printing `RDP`.
    """, 'port = 3389\nif port == 22:\n    print("SSH")\nelif port == 3389:\n    print("RDP")\nelse:\n    print("OTHER")',
      starter="port = 3389",
      check="""
        import re
        for value, expected in ((22, "SSH"), (3389, "RDP"), (443, "OTHER")):
            src = re.sub(r"^port\\s*=.*$", "port = %d" % value, __source__, count=1, flags=re.M)
            out = __capture__(exec, src, {})
            assert out.strip() == expected, "with port = %d your code printed %r, expected %r" % (value, out.strip(), expected)
      """,
      require=["if", "elif", "else"],
      hints=["Start with `if port == 22:` and indent the print under it by 4 spaces.",
             "Then `elif port == 3389:` with its own indented print, then `else:`.",
             'if port == 22:\n    print("SSH")\nelif port == 3389:\n    print("RDP")\nelse:\n    print("OTHER")']),
    C("""
        A firewall rule is described by `cidr = "0.0.0.0/0"` and `port = 22`.

        Print `DANGER` when the source is the whole internet (`"0.0.0.0/0"`) **and** the port is 22 or
        3389. Otherwise print `ok`. (It will be tested with other values too.)
    """, 'cidr = "0.0.0.0/0"\nport = 22\nif cidr == "0.0.0.0/0" and (port == 22 or port == 3389):\n    print("DANGER")\nelse:\n    print("ok")',
      starter='cidr = "0.0.0.0/0"\nport = 22',
      check="""
        import re
        cases = (("0.0.0.0/0", 22, "DANGER"), ("0.0.0.0/0", 3389, "DANGER"), ("0.0.0.0/0", 443, "ok"),
                 ("10.0.0.0/8", 22, "ok"))
        for c, p, expected in cases:
            src = re.sub(r"^cidr\\s*=.*$", "cidr = %r" % c, __source__, count=1, flags=re.M)
            src = re.sub(r"^port\\s*=.*$", "port = %d" % p, src, count=1, flags=re.M)
            out = __capture__(exec, src, {})
            assert out.strip() == expected, "cidr=%s port=%d printed %r, expected %r" % (c, p, out.strip(), expected)
      """,
      require=["and"],
      hints=["You need `and` to require both conditions.",
             "Brackets group the port check: (port == 22 or port == 3389)",
             'if cidr == "0.0.0.0/0" and (port == 22 or port == 3389):']),
], summary="""
    - Comparisons `== != < <= > >= in` produce `True`/`False`. One `=` assigns; `==` compares.
    - `if cond:` / `elif cond:` / `else:` - colon, then a 4-space indented block. First match wins.
    - `and`, `or`, `not` combine conditions; use brackets to group.
    - Empty values (`""`, `0`, `None`, empty collections) are falsy. Use `is None` to test for "missing".
""")

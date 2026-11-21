from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l5", "Lists and loops", [
    T("""
        **Lists**

        A **list** holds several values in order, inside square brackets:

        ```
        regions = ["us-east-1", "eu-west-1", "ap-southeast-2"]
        ports = [22, 80, 443]
        ```

        Lists use the same indexing as strings (`regions[0]`, `regions[-1]`, `regions[1:]`), and
        `len(regions)` counts the items. Unlike strings, lists **can be changed**:

        - `.append(x)` adds to the end, `.remove(x)` removes the first matching item
        - `x in my_list` checks membership
        - `sorted(my_list)` returns a sorted copy; `sum`, `min`, `max` work on lists of numbers
    """),
    Ex("""
        ports = [443, 22, 80]
        ports.append(3389)
        print(ports)
        print(len(ports), "ports, first:", ports[0], "last:", ports[-1])
        print(22 in ports, 8080 in ports)
        print(sorted(ports), "max:", max(ports))
    """),
    P("""
        zones = ["a", "b"]
        zones.append("c")
        print(zones)
        print(len(zones))
    """),
    T("""
        **for loops**

        A `for` loop runs its indented block once for **each item**, with the loop variable set to that item:

        ```
        for region in regions:
            print("deploying to", region)
        ```

        This is the most important pattern in automation: do the same thing to every resource, every
        rule, every region.
    """),
    Ex("""
        actions = ["create", "update", "delete", "create"]
        for action in actions:
            print("planned:", action)
        print("total:", len(actions))
    """),
    T("""
        **Accumulating results**

        To build an answer while looping, start with an empty value *before* the loop and update it
        *inside*:

        ```
        creates = 0
        for action in actions:
            if action == "create":
                creates = creates + 1      # or: creates += 1
        ```

        The same pattern builds lists: start with `found = []` and `found.append(...)` inside the loop.
    """),
    P("""
        sizes = [20, 100, 8]
        total = 0
        for size in sizes:
            total += size
        print(total)
    """),
    T("""
        **range and enumerate**

        - `range(5)` counts 0, 1, 2, 3, 4. `range(1, 4)` counts 1, 2, 3 (the end is excluded, like slices).
        - `enumerate(items)` gives you a counter and the item together:

        ```
        for n, rule in enumerate(rules, 1):     # start counting at 1
            print("rule", n, "is", rule)
        ```
    """),
    Ex("""
        for i in range(3):
            print("attempt", i)
        rules = ["allow 443", "allow 22", "deny all"]
        for n, rule in enumerate(rules, 1):
            print(n, rule)
    """),
    T("""
        **break, continue and while**

        - `continue` skips to the next item; `break` leaves the loop entirely.
        - A `while` loop repeats as long as a condition is true. Make sure something inside changes, or it
          will run forever (the app stops runaway programs after a few seconds).

        ```
        attempts = 0
        while attempts < 3:
            attempts += 1
        ```

        In automation, `for` is far more common than `while`. Reach for `while` when you don't know in
        advance how many times to repeat - like retrying until a deploy finishes.
    """),
    P("""
        for port in [80, 22, 443, 3389]:
            if port == 443:
                break
            if port == 22:
                continue
            print(port)
    """, explain="80 prints; 22 is skipped by continue; at 443 break ends the loop, so 3389 never runs."),
    Q("What does `list(range(2, 5))` contain?", "[2, 3, 4]", "[2, 3, 4, 5]", "[3, 4, 5]", "[0, 1, 2, 3, 4]"),
    C("""
        Given `actions = ["create", "delete", "update", "delete", "create", "delete"]`, use a loop to count
        the deletes and print:

        ```output
        3 resources will be destroyed
        ```

        Count with a loop (no `.count()` for this one - practise the pattern).
    """, 'actions = ["create", "delete", "update", "delete", "create", "delete"]\ndeletes = 0\nfor action in actions:\n    if action == "delete":\n        deletes += 1\nprint(f"{deletes} resources will be destroyed")',
      starter='actions = ["create", "delete", "update", "delete", "create", "delete"]',
      require=["for"], forbid=[".count("],
      hints=["Start a counter at 0 before the loop.",
             'Inside the loop: if action == "delete": deletes += 1',
             'After the loop: print(f"{deletes} resources will be destroyed")']),
    C("""
        Given `ports = [22, 443, 3389, 8080, 5432]` and `sensitive = [22, 3389, 5432]`, build a list
        `exposed` of the ports that are in `sensitive`, in their original order, then print it:

        ```output
        [22, 3389, 5432]
        ```
    """, 'ports = [22, 443, 3389, 8080, 5432]\nsensitive = [22, 3389, 5432]\nexposed = []\nfor port in ports:\n    if port in sensitive:\n        exposed.append(port)\nprint(exposed)',
      starter="ports = [22, 443, 3389, 8080, 5432]\nsensitive = [22, 3389, 5432]",
      check='assert exposed == [22, 3389, 5432], "exposed should be [22, 3389, 5432], got %r" % (exposed,)',
      require=["for", "append"],
      hints=["Start with exposed = [] and loop over ports.",
             "Use `if port in sensitive:` and exposed.append(port).",
             "for port in ports:\n    if port in sensitive:\n        exposed.append(port)\nprint(exposed)"]),
    C("""
        Number the regions starting at 1 with `enumerate`. Given
        `regions = ["us-east-1", "eu-west-1", "ap-south-1"]`, print:

        ```output
        1. us-east-1
        2. eu-west-1
        3. ap-south-1
        ```
    """, 'regions = ["us-east-1", "eu-west-1", "ap-south-1"]\nfor n, region in enumerate(regions, 1):\n    print(f"{n}. {region}")',
      starter='regions = ["us-east-1", "eu-west-1", "ap-south-1"]',
      require=["enumerate"],
      hints=["enumerate(regions, 1) gives pairs: (1, 'us-east-1'), (2, 'eu-west-1'), ...",
             'for n, region in enumerate(regions, 1):\n    print(f"{n}. {region}")']),
], summary="""
    - Lists: `[a, b, c]`, indexing/slicing like strings, `len`, `.append(x)`, `.remove(x)`, `x in list`,
      `sorted(list)`, `sum/min/max`.
    - `for item in items:` runs the block once per item. Accumulate with a variable set before the loop.
    - `range(n)` / `range(a, b)` (end excluded); `enumerate(items, 1)` gives (number, item).
    - `continue` skips to the next item, `break` leaves the loop; `while cond:` repeats while true.
""")

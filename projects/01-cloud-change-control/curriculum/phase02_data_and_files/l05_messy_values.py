from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p02l5", "Taming messy values", [
    T("""
        **Real data is inconsistent**

        Terraform's JSON isn't always shaped the way you'd hope:

        - An attribute may be `null`, a single value, or a list: `"cidr_blocks": "0.0.0.0/0"` in one
          resource, `["0.0.0.0/0", "10.0.0.0/8"]` in another.
        - Nested configuration **blocks** appear as a *list containing one object*:
          `"settings": [{"tier": "db-f1-micro"}]`.
        - Ports may be numbers (`22`) or strings (`"22"`, `"8000-8080"`).

        Policies stay simple if small helper functions **normalise** these values first.
    """),
    T("""
        **Tuples**

        A **tuple** is like a list that can't be changed, written with round brackets: `(8000, 8080)`.
        Use tuples for small fixed groups of values, like a port range's low and high ends.

        Functions can return several values as a tuple, and you can **unpack** them into separate names:

        ```
        def split_range(text):
            low, high = text.split("-")
            return int(low), int(high)

        low, high = split_range("8000-8080")
        ```
    """),
    Ex("""
        port_range = (8000, 8080)
        low, high = port_range
        print(low, high, high - low + 1, "ports")
        print(type(port_range), port_range[0])
        for name, value in [("from_port", 22), ("to_port", 22)]:
            print(name, value)
    """),
    T("""
        **isinstance with several types**

        `isinstance(value, (list, tuple, set))` checks against several types at once. It's how a helper
        decides "is this already a collection, or a single value I should wrap?"

        Careful: a **string** is technically a sequence of characters, so `list("abc")` gives
        `["a", "b", "c"]`. Treat strings as single values, not collections.
    """),
    P("""
        for value in [None, "0.0.0.0/0", ["10.0.0.0/8"], (1, 2)]:
            print(isinstance(value, (list, tuple)))
    """),
    C("""
        Write `as_text_list(value)` that returns:

        - `[]` for `None`
        - the same items as a list for a list or tuple
        - `[value]` for anything else (including strings)
    """, "def as_text_list(value):\n    if value is None:\n        return []\n    if isinstance(value, (list, tuple)):\n        return list(value)\n    return [value]",
      check="""
        assert as_text_list(None) == []
        assert as_text_list("0.0.0.0/0") == ["0.0.0.0/0"], "a string is one value: got %r" % (as_text_list("0.0.0.0/0"),)
        assert as_text_list(["a", "b"]) == ["a", "b"]
        assert as_text_list(("a",)) == ["a"] and isinstance(as_text_list(("a",)), list)
        assert as_text_list(22) == [22]
      """,
      require=["isinstance"],
      hints=["Check None first, then isinstance(value, (list, tuple)), then the fallback.",
             "list(value) turns a tuple into a list."]),
    T("""
        **Ranges and inclusive counting**

        Firewall rules use **inclusive** ranges: `8000-8080` includes both ends. A port `p` is inside when
        `low <= p <= high` - Python lets you chain comparisons like that.

        Turning `"8000-8080"` into `(8000, 8080)` means: convert to text, strip spaces, split on `-` if
        present, and convert each side with `int()`.
    """),
    P("""
        low, high = 3000, 4000
        sensitive = [22, 3306, 3389, 5432]
        print([p for p in sensitive if low <= p <= high])
    """),
    B("p2-lists-and-blocks", intro="These two helpers live in `changegate/policies/helpers.py`. Every policy you "
                                  "write in Phase 4 will use them."),
    B("p2-ports", intro="Same file: the port helpers behind the 'SSH open to the internet' rules."),
], summary="""
    - Normalise messy values with small helpers before applying rules.
    - Tuples: `(a, b)`, immutable; unpack with `low, high = pair`; functions return tuples with `return a, b`.
    - `isinstance(x, (list, tuple, set))`; treat strings as single values.
    - Chained comparisons: `low <= p <= high` for inclusive ranges.
""")

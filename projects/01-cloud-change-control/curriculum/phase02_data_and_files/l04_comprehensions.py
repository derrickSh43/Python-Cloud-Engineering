from pce.lesson import T, Ex, Q, P, C, B, Lesson

CHANGES = '''changes = [
    {"address": "aws_s3_bucket.logs", "type": "aws_s3_bucket", "actions": ["create"]},
    {"address": "aws_instance.web", "type": "aws_instance", "actions": ["update"]},
    {"address": "aws_db_instance.orders", "type": "aws_db_instance", "actions": ["delete", "create"]},
    {"address": "google_storage_bucket.reports", "type": "google_storage_bucket", "actions": ["create"]},
    {"address": "aws_instance.old", "type": "aws_instance", "actions": ["no-op"]},
]'''

LESSON = Lesson("p02l4", "Comprehensions, sets and canonical data", [
    T("""
        **List comprehensions**

        Building a list with a loop is so common that Python has a short form for it:

        ```
        addresses = []
        for c in changes:
            addresses.append(c["address"])

        addresses = [c["address"] for c in changes]      # the same thing, in one line
        ```

        Add a condition to filter: `[c["address"] for c in changes if c["actions"] != ["no-op"]]`.
        Read it as "the address, for each change, if it isn't a no-op".
    """),
    Ex(CHANGES + '''
print([c["address"] for c in changes])
print([c["type"] for c in changes if c["type"].startswith("google_")])
print([len(c["actions"]) for c in changes])
'''),
    P("""
        ports = [22, 80, 443, 3389]
        print([p * 10 for p in ports if p < 1000])
    """),
    T("""
        **Sets**

        A **set** is an unordered collection with **no duplicates**, written `{1, 2, 3}` (an empty set is
        `set()` - `{}` is an empty dict). Sets are perfect for "which distinct things?" and fast membership
        checks, and support maths-style operations:

        - `a | b` union (in either), `a & b` intersection (in both), `a - b` difference (in a, not b)
    """),
    Ex("""
        types = ["aws_instance", "aws_s3_bucket", "aws_instance", "aws_instance"]
        print(set(types))
        allowed = {"aws_s3_bucket", "aws_instance"}
        planned = {"aws_s3_bucket", "aws_iam_policy"}
        print("not allowed:", planned - allowed)
        print("in both:", planned & allowed)
    """),
    T("""
        **Dict and set comprehensions, any and all**

        - `{c["address"]: c["actions"] for c in changes}` builds a dict
        - `{c["type"] for c in changes}` builds a set
        - `any(...)` is True if any item is true; `all(...)` if every item is - perfect with a
          comprehension-style expression: `any(c["actions"] == ["delete"] for c in changes)`
    """),
    Ex(CHANGES + '''
by_address = {c["address"]: c["actions"] for c in changes}
print(by_address["aws_db_instance.orders"])
print(sorted({c["type"].split("_")[0] for c in changes}))
print(any("delete" in c["actions"] for c in changes))
print(all(c["address"].startswith("aws_") for c in changes))
'''),
    Q("What is `{x % 3 for x in range(6)}`?", "{0, 1, 2}", "[0, 1, 2, 0, 1, 2]", "{0, 1, 2, 0, 1, 2}", "{0, 3}"),
    C("""
        Using the provided `changes` list, build a list `active` of the addresses of every change whose
        actions are **not** `["no-op"]`, using a list comprehension, and print it.
    """, CHANGES + '''
active = [c["address"] for c in changes if c["actions"] != ["no-op"]]
print(active)''',
      starter=CHANGES,
      check='assert active == ["aws_s3_bucket.logs", "aws_instance.web", "aws_db_instance.orders", "google_storage_bucket.reports"], "got %r" % (active,)',
      require=["[", " for ", " if "], forbid=[".append("],
      hints=['The shape is [<what> for c in changes if <condition>].',
             'active = [c["address"] for c in changes if c["actions"] != ["no-op"]]']),
    C("""
        Print the **sorted list of distinct clouds** in `changes`, where the cloud is the part of the type
        before the first underscore (`"aws"` or `"google"`):

        ```output
        ['aws', 'google']
        ```
    """, CHANGES + '''
print(sorted({c["type"].split("_")[0] for c in changes}))''',
      starter=CHANGES,
      require=["{"],
      hints=['A set comprehension removes duplicates: {c["type"].split("_")[0] for c in changes}',
             "sorted(...) turns the set into a sorted list."]),
    T("""
        **Canonical JSON**

        Two dicts with the same contents are equal in Python, but `json.dumps` writes keys in insertion
        order, so `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` produce **different text** - and different
        SHA-256 fingerprints.

        When data will be signed or hashed, it must be written in **one canonical form**: keys sorted,
        no optional whitespace, and consistent character handling. `json.dumps` can do all of that:

        ```
        json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        ```

        ChangeGate signs approvals and chains audit records this way (Phase 5). You'll write the helper now.
    """),
    Ex("""
        import json
        a = {"risk": "HIGH", "approver": "alice"}
        b = {"approver": "alice", "risk": "HIGH"}
        print(json.dumps(a) == json.dumps(b))
        print(json.dumps(a, sort_keys=True, separators=(",", ":")))
        print(json.dumps(a, sort_keys=True, separators=(",", ":")) == json.dumps(b, sort_keys=True, separators=(",", ":")))
    """),
    B("p2-canonical"),
], summary="""
    - List comprehension: `[expr for x in items if cond]`. Dict: `{k: v for ...}`. Set: `{expr for ...}`.
    - Sets: no duplicates, `set()` for empty; `a | b`, `a & b`, `a - b`; fast `in`.
    - `any(cond for x in items)`, `all(cond for x in items)`.
    - Canonical JSON for hashing/signing: `json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
""")

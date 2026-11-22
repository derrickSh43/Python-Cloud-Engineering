from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p03l6", "From JSON to objects", [
    T("""
        **The parser's job**

        Everything after the parser - policies, risk, approvals - works with `ResourceChange` objects, never
        raw JSON. The parser is the **one place** that knows the shape of Terraform's output:

        ```
        plan JSON entry                         ResourceChange
        ───────────────                         ──────────────
        "address": "aws_db_instance.orders"  →  address
        "type": "aws_db_instance"            →  type
        "provider_name": ".../hashicorp/aws" →  provider = "aws", cloud = "aws"
        "change": {"actions": [...]}         →  action = Action.REPLACE
        "change": {"before", "after", ...}   →  before, after, after_unknown
        ```

        If Terraform ever changes its format, only the parser changes. This idea - convert external data at
        the **boundary**, use clean types inside - is one of the most valuable habits in software.
    """),
    T("""
        **Required vs optional fields**

        Some keys must exist (an entry without an `address` is useless); others are optional (`module_address`
        only appears for resources inside modules). The parser should:

        - read required keys with `[...]` inside a `try`, turning `KeyError` into a clear `PlanError`
        - read optional keys with `.get(key, default)`
        - treat `null` and missing the same where it makes sense: `change.get("after_unknown") or {}`

        One more trap: if the entry isn't a dict at all (say, a string), `entry["address"]` raises
        `TypeError`, not `KeyError`. Catch both with `except (KeyError, TypeError):`.
    """),
    Ex("""
        class PlanError(Exception):
            pass

        def read_required(entry):
            try:
                return entry["address"], entry["change"]["actions"]
            except (KeyError, TypeError):
                raise PlanError("resource change is missing address/change/actions: %r" % (entry,)) from None

        print(read_required({"address": "a.b", "change": {"actions": ["create"]}}))
        for bad in ({"address": "a.b"}, "not a dict"):
            try:
                read_required(bad)
            except PlanError as e:
                print("PlanError:", e)
    """),
    T("""
        **Errors that point at the problem**

        When one entry out of 300 has a bad action, "unrecognised actions" isn't enough - which resource?
        Prefix the message with the address:

        ```
        try:
            action = Action.from_terraform(actions)
        except ValueError as e:
            raise PlanError("%s: %s" % (address, e)) from None
        ```
    """),
    P("""
        entries = [{"mode": "managed", "address": "a.x"}, {"mode": "data", "address": "data.b.y"},
                   {"mode": "managed", "address": "c.z"}]
        print([e["address"] for e in entries if e.get("mode") != "data"])
    """, explain="Data sources (mode 'data') are reads, not changes - the parser skips them by default."),
    Q("What does this print?", "{} {}", "None {}", "None None", "An error",
      code="""
        change = {"after_unknown": None}
        print(change.get("after_unknown") or {}, change.get("missing") or {})
      """, explain="`x or {}` replaces None (and anything else falsy) with an empty dict, so null and missing behave the same."),
    C("""
        Practise the pattern on a smaller shape. Write `parse_rule(entry)` that returns a tuple
        `(name, port, sources)`:

        - `name` = `entry["name"]` (required)
        - `port` = `int(entry["port"])` (required; it may arrive as text)
        - `sources` = `entry.get("sources")`, with `None` or missing becoming `[]`

        If `name` or `port` is missing, or `entry` isn't a dict, raise `ValueError("bad rule: <entry>")`.
    """, 'def parse_rule(entry):\n    try:\n        name = entry["name"]\n        port = int(entry["port"])\n    except (KeyError, TypeError):\n        raise ValueError("bad rule: %r" % (entry,)) from None\n    return name, port, entry.get("sources") or []',
      check="""
        assert parse_rule({"name": "ssh", "port": "22", "sources": ["0.0.0.0/0"]}) == ("ssh", 22, ["0.0.0.0/0"])
        assert parse_rule({"name": "web", "port": 443, "sources": None}) == ("web", 443, [])
        assert parse_rule({"name": "web", "port": 443}) == ("web", 443, [])
        for bad in ({"port": 22}, {"name": "x"}, "text", None):
            try:
                parse_rule(bad)
            except ValueError as e:
                assert str(e).startswith("bad rule"), "message should start with 'bad rule', got %r" % str(e)
            else:
                raise AssertionError("parse_rule(%r) should raise ValueError" % (bad,))
      """,
      require=["try", "except"],
      hints=["Read name and port inside try; catch (KeyError, TypeError).",
             'entry.get("sources") or [] turns None/missing into [].',
             'except (KeyError, TypeError):\n    raise ValueError("bad rule: %r" % (entry,)) from None']),
    B("p3-parse-change", intro="One entry → one `ResourceChange`. Use `providers.provider_key` and "
                              "`providers.cloud_for` from the previous exercise."),
    B("p3-parse-plan", intro="And the whole plan. After this, `load_plan(path)` turns any sample plan into objects."),
], summary="""
    - Convert external data at the boundary (the parser); the rest of the code uses typed objects.
    - Required keys: `[...]` in `try`, catch `(KeyError, TypeError)`, raise a clear error `from None`.
    - Optional keys: `.get(key, default)`; `value or {}` treats null like missing.
    - Prefix errors with the resource address so the user can find the problem.
""")

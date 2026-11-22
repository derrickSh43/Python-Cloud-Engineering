from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p04cp", "Rules as code", """
    Read some rule code, then write a small rule from scratch.
""", [
    Q("What does this print?", "['HIGH']", "[]", "['HIGH', 'HIGH']", "An error",
      code="""
        def check(port):
            if port in (22, 3389):
                yield "HIGH"

        print(list(check(22)))
      """, explain="A generator yields zero or more values; list() collects them."),
    Q("What does this print?", "0", "22", "None", "An error",
      code="""
        rule = {"from_port": 0}
        port = rule.get("from_port")
        print(port if port is not None else 22)
      """, explain="0 is a real port. `is not None` keeps it; `rule.get(...) or 22` would wrongly replace it."),
    Q("What does this print?", "4", "3", "5", "An error",
      code="""
        LOW, MEDIUM, HIGH, CRITICAL = 1, 2, 3, 4
        risk = max([LOW, HIGH], default=LOW)
        deletes = 5
        if deletes >= 5:
            risk = min(risk + 1, CRITICAL)
        print(risk)
      """, explain="max gives HIGH (3); five deletes bump it one level to 4, capped at CRITICAL."),
    Q("What does this print?", "['allUsers']", "[]", "['allAuthenticatedUsers', 'allUsers']", "An error",
      code="""
        PUBLIC = {"allUsers", "allAuthenticatedUsers"}
        members = ["user:a@example.com", "allUsers"]
        print(sorted(PUBLIC & set(members)))
      """, explain="`&` is set intersection: only the members that appear in both."),
    C("""
        Write a generator `public_snapshot_findings(change)` for a hypothetical rule. `change` is a dict with
        `type` and `after`. For `aws_db_snapshot` (and only that type), yield
        `("HIGH", "snapshot shared publicly")` when `after["shared_accounts"]` (a list, possibly missing or
        None) contains `"all"`, and `("MEDIUM", "snapshot shared with N account(s)")` when it lists other
        accounts but not `"all"`.
    """, '''def public_snapshot_findings(change):
    if change["type"] != "aws_db_snapshot":
        return
    shared = (change.get("after") or {}).get("shared_accounts") or []
    if "all" in shared:
        yield ("HIGH", "snapshot shared publicly")
    elif shared:
        yield ("MEDIUM", "snapshot shared with %d account(s)" % len(shared))''',
      check="""
        def f(t, after):
            return list(public_snapshot_findings({"type": t, "after": after}))
        assert f("aws_db_snapshot", {"shared_accounts": ["all"]}) == [("HIGH", "snapshot shared publicly")]
        assert f("aws_db_snapshot", {"shared_accounts": ["123456789012", "210987654321"]}) == [("MEDIUM", "snapshot shared with 2 account(s)")]
        assert f("aws_db_snapshot", {"shared_accounts": None}) == [] and f("aws_db_snapshot", {}) == []
        assert f("aws_db_snapshot", None) == [], "after may be None (e.g. for a delete)"
        assert f("aws_s3_bucket", {"shared_accounts": ["all"]}) == []
      """,
      require=["yield"],
      hints=["Return early for any other resource type.",
             '(change.get("after") or {}).get("shared_accounts") or [] copes with every missing case.',
             'if "all" in shared: yield (...)  elif shared: yield (...)']),
])

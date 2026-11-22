from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l3", "Rules for a trustworthy approval", [
    T("""
        **A chain of checks that returns the first problem**

        `approval_problem()` runs a list of checks **in order** and returns the first failure as a message,
        or `None` when the approval is valid. The pattern is one `if ... return` per check:

        1. the signature doesn't verify
        2. the plan hash doesn't match
        3. issued in the future (beyond a small tolerance)
        4. expired
        5. too old
        6. the approver is the change's author
        7. the approver isn't on the allowed list
        8. it was signed for a lower risk level than the plan has now

        The signature comes first because the other fields can't be trusted until it verifies.
    """),
    T("""
        **Comparing names**

        `Alice` and `alice ` should count as the same person. Strip spaces and compare with
        `str.casefold()`, a more thorough `lower()` meant for comparisons. The author's name comes from
        `--author` or the `CHANGEGATE_AUTHOR` environment variable.
    """),
    Ex("""
        def same_identity(a, b):
            return a.strip().casefold() == b.strip().casefold()

        print(same_identity("Alice", "alice "), same_identity("alice", "bob"))
        print("Straße".lower(), "Straße".casefold())
    """),
    T("""
        **A tolerance with timedelta**

        Machine clocks drift a little, so "issued in the future" allows `CLOCK_SKEW = timedelta(minutes=5)`:
        reject only when `issued_at > now + CLOCK_SKEW`.

        **Counting approvals**

        `check_approvals()` calls `approval_problem()` on each approval, keeps the valid ones, counts each
        person **once**, and compares the count with the number required for the risk level. ALLOW needs
        none, and a BLOCK decision is never unlocked by approvals.
    """),
    P("""
        approved_by = []
        for who in ["alice", "Bob", "ALICE", "carol"]:
            if any(who.casefold() == seen.casefold() for seen in approved_by):
                print("duplicate:", who)
            else:
                approved_by.append(who)
        print(approved_by)
    """),
    Q("What does this print?", "expired", "not an approver", "None", "expired not an approver",
      code="""
        def problem(approval):
            if approval["expired"]:
                return "expired"
            if approval["who"] not in ("alice", "bob"):
                return "not an approver"
            return None

        print(problem({"who": "mallory", "expired": True}))
      """, explain="The function returns at the first failing check, so later checks never run."),
    Q("What does this print?", "True", "False", "An error",
      code="""
        def same(a, b):
            return a.strip().casefold() == b.strip().casefold()

        print(same(" Alice", "ALICE "))
      """),
    C("""
        Write `first_problem(approval, now, approvers, author)` where `approval` is a dict with `approver`,
        `issued_at` and `expires_at` (aware datetimes). Return the first problem as a string, or `None`:

        1. issued more than 5 minutes after `now` → `"<approver>: issued in the future"`
        2. `now >= expires_at` → `"<approver>: expired"`
        3. approver is the author (case-insensitive) → `"<approver>: authors cannot approve their own change"`
        4. approver not in `approvers` (case-insensitive) → `"<approver>: not an approver"`
    """, '''from datetime import timedelta

def first_problem(approval, now, approvers, author):
    who = approval["approver"]
    if approval["issued_at"] > now + timedelta(minutes=5):
        return "%s: issued in the future" % who
    if now >= approval["expires_at"]:
        return "%s: expired" % who
    if author and who.casefold() == author.casefold():
        return "%s: authors cannot approve their own change" % who
    if not any(who.casefold() == a.casefold() for a in approvers):
        return "%s: not an approver" % who
    return None''',
      check="""
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        def a(who, issued=now, ttl=24):
            return {"approver": who, "issued_at": issued, "expires_at": issued + timedelta(hours=ttl)}
        team = ["alice", "bob"]
        assert first_problem(a("alice"), now, team, "dave") is None
        assert first_problem(a("Alice", issued=now + timedelta(minutes=2)), now, team, "dave") is None, "allow small clock skew"
        assert first_problem(a("alice", issued=now + timedelta(hours=1)), now, team, "dave") == "alice: issued in the future"
        assert first_problem(a("alice", issued=now - timedelta(hours=2), ttl=1), now, team, "dave") == "alice: expired"
        assert first_problem(a("dave"), now, team + ["dave"], "Dave") == "dave: authors cannot approve their own change"
        assert first_problem(a("mallory"), now, team, "dave") == "mallory: not an approver"
      """,
      hints=["One `if ... return` per rule, in the given order; finish with return None.",
             "Future: approval[\"issued_at\"] > now + timedelta(minutes=5)",
             "Compare names with .casefold() on both sides."]),
    B("p5-approval-rules"),
    B("p5-check-approvals"),
], summary="""
    - A validation chain: one `if ... return message` per check, in order; `return None` at the end.
    - Compare identities with `strip().casefold()`.
    - Tolerances with `timedelta`. Count each approver once with a set of casefolded names.
""")

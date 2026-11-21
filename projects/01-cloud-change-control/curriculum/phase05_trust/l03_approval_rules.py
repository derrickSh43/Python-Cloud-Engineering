from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l3", "Rules for a trustworthy approval", [
    T("""
        **What can go wrong with an approval?**

        Think like an attacker - or just a tired colleague:

        - The file was **edited** after signing (approver changed, expiry pushed out).
        - It approves a **different plan** - last week's harmless one.
        - It's **old**: approved before the weekend, used on Monday after the plan changed.
        - Its timestamp is in the **future**, to dodge expiry checks.
        - The **author approves their own change** - defeating the point of review.
        - It's from someone **not authorised** to approve.
        - It approved a MEDIUM-risk plan, but new policy settings now rate the same plan HIGH.
        - The same person approved **twice** to satisfy a two-approver rule.

        Each of these becomes one check.
    """),
    T("""
        **Order matters: trust nothing until the signature checks out**

        The first check must be the signature. Until it verifies, every field in the file - the approver's
        name, the times, the plan hash - is just text an attacker could have typed. Checking "is the approver
        on the list?" first would leak information and, worse, invites code that acts on unverified data.

        ChangeGate's `approval_problem()` returns the **first** problem as a message (or `None` if the
        approval is valid), in this order: signature → plan hash → future timestamp → expired → too old →
        self-approval → approver list → risk level.
    """),
    T("""
        **Separation of duties**

        "Authors cannot approve their own change" is called **separation of duties**: one person can't both
        make and authorise a risky change. It protects against mistakes as much as malice. ChangeGate gets
        the author from `--author` or `$CHANGEGATE_AUTHOR` (in CI, the person who opened the pull request).

        Identities are compared **case-insensitively** after stripping spaces - `Alice` and `alice ` are the
        same person - using `str.casefold()`, a more thorough `lower()` for comparisons.
    """),
    Ex("""
        def same_identity(a, b):
            return a.strip().casefold() == b.strip().casefold()

        print(same_identity("Alice", "alice "), same_identity("alice", "bob"))
        print("Straße".lower(), "Straße".casefold())
    """),
    T("""
        **Clock skew**

        Two computers' clocks are never exactly in sync. An approval signed on a laptop whose clock runs a
        minute fast would look "issued in the future" to a CI runner. So the future-timestamp check allows a
        small tolerance - `CLOCK_SKEW = timedelta(minutes=5)` - and only rejects times beyond it.
    """),
    T("""
        **Counting approvals**

        `check_approvals()` uses `approval_problem()` on every approval and then:

        - ALLOW decisions need nothing; BLOCK decisions can **never** be approved - a block means "fix the plan".
        - The number required depends on the risk (`[approvals.required]`, e.g. HIGH needs 2).
        - Valid approvals count **once per person**.
        - Every rejected approval is explained, so the report can say exactly why the gate is still closed.
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
    Q("Why is the signature checked before the approver list?",
      "Until the signature verifies, every field might be forged, so nothing else should be trusted",
      "Signature checks are faster", "The approver list might be empty", "It doesn't matter which comes first"),
    Q("A plan is BLOCKED. Three managers approve it. What does ChangeGate do?",
      "Still blocks it - approvals can't override a block", "Allows it - three is more than two",
      "Allows it only if one approver is an admin", "Downgrades the risk to HIGH"),
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
    - Threats: edits, wrong plan, old/future approvals, self-approval, unauthorised approvers,
      changed risk, duplicate approvers.
    - Verify the signature first; until then nothing in the approval is trusted.
    - Separation of duties: authors can't approve their own change. Compare identities with `strip().casefold()`.
    - Allow small clock skew. BLOCK can never be approved. Count each approver once; explain every rejection.
""")

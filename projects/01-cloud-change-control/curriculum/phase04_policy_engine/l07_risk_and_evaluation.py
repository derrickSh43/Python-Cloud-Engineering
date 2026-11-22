from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l7", "Risk, decisions and the pipeline", [
    T("""
        **From many findings to one risk level**

        A plan may produce a dozen findings. People need **one** answer. ChangeGate's rule is deliberately
        simple and explainable:

        1. Ignore changes that don't change anything (`no-op`, `read`).
        2. No changes and no findings → LOW, "the plan makes no changes".
        3. Risk starts at the **highest finding severity** (LOW if there are none).
        4. Many destructive changes add up: if the number of deletes/replaces reaches the configured
           threshold, risk goes **up one level** (never beyond CRITICAL).

        Every step adds a **reason** string, so the report can say *why* - "3 findings; highest severity HIGH",
        "6 destructive changes (threshold 5) raise risk from HIGH to CRITICAL".
    """),
    T("""
        **max with a default**

        `max([])` raises ValueError - there's no maximum of nothing. Give it a fallback:

        ```
        level = max((f.severity for f in findings), default=Severity.LOW)
        ```

        The first argument is a **generator expression** - like a list comprehension in round brackets. It
        produces values one at a time without building a list.
    """),
    P("""
        print(max([3, 1, 2]))
        print(max([], default=0))
        print(sum(1 for word in ["delete", "create", "delete"] if word == "delete"))
    """),
    T("""
        **Thresholds to decisions**

        The decision comes from two configurable thresholds:

        - risk ≥ `block_at` (default CRITICAL) → **BLOCK** (unless `block_at` is `None`, meaning "never block")
        - otherwise risk ≥ `approval_at` (default MEDIUM) → **REQUIRE_APPROVAL**
        - otherwise → **ALLOW**

        Order matters: check block first. Because `Severity` is an `IntEnum`, `risk >= cfg.block_at` is an
        ordinary comparison.
    """),
    T("""
        **Sorting with a key**

        Findings should be listed most severe first, then by resource, then by policy id. `sorted` takes a
        `key` function that turns each item into the value to sort by. A **tuple** key sorts by the first
        element, then breaks ties with the next. Negating an IntEnum sorts it high-to-low:

        ```
        sorted(findings, key=lambda f: (-f.severity, f.address, f.policy_id))
        ```

        `lambda f: ...` is a tiny unnamed function - handy for one-line keys.
    """),
    Ex("""
        from enum import IntEnum

        class Severity(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        findings = [("b.y", Severity.MEDIUM), ("a.x", Severity.HIGH), ("c.z", Severity.HIGH), ("a.a", Severity.LOW)]
        for address, level in sorted(findings, key=lambda f: (-f[1], f[0])):
            print(level.name, address)
    """),
    T("""
        **The pipeline**

        `evaluator.py` is short because each step is its own tested function:

        ```
        raw bytes ─► decode_plan ─► parse_plan ─► run_policies ─► sort ─► classify ─► decide ─► Evaluation
                         └───────────── plan_digest(raw) ──────────────────────────────────────────┘
        ```

        After this lesson your ChangeGate can evaluate every sample plan. Try it from the project folder:

        ```
        cd projects/01-cloud-change-control/workspace
        python -c "from changegate.evaluator import evaluate_file; e = evaluate_file('../sample_data/plans/gcp_risky.json'); print(e.risk, e.decision)"
        ```
    """),
    Q("What does this print?", "HIGH", "MEDIUM", "CRITICAL", "LOW",
      code="""
        from enum import IntEnum

        class Severity(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        findings = [Severity.MEDIUM, Severity.HIGH, Severity.LOW]
        deletes, threshold = 2, 5
        risk = max(findings, default=Severity.LOW)
        if deletes >= threshold:
            risk = Severity(min(risk + 1, Severity.CRITICAL))
        print(risk.name)
      """, explain="The highest severity is HIGH, and 2 deletes don't reach the threshold of 5."),
    C("""
        Write `decide(risk, approval_at=2, block_at=4)` using plain integers (1=LOW ... 4=CRITICAL) that
        returns `"block"`, `"approval"` or `"allow"`. `block_at=None` means never block.
    """, 'def decide(risk, approval_at=2, block_at=4):\n    if block_at is not None and risk >= block_at:\n        return "block"\n    if risk >= approval_at:\n        return "approval"\n    return "allow"',
      check="""
        assert [decide(r) for r in (1, 2, 3, 4)] == ["allow", "approval", "approval", "block"], [decide(r) for r in (1, 2, 3, 4)]
        assert decide(4, block_at=None) == "approval", "block_at=None means never block"
        assert decide(3, approval_at=4, block_at=None) == "allow"
      """,
      hints=["Check the block case first, and only when block_at is not None.",
             'if block_at is not None and risk >= block_at:\n    return "block"']),
    B("p4-risk"),
    B("p4-evaluator", intro="The last piece of the engine. Its tests run every sample plan through your code."),
], summary="""
    - Risk = highest finding severity (LOW if none), +1 level when destructive changes reach the threshold;
      every step records a reason.
    - `max(gen, default=...)`; generator expressions `(x for x in items if ...)`; count with `sum(1 for ...)`.
    - Decision: BLOCK if risk ≥ block_at (unless None), else APPROVAL if ≥ approval_at, else ALLOW.
    - `sorted(items, key=lambda f: (-f.severity, f.address))` - tuple keys, negate to reverse one part.
""")

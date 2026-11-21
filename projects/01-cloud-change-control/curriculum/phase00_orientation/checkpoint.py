from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p00cp", "Ready to start", """
    A quick check that you're comfortable with the app before Phase 1.
""", [
    Q("Which order does ChangeGate work in?",
      "parse → policies → risk → decision → approvals → audit",
      "audit → parse → decision → policies",
      "approvals → parse → audit → risk"),
    C("""
        Print these two lines, in this order:

        ```output
        plan evaluated
        decision: allow
        ```
    """, 'print("plan evaluated")\nprint("decision: allow")',
      hints=["You need two print() calls, one per line.",
             'print("plan evaluated") on line 1, print("decision: allow") on line 2, then run.']),
])

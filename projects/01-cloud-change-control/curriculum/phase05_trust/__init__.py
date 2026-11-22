from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p05", 5, "Trust and accountability", "Time, signatures, approvals and a tamper-evident audit log",
    """
    A gate that says "this plan needs approval" is only useful if approvals can be **trusted**: they must
    come from the right people, apply to exactly this plan, expire, and be impossible to forge or edit.
    And every decision should leave a record that nobody can quietly rewrite.

    In this phase you learn to handle time correctly with `datetime`, sign data with `hmac`, write a chain
    of validation checks, and build a hash-chained, append-only log file.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Work with timezone-aware datetimes, ISO-8601 timestamps and timedeltas",
        "Sign and verify data with HMAC-SHA256, keeping the key out of code",
        "Explain timing attacks and use hmac.compare_digest",
        "Write a validation chain that returns the first problem, and count unique approvers",
        "Build and verify a hash-chained, append-only JSON Lines log",
    ],
)

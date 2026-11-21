from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p06", 6, "Production automation", "Reports, the CLI, packaging, CI and the capstone",
    """
    Your ChangeGate can evaluate plans and verify approvals - as a library. Now you make it a **tool**:
    reports people and machines can read, a command-line interface with proper exit codes, a package anyone
    can install, and a CI workflow that gates every pull request.

    The phase ends with the capstone: the full ChangeGate test suite, the same 190+ tests the reference
    implementation passes, running against your code. Pass it and the course is complete. Connecting real
    AWS and GCP accounts is an optional extra once you're done.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Render the same result as aligned text, JSON and Markdown",
        "Build a command-line interface with argparse subcommands, options and environment defaults",
        "Design exit codes, separate stdout from stderr, and log with the logging module",
        "Package a tool with pyproject.toml and an entry point, and install it with pip",
        "Run your tool as a CI/CD gate with GitHub Actions, using variables and secrets instead of hard-coded values",
        "Pass the complete ChangeGate test suite",
    ],
)

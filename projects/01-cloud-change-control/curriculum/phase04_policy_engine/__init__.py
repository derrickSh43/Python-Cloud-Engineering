from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p04", 4, "The policy engine", "Config, plugins, AWS and GCP rules, risk",
    """
    This is the heart of ChangeGate: a **rule engine** that runs every change through a set of checks,
    rates the overall risk, and decides whether a plan is allowed, needs approval, or is blocked.

    The Python here is what most infrastructure tooling needs: configuration loaded from a file instead of
    hard-coded, a plugin system (abstract base classes, decorators, dynamic imports), and rules written as
    small generator functions over nested dicts. Each exercise spells out the data and the rule to code.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Reason about IP ranges with the ipaddress module",
        "Load and strictly validate TOML configuration, with secrets and paths from the environment",
        "Build a plugin framework with abstract base classes, class attributes and a registering decorator",
        "Implement rules as generators over nested data: lookups, tables, JSON-in-JSON and string-or-list values",
        "Combine findings into a risk level and an explainable allow / approval / block decision",
        "Evaluate every sample plan end to end",
    ],
)

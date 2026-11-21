from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p04", 4, "The policy engine", "Config, plugins, AWS and GCP rules, risk",
    """
    This is the heart of ChangeGate: a **policy engine** that checks every change against security rules
    for AWS and Google Cloud, rates the overall risk, and decides whether a plan is allowed, needs approval,
    or is blocked.

    Along the way you'll learn how real tools are made configurable without editing code, how plugin
    systems work (abstract base classes, decorators, dynamic imports), and - just as important - **why**
    each security rule exists.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Reason about IP ranges with the ipaddress module",
        "Load and strictly validate TOML configuration, with secrets and paths from the environment",
        "Build a plugin framework with abstract base classes, class attributes and a registering decorator",
        "Explain and implement security policies for S3, security groups, encryption, IAM, GCS, firewalls and Cloud SQL",
        "Combine findings into a risk level and an explainable allow / approval / block decision",
        "Evaluate every sample plan end to end",
    ],
)

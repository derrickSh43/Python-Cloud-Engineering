from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p03", 3, "Structure and testing", "Classes, enums, dataclasses, packages and pytest",
    """
    Dictionaries got you a long way, but a real tool needs **types of its own**: a `ResourceChange` that
    always has an address and an action, a `Severity` that knows HIGH is worse than MEDIUM, a `Finding`
    that can't be accidentally edited. In this phase you learn classes, enums and dataclasses, organise
    code into packages, and start testing it properly with pytest.

    By the end, ChangeGate turns raw plan JSON into clean, typed objects.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Write classes with __init__, methods, properties and class methods",
        "Model fixed sets of values with Enum and IntEnum",
        "Define data types with frozen dataclasses and type hints",
        "Organise code in a package with relative imports and a registry",
        "Create a virtual environment, install pytest, and write tests with fixtures and parametrize",
        "Parse a whole Terraform plan into ResourceChange objects",
    ],
)

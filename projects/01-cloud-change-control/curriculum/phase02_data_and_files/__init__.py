from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p02", 2, "Data and files", "Bytes, files, JSON and real Terraform plans",
    """
    ChangeGate's input is a file: the JSON that `terraform show -json` produces. In this phase you learn
    to read files safely, work with bytes and JSON, handle bad input with clear errors, and navigate the
    nested data inside a real plan.

    This is also where you start **building ChangeGate itself**. From now on, many lessons end with a
    build exercise: you open a real file in your own editor, write a function, and run its tests.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Explain the difference between text and bytes and fingerprint data with SHA-256",
        "Read files with pathlib and turn low-level errors into clear, custom exceptions",
        "Parse JSON, validate its shape, and navigate a Terraform plan",
        "Use comprehensions, isinstance checks and tuple unpacking to tidy messy data",
        "Write generators with yield",
        "Implement the first eight functions of ChangeGate and pass their tests",
    ],
)

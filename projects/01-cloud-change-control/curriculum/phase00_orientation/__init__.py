from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p00", 0, "Orientation", "How the course works and what you'll build",
    """
    Before writing any real code, take five minutes to learn how this course works and to see the
    finished tool you're going to build: **Cloud ChangeGate**.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Move through lessons, answer questions and solve exercises in the app",
        "Use graduated hints without giving away the answer",
        "Describe the Python tool you'll build and the skills each phase covers",
    ],
)

from pce.lesson import Phase, collect

from .checkpoint import CHECKPOINT

PHASE = Phase(
    "p01", 1, "Python fundamentals", "Values, decisions, loops, collections, functions",
    """
    Every tool you'll build in this course is made of the same few ideas: values stored in variables,
    decisions, loops, collections of data, and functions. This phase teaches them from zero, using the
    things a cloud engineer actually handles - resource names, tags, ports, regions and plan actions -
    as the examples.

    No experience needed. Type every exercise yourself; reading code is not the same as writing it.
    """,
    lessons=collect(__name__, __path__, "l", "LESSON"),
    checkpoint=CHECKPOINT,
    outcomes=[
        "Store and print values; use strings, numbers and booleans and convert between them",
        "Make decisions with if / elif / else and combine conditions",
        "Work with lists and dictionaries, including nested data like Terraform resources",
        "Repeat work with for and while loops",
        "Package logic into functions with parameters and return values",
        "Read Python's error messages and fix the code they point to",
    ],
)

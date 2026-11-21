"""Constructors that keep curriculum files readable.

Steps (the things a learner works through inside a lesson):

    T(text)                          a page of explanation (light markdown: **bold**, `code`, - bullets, ``` blocks)
    Ex(code, note)                   example code that is run live and its output shown
    Q(question, correct, *wrong)     multiple choice (options are shuffled when shown)
    P(code)                          "predict the output" - the answer is computed by running the code
    C(task, solution, ...)           a coding exercise, graded by running the learner's code

Structure:

    Lesson(id, title, steps, summary)              summary becomes the lesson's reference card
    Checkpoint(id, title, intro, steps)            end-of-phase assessment; passing unlocks the next phase
    Phase(id, number, title, topic, overview, lessons, checkpoint, outcomes)
"""

import importlib
import pkgutil
from textwrap import dedent

STEP_TYPES = ("text", "example", "quiz", "predict", "code")


def _clean(text):
    return dedent(text).strip("\n").rstrip()


def T(text):
    return {"type": "text", "text": _clean(text)}


def Ex(code, note="", inputs=(), files=None, error_ok=False):
    return {"type": "example", "code": _clean(code), "note": _clean(note), "inputs": list(inputs),
            "files": files, "error_ok": error_ok}


def Q(question, correct, *wrong, explain="", code=None):
    return {"type": "quiz", "question": _clean(question), "correct": correct, "wrong": list(wrong),
            "explain": _clean(explain), "code": _clean(code) if code else None}


def P(code, explain="", inputs=(), files=None):
    return {"type": "predict", "code": _clean(code), "explain": _clean(explain), "inputs": list(inputs),
            "files": files}


def C(task, solution, check=None, starter="", hints=(), require=(), forbid=(), inputs=(), cases=None,
      match_output=None, files=None, title="Exercise"):
    """A coding exercise.

    hints: graduated - write them from a gentle nudge to an almost-complete answer.
    match_output: defaults to True when there is no `check` code.
    require/forbid: snippets that must / must not appear in the code. A tuple inside `require`
    means "any one of these".  cases: list of input lists, each run separately.
    """
    return {"type": "code", "title": title, "task": _clean(task), "solution": _clean(solution),
            "check": _clean(check) if check else None, "starter": _clean(starter), "hints": list(hints),
            "require": list(require), "forbid": list(forbid), "inputs": list(inputs),
            "cases": [list(c) for c in cases] if cases else None,
            "match_output": (check is None) if match_output is None else match_output, "files": files}


def Lesson(lesson_id, title, steps, summary):
    return {"id": lesson_id, "title": title, "steps": steps, "summary": _clean(summary)}


def Checkpoint(checkpoint_id, title, intro, steps):
    return {"id": checkpoint_id, "title": title, "intro": _clean(intro), "steps": steps}


def Phase(phase_id, number, title, topic, overview, lessons, checkpoint, outcomes=()):
    return {"id": phase_id, "number": number, "title": title, "topic": topic, "overview": _clean(overview),
            "lessons": lessons, "checkpoint": checkpoint, "outcomes": list(outcomes)}


def collect(package_name, package_path, prefix, attribute):
    """Import every submodule of a package whose name starts with `prefix` (sorted by name) and
    return each one's `attribute`. Used by curriculum packages to list their phases / lessons."""
    names = sorted(name for _, name, _ in pkgutil.iter_modules(package_path) if name.startswith(prefix))
    return [getattr(importlib.import_module(package_name + "." + name), attribute) for name in names]

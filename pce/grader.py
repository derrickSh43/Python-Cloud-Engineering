"""Decides whether a learner's code solves a challenge."""

from .runner import run_code

_expected = {}


class Verdict:
    def __init__(self, passed, kind="", **info):
        self.passed = passed
        self.kind = kind  # empty | require | forbid | error | timeout | output | check | crash
        self.info = info

    def __repr__(self):
        return "Verdict(%r, %r, %r)" % (self.passed, self.kind, self.info)


def normalize(text):
    return "\n".join(line.rstrip() for line in text.strip("\n").split("\n")).strip("\n")


def expected_output(step, inputs):
    key = (step["solution"], tuple(inputs), repr(step.get("files")))
    if key not in _expected:
        result = run_code(step["solution"], inputs, files=step.get("files"))
        if not result.ok and not result.check_error:
            raise RuntimeError("Reference solution failed: %r %r" % (result.error, result.crashed))
        _expected[key] = result.output
    return _expected[key]


def static_problem(step, code):
    """Checks that don't need running the code."""
    if not code.strip():
        return Verdict(False, "empty")
    try:
        compile(code, "<your code>", "exec")
    except SyntaxError as e:
        return Verdict(False, "error", error={"type": type(e).__name__, "message": e.msg, "line": e.lineno})
    for rule in step.get("require", ()):
        options = rule if isinstance(rule, (tuple, list)) else (rule,)
        if not any(option in code for option in options):
            return Verdict(False, "require", needed=options)
    for bad in step.get("forbid", ()):
        if bad in code:
            return Verdict(False, "forbid", bad=bad)
    return None


def grade(step, code):
    problem = static_problem(step, code)
    if problem:
        return problem
    for inputs in step.get("cases") or [step.get("inputs", [])]:
        result = run_code(code, inputs, check=step.get("check"), files=step.get("files"))
        if result.timed_out:
            return Verdict(False, "timeout", inputs=inputs)
        if result.crashed:
            return Verdict(False, "crash", detail=result.crashed)
        if result.error:
            return Verdict(False, "error", error=result.error, output=result.output, inputs=inputs)
        if step.get("match_output"):
            expected = expected_output(step, inputs)
            if normalize(result.output) != normalize(expected):
                return Verdict(False, "output", expected=expected, got=result.output, inputs=inputs)
        if result.check_error:
            return Verdict(False, "check", message=result.check_error, output=result.output, inputs=inputs)
    return Verdict(True)


def describe_output_difference(expected, got):
    """A short human explanation of how two outputs differ."""
    e, g = normalize(expected), normalize(got)
    if not g:
        return "Your program didn't print anything. Did you forget to call print()?"
    if e.lower() == g.lower():
        return "So close! Only capital letters are different. Python treats 'A' and 'a' as different characters."
    if e.replace(" ", "") == g.replace(" ", ""):
        return "Almost! Only spaces are different. Check spaces around commas and words."
    if e.replace("'", "").replace('"', "") == g.replace("'", "").replace('"', ""):
        return "Almost! The only difference is quote marks."
    el, gl = e.split("\n"), g.split("\n")
    if len(el) != len(gl):
        return "Expected %d line(s) of output but your program printed %d." % (len(el), len(gl))
    for n, (a, b) in enumerate(zip(el, gl), 1):
        if a != b:
            return "The first difference is on line %d of the output." % n
    return "The outputs are different."

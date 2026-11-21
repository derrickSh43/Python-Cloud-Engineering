"""Runs one learner program in its own Python process.

Reads a JSON job from stdin:  {"code", "inputs", "check", "echo"}
Writes a JSON report after a marker on stdout: {"output", "error", "check_error"}

This file is executed by runner.py with `python -I harness.py`; it must only use the standard library.
"""

import builtins
import io
import json
import sys
import traceback

MARK = "@@PCE_REPORT@@"
MAX_OUTPUT = 100_000


class TooMuchOutput(Exception):
    pass


class CappedOutput(io.StringIO):
    def write(self, text):
        if self.tell() + len(text) > MAX_OUTPUT:
            raise TooMuchOutput("Your program printed more than 100,000 characters")
        return super().write(text)


def describe(exc, filename="<your code>"):
    if isinstance(exc, SyntaxError):
        line = exc.lineno if exc.filename == filename else None
        return {"type": type(exc).__name__, "message": exc.msg, "line": line}
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == filename:
            line = frame.lineno
    return {"type": type(exc).__name__, "message": str(exc), "line": line}


def main():
    job = json.loads(sys.stdin.read())
    real_stdout = sys.stdout
    out = CappedOutput()
    feed = list(job.get("inputs") or [])
    echo = job.get("echo", False)

    def fake_input(prompt=""):
        if echo:
            out.write(str(prompt))
        if not feed:
            raise EOFError("input() was called more times than this challenge types answers for")
        value = feed.pop(0)
        if echo:
            out.write(value + "\n")
        return value

    builtins.input = fake_input
    namespace = {"__name__": "__main__"}
    report = {"output": "", "error": None, "check_error": None}

    sys.stdout = out
    try:
        exec(compile(job["code"], "<your code>", "exec"), namespace)
    except SystemExit:
        pass
    except BaseException as exc:  # noqa: BLE001 - we report every failure to the learner
        report["error"] = describe(exc)
    report["output"] = out.getvalue()

    if report["error"] is None and job.get("check"):
        def capture(fn, *args, **kwargs):
            """Call fn and return whatever it printed."""
            buf = CappedOutput()
            previous = sys.stdout
            sys.stdout = buf
            try:
                fn(*args, **kwargs)
            finally:
                sys.stdout = previous
            return buf.getvalue()

        namespace["__output__"] = report["output"]
        namespace["__source__"] = job["code"]
        namespace["__capture__"] = capture
        sys.stdout = CappedOutput()
        try:
            exec(compile(job["check"], "<check>", "exec"), namespace)
        except AssertionError as exc:
            report["check_error"] = str(exc) or "Your code ran, but the result isn't quite right yet."
        except NameError as exc:
            name = str(exc).split("'")[1] if "'" in str(exc) else str(exc)
            report["check_error"] = (
                "I couldn't find `" + name + "` in your code. Make sure you created it, "
                "spelled exactly like that (capital letters matter)."
            )
        except BaseException as exc:  # noqa: BLE001
            report["check_error"] = (
                "While testing your code it raised " + type(exc).__name__ + ": " + str(exc)
            )

    sys.stdout = real_stdout
    real_stdout.write("\n" + MARK + json.dumps(report))
    real_stdout.flush()


if __name__ == "__main__":
    main()

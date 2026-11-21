"""Runs one exercise's test file against a learner's code, in its own Python process.

Reads a JSON job from stdin: {"src", "tests_dir", "test_file"}. Every top-level function named
test_* is called in the order it is defined. Writes a JSON report after a marker on stdout.
Standard library only: learners use this before they have installed pytest.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import traceback

MARK = "@@PCE_CHECK@@"
TODO = re.compile(r"TODO\(([\w-]+)\)")


def location(tb, root):
    """The last traceback frame inside `root` (the learner's code): (relative path, line, text)."""
    found = None
    root = os.path.normcase(os.path.abspath(root))
    for frame in traceback.extract_tb(tb):
        if os.path.normcase(os.path.abspath(frame.filename)).startswith(root):
            found = (os.path.relpath(frame.filename, root).replace("\\", "/"), frame.lineno, (frame.line or "").strip())
    return found


def test_line(tb, test_path):
    for frame in reversed(traceback.extract_tb(tb)):
        if os.path.normcase(os.path.abspath(frame.filename)) == os.path.normcase(os.path.abspath(test_path)):
            return (frame.line or "").strip()
    return ""


def run_test(fn, src, test_path):
    out = io.StringIO()
    result = {"name": fn.__name__, "doc": (fn.__doc__ or "").strip(), "status": "pass", "message": "",
              "where": None, "output": ""}
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            fn()
    except NotImplementedError as e:
        match = TODO.search(str(e))
        result["status"] = "todo" if match else "error"
        result["todo"] = match.group(1) if match else None
        result["message"] = str(e)
        result["where"] = location(e.__traceback__, src)
    except AssertionError as e:
        result["status"] = "fail"
        result["message"] = str(e) or "this check failed: " + test_line(e.__traceback__, test_path)
        result["where"] = location(e.__traceback__, src)
    except BaseException as e:  # noqa: BLE001 - report every failure
        if isinstance(e, KeyboardInterrupt):
            raise
        result["status"] = "error"
        result["message"] = "%s: %s" % (type(e).__name__, e)
        result["where"] = location(e.__traceback__, src)
    result["output"] = out.getvalue()[-2000:]
    return result


def main():
    job = json.loads(sys.stdin.read())
    src, tests_dir, test_path = job["src"], job["tests_dir"], job["test_file"]
    sys.path[:0] = [src, tests_dir]
    report = {"import_error": None, "results": []}
    real_stdout = sys.stdout
    try:
        spec = importlib.util.spec_from_file_location("exercise_test", test_path)
        module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(module)
    except BaseException as e:  # noqa: BLE001
        match = TODO.search(str(e)) if isinstance(e, NotImplementedError) else None
        where = location(e.__traceback__, src)
        if isinstance(e, SyntaxError) and e.filename and os.path.abspath(e.filename).startswith(os.path.abspath(src)):
            where = (os.path.relpath(e.filename, src).replace("\\", "/"), e.lineno, (e.text or "").strip())
        report["import_error"] = {"type": type(e).__name__, "message": str(e), "where": where,
                                  "todo": match.group(1) if match else None}
    else:
        tests = [fn for name, fn in vars(module).items() if name.startswith("test_") and callable(fn)]
        report["results"] = [run_test(fn, src, test_path) for fn in tests]
    real_stdout.write("\n" + MARK + json.dumps(report))
    real_stdout.flush()


if __name__ == "__main__":
    main()

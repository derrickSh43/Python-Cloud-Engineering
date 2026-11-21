"""Checks a build exercise: runs its tests against a source tree and explains the result."""

import json
import os
import subprocess
import sys

from . import ui
from .ui import style

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_harness.py")
MARK = "@@PCE_CHECK@@"
TIME_LIMIT = 60


class CheckResult:
    def __init__(self, exercise_id, results=(), import_error=None, crash=None, timed_out=False):
        self.exercise_id = exercise_id
        self.results = list(results)
        self.import_error = import_error
        self.crash = crash
        self.timed_out = timed_out

    @property
    def passed(self):
        return bool(self.results) and not (self.import_error or self.crash or self.timed_out) and \
            all(r["status"] == "pass" for r in self.results)

    @property
    def counts(self):
        done = sum(r["status"] == "pass" for r in self.results)
        return done, len(self.results)

    def blocking_todos(self):
        """TODOs from *other* exercises that stopped this one's tests (they must be done first)."""
        ids = {r.get("todo") for r in self.results if r["status"] == "todo"}
        if self.import_error and self.import_error.get("todo"):
            ids.add(self.import_error["todo"])
        ids.discard(None)
        ids.discard(self.exercise_id)
        return sorted(ids)


def run_check(exercise_set, exercise, src=None, timeout=TIME_LIMIT):
    if exercise.kind != "unit":
        raise ValueError("run_check only handles unit exercises; use run_suite for %s" % exercise.id)
    src = src or exercise_set.workspace_dir
    job = json.dumps({"src": os.path.abspath(src), "tests_dir": os.path.abspath(exercise_set.tests_dir),
                      "test_file": os.path.abspath(os.path.join(exercise_set.tests_dir, exercise.test))})
    try:
        proc = subprocess.run([sys.executable, "-X", "utf8", "-I", HARNESS], input=job, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              cwd=os.path.abspath(src))
    except subprocess.TimeoutExpired:
        return CheckResult(exercise.id, timed_out=True)
    if MARK not in proc.stdout:
        return CheckResult(exercise.id, crash=(proc.stderr or proc.stdout or "the test run stopped unexpectedly")[-2000:])
    report = json.loads(proc.stdout.rsplit(MARK, 1)[1])
    return CheckResult(exercise.id, report["results"], report["import_error"])


def pytest_available():
    try:
        import pytest  # noqa: F401
        return True
    except ImportError:
        return False


def run_suite(exercise_set, src=None, extra_args=()):
    """The capstone: the project's full pytest suite against the learner's code. Returns the exit code."""
    env = dict(os.environ, CHANGEGATE_SRC=os.path.abspath(src or exercise_set.workspace_dir))
    cmd = [sys.executable, "-m", "pytest", exercise_set.suite_dir, "-q", "-p", "no:cacheprovider"] + list(extra_args)
    return subprocess.call(cmd, env=env, cwd=exercise_set.project_path)


# ---------------------------------------------------------------- display

ICON = {"pass": ("✔", "lime"), "fail": ("✘", "red"), "error": ("✘", "red"), "todo": ("…", "yellow")}


def show(result, verbose_passes=False):
    if result.timed_out:
        print(style("  ⏳ The tests were still running after %d seconds and were stopped." % TIME_LIMIT, "red", "bold"))
        ui.render("Look for a loop that never ends in the code you just wrote.", indent=4)
        return
    if result.crash:
        print(style("  The test run crashed:", "red", "bold"))
        print(style(result.crash, "grey"))
        return
    if result.import_error:
        err = result.import_error
        print(style("  ✘ Your code couldn't be imported: %s" % err["type"], "red", "bold"))
        if err.get("where"):
            path, line, text = err["where"]
            print(style("    %s, line %s" % (path, line), "grey") + ("  " + ui.highlight(text) if text else ""))
        print(style("    " + err["message"], "red"))
        if err.get("todo") and err["todo"] != result.exercise_id:
            print(style("    This needs exercise %s to be finished first." % err["todo"], "yellow"))
        return
    for r in result.results:
        icon, color = ICON[r["status"]]
        label = r["doc"] or r["name"].replace("test_", "").replace("_", " ")
        if r["status"] == "pass" and not verbose_passes:
            print("  " + style(icon, color) + " " + style(label, "grey"))
            continue
        print("  " + style(icon, color, "bold") + " " + style(label, "white" if r["status"] != "pass" else "grey"))
        if r["status"] == "todo":
            if r.get("todo") == result.exercise_id:
                print(style("      not written yet (still raises NotImplementedError)", "yellow"))
            else:
                print(style("      needs exercise %s first" % r.get("todo"), "yellow"))
            continue
        if r["status"] in ("fail", "error"):
            ui.render(r["message"], indent=6)
            if r.get("where"):
                path, line, text = r["where"]
                print(style("      at %s:%s" % (path, line), "grey") + ("  " + ui.highlight(text) if text else ""))
            if r.get("output", "").strip():
                ui.output_box(r["output"], title="Your code printed", color="grey", indent=6, max_lines=8)
    done, total = result.counts
    print()
    if result.passed:
        print(style("  ✔ All %d checks pass." % total, "lime", "bold"))
    else:
        print(style("  %d of %d checks pass." % (done, total), "yellow", "bold"))
        blockers = result.blocking_todos()
        if blockers:
            print(style("  Finish these exercises first: " + ", ".join(blockers), "yellow"))

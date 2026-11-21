"""Build-exercise actions shared by the command line (learn.py) and the interactive app:
workspace setup, show, check, hint, solution, listing."""

import datetime
import os
import shlex
import shutil
import subprocess
import sys

from . import checker, exercises, ui
from .ui import style

SOLUTION_AFTER_FAILS = 3


class Session:
    """One learner working on one project's exercises."""

    def __init__(self, project, profile):
        self.project = project
        self.profile = profile
        self.ex_set = exercises.load(project.path)
        if self.ex_set is None:
            raise exercises.ExerciseError("%s has no build exercises" % project.title)

    @property
    def prog(self):
        return self.profile.project(self.project.id)

    def record(self, exercise_id):
        return self.prog.exercise(exercise_id)

    def save(self):
        self.profile.save()

    # ------------------------------------------------------------ workspace
    @property
    def workspace(self):
        return self.ex_set.workspace_dir

    def ensure_workspace(self, quiet=False):
        if os.path.isdir(self.workspace):
            return False
        exercises.build_workspace(self.ex_set, self.workspace)
        if not quiet:
            print(style("  Created your workspace: ", "lime") + style(self.workspace, "cyan"))
            ui.render("It's a copy of ChangeGate with every exercise left as a TODO. It's yours to edit and is "
                      "git-ignored.", indent=4)
        return True

    def reset_file(self, rel):
        rel = rel.replace("\\", "/")
        if rel.startswith("workspace/"):
            rel = rel[len("workspace/"):]
        target = os.path.join(self.workspace, rel)
        if not os.path.isfile(os.path.join(self.ex_set.reference_dir, rel)):
            raise exercises.ExerciseError("%s is not a file in the project (e.g. changegate/plan_parser.py)" % rel)
        backup = None
        if os.path.exists(target):
            backup = target + ".bak"
            shutil.copyfile(target, backup)
        exercises.build_workspace(self.ex_set, self.workspace, only_file=rel)
        reopened = []
        for ex in self.ex_set.exercises:
            if ex.file == rel and self.record(ex.id)["passed"]:
                self.record(ex.id)["passed"] = False
                reopened.append(ex.id)
        self.save()
        return os.path.normpath(target), backup and os.path.normpath(backup), reopened

    def path_for(self, exercise):
        return os.path.normpath(os.path.join(self.workspace, exercise.file)) if exercise.file else self.workspace

    # ------------------------------------------------------------ progress queries
    def passed(self, exercise_id):
        return self.record(exercise_id)["passed"]

    def next_unfinished(self):
        return next((ex for ex in self.ex_set.exercises if not self.passed(ex.id)), None)

    def solution_unlocked(self, exercise):
        rec = self.record(exercise.id)
        return rec["passed"] or rec["hints"] >= len(exercise.hints) or rec["fails"] >= SOLUTION_AFTER_FAILS

    # ------------------------------------------------------------ actions
    def show(self, exercise):
        ui.banner("%s · %s" % (exercise.id, exercise.title), color="orange")
        print()
        if exercise.file:
            print(style("  File: ", "grey") + style(self.path_for(exercise), "cyan"))
            print(style("  Implement: ", "grey") + style(", ".join(exercise.stubs), "cyan"))
            print()
        ui.render(exercise.task)
        rec = self.record(exercise.id)
        for n in range(rec["hints"]):
            print()
            print(style("  Hint %d/%d:" % (n + 1, len(exercise.hints)), "yellow"))
            ui.render(exercise.hints[n], indent=4)
        print()
        status = "passed ✔" if rec["passed"] else "not passed yet"
        print(style("  Status: %s · hints %d/%d · checks run %d" % (status, rec["hints"], len(exercise.hints),
                                                                   rec["checks"]), "grey"))

    def check(self, exercise):
        """Run the exercise's tests against the workspace, record and display the result. Returns passed."""
        self.ensure_workspace()
        rec = self.record(exercise.id)
        if exercise.kind == "suite":
            if not checker.pytest_available():
                print(style("  The capstone uses pytest. Install it first:", "yellow"))
                print(style("    python -m pip install -r requirements-dev.txt", "cyan"))
                return False
            print(style("  Running the full ChangeGate test suite against your workspace...", "grey"))
            passed = checker.run_suite(self.ex_set) == 0
        else:
            print(style("  Checking %s against %s ..." % (exercise.id, display_path(self.path_for(exercise))), "grey"))
            result = checker.run_check(self.ex_set, exercise)
            print()
            checker.show(result)
            passed = result.passed
            # only a real attempt counts towards unlocking the solution: code still at TODO doesn't
            untouched = any(r["status"] == "todo" for r in result.results)
            if not passed and not untouched and not result.blocking_todos() and not result.import_error:
                rec["fails"] += 1
        rec["checks"] += 1
        self.prog.stats["runs"] += 1
        if passed and not rec["passed"]:
            rec["passed"] = True
            rec["passed_on"] = datetime.date.today().isoformat()
            self.prog.stats["solved"] += 1
            self.prog.stats["first_try"] += rec["checks"] == 1
            self.prog.stats["without_hints"] += rec["hints"] == 0
            self.profile.record_answer(rec["checks"] == 1 and rec["hints"] == 0)
        self.save()
        if passed:
            nxt = self.next_unfinished()
            print()
            print(style("  ✔ %s complete." % exercise.id, "lime", "bold") +
                  (style("  Next: %s - %s" % (nxt.id, nxt.title), "cyan") if nxt else ""))
        elif exercise.kind == "unit" and rec["fails"] >= 2 and rec["hints"] < len(exercise.hints):
            print(style("  Stuck? `python learn.py hint %s` (or h in the app) reveals the next hint." % exercise.id, "yellow"))
        return passed

    def hint(self, exercise):
        rec = self.record(exercise.id)
        total = len(exercise.hints)
        if rec["hints"] >= total:
            print(style("  You've seen all %d hints. The reference solution is unlocked." % total, "grey"))
            for n in range(total):
                print(style("  Hint %d/%d:" % (n + 1, total), "yellow"))
                ui.render(exercise.hints[n], indent=4)
            return
        rec["hints"] += 1
        self.prog.stats["hints"] += 1
        self.save()
        print(style("  Hint %d/%d:" % (rec["hints"], total), "yellow", "bold"))
        ui.render(exercise.hints[rec["hints"] - 1], indent=4)
        if rec["hints"] == total:
            print(style("  That was the last hint; the reference solution is now available.", "grey"))

    def solution(self, exercise, confirm=None):
        rec = self.record(exercise.id)
        if exercise.kind != "unit":
            print(style("  The capstone has no single solution - each failing test points to an earlier exercise.", "grey"))
            return False
        if not self.solution_unlocked(exercise):
            print(style("  The reference solution unlocks after every hint (%d/%d seen) or %d failed checks (%d so far)."
                        % (rec["hints"], len(exercise.hints), SOLUTION_AFTER_FAILS, rec["fails"]), "grey"))
            return False
        if confirm and not rec["passed"] and not confirm("Show the reference solution for %s?" % exercise.id):
            return False
        if not rec["passed"] and not rec["solution"]:
            rec["solution"] = True
            self.prog.stats["solutions"] += 1
            self.save()
        ui.code_box(exercises.solution_source(self.ex_set, exercise), title="Reference: " + exercise.file, color="purple")
        if not rec["passed"]:
            ui.render("Read it, close it, then write your own version - copying it in won't teach you much. "
                      "Run the check when you're done.", indent=4)
        return True

    def listing(self):
        todos = exercises.todo_count(self.ex_set) if os.path.isdir(self.workspace) else {}
        current = None
        nxt = self.next_unfinished()
        for ex in self.ex_set.exercises:
            if ex.phase != current:
                current = ex.phase
                print(style("  Phase %d" % ex.phase, "gold", "bold"))
            rec = self.record(ex.id)
            if rec["passed"]:
                mark = style("✔", "lime")
            elif nxt and ex.id == nxt.id:
                mark = style("▸", "yellow")
            else:
                mark = style("·", "grey")
            extra = ""
            if not rec["passed"] and todos.get(ex.id):
                extra = style("  %d TODO" % todos[ex.id], "grey")
            print("   %s %s %s%s" % (mark, style(ex.id.ljust(24), "cyan"), ex.title, extra))
        done = sum(self.passed(ex.id) for ex in self.ex_set.exercises)
        print()
        print(style("  %d of %d exercises complete." % (done, len(self.ex_set.exercises)), "white", "bold"))
        if nxt:
            print(style("  Next: python learn.py show %s" % nxt.id, "grey"))


def display_path(path):
    """A path relative to the current directory when possible. os.path.relpath raises on Windows when
    the two are on different drives (e.g. the repo on D: and a temp folder on C:)."""
    try:
        return os.path.relpath(path)
    except ValueError:
        return path


def open_in_editor(path):
    """Open a file in the learner's editor ($VISUAL/$EDITOR, else the OS default). Returns a message."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    try:
        if editor:
            subprocess.Popen(shlex.split(editor, posix=os.name != "nt") + [path])
        elif os.name == "nt":
            os.startfile(path)  # noqa: S606 - opens with the user's associated editor
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-t", path])
        elif shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", path])
        else:
            return "Open this file in your editor: " + path
    except OSError as e:
        return "Couldn't open an editor (%s). Open this file yourself: %s" % (e, path)
    return "Opened %s - save your changes, then check." % path

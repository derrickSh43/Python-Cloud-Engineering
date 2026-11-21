"""Tests for build exercises: stub generation, the check harness, ordering validation, the CLI
commands and the in-app build step - using a tiny throwaway project so they don't depend on the
real curriculum."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pce import checker, exercises, selftest  # noqa: E402
from pce.projects import Project  # noqa: E402

REFERENCE = '''
"""Tiny calculator."""

from dataclasses import dataclass


def add(a, b):
    """Return a + b."""
    return a + b


def sub(a, b):
    # subtract: this comment explains the answer and must be removed
    return a - b


@dataclass(frozen=True)
class Pair:
    """Two numbers."""
    left: int
    right: int

    def total(self):
        return add(self.left, self.right)
'''

MANIFEST = '''
[[exercise]]
id = "demo-add"
phase = 0
title = "Add two numbers"
file = "calc/ops.py"
stubs = ["add"]
test = "test_demo_add.py"
task = "Implement add(a, b)."
hints = ["Use +.", "return a + b", "That's it: return a + b"]

[[exercise]]
id = "demo-sub"
phase = 0
title = "Subtract"
file = "calc/ops.py"
stubs = ["sub"]
test = "test_demo_sub.py"
task = "Implement sub(a, b)."
hints = ["Use -.", "return a - b", "return a - b"]

[[exercise]]
id = "demo-pair"
phase = 0
title = "A pair"
file = "calc/ops.py"
stubs = ["Pair"]
test = "test_demo_pair.py"
task = "Write Pair."
hints = ["dataclass", "frozen", "total uses add"]
'''

TESTS = {
    "test_demo_add.py": 'from calc.ops import add\n\n\ndef test_adds():\n    """add(2, 3) is 5"""\n    assert add(2, 3) == 5, "expected 5"\n',
    "test_demo_sub.py": 'from calc.ops import sub\n\n\ndef test_subtracts():\n    """sub(5, 3) is 2"""\n    assert sub(5, 3) == 2\n',
    "test_demo_pair.py": 'from calc.ops import Pair\n\n\ndef test_pair():\n    """Pair(1, 2).total() is 3"""\n    assert Pair(1, 2).total() == 3\n',
}

CURRICULUM = '''
from pce.lesson import Phase, Lesson, Checkpoint, T, B, Q

PHASES = [Phase("d0", 0, "Demo", "demo", "Demo phase.", lessons=[
    Lesson("d0l1", "Build it", [T("Intro."), B("demo-add", intro="Write add.")], summary="add"),
], checkpoint=Checkpoint("d0cp", "Check", "Quick.", [Q("1+1?", "2", "3")]))]
'''


@pytest.fixture
def demo(tmp_path):
    project = tmp_path / "projects" / "demo"
    (project / "reference" / "calc").mkdir(parents=True)
    (project / "reference" / "calc" / "__init__.py").write_text("")
    (project / "reference" / "calc" / "ops.py").write_text(REFERENCE)
    (project / "exercises" / "tests").mkdir(parents=True)
    (project / "exercises" / "phase0.toml").write_text(MANIFEST)
    for name, body in TESTS.items():
        (project / "exercises" / "tests" / name).write_text(body)
    (project / "curriculum").mkdir()
    (project / "curriculum" / "__init__.py").write_text(CURRICULUM)
    (project / "project.toml").write_text('id = "demo"\ntitle = "Demo"\n')
    return project


def test_load_manifest(demo):
    ex_set = exercises.load(str(demo))
    assert [e.id for e in ex_set.exercises] == ["demo-add", "demo-sub", "demo-pair"]
    assert ex_set.before("demo-pair") == ["demo-add", "demo-sub"]
    with pytest.raises(exercises.ExerciseError):
        ex_set.get("nope")


def test_stub_source_keeps_signatures_and_docstrings():
    stubbed = exercises.stub_source(REFERENCE, [("add", "demo-add"), ("sub", "demo-sub"), ("Pair", "demo-pair")])
    assert 'def add(a, b):\n    """Return a + b."""\n' in stubbed
    assert 'raise NotImplementedError("TODO(demo-add): add")' in stubbed
    assert "return a + b" not in stubbed and "return a - b" not in stubbed
    assert "this comment explains the answer" not in stubbed
    assert "@dataclass" not in stubbed and "class Pair:" in stubbed and "TODO(demo-pair)" in stubbed
    compile(stubbed, "ops.py", "exec")


def test_stub_unknown_symbol():
    with pytest.raises(exercises.ExerciseError):
        exercises.stub_source(REFERENCE, [("missing", "x")])


def test_solution_source(demo):
    ex_set = exercises.load(str(demo))
    assert exercises.solution_source(ex_set, ex_set.get("demo-pair")).startswith("@dataclass(frozen=True)\nclass Pair:")


def test_check_starter_vs_solved(demo, tmp_path):
    ex_set = exercises.load(str(demo))
    starter = exercises.build_workspace(ex_set, str(tmp_path / "w0"))
    result = checker.run_check(ex_set, ex_set.get("demo-add"), src=starter)
    assert not result.passed and result.results[0]["status"] == "todo" and result.results[0]["todo"] == "demo-add"
    solved = exercises.build_workspace(ex_set, str(tmp_path / "w1"), solved=["demo-add"])
    assert checker.run_check(ex_set, ex_set.get("demo-add"), src=solved).passed
    blocked = checker.run_check(ex_set, ex_set.get("demo-pair"), src=solved)
    assert blocked.results[0]["todo"] == "demo-pair"


def test_check_reports_failures_and_syntax_errors(demo, tmp_path):
    ex_set = exercises.load(str(demo))
    ws = Path(exercises.build_workspace(ex_set, str(tmp_path / "w")))
    ops = ws / "calc" / "ops.py"
    ops.write_text(ops.read_text().replace('raise NotImplementedError("TODO(demo-add): add")', "return a * b"))
    result = checker.run_check(ex_set, ex_set.get("demo-add"), src=str(ws))
    assert result.results[0]["status"] == "fail" and result.results[0]["message"] == "expected 5"
    assert result.results[0]["doc"] == "add(2, 3) is 5"
    ops.write_text(ops.read_text().replace("return a * b", "return (a +"))
    broken = checker.run_check(ex_set, ex_set.get("demo-add"), src=str(ws))
    assert broken.import_error["type"] == "SyntaxError" and broken.import_error["where"][0] == "calc/ops.py"


def test_check_times_out(demo, tmp_path):
    ex_set = exercises.load(str(demo))
    ws = Path(exercises.build_workspace(ex_set, str(tmp_path / "w")))
    ops = ws / "calc" / "ops.py"
    ops.write_text(ops.read_text().replace('raise NotImplementedError("TODO(demo-add): add")', "while True: pass"))
    assert checker.run_check(ex_set, ex_set.get("demo-add"), src=str(ws), timeout=2).timed_out


def test_ordering_validation(demo):
    project = Project(str(demo), {"id": "demo", "title": "Demo"})
    problems, count = selftest.exercise_problems(project)
    assert count == 3 and problems == []
    # a test that passes without the exercise being solved is caught
    (demo / "exercises" / "tests" / "test_demo_sub.py").write_text("def test_nothing():\n    assert True\n")
    problems, _ = selftest.exercise_problems(project)
    assert problems == [("demo-sub", "tests already pass before the exercise is solved")]


def test_ordering_catches_dependency_on_later_exercise(demo):
    # demo-add's test secretly needs sub (a later exercise)
    (demo / "exercises" / "tests" / "test_demo_add.py").write_text(
        "from calc.ops import add, sub\n\n\ndef test_adds():\n    assert add(2, 3) == 5 and sub(1, 1) == 0\n")
    problems, _ = selftest.exercise_problems(Project(str(demo), {"id": "demo", "title": "Demo"}))
    assert problems and problems[0][0] == "demo-add" and "fail with the reference" in problems[0][1]


def learn(args, tmp_path, stdin=""):
    env = dict(os.environ, PCE_PROJECTS_DIR=str(tmp_path / "projects"), PCE_PROGRESS_DIR=str(tmp_path / "progress"),
               NO_COLOR="1")
    return subprocess.run([sys.executable, str(ROOT / "learn.py"), "--project", "demo"] + args, input=stdin,
                          capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(ROOT), timeout=120)


def progress(tmp_path):
    return json.loads((tmp_path / "progress" / "profile.json").read_text())["projects"]["demo"]["exercises"]


def test_cli_flow(demo, tmp_path):
    out = learn(["exercises"], tmp_path)
    assert "demo-add" in out.stdout and "0 of 3" in out.stdout
    assert not (demo / "workspace").exists()
    out = learn(["check"], tmp_path)                      # next unfinished = demo-add; creates the workspace
    assert out.returncode == 1 and "not written yet" in out.stdout and (demo / "workspace").is_dir()
    assert progress(tmp_path)["demo-add"]["fails"] == 0, "an untouched TODO is not an attempt"
    out = learn(["solution", "demo-add"], tmp_path)
    assert "unlocks after" in out.stdout and "return a + b" not in out.stdout
    for _ in range(3):
        learn(["hint", "demo-add"], tmp_path)
    out = learn(["solution", "demo-add"], tmp_path)
    assert "return a + b" in out.stdout
    ops = demo / "workspace" / "calc" / "ops.py"
    ops.write_text(ops.read_text().replace('raise NotImplementedError("TODO(demo-add): add")', "return a + b"))
    out = learn(["check", "demo-add"], tmp_path)
    assert out.returncode == 0 and "Next: demo-sub" in out.stdout
    rec = progress(tmp_path)["demo-add"]
    assert rec["passed"] and rec["hints"] == 3 and rec["solution"] is True
    out = learn(["workspace", "reset", "calc/ops.py"], tmp_path)
    assert "back to TODO" in out.stdout and (demo / "workspace" / "calc" / "ops.py.bak").exists()
    assert progress(tmp_path)["demo-add"]["passed"] is False


def test_cli_selftest_includes_exercises(demo, tmp_path):
    out = learn(["selftest"], tmp_path)
    assert out.returncode == 0, out.stdout
    assert "3 build exercises checked" in out.stdout


def test_build_step_in_the_app(demo, tmp_path):
    ex_set = exercises.load(str(demo))
    exercises.build_workspace(ex_set, str(demo / "workspace"), solved=["demo-add"])   # learner already wrote it
    keys = ["Sam", "", "1", "", "",        # name, intro, continue, phase overview, text step
            "",                            # Enter before checking: not allowed yet
            "h",                           # a hint
            "c",                           # check -> passes
            "",                            # continue
            "",                            # lesson complete
            "n", "0"]
    out = learn([], tmp_path, "\n".join(keys) + "\n")
    assert "BUILD: ADD TWO NUMBERS" in out.stdout, out.stdout[-3000:]
    assert "Run the checks with c" in out.stdout and "Hint 1/3" in out.stdout
    assert "All 1 checks pass" in out.stdout and "LESSON COMPLETE" in out.stdout
    saved = json.loads((tmp_path / "progress" / "profile.json").read_text())["projects"]["demo"]
    assert saved["completed_lessons"] == ["d0l1"] and saved["exercises"]["demo-add"]["passed"]

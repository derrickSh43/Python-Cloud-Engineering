"""End-to-end: a scripted learner plays through the ENTIRE real course in the actual app.

Every phase, lesson and checkpoint, in order, through the real engine and editor: answering each quiz,
typing each prediction, typing each exercise solution line by line into the editor and running it,
and passing every build exercise against a workspace - finishing with the capstone, which runs the full
ChangeGate test suite against that workspace. The test then checks the saved progress says the course
is complete.

It works on a temporary copy of the project, so the repository's own workspace is never touched.
"""

import builtins
import random
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pce import checker, exercises  # noqa: E402
from pce.grader import normalize  # noqa: E402
from pce.runner import run_code  # noqa: E402

PROJECT = ROOT / "projects" / "01-cloud-change-control"

pytestmark = pytest.mark.skipif(not checker.pytest_available(), reason="the capstone needs pytest")


class Learner:
    """Answers the app's prompts. While a step is on screen it answers from that step's data;
    between steps it answers the menus and pauses it expects - and fails loudly on anything else."""

    def __init__(self):
        self.queue = []
        self.step = None
        self.finished = False
        self.prompts = 0

    def answers_for(self, step):
        kind = step["type"]
        if kind in ("text", "example"):
            return [""]
        if kind == "quiz":
            return ["a", ""]                    # random.shuffle is disabled, so the correct option is (a)
        if kind == "predict":
            result = run_code(step["code"], step["inputs"], files=step["files"])
            return normalize(result.output).split("\n") + [""]
        if kind == "code":
            return [":clear"] + step["solution"].split("\n") + ["run", ""]
        if kind == "build":
            return ["c", ""]                    # the workspace already contains working code
        raise AssertionError("unknown step type %r" % kind)

    def __call__(self, prompt=""):
        self.prompts += 1
        text = re.sub(r"\x1b\[[0-9;]*m", "", str(prompt)).strip()
        if self.queue:
            return self.queue.pop(0)
        if "What should I call you" in text:
            return "Scripted Learner"
        if text.startswith("▸ Press Enter"):
            return ""
        if text.startswith("Choose:"):
            return "0" if self.finished else "1"
        if text.startswith("Continue to the next lesson?"):
            return "y"
        where = "while showing a %s step" % self.step["type"] if self.step else "between steps"
        raise AssertionError("unexpected prompt %s: %r" % (where, text))


@pytest.fixture
def course(tmp_path, monkeypatch):
    """A private copy of the project with a fully written workspace, and isolated progress."""
    projects_dir = tmp_path / "projects"
    copy = projects_dir / PROJECT.name
    shutil.copytree(PROJECT, copy, ignore=shutil.ignore_patterns("workspace", "__pycache__", "*.egg-info",
                                                                  "approvals", "changegate-audit.jsonl"))
    ex_set = exercises.load(str(copy))
    exercises.build_workspace(ex_set, ex_set.workspace_dir, solved=[e.id for e in ex_set.exercises])
    monkeypatch.setenv("PCE_PROJECTS_DIR", str(projects_dir))
    monkeypatch.setenv("PCE_PROGRESS_DIR", str(tmp_path / "progress"))
    return copy, ex_set


def test_play_the_whole_course(course, monkeypatch):
    copy, ex_set = course
    from pce import engine
    from pce.progress import Profile

    learner = Learner()
    monkeypatch.setattr(builtins, "input", learner)
    monkeypatch.setattr(random, "shuffle", lambda items: None)

    original_do_step = engine.App.do_step
    original_complete = engine.App.course_complete
    seen = {"steps": 0, "by_type": {}}

    def do_step(self, step, ctx):
        assert not learner.queue, "unused answers left over: %r" % learner.queue
        learner.step = step
        learner.queue = learner.answers_for(step)
        seen["steps"] += 1
        seen["by_type"][step["type"]] = seen["by_type"].get(step["type"], 0) + 1
        result = original_do_step(self, step, ctx)
        assert not learner.queue, "step %r finished but answers were left: %r" % (step["type"], learner.queue)
        learner.step = None
        return result

    def course_complete(self):
        learner.finished = True
        return original_complete(self)

    monkeypatch.setattr(engine.App, "do_step", do_step)
    monkeypatch.setattr(engine.App, "course_complete", course_complete)

    engine.App().run()

    assert learner.finished, "the course-complete screen was never reached"
    profile = Profile.load()
    prog = profile.projects["01-cloud-change-control"]
    from pce import projects
    project = projects.find("01-cloud-change-control")
    every_lesson = [lesson["id"] for _, lesson in project.lessons()]
    assert sorted(prog.completed_lessons) == sorted(every_lesson)
    assert set(prog.checkpoints) == {phase["checkpoint"]["id"] for phase in project.phases}
    assert all(not cp["assisted"] for cp in prog.checkpoints.values())
    passed = {eid for eid, rec in prog.exercises.items() if rec["passed"]}
    assert passed == {e.id for e in ex_set.exercises}, "not passed: %s" % ({e.id for e in ex_set.exercises} - passed)
    assert prog.stats["solutions"] == 0 and prog.stats["hints"] == 0
    total_steps = sum(len(l["steps"]) for _, l in project.lessons()) + sum(len(p["checkpoint"]["steps"]) for p in project.phases)
    assert seen["steps"] == total_steps
    assert seen["by_type"]["build"] == len(ex_set.exercises)
    print("played %d steps: %s" % (seen["steps"], seen["by_type"]))


def test_capstone_fails_for_the_untouched_starter(tmp_path):
    copy = tmp_path / PROJECT.name
    shutil.copytree(PROJECT, copy, ignore=shutil.ignore_patterns("workspace", "__pycache__", "*.egg-info"))
    ex_set = exercises.load(str(copy))
    exercises.build_workspace(ex_set, ex_set.workspace_dir)
    assert checker.run_suite(ex_set, extra_args=["-x", "--tb=no", "-p", "no:cacheprovider"]) != 0

"""Tests for the learning platform itself (pce/): projects, progress, grading, self-test and a
scripted walk through the interactive app."""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pce import grader, lesson, projects, selftest  # noqa: E402
from pce.progress import Profile  # noqa: E402


@pytest.fixture
def progress_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PCE_PROGRESS_DIR", str(tmp_path / "progress"))
    return tmp_path / "progress"


def test_discover_projects():
    found = projects.discover()
    assert [p.id for p in found][0] == "01-cloud-change-control"
    project = projects.find("01-cloud-change-control")
    assert project.phases[0]["number"] == 0
    assert projects.find("01-cloud-change-control").title == "Cloud Change Control"


def test_find_unknown_project():
    with pytest.raises(projects.ProjectError, match="No project"):
        projects.find("99-nothing")


def test_discover_rejects_bad_metadata(tmp_path):
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "project.toml").write_text('title = "no id"\n')
    with pytest.raises(projects.ProjectError, match="missing: id"):
        projects.discover(tmp_path)


def test_progress_roundtrip(progress_dir):
    assert Profile.load() is None
    profile = Profile("Sam")
    prog = profile.project("demo")
    prog.completed_lessons.append("l1")
    prog.done_steps.add("l1:0")
    prog.hints["l1:3"] = 2
    prog.note_error("NameError")
    prog.note_error("NameError")
    profile.record_answer(True)
    profile.record_answer(True)
    profile.save()
    loaded = Profile.load()
    assert loaded.name == "Sam" and loaded.best_streak == 2
    p = loaded.project("demo")
    assert p.completed_lessons == ["l1"] and p.done_steps == {"l1:0"} and p.hints == {"l1:3": 2}
    assert p.stats["errors"] == 2 and p.stats["error_types"] == ["NameError"]
    loaded.reset_project("demo")
    assert loaded.project("demo").completed_lessons == []


def test_progress_file_is_valid_json_and_atomic(progress_dir):
    Profile("x").save()
    files = os.listdir(progress_dir)
    assert files == ["profile.json"]
    assert json.loads((progress_dir / "profile.json").read_text())["schema"] == 1


def test_day_streak():
    p = Profile()
    p.touch_day(datetime.date(2026, 1, 1))
    p.touch_day(datetime.date(2026, 1, 2))
    p.touch_day(datetime.date(2026, 1, 2))
    assert p.day_streak == 2
    p.touch_day(datetime.date(2026, 1, 5))
    assert p.day_streak == 1


def test_record_answer_resets_streak():
    p = Profile()
    for clean in (True, True, True, False, True):
        p.record_answer(clean)
    assert p.streak == 1 and p.best_streak == 3


def test_grader_output_and_check():
    step = lesson.C("print hi", 'print("hi")', hints=["a", "b"])
    assert grader.grade(step, 'print("hi")').passed
    assert grader.grade(step, 'print("Hi")').kind == "output"
    assert grader.grade(step, "print(").kind == "error"
    checked = lesson.C("make x", "x = 5", check="assert x == 5, 'x should be 5'", hints=["a", "b"])
    assert grader.grade(checked, "x = 5").passed
    verdict = grader.grade(checked, "x = 4")
    assert verdict.kind == "check" and "x should be 5" in verdict.info["message"]


def test_grader_timeout_and_require():
    step = lesson.C("loop", "for i in range(3):\n    print(i)", require=["for"], hints=["a", "b"])
    assert grader.grade(step, "print(0)\nprint(1)\nprint(2)").kind == "require"
    assert grader.grade(step, "for _ in iter(int, 1):\n    pass").kind == "timeout"


def test_selftest_catches_broken_content():
    bad = lesson.C("print hi", 'print("bye")', check="assert False, 'never passes'", hints=["only one"])
    problems = [p for _, p in selftest.check_step("demo", bad)]
    assert any("solution FAILS" in p for p in problems)
    assert any("graduated hints" in p for p in problems)
    passes_starter = lesson.C("x", 'print("a")', starter='print("a")', hints=["a", "b"])
    assert any("starter" in p for _, p in selftest.check_step("demo", passes_starter))


def test_selftest_checks_code_questions():
    def problems(step):
        return [p for _, p in selftest.check_step("demo", step)]
    assert problems(lesson.Q("What does this print?", "3", "2", code="print(1 + 2)")) == []
    assert any("prints '3'" in p for p in problems(lesson.Q("What does this print?", "2", "3", code="print(1 + 2)")))
    assert problems(lesson.Q("What happens?", "A KeyError", "1", code="{}['x']")) == []
    assert any("doesn't name" in p for p in problems(lesson.Q("What happens?", "None", "A KeyError", code="{}['x']")))


def test_selftest_all_projects_clean():
    assert selftest.run(projects.discover(), out=lambda *_: None) == []


def run_learn(args, stdin, progress_dir):
    env = dict(os.environ, PCE_PROGRESS_DIR=str(progress_dir), NO_COLOR="1")
    return subprocess.run([sys.executable, str(ROOT / "learn.py")] + args, input=stdin, capture_output=True,
                          text=True, encoding="utf-8", env=env, cwd=str(ROOT), timeout=60)


def test_cli_list_and_selftest(progress_dir):
    out = run_learn(["list"], "", progress_dir)
    assert out.returncode == 0 and "01-cloud-change-control" in out.stdout
    out = run_learn(["selftest"], "", progress_dir)
    assert out.returncode == 0 and "0 problems" in out.stdout


def test_scripted_walkthrough_saves_progress(progress_dir):
    """Drive the real app through the orientation lesson 1 with scripted keyboard input."""
    keys = [
        "Sam",              # name
        "",                 # how-it-works pause
        "1",                # continue
        "",                 # phase overview
        "",                 # text step
        "",                 # example step
        "plan", "apply",    # predict (two lines)
        "",                 # pause after predict
        "",                 # text step
        'print("ChangeGate is ready")', "run",   # exercise
        "",                 # continue after exercise
    ]
    # quiz: answer each letter until correct (wrong letters are crossed out, never repeated)
    keys += ["a", "b", "c", ""]
    keys += [""]            # lesson complete pause
    keys += ["n", "0"]      # don't continue; quit
    out = run_learn([], "\n".join(keys) + "\n", progress_dir)
    assert "LESSON COMPLETE" in out.stdout, out.stdout[-2000:]
    saved = json.loads((progress_dir / "profile.json").read_text())
    prog = saved["projects"]["01-cloud-change-control"]
    assert saved["name"] == "Sam"
    assert prog["completed_lessons"] == ["p00l1"]
    assert prog["stats"]["solved"] == 1


def test_resume_position_is_saved(progress_dir):
    keys = ["", "", "1", "", "", ":menu", "0"]   # skip name, start, read one step, leave mid-lesson
    run_learn([], "\n".join(keys) + "\n", progress_dir)
    saved = json.loads((progress_dir / "profile.json").read_text())
    assert saved["projects"]["01-cloud-change-control"]["position"]["p00l1"] == 1

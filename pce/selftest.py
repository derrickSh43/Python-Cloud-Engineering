"""Validates curriculum content so broken lessons never reach a learner.

For every project it checks that: ids are unique; phases are numbered in order and each has a
checkpoint; examples run (or fail when marked error_ok); predictions print something; every
reference solution passes its own exercise; starter code alone does NOT pass; trivial code does
NOT pass; and every exercise offers graduated hints.
"""

from concurrent.futures import ThreadPoolExecutor

from .grader import grade
from .lesson import STEP_TYPES
from .runner import run_code

MIN_HINTS = 2


def check_step(where, step):
    problems = []
    kind = step.get("type")
    if kind not in STEP_TYPES:
        return [(where, "unknown step type %r" % kind)]
    if kind == "example":
        r = run_code(step["code"], step["inputs"], files=step["files"], echo=True)
        if step["error_ok"] and not r.error:
            problems.append("example marked error_ok but ran fine")
        if not step["error_ok"] and not r.ok:
            problems.append("example failed: %r %r timeout=%s" % (r.error, r.crashed, r.timed_out))
    elif kind == "predict":
        r = run_code(step["code"], step["inputs"], files=step["files"])
        if not r.ok:
            problems.append("predict code failed: %r" % (r.error,))
        elif not r.output.strip():
            problems.append("predict prints nothing")
    elif kind == "quiz":
        if step["correct"] in step["wrong"]:
            problems.append("correct answer also listed as wrong")
        if len(step["wrong"]) < 1:
            problems.append("quiz has no wrong answers")
    elif kind == "code":
        v = grade(step, step["solution"])
        if not v.passed:
            problems.append("solution FAILS: %r" % (v,))
        if step["starter"] and grade(step, step["starter"]).passed:
            problems.append("starter code alone passes")
        if grade(step, "x = 1").passed:
            problems.append("trivial code 'x = 1' passes")
        if len(step["hints"]) < MIN_HINTS:
            problems.append("needs at least %d graduated hints (has %d)" % (MIN_HINTS, len(step["hints"])))
    return [(where, p) for p in problems]


def structure_problems(project):
    problems = []
    ids = set()
    for n, phase in enumerate(project.phases):
        where = "%s phase %s" % (project.id, phase.get("number"))
        if n > 0 and phase["number"] != project.phases[n - 1]["number"] + 1:
            problems.append((where, "phase numbers must increase by 1"))
        if not phase["lessons"]:
            problems.append((where, "phase has no lessons"))
        if not phase.get("checkpoint") or not phase["checkpoint"]["steps"]:
            problems.append((where, "phase has no checkpoint steps"))
        for item_id in [phase["id"], phase["checkpoint"]["id"]] + [lesson["id"] for lesson in phase["lessons"]]:
            if item_id in ids:
                problems.append((where, "duplicate id " + item_id))
            ids.add(item_id)
        for lesson in phase["lessons"]:
            if not lesson["summary"].strip():
                problems.append((where, lesson["id"] + " has no summary (reference card)"))
    return problems


def jobs_for(project, only_phase=None):
    jobs = []
    for phase in project.phases:
        if only_phase is not None and phase["number"] != only_phase:
            continue
        for lesson in phase["lessons"]:
            for i, step in enumerate(lesson["steps"]):
                jobs.append(("%s step %d (%s)" % (lesson["id"], i, step["type"]), step))
        for i, step in enumerate(phase["checkpoint"]["steps"]):
            jobs.append(("%s step %d (%s)" % (phase["checkpoint"]["id"], i, step["type"]), step))
    return jobs


def run(projects, only_phase=None, workers=8, out=print):
    failures = []
    total = 0
    for project in projects:
        failures += structure_problems(project)
        jobs = jobs_for(project, only_phase)
        total += len(jobs)
        with ThreadPoolExecutor(workers) as pool:
            for result in pool.map(lambda job: check_step(*job), jobs):
                failures += result
        out("%s: %d phases, %d steps checked" % (project.id, len(project.phases), len(jobs)))
    for where, problem in failures:
        out("FAIL %s - %s" % (where, problem))
    out("%d project(s), %d steps, %d problems" % (len(projects), total, len(failures)))
    return failures

# Verification status

What has been verified, how, and what needs live cloud infrastructure. Updated at every milestone.

## Summary

The whole course - from the first `print()` to a ChangeGate that passes the full test suite - works from a
fresh clone with nothing but Python 3.11+ (pytest from Phase 3). Everything below is verified **without any
cloud account**. What needs live AWS/GCP is listed separately and has **not** been verified.

## Verified locally (no cloud account needed)

| Area | How it is verified |
|---|---|
| **The entire course, played start to finish in the real app** by a scripted learner: all 7 phases, 465 steps (quizzes, predictions, 66 exercises typed into the editor, 49 build steps), every checkpoint, ending with the capstone passing the full suite (193 tests) against the workspace; no hints or solutions | `tests/test_full_course.py` |
| Capstone fails for the untouched starter workspace | `tests/test_full_course.py` |
| Learning platform: project discovery, lesson flow, quizzes, predictions, exercises, graded hints, saved progress, resume | `tests/test_platform.py` (includes a scripted walk through a full lesson in the real app) |
| Every lesson's examples, predictions and exercises (reference passes, starter fails, ≥2 hints) - Phases 0-6, 465 steps; every build exercise embedded in exactly one lesson | `python learn.py selftest` |
| All 48 build exercises: tests fail with only earlier exercises solved and pass once solved (proves the order works) | `python learn.py selftest` |
| Workspace generation, check harness (failures, syntax errors, timeouts), hint/solution gating, file reset, the in-app build step | `tests/test_exercise_system.py` |
| CI gate template: its gate script runs against the reference - safe plans pass (0), a risky plan blocks (1), a HIGH plan needs approval (2); variables/secrets only | `tests/test_ci_template.py` |
| Packaging lesson workflow: `pip install -e workspace`, approve x2, verify → APPROVED, audit verify | run manually (M5) |
| ChangeGate parser, models, providers, config, all 14 policies, risk, decisions | `projects/01-cloud-change-control/tests/` (193 tests) |
| Expected outcome of every sample plan (AWS, GCP, multi-cloud) | `test_risk_and_evaluator.py::test_sample_outcomes` |
| Full approval workflow: evaluate → approve ×2 → verify, self-approval refused, approvals invalid after plan edit | `test_cli.py` |
| Audit chain: modification, deletion, reordering, truncation (with expected head) | `test_audit.py`, `test_cli.py` |
| No secrets or real account ids committed | `tests/test_no_hardcoding.py` |
| CI runs all of the above on Linux and Windows, Python 3.11-3.13 | `.github/workflows/ci.yml` |
| Fresh `git clone` from GitHub, following the README: app start/resume, `exercises`, `check` (creates the workspace), new venv + `pip install -r requirements-dev.txt`, selftest, full test suite, full-course test; `git status` stays clean (workspace and progress are ignored) | run manually on Python 3.13 (M6) |

## Requires live AWS / GCP (Phase 6B - not verified until you run it)

| Area | Why it can't be verified locally |
|---|---|
| Producing plans with `terraform plan` against real providers | needs cloud credentials and API access |
| GitHub OIDC → AWS IAM role, Workload Identity Federation → GCP service account | needs real accounts and a GitHub repository with variables set |
| Protected-environment approval flow and `terraform apply` in CI | needs the above plus configured GitHub environments |

The sample plans in `sample_data/plans/` are hand-authored to match the `terraform show -json`
format (version 1.2) and the attribute names of the hashicorp/aws and hashicorp/google providers.
Phase 6B includes a step to diff a real plan from your account against the samples.

## Milestone log

| Milestone | Status |
|---|---|
| M1 Platform port + ChangeGate reference + sample data + tests | done |
| M2 Exercise system: workspace stubs, per-exercise tests, `learn.py check` | done |
| M3 Phases 1-2: 14 lessons + 2 checkpoints, Phase 2 leads into its 8 build exercises | done |
| M4 Phases 3-4: 14 lessons + 2 checkpoints leading into 27 build exercises | done |
| M5 Phases 5-6A (11 lessons + 2 checkpoints, incl. capstone) + offline CI gate template | done |
| M6 End-to-end verification: automated full-course playthrough + fresh-clone run | done |
| M7 Phase 6B cloud (when you choose) | planned |

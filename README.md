# Python Cloud Engineering

Hands-on Python for cloud engineers, in your terminal. Every lesson has you write real code; the app
runs it, checks it, explains errors in plain English, gives graduated hints, and saves your progress.

The platform hosts independent **learning projects**. Each one takes you from fundamentals to a real,
tested tool.

| Project | You build | Status |
|---|---|---|
| [01 - Cloud Change Control](projects/01-cloud-change-control/) | **Cloud ChangeGate**: Terraform plan evaluation, AWS + GCP security policies, risk classification, signed approvals, audit trail, CLI for CI/CD | Phases 0-2 playable; 3-6 in progress (see [build status](projects/01-cloud-change-control/docs/VERIFICATION.md)) |

## Quick start

Requires **Python 3.11+** and nothing else to begin.

```
git clone https://github.com/derrickSh43/Python-Cloud-Engineering.git
cd Python-Cloud-Engineering
python learn.py
```

Use a terminal at least 90 characters wide.

| Command | What it does |
|---|---|
| `python learn.py` | start or continue |
| `python learn.py list` | list projects |
| `python learn.py --project 01-cloud-change-control` | open a specific project |
| `python learn.py --unlock-all` | open every phase (instructors / reviewers) |
| `python learn.py selftest` | validate every lesson and exercise |
| `python learn.py reset` | erase progress for the current project |
| `python learn.py exercises` | list build exercises and your progress |
| `python learn.py show ID` / `check [ID]` / `hint ID` / `solution ID` | work on a build exercise |
| `python learn.py workspace reset FILE` | restore one of your workspace files to its starting state |

## How a course works

- **Phases** contain short **lessons** and end with a **checkpoint** that unlocks the next phase.
- Lessons mix explanations, **live examples**, **questions**, **"what will this print?"** and **exercises**.
- **Build exercises** have you write the real application piece by piece in your own editor. Your
  `workspace/` starts as the finished tool with every piece you'll write left as a TODO;
  `python learn.py check <id>` runs focused tests against your code and explains what's wrong.
- **Hints are graduated**: each `:hint` reveals more. Reference solutions unlock only after you've used
  every hint or made several attempts.
- Finished lessons become **reference cards**; **review practice** mixes old questions so they stick.
- A **playground** runs anything you like.

No accounts, no cloud, no internet needed for the course itself. Cloud integration (AWS, GCP) is an
optional final phase, and every value it needs is supplied through config files and CI variables,
never hard-coded.

## Repository layout

```
learn.py                 entry point
pce/                     the learning platform (standard library only)
projects/<id>/           independent learning projects (curriculum, reference, tests, data, docs)
tests/                   platform tests + repository guards
```

## For contributors

```
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
python learn.py selftest
```

A new project is a folder under `projects/` with a `project.toml` and a `curriculum/` package that
defines `PHASES`; see `pce/lesson.py` for the content format. The learning experience was adapted
from [Python Quest](https://github.com/derrickSh43/python_quest), with the game elements removed.

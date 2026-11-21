"""Saved progress: one JSON file per learner, with a separate section for every project.

Saved to .progress/profile.json at the repository root (git-ignored). Set PCE_PROGRESS_DIR to keep
it somewhere else (the tests do this). Writes are atomic so a crash can't corrupt the file.
"""

import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_VERSION = 1


def progress_dir():
    return os.environ.get("PCE_PROGRESS_DIR") or os.path.join(ROOT, ".progress")


def profile_path():
    return os.path.join(progress_dir(), "profile.json")


def _new_stats():
    return {
        "solved": 0, "first_try": 0, "without_hints": 0, "hints": 0, "solutions": 0, "runs": 0,
        "errors": 0, "error_types": [], "timeouts": 0, "quiz_right": 0, "quiz_total": 0,
        "predict_right": 0, "predict_total": 0, "review_rounds": 0, "playground_runs": 0,
    }


class ProjectProgress:
    """Everything remembered about one project."""

    def __init__(self, data=None):
        data = data or {}
        self.position = data.get("position", {})                 # lesson/checkpoint id -> next step index
        self.completed_lessons = data.get("completed_lessons", [])
        self.checkpoints = data.get("checkpoints", {})           # checkpoint id -> {"mistakes", "assisted", "date"}
        self.done_steps = set(data.get("done_steps", []))        # "id:index" of answered steps
        self.hints = data.get("hints", {})                       # "id:index" -> hints revealed so far
        self.attempts = data.get("attempts", {})                 # "id:index" -> failed runs so far
        self.solutions_viewed = data.get("solutions_viewed", [])
        self.seen_overviews = data.get("seen_overviews", [])
        self.exercises = data.get("exercises", {})               # build exercise id -> see exercise()
        self.stats = _new_stats()
        self.stats.update(data.get("stats", {}))

    def to_dict(self):
        return {
            "position": self.position, "completed_lessons": self.completed_lessons,
            "checkpoints": self.checkpoints, "done_steps": sorted(self.done_steps), "hints": self.hints,
            "attempts": self.attempts, "solutions_viewed": self.solutions_viewed,
            "seen_overviews": self.seen_overviews, "exercises": self.exercises, "stats": self.stats,
        }

    def exercise(self, exercise_id):
        """Progress record for one build exercise (created on first use)."""
        if exercise_id not in self.exercises:
            self.exercises[exercise_id] = {"passed": False, "passed_on": "", "checks": 0, "fails": 0,
                                           "hints": 0, "solution": False}
        return self.exercises[exercise_id]

    def note_error(self, etype):
        self.stats["errors"] += 1
        if etype not in self.stats["error_types"]:
            self.stats["error_types"].append(etype)


class Profile:
    def __init__(self, name=""):
        self.name = name
        self.current_project = None
        self.projects = {}
        self.streak = 0          # answers right first time in a row
        self.best_streak = 0
        self.last_day = ""
        self.day_streak = 0

    def project(self, project_id):
        if project_id not in self.projects:
            self.projects[project_id] = ProjectProgress()
        return self.projects[project_id]

    # ------------------------------------------------------------ persistence
    @classmethod
    def load(cls):
        path = profile_path()
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        profile = cls(data.get("name", ""))
        profile.current_project = data.get("current_project")
        for key in ("streak", "best_streak", "last_day", "day_streak"):
            if key in data:
                setattr(profile, key, data[key])
        profile.projects = {pid: ProjectProgress(p) for pid, p in data.get("projects", {}).items()}
        return profile

    def save(self):
        path = profile_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "schema": SCHEMA_VERSION, "name": self.name, "current_project": self.current_project,
            "streak": self.streak, "best_streak": self.best_streak, "last_day": self.last_day,
            "day_streak": self.day_streak,
            "projects": {pid: p.to_dict() for pid, p in self.projects.items()},
        }
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, path)

    def reset_project(self, project_id):
        self.projects[project_id] = ProjectProgress()

    # ------------------------------------------------------------ bookkeeping
    def touch_day(self, today=None):
        today = today or datetime.date.today()
        if self.last_day == today.isoformat():
            return
        yesterday = (today - datetime.timedelta(days=1)).isoformat()
        self.day_streak = self.day_streak + 1 if self.last_day == yesterday else 1
        self.last_day = today.isoformat()

    def record_answer(self, clean):
        """clean = right on the first try without hints."""
        if clean:
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.streak = 0

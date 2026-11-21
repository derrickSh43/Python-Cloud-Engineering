"""Finds learning projects under projects/ and loads their curriculum.

A project is a folder containing `project.toml`:

    id = "01-cloud-change-control"
    title = "Cloud Change Control"
    summary = "One sentence shown in the project picker."
    order = 1

and a `curriculum/` Python package whose `__init__.py` defines `PHASES` (a list of Phase dicts).
Projects are completely independent: each has its own curriculum, exercises and saved progress.
"""

import importlib.util
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(ROOT, "projects")


class ProjectError(Exception):
    pass


class Project:
    def __init__(self, path, meta):
        self.path = path
        self.id = meta["id"]
        self.title = meta["title"]
        self.summary = meta.get("summary", "")
        self.order = meta.get("order", 999)
        self._phases = None

    def __repr__(self):
        return "Project(%r)" % self.id

    @property
    def phases(self):
        if self._phases is None:
            self._phases = load_curriculum(self)
        return self._phases

    def lessons(self):
        """Every (phase, lesson) pair in order."""
        return [(phase, lesson) for phase in self.phases for lesson in phase["lessons"]]


def default_dir():
    """projects/ in the repository, or $PCE_PROJECTS_DIR (used by the platform's own tests)."""
    return os.environ.get("PCE_PROJECTS_DIR") or PROJECTS_DIR


def discover(projects_dir=None):
    projects_dir = projects_dir or default_dir()
    projects = []
    if not os.path.isdir(projects_dir):
        return projects
    for name in sorted(os.listdir(projects_dir)):
        meta_path = os.path.join(projects_dir, name, "project.toml")
        if not os.path.isfile(meta_path):
            continue
        with open(meta_path, "rb") as f:
            try:
                meta = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ProjectError("%s is not valid TOML: %s" % (meta_path, e)) from None
        missing = [key for key in ("id", "title") if key not in meta]
        if missing:
            raise ProjectError("%s is missing: %s" % (meta_path, ", ".join(missing)))
        projects.append(Project(os.path.join(projects_dir, name), meta))
    projects.sort(key=lambda p: (p.order, p.id))
    return projects


def find(project_id, projects_dir=None):
    for project in discover(projects_dir):
        if project.id == project_id or os.path.basename(project.path) == project_id:
            return project
    raise ProjectError("No project called %r. Available: %s" % (
        project_id, ", ".join(p.id for p in discover(projects_dir)) or "(none)"))


def load_curriculum(project):
    init = os.path.join(project.path, "curriculum", "__init__.py")
    if not os.path.isfile(init):
        raise ProjectError("%s has no curriculum/__init__.py" % project.path)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)  # so curriculum files can `from pce.lesson import ...`
    module_name = "pce_curriculum_" + re.sub(r"\W", "_", project.id)
    spec = importlib.util.spec_from_file_location(
        module_name, init, submodule_search_locations=[os.path.dirname(init)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    phases = getattr(module, "PHASES", None)
    if not isinstance(phases, list):
        raise ProjectError("%s must define PHASES = [...]" % init)
    return phases

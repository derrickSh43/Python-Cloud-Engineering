"""Build exercises: learners implement pieces of a real application in their own files.

A project declares its exercises in `exercises/*.toml` (sorted by filename, then in file order):

    [[exercise]]
    id = "p2-read-plan"
    phase = 2
    title = "Read a plan file safely"
    file = "changegate/plan_parser.py"          # path inside the reference/workspace package root
    stubs = ["read_plan_bytes"]                  # functions, classes, or Class.method in that file
    test = "test_p2_read_plan.py"                # in exercises/tests/
    task = '''What to build (light markdown).'''
    hints = ["gentle nudge", "the approach", "nearly the answer"]

The learner's workspace is GENERATED from the reference implementation: every symbol listed in any
exercise has its body replaced with `raise NotImplementedError("TODO(<exercise id>)")`, keeping
signatures and docstrings. So the starter code can never drift from the reference, and the reference
solution for an exercise is simply the original source of its stubs.
"""

import ast
import os
import shutil
import tomllib
from dataclasses import dataclass, field

COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.egg-info", "build", "dist", "*.pyc")
TODO_PREFIX = "TODO("


class ExerciseError(Exception):
    pass


@dataclass
class Exercise:
    id: str
    phase: int
    title: str
    file: str
    stubs: list
    test: str
    task: str
    hints: list
    order: int = 0
    kind: str = "unit"          # "unit" (per-exercise tests) or "suite" (the full pytest suite)
    extra: dict = field(default_factory=dict)


@dataclass
class ExerciseSet:
    project_path: str
    exercises: list
    reference_dir: str
    workspace_dir: str
    tests_dir: str
    suite_dir: str

    def get(self, exercise_id):
        for ex in self.exercises:
            if ex.id == exercise_id:
                return ex
        raise ExerciseError("No exercise called %r. Run `python learn.py exercises` to list them." % exercise_id)

    def index(self, exercise_id):
        return self.exercises.index(self.get(exercise_id))

    def before(self, exercise_id):
        """Ids of every exercise that comes before this one."""
        return [ex.id for ex in self.exercises[: self.index(exercise_id)]]

    def stubbed_files(self):
        return sorted({ex.file for ex in self.exercises if ex.kind == "unit"})


# ---------------------------------------------------------------- loading

def load(project_path):
    """Load a project's exercises, or None if it has none."""
    project_path = os.path.abspath(project_path)
    ex_dir = os.path.join(project_path, "exercises")
    if not os.path.isdir(ex_dir):
        return None
    manifests = sorted(f for f in os.listdir(ex_dir) if f.endswith(".toml"))
    exercises, seen = [], set()
    for name in manifests:
        with open(os.path.join(ex_dir, name), "rb") as f:
            try:
                data = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ExerciseError("exercises/%s is not valid TOML: %s" % (name, e)) from None
        for raw in data.get("exercise", []):
            missing = [k for k in ("id", "phase", "title", "task", "hints") if k not in raw]
            if missing:
                raise ExerciseError("exercises/%s: exercise %r is missing %s" % (name, raw.get("id"), ", ".join(missing)))
            if raw["id"] in seen:
                raise ExerciseError("duplicate exercise id %r" % raw["id"])
            seen.add(raw["id"])
            kind = raw.get("kind", "unit")
            exercises.append(Exercise(
                id=raw["id"], phase=raw["phase"], title=raw["title"], file=raw.get("file", ""),
                stubs=list(raw.get("stubs", [])), test=raw.get("test", ""), task=raw["task"].strip(),
                hints=list(raw["hints"]), order=len(exercises), kind=kind,
                extra={k: v for k, v in raw.items() if k not in Exercise.__dataclass_fields__}))
    return ExerciseSet(
        project_path=project_path, exercises=exercises,
        reference_dir=os.path.join(project_path, "reference"),
        workspace_dir=os.path.join(project_path, "workspace"),
        tests_dir=os.path.join(ex_dir, "tests"),
        suite_dir=os.path.join(project_path, "tests"),
    )


# ---------------------------------------------------------------- finding symbols

def _decorated_start(node):
    return min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])


def find_symbol(tree, dotted):
    """Find `name` or `Class.method` at module level. Returns the AST node or None."""
    parts = dotted.split(".")
    scope = tree.body
    node = None
    for part in parts:
        node = next((n for n in scope if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and n.name == part), None)
        if node is None:
            return None
        scope = node.body if isinstance(node, ast.ClassDef) else []
    return node


def symbol_source(source, dotted):
    """The full source (decorators included) of a symbol, de-indented for display."""
    tree = ast.parse(source)
    node = find_symbol(tree, dotted)
    if node is None:
        raise ExerciseError("symbol %s not found" % dotted)
    lines = source.split("\n")[_decorated_start(node) - 1: node.end_lineno]
    indent = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[indent:] for l in lines)


# ---------------------------------------------------------------- stubbing

def _docstring_node(node):
    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) \
            and isinstance(node.body[0].value.value, str):
        return node.body[0]
    return None


def stub_source(source, stubs):
    """Return `source` with each (dotted_name, exercise_id) in `stubs` replaced by a TODO stub."""
    tree = ast.parse(source)
    lines = source.split("\n")
    edits = []  # (start_line, end_line, replacement_lines) - 1-based inclusive
    for dotted, ex_id in stubs:
        node = find_symbol(tree, dotted)
        if node is None:
            raise ExerciseError("cannot stub %s: not found" % dotted)
        todo = 'raise NotImplementedError("%s%s): %s")' % (TODO_PREFIX, ex_id, dotted)
        if isinstance(node, ast.ClassDef):
            pad = " " * node.col_offset
            doc = ast.get_docstring(node)
            body = [pad + "class %s:" % node.name,
                    pad + '    """TODO(%s): write this class. Run `python learn.py show %s` for the task.%s"""' % (
                        ex_id, ex_id, ("\n\n" + pad + "    " + doc.replace("\n", "\n" + pad + "    ")) if doc else ""),
                    "",
                    pad + "    def __init__(self, *args, **kwargs):",
                    pad + "        " + todo]
            edits.append((_decorated_start(node), node.end_lineno, body))
        else:
            doc = _docstring_node(node)
            first_body = node.body[0]
            pad = " " * first_body.col_offset
            if doc is not None:
                keep_until = doc.end_lineno
                replacement = [pad + "# TODO(%s): implement this. `python learn.py show %s`" % (ex_id, ex_id), pad + todo]
            else:
                # keep only the `def ...:` header - comments before the first statement often explain the answer
                keep_until = first_body.lineno - 1
                for i in range(node.lineno - 1, first_body.lineno - 1):
                    if lines[i].split("#")[0].rstrip().endswith(":"):
                        keep_until = i + 1
                        break
                replacement = [pad + "# TODO(%s): implement this. `python learn.py show %s`" % (ex_id, ex_id), pad + todo]
            edits.append((keep_until + 1, node.end_lineno, replacement))
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start - 1:end] = replacement
    result = "\n".join(lines)
    ast.parse(result)  # the starter must always be valid Python
    return result


def stubs_by_file(exercise_set, solved=()):
    """{file: [(dotted, exercise_id), ...]} for every exercise not in `solved`."""
    solved = set(solved)
    result = {}
    for ex in exercise_set.exercises:
        if ex.kind != "unit" or ex.id in solved:
            continue
        for dotted in ex.stubs:
            result.setdefault(ex.file, []).append((dotted, ex.id))
    return result


def build_workspace(exercise_set, out_dir, solved=(), only_file=None):
    """Write a workspace to `out_dir`: the reference tree with unsolved exercises stubbed out.
    With only_file, (re)write just that one file."""
    plan = stubs_by_file(exercise_set, solved)
    if only_file is None:
        if os.path.exists(out_dir):
            raise ExerciseError("%s already exists" % out_dir)
        shutil.copytree(exercise_set.reference_dir, out_dir, ignore=COPY_IGNORE)
        files = plan.keys()
    else:
        files = [only_file]
    for rel in files:
        src_path = os.path.join(exercise_set.reference_dir, rel)
        with open(src_path, encoding="utf-8") as f:
            source = f.read()
        if plan.get(rel):
            source = stub_source(source, plan[rel])
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(source)
    readme = os.path.join(out_dir, "README.md")
    if only_file is None:
        with open(readme, "w", encoding="utf-8", newline="\n") as f:
            f.write(WORKSPACE_README)
    return out_dir


def solution_source(exercise_set, exercise):
    with open(os.path.join(exercise_set.reference_dir, exercise.file), encoding="utf-8") as f:
        source = f.read()
    return "\n\n".join(symbol_source(source, dotted) for dotted in exercise.stubs)


def todo_count(exercise_set):
    """{exercise_id: number of TODO markers still present in the learner's workspace}."""
    counts = {}
    for ex in exercise_set.exercises:
        if ex.kind != "unit":
            continue
        path = os.path.join(exercise_set.workspace_dir, ex.file)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()
        counts[ex.id] = text.count('NotImplementedError("' + TODO_PREFIX + ex.id + ")")
    return counts


WORKSPACE_README = """# Your ChangeGate workspace

This folder is yours. It was generated from the reference implementation with every exercise's code
replaced by `raise NotImplementedError("TODO(<exercise id>)...")`. Fill them in one exercise at a time:

    python learn.py show <exercise-id>      read the task
    python learn.py check <exercise-id>     run that exercise's tests against this folder
    python learn.py hint <exercise-id>      reveal the next hint
    python learn.py exercises               see what's done and what's next

`python learn.py workspace reset FILE` restores one file to its starting state (a .bak copy of your
version is kept). This folder is git-ignored, so your work never conflicts with course updates.
"""

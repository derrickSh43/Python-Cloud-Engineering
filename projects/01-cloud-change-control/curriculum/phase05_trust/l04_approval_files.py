from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l4", "Approval files", [
    T("""
        **Approvals as files**

        `changegate approve plan.json --approver alice` writes a small JSON file into an `approvals/` folder.
        `changegate verify plan.json` reads every file in that folder. Files are simple to pass between CI
        jobs (as artifacts), easy to inspect, and easy to delete when stale.

        File names should be **predictable and safe**: the first 12 characters of the plan hash plus the
        approver's name, with anything that isn't a letter, digit, `_`, `.` or `-` replaced, so a name like
        `alice smith` or `../../etc` can't produce a strange or dangerous path.
    """),
    Ex("""
        import re
        def safe(text):
            return re.sub(r"[^A-Za-z0-9_.-]", "_", text)[:64] or "approver"

        for name in ["alice", "alice smith", "../../etc/passwd", ""]:
            print(repr(name), "->", safe(name))
    """, note="`re.sub(pattern, replacement, text)` replaces every match. `[^...]` means 'any character NOT in this set'."),
    T("""
        **Finding files: glob**

        `Path.glob("*.json")` yields every path in a folder matching a pattern (`*` matches any characters).
        `sorted(...)` makes the order predictable - important for reproducible output and tests.

        ```
        files = sorted(Path("approvals").glob("*.json"))
        ```

        `Path.mkdir(parents=True, exist_ok=True)` creates a folder (and any missing parents) and doesn't
        complain if it already exists.
    """),
    Ex("""
        from pathlib import Path
        folder = Path("approvals")
        folder.mkdir(parents=True, exist_ok=True)
        for name in ["b.json", "a.json", "notes.txt"]:
            (folder / name).write_text("{}", encoding="utf-8")
        print([p.name for p in sorted(folder.glob("*.json"))])
    """),
    T("""
        **Robust loading**

        One malformed file must not break everything - and must never count as an approval. Load each file
        inside its own `try`, collect a problem message for anything that fails, and carry on:

        ```
        approvals, problems = [], []
        for f in files:
            try:
                approvals.append(Approval.from_dict(json.loads(f.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError, ApprovalError) as e:
                problems.append("%s: %s" % (f.name, e))
        return approvals, problems
        ```

        Returning **two** things - the good results and the problems - lets the report show both.
        `OSError` is the parent of file errors like `FileNotFoundError` and `PermissionError`.
    """),
    P("""
        import json
        results, problems = [], []
        for name, text in [("a.json", '{"ok": 1}'), ("b.json", "{bad"), ("c.json", '{"ok": 2}')]:
            try:
                results.append(json.loads(text)["ok"])
            except json.JSONDecodeError as e:
                problems.append(name)
        print(results, problems)
    """),
    Q("An approvals folder has 3 valid files and 1 corrupt one. What should loading do?",
      "Return the 3 approvals and report a problem for the corrupt file",
      "Raise an error and load nothing", "Ignore the corrupt file silently", "Count the corrupt file as half an approval"),
    C("""
        Write `load_all(folder)` that reads every `*.json` file in `folder` (sorted by name) and returns
        `(values, problems)`: `values` is the list of each file's `"approver"` value; `problems` lists
        `"<file name>: invalid"` for files that aren't valid JSON or lack `"approver"`.

        The folder `approvals/` in your working directory contains `a.json`, `b.json` (broken) and `c.json`.
    """, '''import json
from pathlib import Path

def load_all(folder):
    values, problems = [], []
    for f in sorted(Path(folder).glob("*.json")):
        try:
            values.append(json.loads(f.read_text(encoding="utf-8"))["approver"])
        except (json.JSONDecodeError, KeyError):
            problems.append("%s: invalid" % f.name)
    return values, problems''',
      files={"approvals/a.json": '{"approver": "alice"}', "approvals/b.json": "{broken",
             "approvals/c.json": '{"approver": "bob"}', "approvals/d.json": '{"name": "x"}'},
      check="""
        values, problems = load_all("approvals")
        assert values == ["alice", "bob"], "got %r" % (values,)
        assert problems == ["b.json: invalid", "d.json: invalid"], "got %r" % (problems,)
      """,
      require=["glob", "try"],
      hints=['sorted(Path(folder).glob("*.json")) lists the files.',
             "Catch (json.JSONDecodeError, KeyError) per file and record the problem.",
             'problems.append("%s: invalid" % f.name)']),
    B("p5-approval-files"),
], summary="""
    - Approvals are JSON files in a folder; names = plan hash prefix + sanitised approver
      (`re.sub(r"[^A-Za-z0-9_.-]", "_", text)`).
    - `sorted(Path(dir).glob("*.json"))`; `Path.mkdir(parents=True, exist_ok=True)`.
    - Load each file in its own try; return `(results, problems)`; never count a bad file. `OSError` covers file errors.
""")

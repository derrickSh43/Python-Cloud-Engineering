from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p06l4", "Packaging: a tool anyone can install", [
    T("""
        **From folder to command**

        Right now ChangeGate runs with `python -m changegate ...` from inside its folder. A real tool installs
        with `pip` and gives you a `changegate` command anywhere. That's what packaging does, and it takes one
        file: **pyproject.toml**. Your workspace already has one (copied from the reference):

        ```
        [build-system]
        requires = ["setuptools>=68"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "changegate"
        version = "1.0.0"
        requires-python = ">=3.11"
        dependencies = []

        [project.scripts]
        changegate = "changegate.cli:main"
        ```

        `[project.scripts]` is the **entry point**: installing creates a `changegate` command that imports
        `changegate.cli` and calls `main()`, using its return value as the exit code. `dependencies = []` -
        ChangeGate needs nothing outside the standard library, which makes it easy to trust and audit.
    """),
    T("""
        **Install your own ChangeGate**

        With your virtual environment active, from the repository root:

        ```
        python -m pip install -e projects/01-cloud-change-control/workspace
        changegate --version
        changegate --config projects/01-cloud-change-control/sample_data/changegate.example.toml evaluate projects/01-cloud-change-control/sample_data/plans/aws_risky.json
        ```

        `-e` means **editable**: the command runs your files in place, so edits take effect immediately without
        reinstalling. (If you installed the reference earlier, this replaces it - both are called `changegate`.)
    """),
    T("""
        **python -m and __main__.py**

        `python -m changegate` runs the package's `__main__.py`, which is just:

        ```
        import sys
        from .cli import main
        sys.exit(main())
        ```

        Handy when a `changegate` command isn't on the PATH, or to be sure *which* Python runs it.
    """),
    T("""
        **The full workflow, end to end**

        Try the whole approval flow with your own tool (PowerShell shown; on macOS/Linux use `export NAME=value`):

        ```
        cd projects/01-cloud-change-control/sample_data
        $env:CHANGEGATE_HMAC_KEY = python -c "import secrets; print(secrets.token_hex(32))"
        $env:CHANGEGATE_AUTHOR = "dave"
        changegate --config changegate.example.toml verify plans/aws_db_replace.json      # exit 2
        changegate --config changegate.example.toml approve plans/aws_db_replace.json --approver alice
        changegate --config changegate.example.toml approve plans/aws_db_replace.json --approver bob
        changegate --config changegate.example.toml verify plans/aws_db_replace.json      # APPROVED, exit 0
        changegate --config changegate.example.toml audit verify
        ```

        `echo $LASTEXITCODE` (PowerShell) or `echo $?` (bash) shows the last exit code. The approvals folder and
        audit log this creates are git-ignored. Delete them when you're done.
    """),
    T("""
        **Versions and dependencies**

        - Version numbers usually follow **semantic versioning**: `MAJOR.MINOR.PATCH` - bump MAJOR for breaking
          changes (like a new exit-code meaning), MINOR for features, PATCH for fixes.
        - When a project *does* need packages, list them in `dependencies` with version ranges
          (`"requests>=2.31,<3"`), and pin exact versions for reproducible CI with a lock or requirements file.
        - Fewer dependencies means less supply-chain risk - worth weighing for security tooling.
    """),
    Q("What does `[project.scripts] changegate = \"changegate.cli:main\"` do?",
      "Installing the package creates a changegate command that calls changegate.cli.main()",
      "It runs main() when pyproject.toml is read", "It lists changegate.cli as a dependency",
      "It renames the package to main"),
    Q("You installed with `pip install -e workspace` and then edit `report.py`. What do you need to do?",
      "Nothing - editable installs run your files in place", "Reinstall the package", "Delete pyproject.toml",
      "Bump the version number"),
    C("""
        Many CLIs share one pattern: `main(argv=None)` uses `sys.argv[1:]` when `argv` is None, and the module
        ends with `if __name__ == "__main__": sys.exit(main())`.

        Write `main(argv=None)` that returns the number of arguments it was given (from `argv`, or from
        `sys.argv[1:]` when `argv` is None), printing `args: <a>, <b>, ...` (or `args: none` for zero), and add
        the `__main__` guard.
    """, '''import sys

def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    print("args: " + (", ".join(args) if args else "none"))
    return len(args)

if __name__ == "__main__":
    sys.exit(main())''',
      check="""
        import sys as _s
        assert __capture__(main, ["evaluate", "plan.json"]).strip() == "args: evaluate, plan.json"
        assert main(["a", "b", "c"]) == 3
        assert __capture__(main, []).strip() == "args: none"
        saved = _s.argv
        _s.argv = ["tool", "x"]
        try:
            assert main() == 1, "with no argv, use sys.argv[1:]"
        finally:
            _s.argv = saved
        assert 'if __name__ == "__main__"' in __source__ or "if __name__ == '__main__'" in __source__, "add the __main__ guard"
      """,
      require=["def main", "sys.argv"],
      hints=["args = sys.argv[1:] if argv is None else argv",
             'Use `argv is None`, not `not argv` - an empty list is a valid, deliberate input.',
             'if __name__ == "__main__":\n    sys.exit(main())']),
], summary="""
    - `pyproject.toml`: `[build-system]`, `[project]` (name, version, requires-python, dependencies),
      `[project.scripts] changegate = "changegate.cli:main"` creates the command.
    - `python -m pip install -e path` - editable install; edits apply immediately.
    - `python -m changegate` runs `__main__.py`. `main(argv=None)` + `if __name__ == "__main__": sys.exit(main())`.
    - Semantic versioning; minimal, pinned dependencies.
""")

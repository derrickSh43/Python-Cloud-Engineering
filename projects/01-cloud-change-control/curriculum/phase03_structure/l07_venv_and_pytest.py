from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p03l7", "Virtual environments and pytest", [
    T("""
        **Virtual environments**

        Real projects depend on packages from PyPI (the Python Package Index). Installing them into your
        system Python mixes every project's dependencies together. A **virtual environment** is a private
        Python for one project. In the repository folder:

        ```
        python -m venv .venv
        .venv\\Scripts\\activate          # Windows PowerShell
        source .venv/bin/activate        # macOS / Linux
        python -m pip install -r requirements-dev.txt
        ```

        Your prompt shows `(.venv)` while it's active; `deactivate` leaves it. `requirements-dev.txt`
        lists what to install - here, just **pytest**. `.venv` is git-ignored: each person creates their own.

        **Do this now** in a terminal (you can keep this app open in another one).
    """),
    T("""
        **pytest**

        Until now the course has checked your code for you. pytest is the standard tool for checking it
        yourself, and it's what ChangeGate's own 190+ tests use. A test is just a function whose name starts
        with `test_`, using plain `assert`, in a file named `test_*.py`:

        ```
        # tests/test_ports.py
        from changegate.policies.helpers import parse_port_range

        def test_single_port():
            assert parse_port_range("22") == (22, 22)

        def test_range():
            assert parse_port_range("8000-8080") == (8000, 8080)
        ```

        Run `python -m pytest` and it finds and runs every test, reporting failures with the values
        involved. `python -m pytest -k port` runs only tests whose names contain "port"; `-x` stops at the
        first failure; `-q` is quieter.
    """),
    T("""
        **Checking for exceptions**

        `pytest.raises` asserts that code raises an exception, and can check the message:

        ```
        import pytest
        from changegate.plan_parser import PlanError, check_format

        def test_rejects_format_2():
            with pytest.raises(PlanError, match="unsupported"):
                check_format({"format_version": "2.0"})
        ```

        The `with` block passes only if a `PlanError` whose message matches `"unsupported"` is raised inside it.
    """),
    T("""
        **parametrize: one test, many cases**

        ```
        @pytest.mark.parametrize("actions, expected", [
            (["create"], Action.CREATE),
            (["delete", "create"], Action.REPLACE),
            (["create", "delete"], Action.REPLACE),
        ])
        def test_from_terraform(actions, expected):
            assert Action.from_terraform(actions) is expected
        ```

        pytest runs the test once per row and reports each separately. Most of ChangeGate's policy tests
        are tables like this.
    """),
    T("""
        **Fixtures**

        A **fixture** provides something a test needs. Name it as a parameter and pytest supplies it.
        Built-in fixtures include:

        - `tmp_path` - a fresh temporary folder (a `Path`) for each test
        - `monkeypatch` - temporarily set environment variables or attributes: `monkeypatch.setenv("KEY", "v")`
        - `capsys` - capture what was printed: `capsys.readouterr().out`

        ```
        def test_missing_file(tmp_path):
            with pytest.raises(PlanError, match="not found"):
                read_plan_bytes(tmp_path / "nope.json")
        ```

        You can write your own with `@pytest.fixture`; shared ones live in a `conftest.py` file.
    """),
    T("""
        **Running ChangeGate's own suite against your code**

        The project's full test suite lives in `projects/01-cloud-change-control/tests/`. Normally it tests
        the reference implementation, but the environment variable `CHANGEGATE_SRC` points it at your
        workspace instead. Try the parser and model tests now - they should pass, since you've written
        those parts:

        ```
        # PowerShell
        $env:CHANGEGATE_SRC="workspace"; python -m pytest projects/01-cloud-change-control/tests/test_models.py projects/01-cloud-change-control/tests/test_plan_parser.py
        # macOS / Linux
        CHANGEGATE_SRC=workspace python -m pytest projects/01-cloud-change-control/tests/test_models.py projects/01-cloud-change-control/tests/test_plan_parser.py
        ```

        The rest of the suite will fail until you've finished the later phases - that's expected. The very
        last exercise of the course is making the entire suite pass.
    """),
    Q("A file `checks.py` contains `def test_ports(): ...`. Will `python -m pytest` run it?",
      "No - test files must be named test_*.py (or *_test.py)", "Yes - any function named test_ runs",
      "Only with -k ports", "Only if the folder has a conftest.py"),
    Q("Which fixture gives each test its own temporary folder?", "tmp_path", "capsys", "monkeypatch", "tempfile"),
    C("""
        Write two pytest-style test functions for this function (the checker runs your tests against the
        correct version and a buggy one):

        ```
        def tag_value(tags, key):
            \"\"\"Return tags[key], or "unset" if the key is missing or tags is None.\"\"\"
            if not tags:
                return "unset"
            return tags.get(key, "unset")
        ```

        The buggy version crashes when `tags` is `None`. Make sure one of your tests would catch it.
    """, '''def tag_value(tags, key):
    if not tags:
        return "unset"
    return tags.get(key, "unset")

def test_present_and_missing():
    assert tag_value({"owner": "x"}, "owner") == "x"
    assert tag_value({"owner": "x"}, "env") == "unset"

def test_none_tags():
    assert tag_value(None, "owner") == "unset"''',
      starter='def tag_value(tags, key):\n    if not tags:\n        return "unset"\n    return tags.get(key, "unset")',
      check="""
        tests = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
        assert len(tests) >= 2, "write at least two test_ functions"
        for t in tests:
            t()
        g = globals()
        original = g["tag_value"]
        g["tag_value"] = lambda tags, key: tags.get(key, "unset")
        caught = False
        try:
            for t in tests:
                t()
        except (AssertionError, AttributeError):
            caught = True
        finally:
            g["tag_value"] = original
        assert caught, "none of your tests caught the version that crashes on tags=None"
      """,
      require=["def test_", "assert"],
      hints=["Test the normal cases first: a key that exists and one that doesn't.",
             "Then a test that calls tag_value(None, \"owner\").",
             'def test_none_tags():\n    assert tag_value(None, "owner") == "unset"']),
], summary="""
    - `python -m venv .venv`, activate it, `python -m pip install -r requirements-dev.txt`. `.venv` is git-ignored.
    - pytest: files `test_*.py`, functions `test_*`, plain `assert`. Run `python -m pytest [-k name] [-x] [-q]`.
    - `with pytest.raises(Error, match="text"):` checks exceptions.
    - `@pytest.mark.parametrize("a, b", [(1, 2), ...])` runs one test per case.
    - Fixtures: `tmp_path`, `monkeypatch`, `capsys`; custom ones with `@pytest.fixture` in `conftest.py`.
    - `CHANGEGATE_SRC=workspace` runs the project's full suite against your code.
""")

from pce.lesson import T, Ex, Q, P, C, B, Lesson

PLAN = '{"format_version": "1.2", "resource_changes": []}'

LESSON = Lesson("p02l2", "Files, paths and exceptions", [
    T("""
        **Paths with pathlib**

        `pathlib.Path` represents a file or folder path and works the same on Windows, macOS and Linux:

        ```
        from pathlib import Path
        plan = Path("plans") / "aws_safe.json"   # / joins path parts
        plan.exists()       # does it exist?
        plan.is_dir()       # is it a folder?
        plan.name           # "aws_safe.json"
        plan.suffix         # ".json"
        plan.read_text(encoding="utf-8")   # the contents as str
        plan.read_bytes()                  # the contents as bytes
        Path("out.txt").write_text("hi", encoding="utf-8")
        ```
    """),
    Ex("""
        from pathlib import Path
        plan = Path("plan.json")
        print(plan.exists(), plan.is_dir(), plan.name, plan.suffix)
        print(plan.read_text(encoding="utf-8"))
        print(plan.read_bytes()[:20])
        print(Path("missing.json").exists())
    """, files={"plan.json": PLAN},
       note="This example runs in a temporary folder that contains a file called plan.json."),
    T("""
        **Exceptions**

        When something goes wrong, Python **raises an exception**. If nothing handles it, the program
        stops with a traceback. You can handle one with `try` / `except`:

        ```
        try:
            data = Path("plan.json").read_bytes()
        except FileNotFoundError:
            print("no plan file - did you run terraform show?")
        ```

        Python runs the `try` block; if one of the named exceptions happens, it jumps to the matching
        `except` block instead of crashing. Catch **specific** exceptions - a bare `except:` hides bugs.
    """),
    Ex("""
        from pathlib import Path
        try:
            data = Path("nope.json").read_bytes()
            print("read", len(data), "bytes")
        except FileNotFoundError:
            print("no plan file found")
        print("the program carries on")
    """),
    Ex("""
        try:
            port = int("eighty")
        except ValueError as e:
            print("bad port:", e)
    """, note="`except SomeError as e:` gives you the exception object; str(e) is its message."),
    T("""
        **Raising your own exceptions**

        Your code can raise exceptions too, with `raise`. Define your own type by making a class that
        **inherits** from `Exception` (classes are covered properly in Phase 3 - for now this two-line
        pattern is all you need):

        ```
        class PlanError(Exception):
            \"\"\"The input is not a usable Terraform plan.\"\"\"

        raise PlanError("plan file not found: plan.json")
        ```

        A custom type lets callers catch *your* errors specifically: `except PlanError:`.
    """),
    Ex("""
        class PlanError(Exception):
            pass

        def check_suffix(name):
            if not name.endswith(".json"):
                raise PlanError("expected a .json file, got " + name)
            return name

        print(check_suffix("plan.json"))
        try:
            check_suffix("plan.tfplan")
        except PlanError as e:
            print("refused:", e)
    """),
    T("""
        **Translating errors: raise ... from None**

        A common pattern catches a low-level error and raises a clear one instead:

        ```
        try:
            return path.read_bytes()
        except FileNotFoundError:
            raise PlanError("plan file not found: %s" % path) from None
        ```

        Without `from None`, Python prints *both* errors ("During handling of the above exception, another
        exception occurred..."), which buries your helpful message. `from None` shows just yours.

        `"text %s" % value` is an older way to format strings, equivalent to `f"text {value}"`. You'll see
        it in ChangeGate's code.
    """),
    P("""
        try:
            int("x")
        except ValueError:
            print("caught")
        finally:
            print("always runs")
    """, explain="`finally` runs whether or not an exception happened - useful for clean-up."),
    Q("Which `except` should you prefer?",
      "except FileNotFoundError:", "except:", "except Exception:", "except BaseException:",
      explain="Catch the specific error you expect. Broad catches hide unrelated bugs."),
    C("""
        Write a function `read_config(path)` that returns the text of the file at `path`
        (use `Path(path).read_text(encoding="utf-8")`). If the file doesn't exist, return the string
        `"MISSING"` instead of crashing.

        A file `team.toml` exists in the folder where your code runs; `absent.toml` doesn't.
    """, 'from pathlib import Path\n\ndef read_config(path):\n    try:\n        return Path(path).read_text(encoding="utf-8")\n    except FileNotFoundError:\n        return "MISSING"',
      files={"team.toml": "[risk]\napproval_at = \"high\"\n"},
      check="""
        assert read_config("team.toml").startswith("[risk]"), "read_config('team.toml') should return the file's text"
        assert read_config("absent.toml") == "MISSING", "a missing file should give 'MISSING'"
      """,
      require=["try", "except FileNotFoundError"],
      hints=["Wrap the read in try: ... except FileNotFoundError:",
             'from pathlib import Path\n\ndef read_config(path):\n    try:\n        return Path(path).read_text(encoding="utf-8")\n    except FileNotFoundError:\n        return "MISSING"']),
    C("""
        Define an exception class `ConfigError` (inheriting from `Exception`). Then write
        `parse_port(text)` that returns `int(text)`, but if `int()` raises `ValueError`, raises
        `ConfigError("not a port: <text>")` instead, **from None**.
    """, 'class ConfigError(Exception):\n    pass\n\ndef parse_port(text):\n    try:\n        return int(text)\n    except ValueError:\n        raise ConfigError("not a port: " + text) from None',
      check="""
        assert parse_port("443") == 443
        try:
            parse_port("https")
        except ConfigError as e:
            assert str(e) == "not a port: https", "message should be 'not a port: https', got %r" % str(e)
            assert e.__suppress_context__, "add `from None` to the raise"
        else:
            raise AssertionError("parse_port('https') should raise ConfigError")
        assert issubclass(ConfigError, Exception)
      """,
      require=["class ConfigError", "from None"],
      hints=["class ConfigError(Exception):\n    pass",
             "Inside parse_port: try: return int(text)  except ValueError: raise ConfigError(...) from None",
             'raise ConfigError("not a port: " + text) from None']),
    B("p2-read-plan", intro="ChangeGate's `PlanError` class is already defined in `plan_parser.py`. "
                           "Use it for both failure cases."),
], summary="""
    - `Path("a") / "b"`, `.exists()`, `.is_dir()`, `.name`, `.suffix`, `.read_text(encoding="utf-8")`,
      `.read_bytes()`, `.write_text(...)`.
    - `try: ... except SpecificError as e: ...` handles an exception; `finally:` always runs.
    - `class MyError(Exception): pass` defines your own; `raise MyError("message")` raises it.
    - `raise NewError(...) from None` replaces a low-level error with a clear one.
""")

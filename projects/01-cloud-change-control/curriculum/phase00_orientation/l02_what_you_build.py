from pce.lesson import T, Ex, P, Lesson

LESSON = Lesson("p00l2", "What you'll build: Cloud ChangeGate", [
    T("""
        **A Python tool for infrastructure work**

        You'll write **Cloud ChangeGate**, a command-line tool of the kind infrastructure teams write all the
        time. It reads a JSON file listing proposed infrastructure changes, checks each change against a set
        of rules, and prints a report with an exit code a pipeline can act on.

        You don't need to know Terraform or the cloud providers well. Each exercise tells you exactly what the
        data looks like and what to check. The course is about the **Python**: reading files, walking nested
        data, writing rules as functions and classes, testing them, and shipping a CLI.
    """),
    Ex("""
        changes = [
            {"address": "aws_s3_bucket.logs", "actions": ["create"]},
            {"address": "aws_db_instance.orders", "actions": ["delete"]},
        ]
        for change in changes:
            if "delete" in change["actions"]:
                print("FLAG ", change["address"], "is being deleted")
            else:
                print("ok   ", change["address"])
    """, note="This is the whole idea in eight lines. The rest of the course grows it into a real, tested tool."),
    T("""
        **The Python you'll use, phase by phase**

        - **Phase 1** - variables, strings, lists, dicts, loops, functions, reading errors.
        - **Phase 2** - files, JSON, exceptions, comprehensions, sets, generators, hashing.
        - **Phase 3** - classes, enums, dataclasses, packages, virtual environments and pytest.
        - **Phase 4** - the `ipaddress` and `tomllib` modules, a plugin system with abstract classes, and
          rules written as generators.
        - **Phase 5** - `datetime`, `hmac`, `hashlib`, and an append-only log file.
        - **Phase 6** - `argparse`, exit codes, `logging`, output formats, and packaging with `pyproject.toml`.

        Everything runs on your machine against sample files. No cloud account is needed.
    """),
    P("""
        actions = ["delete", "create"]
        print("delete" in actions, len(actions))
    """, explain="`in` checks whether a value is in the list; `len` counts the items."),
], summary="""
    - You'll build **Cloud ChangeGate**: a Python CLI that reads a JSON file of infrastructure changes,
      checks them against rules, and reports with an exit code.
    - Each exercise describes the data and the rule; the focus is the Python.
""")

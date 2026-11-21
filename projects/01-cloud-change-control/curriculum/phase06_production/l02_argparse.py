from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p06l2", "Command-line interfaces with argparse", [
    T("""
        **The shape of a CLI**

        ```
        changegate --config team.toml evaluate plan.json --format markdown
        └─ program ─┘└─ global option ─┘└ command ┘└ positional┘└── command option ──┘
        ```

        - **Positional arguments** are required and identified by position (`plan.json`).
        - **Options** start with `--` (or a short `-v`), are usually optional, and may take a value.
        - **Subcommands** (`evaluate`, `approve`, `verify`...) group related options, like `git commit` vs `git push`.

        The standard library's `argparse` turns `sys.argv` into a tidy object, generates `--help`, and reports
        usage errors.
    """),
    Ex("""
        import argparse
        parser = argparse.ArgumentParser(prog="changegate")
        parser.add_argument("--config", help="path to changegate.toml")
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("plan")
        parser.add_argument("--format", choices=["text", "json"], default="text")

        args = parser.parse_args(["-v", "plan.json", "--format", "json"])
        print(args)
        print(args.plan, args.format, args.verbose, args.config)
    """, note="`parse_args(list)` parses the list you give it - perfect for tests. With no argument it reads the real command line."),
    T("""
        **Option types**

        - `action="store_true"` - a flag: present → True, absent → False. `--no-audit` becomes `args.no_audit`.
        - `type=int` / `type=float` - convert the value (and error clearly if it can't).
        - `choices=[...]` - only allow listed values.
        - `nargs="*"` - zero or more values, collected into a list.
        - `default=...` - used when the option is absent. A default can come from the environment:
          `default=os.environ.get("CHANGEGATE_AUTHOR")` - which is how CI supplies identities without flags.
    """),
    Ex("""
        import argparse, os
        os.environ["CHANGEGATE_AUTHOR"] = "dave"
        p = argparse.ArgumentParser()
        p.add_argument("--approvals", nargs="*", default=["approvals"])
        p.add_argument("--author", default=os.environ.get("CHANGEGATE_AUTHOR"))
        p.add_argument("--tail", type=int, default=10)
        print(p.parse_args([]))
        print(p.parse_args(["--approvals", "a.json", "b.json", "--author", "erin", "--tail", "3"]))
    """),
    T("""
        **Subcommands**

        ```
        sub = parser.add_subparsers(dest="command", required=True)
        evaluate = sub.add_parser("evaluate", help="evaluate a plan")
        evaluate.add_argument("plan")
        audit = sub.add_parser("audit")
        audit_sub = audit.add_subparsers(dest="audit_command", required=True)   # nested: audit verify / audit show
        ```

        `args.command` then says which subcommand ran. To share options between subcommands, write a small
        function that adds them and call it on each subparser.
    """),
    T("""
        **Usage errors and exit codes**

        On bad usage argparse prints a message and exits with code **2**. For ChangeGate that's a problem:
        exit code 2 already means "approval required", so a typo in a CI script would look like a policy
        result. ChangeGate subclasses `ArgumentParser` and overrides `error()` to exit with **3** instead -
        and passes `parser_class=Parser` to `add_subparsers` so subcommands use it too.
    """),
    Ex("""
        import argparse, sys

        class Parser(argparse.ArgumentParser):
            def error(self, message):
                self.exit(3, "%s: error: %s\\n" % (self.prog, message))

        p = Parser(prog="demo")
        p.add_argument("plan")
        try:
            p.parse_args([])
        except SystemExit as e:
            print("exit code:", e.code)
    """, note="argparse writes the error to stderr and raises SystemExit; here we catch it to show the code."),
    Q("What does `parser.add_argument(\"--no-audit\", action=\"store_true\")` create?",
      "args.no_audit, True when the flag is given", "args.audit, False when the flag is given",
      "A required option that takes a value", "args['--no-audit']"),
    C("""
        Write `build_parser()` returning an `argparse.ArgumentParser(prog="tagcheck")` with:

        - a global flag `-q/--quiet`
        - a required subcommand `scan` taking a positional `path` and an option `--require` that accepts zero
          or more tag names (default `["owner"]`)
        - a subcommand `version` with no arguments

        `build_parser().parse_args(["scan", "plan.json", "--require", "owner", "env"])` gives
        `command="scan"`, `path="plan.json"`, `require=["owner", "env"]`, `quiet=False`.
    """, '''import argparse

def build_parser():
    parser = argparse.ArgumentParser(prog="tagcheck")
    parser.add_argument("-q", "--quiet", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan")
    scan.add_argument("path")
    scan.add_argument("--require", nargs="*", default=["owner"])
    sub.add_parser("version")
    return parser''',
      check="""
        a = build_parser().parse_args(["scan", "plan.json", "--require", "owner", "env"])
        assert (a.command, a.path, a.require, a.quiet) == ("scan", "plan.json", ["owner", "env"], False), vars(a)
        b = build_parser().parse_args(["-q", "scan", "x.json"])
        assert b.quiet is True and b.require == ["owner"]
        assert build_parser().parse_args(["version"]).command == "version"
        import io, contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                build_parser().parse_args([])
            except SystemExit:
                pass
            else:
                raise AssertionError("a subcommand should be required")
      """,
      require=["add_subparsers", "argparse"],
      hints=['sub = parser.add_subparsers(dest="command", required=True)',
             'scan = sub.add_parser("scan"); scan.add_argument("path"); scan.add_argument("--require", nargs="*", default=["owner"])',
             'Global flag: parser.add_argument("-q", "--quiet", action="store_true") - added to the main parser before subcommands.']),
    B("p6-cli-parser"),
], summary="""
    - `argparse.ArgumentParser(prog=...)`; positionals `add_argument("plan")`; options `--format`, flags
      `action="store_true"`, `type=int`, `choices=[...]`, `nargs="*"`, `default=os.environ.get(...)`.
    - Subcommands: `sub = parser.add_subparsers(dest="command", required=True)`; `sub.add_parser("name")`; nest for `audit verify`.
    - `parse_args(list)` for tests. Usage errors exit 2 by default; override `error()` when 2 means something else.
""")

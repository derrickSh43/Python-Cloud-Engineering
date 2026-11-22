from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p06l3", "Commands, exit codes and logging", [
    T("""
        **Exit codes are an API**

        When a program finishes it returns a number to whatever ran it. `0` means success; anything else
        means something else. CI systems, shell scripts and `make` all branch on it. ChangeGate defines:

        | code | meaning |
        |---|---|
        | `0` | allowed (or approved) |
        | `1` | blocked (or audit verification failed) |
        | `2` | approval required |
        | `3` | error: bad input, bad config, missing key, usage mistake |

        A CI step fails on any non-zero code, so a plan that needs approval stops the pipeline until the
        approvals exist - exactly what a gate should do. `sys.exit(code)` sets it.
    """),
    T("""
        **stdout and stderr**

        Programs have two output streams. **stdout** is for the result (the report, the JSON). **stderr** is
        for diagnostics and errors. Keeping them separate means `changegate evaluate plan.json --format json >
        report.json` writes clean JSON even if there's a warning. `print(..., file=sys.stderr)` writes to stderr.
    """),
    Ex("""
        import sys
        print('{"decision": "allow"}')
        print("warning: config not found, using defaults", file=sys.stderr)
        print("(the example runner shows only stdout - the warning went to stderr)")
    """),
    T("""
        **One function per command**

        Each subcommand is a small function `cmd_evaluate(args, config) -> int`, and a dict maps command names
        to functions:

        ```
        COMMANDS = {"evaluate": cmd_evaluate, "approve": cmd_approve, "verify": cmd_verify, ...}
        return COMMANDS[args.command](args, config)
        ```

        The same idea as `RENDERERS`: adding a command means adding one function and one entry.
    """),
    T("""
        **main(): one place for expected errors**

        Every expected failure - missing plan file, bad config, missing signing key - is a specific exception
        type raised deep inside the code. `main()` catches **exactly those**, prints one clean line to stderr and
        returns 3:

        ```
        try:
            config = load_config(args.config)
            return COMMANDS[args.command](args, config)
        except (ConfigError, PlanError, ApprovalError, ...) as e:
            print("changegate: error: %s" % e, file=sys.stderr)
            return EXIT_ERROR
        ```

        It deliberately does **not** catch everything: a genuine bug should still show its full traceback so
        it gets fixed, rather than being disguised as "bad input".
    """),
    T("""
        **logging**

        `print` is for output. For diagnostic detail - which config file was loaded, where an audit record
        went - use the `logging` module: messages have levels (DEBUG, INFO, WARNING, ERROR), and the user
        chooses how much to see. ChangeGate shows DEBUG with `-v`:

        ```
        import logging
        log = logging.getLogger("changegate")
        logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                            format="changegate: %(levelname)s: %(message)s", stream=sys.stderr)
        log.debug("config: %s", path)        # shown only with -v
        ```

        Pass values as arguments (`log.debug("x: %s", x)`) rather than pre-formatting - the string is only
        built if the message will actually be shown.
    """),
    Ex("""
        import logging, sys
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout)
        log = logging.getLogger("demo")
        log.debug("hidden at INFO level")
        log.info("loaded %d policies", 14)
        log.warning("no approvers configured")
    """, note="This example logs to stdout so you can see it; ChangeGate logs to stderr."),
    Q("What does this print?", "error", "verify", "2", "It crashes with KeyError",
      code="""
        def cmd_verify(args):
            return 2

        COMMANDS = {"verify": cmd_verify}

        def main(command):
            try:
                return COMMANDS[command](None)
            except KeyError:
                return "error"

        print(main("verfy"))
      """, explain="The misspelt command isn't a key in the dict, so the KeyError is caught."),
    C("""
        Write `main(argv)` for a tiny tool. It parses `argv` with a parser that has one positional `count`
        (an int) - use a parser whose `error()` exits with code 3. Then:

        - return `0` if count is 0, `1` if it's negative, `2` if it's positive
        - if parsing fails (SystemExit), let it propagate - the test checks its code is 3
        - print nothing to stdout except the line `count: <n>`
    """, '''import argparse

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(3, "%s: error: %s\\n" % (self.prog, message))

def main(argv):
    parser = Parser(prog="counter")
    parser.add_argument("count", type=int)
    args = parser.parse_args(argv)
    print("count: %d" % args.count)
    if args.count == 0:
        return 0
    return 1 if args.count < 0 else 2''',
      check="""
        import io, contextlib
        assert __capture__(main, ["5"]).strip() == "count: 5"
        assert main(["0"]) == 0 and main(["-4"]) == 1 and main(["7"]) == 2
        with contextlib.redirect_stderr(io.StringIO()):
            for bad in ([], ["seven"]):
                try:
                    main(bad)
                except SystemExit as e:
                    assert e.code == 3, "usage errors should exit 3, got %r" % e.code
                else:
                    raise AssertionError("main(%r) should exit with a usage error" % (bad,))
      """,
      require=["argparse", "def error"],
      hints=["Subclass argparse.ArgumentParser and override error(self, message) to call self.exit(3, ...).",
             'parser.add_argument("count", type=int) converts and validates the value.',
             'Note: "-4" works as a positional because argparse treats negative numbers specially when no option looks like one.']),
    B("p6-cli-commands", intro="`cmd_policies` and `cmd_hash` are written for you - use them as a guide."),
    B("p6-cli-main"),
], summary="""
    - Exit codes: 0 allow/approved, 1 blocked, 2 approval required, 3 error. CI fails on non-zero.
    - stdout for results, stderr for diagnostics: `print(..., file=sys.stderr)`.
    - One function per command, dispatched through a `COMMANDS` dict.
    - `main()` catches only expected error types → one clean stderr line + exit 3; real bugs keep their traceback.
    - `logging`: levels, `basicConfig(level=..., format=..., stream=sys.stderr)`, `log.debug("x: %s", x)`.
""")

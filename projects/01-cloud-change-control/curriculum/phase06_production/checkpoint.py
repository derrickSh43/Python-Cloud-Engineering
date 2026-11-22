from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p06cp", "Ship it", """
    A final check on the production habits from this phase.
""", [
    Q("What does this print?", "3", "2", "0", "Nothing - the program exits",
      code="""
        import argparse

        class Parser(argparse.ArgumentParser):
            def error(self, message):
                raise SystemExit(3)

        parser = Parser(prog="gate")
        parser.add_argument("count", type=int)
        try:
            parser.parse_args(["many"])
        except SystemExit as e:
            print(e.code)
      """, explain="Overriding error() replaces argparse's default exit code 2 with 3."),
    Q("Which stream does `print(\"warning\", file=sys.stderr)` write to?",
      "stderr, so it stays out of a redirected report", "stdout", "A file named sys.stderr", "The log file"),
    Q("What does this print?", "True", "False", "An error",
      code="""
        import os
        os.environ["CHANGEGATE_CONFIG"] = "ci/changegate.toml"
        path = os.environ.get("CHANGEGATE_CONFIG", "changegate.toml")
        print(path.endswith(".toml"))
      """, explain="Configuration comes from the environment, with a default when it isn't set."),
    C("""
        Write `run(argv)` - a miniature ChangeGate. It parses `argv` with argparse: a positional `risk`
        (choices `low`, `medium`, `high`, `critical`) and an option `--format` (choices `text`, `json`,
        default `text`). Map the risk to a decision - low → allow, medium/high → approval, critical → block -
        print it (text: `decision: <d>`; json: `{"decision": "<d>"}` via json.dumps), and return the exit code
        (allow 0, block 1, approval 2).
    """, '''import argparse, json

CODES = {"allow": 0, "block": 1, "approval": 2}

def run(argv):
    parser = argparse.ArgumentParser(prog="minigate")
    parser.add_argument("risk", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    decision = {"low": "allow", "critical": "block"}.get(args.risk, "approval")
    if args.format == "json":
        print(json.dumps({"decision": decision}))
    else:
        print("decision: %s" % decision)
    return CODES[decision]''',
      check="""
        import json as _j
        assert __capture__(run, ["low"]).strip() == "decision: allow"
        assert _j.loads(__capture__(run, ["critical", "--format", "json"])) == {"decision": "block"}
        assert run(["low"]) == 0 and run(["critical"]) == 1 and run(["medium"]) == 2 and run(["high"]) == 2
        import io, contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                run(["severe"])
            except SystemExit:
                pass
            else:
                raise AssertionError("an invalid risk should be rejected by argparse (choices=...)")
      """,
      require=["argparse"],
      hints=['parser.add_argument("risk", choices=[...]) and parser.add_argument("--format", choices=["text", "json"], default="text")',
             'decision = {"low": "allow", "critical": "block"}.get(args.risk, "approval")',
             'Return {"allow": 0, "block": 1, "approval": 2}[decision].']),
])

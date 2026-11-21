from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p06cp", "Ship it", """
    A final check on the production habits from this phase.
""", [
    Q("Why does ChangeGate exit with 3, not argparse's default 2, on a usage error?",
      "2 already means 'approval required'; a typo must not look like a policy result",
      "3 is the POSIX standard for usage errors", "argparse can't exit with 2 on Windows", "It's arbitrary"),
    Q("Where should a JSON report go, and where should a warning go?",
      "Report to stdout, warning to stderr", "Both to stdout", "Both to stderr", "Report to stderr, warning to stdout"),
    Q("Which value belongs in a GitHub secret rather than a variable?",
      "CHANGEGATE_HMAC_KEY", "CHANGEGATE_CONFIG", "CHANGEGATE_PLANS", "CHANGEGATE_PACKAGE"),
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

from changegate import cli
from support import captured, env, raises


def parse(*argv):
    return cli.build_parser().parse_args(list(argv))


def test_evaluate_defaults():
    """evaluate PLAN has format text, no output, audit on"""
    args = parse("evaluate", "plan.json")
    assert args.command == "evaluate" and args.plan == "plan.json"
    assert args.format == "text" and args.output is None and args.no_audit is False
    assert args.config is None and args.verbose is False


def test_global_options():
    """--config and -v come before the subcommand"""
    args = parse("--config", "team.toml", "-v", "evaluate", "p.json", "--format", "markdown", "--no-audit")
    assert args.config == "team.toml" and args.verbose and args.format == "markdown" and args.no_audit


def test_verify_options():
    """verify takes approvals (default ['approvals']) and an author from the environment"""
    with env(CHANGEGATE_AUTHOR="dave"):
        args = parse("verify", "p.json")
    assert args.approvals == ["approvals"] and args.author == "dave"
    args = parse("verify", "p.json", "--approvals", "a1.json", "dir", "--author", "erin", "--format", "json")
    assert args.approvals == ["a1.json", "dir"] and args.author == "erin" and args.format == "json"


def test_approve_options():
    """approve has approver, comment, ttl-hours (float) and out-dir"""
    with env(CHANGEGATE_APPROVER="alice"):
        args = parse("approve", "p.json")
    assert args.approver == "alice" and args.comment == "" and args.ttl_hours is None and args.out_dir == "approvals"
    args = parse("approve", "p.json", "--approver", "bob", "--ttl-hours", "1.5", "--out-dir", "x")
    assert args.approver == "bob" and args.ttl_hours == 1.5 and args.out_dir == "x"


def test_audit_and_other_commands():
    """audit verify/show, policies and hash parse"""
    args = parse("audit", "verify", "--expect-head", "abc")
    assert args.command == "audit" and args.audit_command == "verify" and args.expect_head == "abc" and args.log is None
    args = parse("audit", "show", "--tail", "3")
    assert args.audit_command == "show" and args.tail == 3
    assert parse("audit", "show").tail == 10
    assert parse("policies").command == "policies"
    assert parse("hash", "p.json").plan == "p.json"


def test_bad_usage_exits_3():
    """bad usage exits with 3 (not 2, which means 'approval required')"""
    for argv in ([], ["evaluate"], ["evaluate", "p.json", "--format", "pdf"], ["audit"]):
        with captured():
            error = raises(SystemExit, cli.build_parser().parse_args, argv)
        assert error.code == cli.EXIT_ERROR, "%s exited with %s" % (argv, error.code)


def test_version():
    """--version prints the version"""
    with captured() as out:
        raises(SystemExit, cli.build_parser().parse_args, ["--version"])
    assert out.stdout.startswith("changegate ")

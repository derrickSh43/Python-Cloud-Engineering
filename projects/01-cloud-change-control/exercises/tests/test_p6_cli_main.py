from changegate import cli
from support import captured, raises, workdir


def main(*argv):
    with captured() as out:
        code = cli.main(list(argv))
    return code, out.stdout, out.stderr


def test_runs_commands():
    """main parses, loads config and returns the command's exit code"""
    with workdir():
        assert main("evaluate", "plans/aws_safe.json")[0] == cli.EXIT_OK
        assert main("evaluate", "plans/aws_db_replace.json")[0] == cli.EXIT_NEEDS_APPROVAL
        code, out, _ = main("policies")
        assert code == cli.EXIT_OK and "AWS-SG-OPEN-INGRESS" in out


def test_expected_errors_exit_3():
    """missing files and bad config print 'changegate: error:' to stderr and return 3"""
    with workdir() as tmp:
        code, out, err = main("evaluate", "plans/nope.json")
        assert code == cli.EXIT_ERROR and err.startswith("changegate: error: ") and "not found" in err
        (tmp / "bad.toml").write_text("[risk]\napproval_at = 'severe'\n")
        code, _, err = main("--config", "bad.toml", "evaluate", "plans/aws_safe.json")
        assert code == cli.EXIT_ERROR and "severe" in err
        code, _, err = main("approve", "plans/aws_db_replace.json")
        assert code == cli.EXIT_ERROR and "approver" in err


def test_usage_errors_exit_3():
    """bad usage still exits with 3"""
    with captured():
        assert raises(SystemExit, cli.main, ["evaluate"]).code == cli.EXIT_ERROR


def test_real_bugs_are_not_hidden():
    """unexpected exceptions are not swallowed"""
    original = cli.COMMANDS["policies"]

    def broken(args, config):
        raise RuntimeError("a real bug")

    cli.COMMANDS["policies"] = broken
    try:
        with workdir():
            raises(RuntimeError, cli.main, ["policies"])
    finally:
        cli.COMMANDS["policies"] = original

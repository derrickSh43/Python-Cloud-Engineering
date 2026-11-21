import json

from changegate import cli
from changegate.config import load_config
from changegate.models import Decision, Evaluation, Severity
from support import TEST_KEY, captured, env, raises, workdir


def run(*argv):
    """Parse and run one command the way main() will, returning (exit code, stdout, stderr)."""
    args = cli.build_parser().parse_args(list(argv))
    with captured() as out:
        code = cli.COMMANDS[args.command](args, load_config(args.config))
    return code, out.stdout, out.stderr


def test_exit_code_for():
    """exit codes: block 1, approval needed 2, otherwise 0"""
    def ev(decision):
        return Evaluation("a" * 64, (), (), Severity.LOW, decision, ())
    assert cli.exit_code_for(ev(Decision.ALLOW)) == cli.EXIT_OK
    assert cli.exit_code_for(ev(Decision.BLOCK), approved=True) == cli.EXIT_BLOCKED
    assert cli.exit_code_for(ev(Decision.REQUIRE_APPROVAL)) == cli.EXIT_NEEDS_APPROVAL
    assert cli.exit_code_for(ev(Decision.REQUIRE_APPROVAL), approved=True) == cli.EXIT_OK


def test_evaluate():
    """evaluate prints the report, writes --output and an audit record, returns the exit code"""
    with workdir() as tmp:
        code, out, _ = run("evaluate", "plans/aws_risky.json", "--format", "json", "--output", "r.json")
        assert code == cli.EXIT_BLOCKED and json.loads(out)["decision"] == "block"
        assert json.loads((tmp / "r.json").read_text())["risk"] == "CRITICAL"
        record = json.loads((tmp / "changegate-audit.jsonl").read_text().splitlines()[0])
        assert record["event"] == "evaluate" and record["data"]["decision"] == "block"
        assert run("evaluate", "plans/aws_safe.json", "--no-audit")[0] == cli.EXIT_OK
        assert len((tmp / "changegate-audit.jsonl").read_text().splitlines()) == 1


def test_approve_and_verify_workflow():
    """approve twice, then verify passes; the author can't approve"""
    with workdir() as tmp, env(CHANGEGATE_HMAC_KEY=TEST_KEY):
        plan = "plans/aws_db_replace.json"
        assert run("verify", plan, "--author", "dave")[0] == cli.EXIT_NEEDS_APPROVAL
        code, out, _ = run("approve", plan, "--approver", "alice")
        assert code == cli.EXIT_OK and "approvals" in out
        run("approve", plan, "--approver", "dave")
        run("approve", plan, "--approver", "bob")
        code, out, _ = run("verify", plan, "--author", "dave")
        assert code == cli.EXIT_OK, out
        assert "APPROVED" in out and "own change" in out
        assert len(list((tmp / "approvals").glob("*.json"))) == 3


def test_approve_refusals():
    """approve: nothing to approve for ALLOW, refuses BLOCK, needs an approver"""
    with workdir() as tmp, env(CHANGEGATE_HMAC_KEY=TEST_KEY):
        code, out, _ = run("approve", "plans/aws_safe.json", "--approver", "alice")
        assert code == cli.EXIT_OK and "Nothing to approve" in out
        code, _, err = run("approve", "plans/aws_risky.json", "--approver", "alice")
        assert code == cli.EXIT_BLOCKED and err and not (tmp / "approvals").exists()
        raises(cli.UsageError, run, "approve", "plans/aws_db_replace.json")


def test_verify_without_key_is_reported():
    """a missing key becomes a listed problem in verify, not a crash"""
    with workdir(), env(CHANGEGATE_HMAC_KEY=None):
        code, out, _ = run("verify", "plans/aws_db_replace.json")
        assert code == cli.EXIT_NEEDS_APPROVAL and "CHANGEGATE_HMAC_KEY" in out


def test_audit_commands():
    """audit verify reports OK or failure; audit show prints records"""
    with workdir() as tmp:
        run("evaluate", "plans/aws_safe.json")
        run("evaluate", "plans/gcp_safe.json")
        code, out, _ = run("audit", "verify")
        assert code == cli.EXIT_OK and out.startswith("audit log OK: 2 record(s), head ")
        code, out, _ = run("audit", "show", "--tail", "1")
        assert json.loads(out)["seq"] == 2
        log = tmp / "changegate-audit.jsonl"
        log.write_text(log.read_text().replace('"allow"', '"block"', 1))
        assert run("audit", "verify")[0] == cli.EXIT_BLOCKED

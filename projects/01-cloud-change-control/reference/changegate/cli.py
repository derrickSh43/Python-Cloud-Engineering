"""The `changegate` command-line tool.

    changegate evaluate PLAN.json                    risk + decision (exit 0 allow, 2 approval, 1 block)
    changegate approve  PLAN.json --approver NAME    write a signed approval for this exact plan
    changegate verify   PLAN.json --approvals DIR    evaluate and check approvals (the CI gate)
    changegate audit verify                          check the audit log's hash chain
    changegate audit show [--tail N]                 print recent audit records
    changegate policies                              list the enabled policies
    changegate hash PLAN.json                        print the plan's SHA-256

Configuration: --config, $CHANGEGATE_CONFIG or ./changegate.toml. Identities can also come from the
environment so CI can supply them: $CHANGEGATE_APPROVER, $CHANGEGATE_AUTHOR.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Sequence

from . import __version__, approvals, evaluator, plan_parser, report
from .audit import AuditError, AuditLog
from .config import Config, ConfigError, load_config
from .models import Decision, Evaluation
from .policies import PolicyLoadError, load_policies

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_NEEDS_APPROVAL = 2
EXIT_ERROR = 3

log = logging.getLogger("changegate")


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    """argparse exits with 2 on bad usage, which would look like 'approval required'. Use 3 instead."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, "%s: error: %s\n" % (self.prog, message))


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(prog="changegate", description="Evaluate Terraform plans against security policy.")
    parser.add_argument("--version", action="version", version="changegate " + __version__)
    parser.add_argument("--config", help="path to changegate.toml")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging to stderr")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)

    def output_options(p):
        p.add_argument("--format", choices=sorted(report.RENDERERS), default="text")
        p.add_argument("--output", help="also write the report to this file")
        p.add_argument("--no-audit", action="store_true", help="don't write an audit record")

    p = sub.add_parser("evaluate", help="evaluate a plan")
    p.add_argument("plan")
    output_options(p)

    p = sub.add_parser("approve", help="sign an approval for a plan")
    p.add_argument("plan")
    p.add_argument("--approver", default=os.environ.get("CHANGEGATE_APPROVER"),
                   help="who is approving (default $CHANGEGATE_APPROVER)")
    p.add_argument("--comment", default="")
    p.add_argument("--ttl-hours", type=float, help="validity (default: approvals.max_age_hours)")
    p.add_argument("--out-dir", default="approvals", help="directory to write the approval file to")
    p.add_argument("--no-audit", action="store_true")

    p = sub.add_parser("verify", help="evaluate a plan and check its approvals")
    p.add_argument("plan")
    p.add_argument("--approvals", nargs="*", default=["approvals"], help="approval files or directories")
    p.add_argument("--author", default=os.environ.get("CHANGEGATE_AUTHOR"),
                   help="who made the change; they can't approve it (default $CHANGEGATE_AUTHOR)")
    output_options(p)

    p = sub.add_parser("audit", help="inspect the audit log")
    audit_sub = p.add_subparsers(dest="audit_command", required=True, parser_class=Parser)
    a = audit_sub.add_parser("verify", help="check the hash chain")
    a.add_argument("--log", help="audit log path (default from config)")
    a.add_argument("--expect-head", help="head hash recorded elsewhere, to detect truncation")
    a = audit_sub.add_parser("show", help="print recent records")
    a.add_argument("--log", help="audit log path (default from config)")
    a.add_argument("--tail", type=int, default=10)

    sub.add_parser("policies", help="list enabled policies")

    p = sub.add_parser("hash", help="print a plan file's SHA-256")
    p.add_argument("plan")
    return parser


# ---------------------------------------------------------------- helpers

def exit_code_for(evaluation: Evaluation, approved: bool = False) -> int:
    if evaluation.decision == Decision.BLOCK:
        return EXIT_BLOCKED
    if evaluation.decision == Decision.REQUIRE_APPROVAL and not approved:
        return EXIT_NEEDS_APPROVAL
    return EXIT_OK


def emit(text: str, output: str | None) -> None:
    sys.stdout.write(text)
    if output:
        Path(output).write_text(text, encoding="utf-8")


def audit(config: Config, args: argparse.Namespace, event: str, data: dict) -> None:
    if getattr(args, "no_audit", False) or not config.audit.enabled:
        return
    record = AuditLog(config.audit.path).append(event, data)
    log.debug("audit record %s written to %s", record["seq"], config.audit.path)


def evaluation_summary(evaluation: Evaluation, plan: str) -> dict:
    return {"plan": os.path.basename(plan), "plan_sha256": evaluation.plan_sha256, "risk": str(evaluation.risk),
            "decision": str(evaluation.decision), "findings": [f.policy_id + " " + f.address for f in evaluation.findings]}


# ---------------------------------------------------------------- commands

def cmd_evaluate(args: argparse.Namespace, config: Config) -> int:
    evaluation = evaluator.evaluate_file(args.plan, config)
    emit(report.RENDERERS[args.format](evaluation), args.output)
    audit(config, args, "evaluate", evaluation_summary(evaluation, args.plan))
    return exit_code_for(evaluation)


def cmd_approve(args: argparse.Namespace, config: Config) -> int:
    if not args.approver:
        raise UsageError("--approver (or $CHANGEGATE_APPROVER) is required")
    evaluation = evaluator.evaluate_file(args.plan, config)
    if evaluation.decision == Decision.ALLOW:
        print("This plan is allowed without approval (risk %s). Nothing to approve." % evaluation.risk)
        return EXIT_OK
    if evaluation.decision == Decision.BLOCK:
        print("This plan is BLOCKED (risk %s). Approvals cannot override a block." % evaluation.risk, file=sys.stderr)
        return EXIT_BLOCKED
    key = approvals.load_key(config.approvals.key_env)
    approval = approvals.create_approval(
        evaluation.plan_sha256, args.approver, evaluation.risk, key,
        ttl_hours=args.ttl_hours or config.approvals.max_age_hours, comment=args.comment)
    path = approvals.write_approval(approval, args.out_dir)
    print("Approval by %s for plan %s... (risk %s) written to %s" % (
        approval.approver, evaluation.plan_sha256[:12], evaluation.risk, path))
    audit(config, args, "approve", {"plan_sha256": evaluation.plan_sha256, "approver": approval.approver,
                                    "risk": str(evaluation.risk), "expires_at": approval.to_dict()["expires_at"]})
    return EXIT_OK


def cmd_verify(args: argparse.Namespace, config: Config) -> int:
    evaluation = evaluator.evaluate_file(args.plan, config)
    found, load_problems = approvals.load_approvals(args.approvals)
    key = None
    if evaluation.decision == Decision.REQUIRE_APPROVAL:
        try:
            key = approvals.load_key(config.approvals.key_env)
        except approvals.ApprovalError as e:
            load_problems.append(str(e))
    check = approvals.check_approvals(evaluation, found, config.approvals, key, author=args.author)
    if load_problems:
        check = approvals.ApprovalCheck(check.satisfied, check.required, check.approved_by,
                                        tuple(load_problems) + check.problems)
    emit(report.RENDERERS[args.format](evaluation, check), args.output)
    code = exit_code_for(evaluation, approved=check.satisfied)
    audit(config, args, "verify", {**evaluation_summary(evaluation, args.plan),
                                   "approved_by": list(check.approved_by), "outcome": report.final_outcome(evaluation, check)})
    return code


def cmd_audit(args: argparse.Namespace, config: Config) -> int:
    log_file = AuditLog(args.log or config.audit.path)
    if args.audit_command == "show":
        for record in log_file.records()[-args.tail:]:
            print(json.dumps(record, sort_keys=True))
        return EXIT_OK
    result = log_file.verify(expected_head=args.expect_head)
    if result.ok:
        print("audit log OK: %d record(s), head %s" % (result.count, result.head))
        return EXIT_OK
    print("audit log FAILED verification (%d record(s)):" % result.count)
    for problem in result.problems:
        print("  - " + problem)
    return EXIT_BLOCKED


def cmd_policies(args: argparse.Namespace, config: Config) -> int:
    for policy in load_policies(config.policies):
        print("%-28s %-8s %s" % (policy.id, policy.level, policy.title))
    return EXIT_OK


def cmd_hash(args: argparse.Namespace, config: Config) -> int:
    print(plan_parser.plan_digest(plan_parser.read_plan_bytes(args.plan)))
    return EXIT_OK


COMMANDS = {"evaluate": cmd_evaluate, "approve": cmd_approve, "verify": cmd_verify, "audit": cmd_audit,
            "policies": cmd_policies, "hash": cmd_hash}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING,
                        format="changegate: %(levelname)s: %(message)s", stream=sys.stderr)
    try:
        config = load_config(args.config)
        log.debug("config: %s", config.source or "built-in defaults")
        return COMMANDS[args.command](args, config)
    except (ConfigError, PolicyLoadError, plan_parser.PlanError, approvals.ApprovalError, AuditError,
            UsageError, OSError) as e:
        print("changegate: error: %s" % e, file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())

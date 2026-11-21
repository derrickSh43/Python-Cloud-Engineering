"""Ties the pipeline together: plan -> changes -> findings -> risk -> decision."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from . import plan_parser, risk
from .config import Config
from .models import Evaluation, ResourceChange
from .policies import Policy, load_policies, run_policies


def evaluate_changes(changes: Iterable[ResourceChange], plan_sha256: str, config: Config | None = None,
                     policies: Iterable[Policy] | None = None) -> Evaluation:
    config = config or Config()
    changes = tuple(changes)
    policies = list(policies) if policies is not None else load_policies(config.policies)
    findings = sorted(run_policies(policies, changes), key=lambda f: (-f.severity, f.address, f.policy_id))
    level, reasons = risk.classify(changes, findings, config.risk)
    decision, why = risk.decide(level, config.risk)
    return Evaluation(plan_sha256=plan_sha256, changes=changes, findings=tuple(findings), risk=level,
                      decision=decision, reasons=tuple(reasons + [why]))


def evaluate_bytes(raw: bytes, config: Config | None = None,
                   policies: Iterable[Policy] | None = None) -> Evaluation:
    plan = plan_parser.decode_plan(raw)
    changes = plan_parser.parse_plan(plan)
    return evaluate_changes(changes, plan_parser.plan_digest(raw), config, policies)


def evaluate_file(path: str | Path, config: Config | None = None,
                  policies: Iterable[Policy] | None = None) -> Evaluation:
    return evaluate_bytes(plan_parser.read_plan_bytes(path), config, policies)

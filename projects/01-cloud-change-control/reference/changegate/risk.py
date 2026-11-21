"""Turns findings into one overall risk level, and the risk level into a decision."""

from __future__ import annotations

from typing import Iterable

from .config import RiskConfig
from .models import Decision, Finding, ResourceChange, Severity


def classify(changes: Iterable[ResourceChange], findings: Iterable[Finding],
             cfg: RiskConfig | None = None) -> tuple[Severity, list[str]]:
    """Return (risk, reasons). Risk starts at the most severe finding (LOW if none); a large number
    of destructive changes raises it one level, because many small deletes add up."""
    cfg = cfg or RiskConfig()
    changes = [c for c in changes if c.action.changes_state]
    findings = list(findings)
    if not changes and not findings:
        return Severity.LOW, ["the plan makes no changes"]
    reasons = []
    level = max((f.severity for f in findings), default=Severity.LOW)
    if findings:
        at_level = sum(1 for f in findings if f.severity == level)
        reasons.append("%d finding(s); highest severity %s (%d at that level)" % (len(findings), level, at_level))
    else:
        reasons.append("no policy findings across %d change(s)" % len(changes))
    destructive = sum(1 for c in changes if c.action.is_destructive)
    threshold = cfg.destructive_escalation_threshold
    if threshold and destructive >= threshold and level < Severity.CRITICAL:
        raised = level.escalate()
        reasons.append("%d destructive changes (threshold %d) raise risk from %s to %s" % (
            destructive, threshold, level, raised))
        level = raised
    return level, reasons


def decide(risk: Severity, cfg: RiskConfig | None = None) -> tuple[Decision, str]:
    cfg = cfg or RiskConfig()
    if cfg.block_at is not None and risk >= cfg.block_at:
        return Decision.BLOCK, "risk %s is at or above the block threshold (%s)" % (risk, cfg.block_at)
    if risk >= cfg.approval_at:
        return Decision.REQUIRE_APPROVAL, "risk %s is at or above the approval threshold (%s)" % (risk, cfg.approval_at)
    return Decision.ALLOW, "risk %s is below the approval threshold (%s)" % (risk, cfg.approval_at)

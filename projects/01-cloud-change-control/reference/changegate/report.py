"""Human- and machine-readable reports of an evaluation (and, optionally, an approval check)."""

from __future__ import annotations

import json

from .approvals import ApprovalCheck
from .models import Decision, Evaluation

ICONS = {Decision.ALLOW: "ALLOW", Decision.REQUIRE_APPROVAL: "APPROVAL REQUIRED", Decision.BLOCK: "BLOCKED"}


def final_outcome(evaluation: Evaluation, check: ApprovalCheck | None) -> str:
    if evaluation.decision == Decision.REQUIRE_APPROVAL and check is not None:
        return "APPROVED" if check.satisfied else "APPROVAL REQUIRED"
    return ICONS[evaluation.decision]


def _actions(evaluation: Evaluation) -> str:
    counts = evaluation.action_counts
    return ", ".join("%d %s" % (n, action) for action, n in sorted(counts.items())) or "no resources"


def render_text(evaluation: Evaluation, check: ApprovalCheck | None = None) -> str:
    lines = [
        "Cloud ChangeGate",
        "  plan:      sha256 %s" % evaluation.plan_sha256,
        "  changes:   %s" % _actions(evaluation),
        "  risk:      %s" % evaluation.risk,
        "  decision:  %s" % final_outcome(evaluation, check),
    ]
    for reason in evaluation.reasons:
        lines.append("             - %s" % reason)
    if evaluation.findings:
        lines.append("")
        lines.append("Findings (%d):" % len(evaluation.findings))
        for f in evaluation.findings:
            lines.append("  [%-8s] %s  %s" % (f.severity, f.policy_id, f.address))
            lines.append("             %s" % f.message)
            if f.remediation:
                lines.append("             fix: %s" % f.remediation)
    if check is not None and evaluation.decision == Decision.REQUIRE_APPROVAL:
        lines.append("")
        lines.append("Approvals: %d of %d required" % (len(check.approved_by), check.required))
        for who in check.approved_by:
            lines.append("  ok   %s" % who)
        for problem in check.problems:
            lines.append("  --   %s" % problem)
    return "\n".join(lines) + "\n"


def render_json(evaluation: Evaluation, check: ApprovalCheck | None = None) -> str:
    data = evaluation.to_dict()
    data["outcome"] = final_outcome(evaluation, check)
    if check is not None:
        data["approvals"] = check.to_dict()
    return json.dumps(data, indent=2) + "\n"


def _md(text: str) -> str:
    return text.replace("|", "\\|")


def render_markdown(evaluation: Evaluation, check: ApprovalCheck | None = None) -> str:
    """Suitable for a pull-request comment or a CI job summary."""
    lines = [
        "## Cloud ChangeGate: %s" % final_outcome(evaluation, check),
        "",
        "| | |", "|---|---|",
        "| Risk | **%s** |" % evaluation.risk,
        "| Changes | %s |" % _actions(evaluation),
        "| Plan SHA-256 | `%s` |" % evaluation.plan_sha256,
        "",
    ]
    lines += ["- %s" % _md(r) for r in evaluation.reasons]
    if evaluation.findings:
        lines += ["", "### Findings", "", "| Severity | Policy | Resource | Problem | Fix |", "|---|---|---|---|---|"]
        for f in evaluation.findings:
            lines.append("| %s | `%s` | `%s` | %s | %s |" % (f.severity, f.policy_id, f.address, _md(f.message),
                                                       _md(f.remediation)))
    if check is not None and evaluation.decision == Decision.REQUIRE_APPROVAL:
        lines += ["", "### Approvals (%d of %d)" % (len(check.approved_by), check.required), ""]
        lines += ["- approved by **%s**" % _md(w) for w in check.approved_by]
        lines += ["- %s" % _md(p) for p in check.problems]
    return "\n".join(lines) + "\n"


RENDERERS = {"text": render_text, "json": render_json, "markdown": render_markdown}

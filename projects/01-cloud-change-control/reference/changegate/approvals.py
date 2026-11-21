"""Signed approvals.

An approval says: "<approver> approves the plan whose SHA-256 is <hash>, at risk <level>, until
<expiry>". It is signed with HMAC-SHA256 using a secret key taken from an environment variable, so
it can't be edited (or moved to a different plan) without the key.

Security model and its limits are documented in docs/SECURITY.md. In short: anyone holding the key
can create approvals, so the key belongs only to the approval service (e.g. a protected CI
environment), never to the people whose changes are being approved.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import os
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .canonical import canonical_bytes
from .config import ApprovalConfig
from .models import Decision, Evaluation, Severity

FORMAT_VERSION = 1
MIN_KEY_BYTES = 32
CLOCK_SKEW = timedelta(minutes=5)


class ApprovalError(Exception):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    if moment.tzinfo is None:
        raise ApprovalError("timestamps must be timezone-aware")
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(text: str, where: str) -> datetime:
    try:
        moment = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        raise ApprovalError("%s is not an ISO-8601 timestamp: %r" % (where, text)) from None
    if moment.tzinfo is None:
        raise ApprovalError("%s must include a timezone: %r" % (where, text))
    return moment


def same_identity(a: str, b: str) -> bool:
    return a.strip().casefold() == b.strip().casefold()


@dataclass(frozen=True)
class Approval:
    plan_sha256: str
    approver: str
    risk: Severity
    issued_at: datetime
    expires_at: datetime
    comment: str = ""
    signature: str = field(default="", compare=False)

    def payload(self) -> dict[str, Any]:
        """Everything that is signed. The signature itself is not part of it."""
        return {"version": FORMAT_VERSION, "plan_sha256": self.plan_sha256, "approver": self.approver,
                "risk": str(self.risk), "issued_at": _iso(self.issued_at), "expires_at": _iso(self.expires_at),
                "comment": self.comment}

    def to_dict(self) -> dict[str, Any]:
        return {**self.payload(), "signature": self.signature}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Approval":
        if not isinstance(data, Mapping):
            raise ApprovalError("approval must be a JSON object")
        missing = [k for k in ("version", "plan_sha256", "approver", "risk", "issued_at", "expires_at", "signature")
                   if k not in data]
        if missing:
            raise ApprovalError("approval is missing: %s" % ", ".join(missing))
        if data["version"] != FORMAT_VERSION:
            raise ApprovalError("unsupported approval version %r" % (data["version"],))
        try:
            risk = Severity.parse(data["risk"])
        except ValueError as e:
            raise ApprovalError(str(e)) from None
        return cls(plan_sha256=str(data["plan_sha256"]), approver=str(data["approver"]), risk=risk,
                   issued_at=_parse_time(data["issued_at"], "issued_at"),
                   expires_at=_parse_time(data["expires_at"], "expires_at"),
                   comment=str(data.get("comment", "")), signature=str(data["signature"]))


# ---------------------------------------------------------------- keys and signatures

def load_key(env_name: str, environ: Mapping[str, str] | None = None) -> bytes:
    environ = os.environ if environ is None else environ
    value = environ.get(env_name, "")
    if not value:
        raise ApprovalError("environment variable %s is not set; it must hold the approval signing key "
                            "(at least %d bytes, e.g. from `python -c \"import secrets; print(secrets.token_hex(32))\"`)"
                            % (env_name, MIN_KEY_BYTES))
    key = value.encode("utf-8")
    if len(key) < MIN_KEY_BYTES:
        raise ApprovalError("%s is too short (%d bytes); use at least %d" % (env_name, len(key), MIN_KEY_BYTES))
    return key


def compute_signature(approval: Approval, key: bytes) -> str:
    return hmac.new(key, canonical_bytes(approval.payload()), hashlib.sha256).hexdigest()


def sign(approval: Approval, key: bytes) -> Approval:
    return replace(approval, signature=compute_signature(approval, key))


def signature_valid(approval: Approval, key: bytes) -> bool:
    # compare_digest takes the same time whether the first or last character differs,
    # so an attacker can't guess a signature one character at a time.
    return hmac.compare_digest(approval.signature, compute_signature(approval, key))


def create_approval(plan_sha256: str, approver: str, risk: Severity, key: bytes, ttl_hours: float,
                    comment: str = "", now: datetime | None = None) -> Approval:
    if not re.fullmatch(r"[0-9a-f]{64}", plan_sha256):
        raise ApprovalError("plan_sha256 must be 64 lowercase hex characters")
    if not approver.strip():
        raise ApprovalError("approver must not be empty")
    if ttl_hours <= 0:
        raise ApprovalError("ttl_hours must be positive")
    now = now or utcnow()
    approval = Approval(plan_sha256, approver.strip(), risk, now, now + timedelta(hours=ttl_hours), comment)
    return sign(approval, key)


# ---------------------------------------------------------------- files

def _safe(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", text)[:64] or "approver"


def write_approval(approval: Approval, directory: str | Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s-%s.json" % (approval.plan_sha256[:12], _safe(approval.approver)))
    path.write_text(json.dumps(approval.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_approvals(paths: Iterable[str | Path]) -> tuple[list[Approval], list[str]]:
    """Load approval files. A directory means every *.json inside it. Unreadable files are reported,
    not fatal - one bad file must not hide the good ones (nor count as an approval)."""
    approvals, problems = [], []
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(p.glob("*.json"))
        elif p.exists():
            files.append(p)
        else:
            problems.append("%s: not found" % p)
    for f in files:
        try:
            approvals.append(Approval.from_dict(json.loads(f.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError, ApprovalError) as e:
            problems.append("%s: %s" % (f.name, e))
    return approvals, problems


# ---------------------------------------------------------------- verification

@dataclass(frozen=True)
class ApprovalCheck:
    satisfied: bool
    required: int
    approved_by: tuple[str, ...]
    problems: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"satisfied": self.satisfied, "required": self.required, "approved_by": list(self.approved_by),
                "problems": list(self.problems)}


def approval_problem(approval: Approval, evaluation: Evaluation, cfg: ApprovalConfig, key: bytes,
                     author: str | None, now: datetime) -> str | None:
    """Why this approval doesn't count, or None if it is valid. Checks run cheapest-to-trust first:
    nothing in an approval is believed until its signature checks out."""
    who = approval.approver or "(unknown)"
    if not signature_valid(approval, key):
        return "%s: signature is invalid (file edited, or signed with a different key)" % who
    if not hmac.compare_digest(approval.plan_sha256, evaluation.plan_sha256):
        return "%s: approval is for a different plan (%s...)" % (who, approval.plan_sha256[:12])
    if approval.issued_at > now + CLOCK_SKEW:
        return "%s: issued in the future (%s)" % (who, _iso(approval.issued_at))
    if now >= approval.expires_at:
        return "%s: expired at %s" % (who, _iso(approval.expires_at))
    if now - approval.issued_at > timedelta(hours=cfg.max_age_hours):
        return "%s: older than the %g hour maximum" % (who, cfg.max_age_hours)
    if author and not cfg.allow_self_approval and same_identity(approval.approver, author):
        return "%s: authors cannot approve their own change" % who
    if not any(same_identity(approval.approver, allowed) for allowed in cfg.approvers):
        return "%s: not in the configured approvers list" % who
    if approval.risk < evaluation.risk:
        return "%s: approved risk %s but the plan is now %s" % (who, approval.risk, evaluation.risk)
    return None


def check_approvals(evaluation: Evaluation, approvals: Iterable[Approval], cfg: ApprovalConfig, key: bytes | None,
                    author: str | None = None, now: datetime | None = None) -> ApprovalCheck:
    if evaluation.decision == Decision.ALLOW:
        return ApprovalCheck(True, 0, (), ())
    if evaluation.decision == Decision.BLOCK:
        return ApprovalCheck(False, 0, (), ("the plan is blocked; approvals cannot override a block",))
    required = cfg.required_for(evaluation.risk)
    approvals = list(approvals)
    if not cfg.approvers:
        return ApprovalCheck(False, required, (), ("no approvers are configured ([approvals] approvers)",))
    if key is None:
        return ApprovalCheck(False, required, (), ("no signing key available to verify approvals",))
    now = now or utcnow()
    approved_by: list[str] = []
    problems: list[str] = []
    for approval in approvals:
        problem = approval_problem(approval, evaluation, cfg, key, author, now)
        if problem:
            problems.append(problem)
        elif any(same_identity(approval.approver, seen) for seen in approved_by):
            problems.append("%s: duplicate approval (counted once)" % approval.approver)
        else:
            approved_by.append(approval.approver)
    satisfied = len(approved_by) >= required
    if not satisfied:
        problems.append("%d of %d required approval(s) for %s risk" % (len(approved_by), required, evaluation.risk))
    return ApprovalCheck(satisfied, required, tuple(approved_by), tuple(problems))

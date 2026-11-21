# Security model

ChangeGate is a teaching project built to production habits. This page states plainly what it protects
against and what it does not, so nobody mistakes it for more than it is.

## What ChangeGate enforces

- **Policy before apply.** Every plan is evaluated; risky changes need approval and critical ones are blocked.
- **Approvals bound to one plan.** An approval signs the SHA-256 of the exact plan JSON. Change one byte of
  the plan and every approval stops counting.
- **Approval rules.** Approvers must be on the configured list, approvals expire, the change author can't
  approve their own change (unless explicitly allowed), duplicates count once, an approval for a lower risk
  doesn't cover a plan that is now riskier, and approvals never override a BLOCK.
- **Tamper evidence.** Each audit record includes the hash of the previous one. Editing, deleting or
  reordering records is detected by `changegate audit verify`.
- **Fail closed.** Crashing policies, unknown config keys and malformed approval files never weaken a decision.

## Limits you must understand

1. **HMAC is a shared secret.** Anyone who holds `CHANGEGATE_HMAC_KEY` can create approvals for any name.
   The key must be available only to the approval step (for example a GitHub *environment* secret on a
   protected environment with required reviewers), never to the people or jobs whose changes are being
   approved. Rotating the key invalidates all outstanding approvals, which is usually what you want.
   For stronger guarantees use asymmetric signatures (e.g. Sigstore/cosign, KMS asymmetric keys) so
   verifiers never hold signing material. The interface in `approvals.py` is small enough to swap.
2. **Approver identity is asserted, not authenticated, by the CLI.** `--approver alice` is trusted because
   only the protected approval job can sign. In CI, take the identity from the platform
   (`github.actor` of the environment approval) rather than from user input.
3. **Truncation of the audit log** (deleting the newest records) cannot be detected from the file alone.
   Print the head hash (`changegate audit verify`) into CI logs or store it elsewhere, and verify with
   `--expect-head`. For real compliance needs, ship records to write-once storage (S3 Object Lock,
   GCS bucket lock) or a SIEM.
4. **Policies only see the plan.** They can't see drift, resources managed outside Terraform, or values
   that are unknown until apply (those are skipped, not guessed). Treat ChangeGate as one layer alongside
   cloud-native guardrails (AWS SCPs/Config, GCP Organization Policies).
5. **Plans can contain secrets.** `terraform show -json` may include sensitive values. Treat plan files and
   CI artifacts as confidential, keep retention short, and never commit them (they are git-ignored).

## Handling secrets in this repository

- No credentials, keys, account numbers or project ids are committed. Sample data uses placeholders
  (`123456789012`, `example-project`). `tests/test_no_hardcoding.py` fails the build if something that
  looks like a real key or account id appears.
- Real configuration lives in git-ignored files: `changegate.toml`, `*.tfvars`, `backend.hcl`.
- The signing key is read from an environment variable whose **name** is configurable
  (`[approvals] key_env`). Generate one with:

  ```
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

## Reporting a problem

Open an issue on the repository describing the behaviour, without including any real credentials or plan files.

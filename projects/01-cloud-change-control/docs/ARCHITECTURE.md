# Cloud ChangeGate architecture

```
terraform show -json plan.tfplan > plan.json
              │
              ▼
   plan_parser.py ──► [ResourceChange]  (models.py; cloud detected via providers.py)
              │
              ▼
   policies/* ──────► [Finding]          (base.py registry; aws.py, gcp.py, common.py; settings from config.py)
              │
              ▼
   risk.py ─────────► Severity  ──► Decision: ALLOW | REQUIRE_APPROVAL | BLOCK
              │
              ▼
   approvals.py ────► ApprovalCheck      (HMAC-signed, bound to the plan's SHA-256, expiring)
              │
              ▼
   audit.py ────────► hash-chained JSONL record
              │
              ▼
   report.py / cli.py ─► text | JSON | Markdown, exit code 0 / 1 / 2 / 3
```

## Design rules

1. **Policies are small and pure.** A policy looks at one `ResourceChange` and yields `Finding`s. No I/O,
   no global state, no knowledge of the final decision. That makes every rule testable in isolation.
2. **Cloud specifics live in one place.** `providers.py` knows how to recognise AWS and GCP, where their
   tags/labels live and which resource types hold data. Adding a cloud = adding one `Provider`.
3. **Nothing environment-specific in code.** Thresholds, approvers, required tags, the audit path and the
   *name* of the key's environment variable all come from `changegate.toml`. Secrets come only from the
   environment. See [SETUP.md](SETUP.md).
4. **Fail closed.** A policy that crashes produces a CRITICAL finding. Unknown config keys, unknown policy
   ids and malformed approvals are errors, not silently ignored.
5. **Explain every decision.** `Evaluation.reasons` and per-finding remediation text make the output
   actionable for the person who has to fix the plan.
6. **Exit codes are an API.** `0` allow/approved, `1` blocked (or audit verification failed), `2` approval
   required, `3` error. CI pipelines branch on these.

## Module reference

| Module | Responsibility |
|---|---|
| `models.py` | `Action`, `Severity`, `Decision`, `ResourceChange`, `Finding`, `Evaluation` |
| `providers.py` | provider registry: AWS, Google (+ google-beta) |
| `plan_parser.py` | read/validate plan JSON → `ResourceChange`s; `plan_digest` |
| `config.py` | load + validate `changegate.toml` |
| `policies/base.py` | `Policy` ABC, `@register`, `load_policies`, `run_policies` |
| `policies/helpers.py`, `network.py` | CIDR/port/IAM-document helpers; shared open-ingress logic |
| `policies/common.py` | `CG-DESTROY-STATEFUL`, `CG-REQUIRED-TAGS` |
| `policies/aws.py` | S3 ACL / public access block / bucket policy, security groups, encryption, IAM wildcards, public RDS |
| `policies/gcp.py` | public GCS IAM, uniform bucket access, firewall, basic/public project IAM, public Cloud SQL |
| `risk.py` | `classify` (max severity + destructive escalation) and `decide` |
| `evaluator.py` | wires parser → policies → risk |
| `canonical.py` | canonical JSON for hashing/signing |
| `approvals.py` | create/sign/verify approvals; approval rules |
| `audit.py` | append-only hash-chained log and verification |
| `report.py` | text, JSON and Markdown renderers |
| `cli.py` | `changegate` command |

## Built-in policies

Run `changegate policies` for the live list. Default severities (overridable in config):

| Id | Severity | Cloud |
|---|---|---|
| CG-DESTROY-STATEFUL | HIGH | any |
| CG-REQUIRED-TAGS | LOW (inactive until `required` is set) | any |
| AWS-S3-PUBLIC-ACL | HIGH (CRITICAL for public-read-write) | AWS |
| AWS-S3-PUBLIC-ACCESS-BLOCK | HIGH | AWS |
| AWS-S3-PUBLIC-POLICY | HIGH | AWS |
| AWS-SG-OPEN-INGRESS | HIGH (CRITICAL for all ports) | AWS |
| AWS-STORAGE-UNENCRYPTED | HIGH | AWS |
| AWS-IAM-WILDCARD | HIGH (CRITICAL for `"Action": "*"`) | AWS |
| AWS-RDS-PUBLIC | HIGH | AWS |
| GCP-GCS-PUBLIC-IAM | HIGH | GCP |
| GCP-GCS-UNIFORM-ACCESS | MEDIUM | GCP |
| GCP-FIREWALL-OPEN-INGRESS | HIGH (CRITICAL for all ports) | GCP |
| GCP-IAM-PRIMITIVE-ROLE | HIGH (CRITICAL for allUsers) | GCP |
| GCP-SQL-PUBLIC-NETWORK | HIGH | GCP |

S3 buckets are encrypted by default (SSE-S3) since January 2023 and Google Cloud encrypts all data at
rest, so there is no "unencrypted bucket" rule for either.

# Curriculum map: worked backward from ChangeGate

The curriculum was designed by starting from the finished tool and asking, for each component,
"what must a learner be able to do to write this themselves?" Every skill below is taught before the
exercise that needs it.

## Content principle: the course teaches Python

The audience is infrastructure and cloud engineers who want to write better tooling, not to learn
Terraform or system design from this course. So:

- **Questions test Python.** A question shows code and asks what it prints or raises, or asks about a
  Python feature. No quizzes on Terraform behaviour, cloud services or security theory. The selftest
  runs every question's code and checks that the marked answer matches.
- **Domain knowledge lives in the task, not the test.** When an exercise needs a fact ("a replacement is
  `["delete", "create"]`", "`allUsers` means public"), the task states it as part of the data spec.
- **Explanations stay short** and describe the data's shape and the rule to code, not the background.
- Infra-flavoured data (resource names, ports, tags, plan JSON) is kept as the material the code works on.

## Components → skills → phase

| Component (reference file) | What it does | Skills it needs | Taught in | Built in |
|---|---|---|---|---|
| — | warm-up | `print`, variables, strings, f-strings, numbers, `input` | 1 | 1 (checkpoint) |
| — | warm-up | `if`/`elif`/`else`, comparisons, booleans | 1 | 1 |
| — | warm-up | lists, loops, `range`, `enumerate`, dicts, nested data | 1 | 1 |
| — | warm-up | functions, parameters, return values, scope | 1 | 1 |
| `plan_parser.py` (part 1) | read a plan file | files, `pathlib`, `json`, bytes vs text, encodings | 2 | 2 |
| `plan_parser.py` (part 2) | navigate plan JSON | nested dict/list access, `.get`, comprehensions, `None` handling | 2 | 2 |
| `plan_parser.py` (errors) | fail with a useful message | exceptions, `try`/`except`/`raise`, custom exception classes, `raise ... from None` | 2 | 2 |
| `plan_parser.plan_digest` | identify a plan exactly | `hashlib`, bytes | 2 | 2 |
| `models.py` | typed data | modules & packages, `dataclasses` (frozen), `Enum`/`IntEnum`, type hints, properties, classmethods | 3 | 3 |
| `providers.py` | cloud adapters | dataclasses, registries (dict of objects), separating data from logic | 3 | 3 |
| tests | prove it works | virtual environments, `pip`, `pytest`, fixtures, `parametrize`, `tmp_path` | 3 | 3 → 6 |
| `policies/base.py` | plugin interface | classes, inheritance, `abc.ABC`, `ClassVar`, decorators, `importlib` | 4 | 4 |
| `policies/helpers.py` | shared logic | `ipaddress`, parsing port ranges, `json` inside JSON | 4 | 4 |
| `policies/aws.py`, `gcp.py`, `common.py` | the security rules | generators (`yield`), sets, applying the above to real resource shapes | 4 | 4 |
| `config.py` | team-specific settings | `tomllib`, validation, defaults, environment variables, "fail loudly on typos" | 4 | 4 |
| `risk.py` | overall risk + decision | `max` with defaults, ordering enums, explaining decisions | 4 | 4 |
| `evaluator.py` | the pipeline | composition, sorting with keys, fail-closed design | 4 | 4 |
| `canonical.py` | stable bytes | deterministic JSON | 5 | 5 |
| `approvals.py` | signed approvals | `hmac`, `compare_digest`, timezone-aware `datetime`, ISO-8601, secrets from env, `dataclasses.replace` | 5 | 5 |
| `audit.py` | tamper-evident log | hash chains, JSON Lines, append-only writes (`os.O_APPEND`) | 5 | 5 |
| `report.py` | human/machine output | string formatting, JSON output, Markdown tables | 6 | 6 |
| `cli.py` | the tool | `argparse` subcommands, exit codes, `logging`, `sys.exit`, stdout vs stderr | 6 | 6 |
| packaging | `changegate` command | `pyproject.toml`, entry points, `pip install -e` | 6 | 6 |
| CI (offline) | gate every PR | `subprocess.run`, exit codes, keeping the worst result; the provided CI template | 6A | 6A |
| Cloud (optional) | real plans | `terraform plan`/`show -json`, OIDC/Workload Identity, environments | 6B | 6B |

## Phase outcomes

- **Phase 0 - Orientation.** Use the app; see the tool you'll build and the Python each phase covers.
- **Phase 1 - Python fundamentals.** Write small programs with variables, decisions, loops, collections and
  functions, using resource names, tags, ports and regions as the examples.
- **Phase 2 - Data and files.** Load and navigate nested JSON from a real plan file; handle bad input with clear errors.
- **Phase 3 - Structure and testing.** Model plan data with dataclasses and enums; organise a package;
  write pytest tests.
- **Phase 4 - Policy engine.** Build pluggable policies for AWS and GCP, config loading, risk and decisions.
- **Phase 5 - Trust and accountability.** Sign and verify approvals; keep a hash-chained audit log; handle
  secrets and time correctly.
- **Phase 6A - Production automation.** Ship the CLI, reports, packaging and an offline CI gate.
  **The course is complete here.**
- **Phase 6B - Cloud deployment (optional).** Run the gate against real AWS/GCP plans in CI.

## Build exercises

Learners don't receive ChangeGate up front. `python learn.py workspace init` (run automatically the first
time it's needed) generates `workspace/` from `reference/`, replacing the body of every symbol below with
`raise NotImplementedError("TODO(<exercise id>)")` - signatures and docstrings stay. Everything not listed
(dataclass declarations for config, CLI helpers, the `Provider` registry entries...) is provided, so each
exercise is focused and the code always imports.

Each exercise has a focused test file in `exercises/tests/` (standard library only - they run before
pytest is introduced), a task and three graduated hints in `exercises/phaseN.toml`, and a reference
solution that is simply the original source of its symbols. `python learn.py selftest` proves, for every
exercise, that its tests **fail** when only the earlier exercises are solved and **pass** once it is solved
too - so the order always works and no exercise secretly depends on a later one.

The final exercise, the capstone, runs the full suite in `tests/` against the learner's workspace
(`CHANGEGATE_SRC=workspace`): the same 190+ tests the reference passes.

49 exercises (48 with focused tests, plus the capstone):

| Phase | Exercise | You implement | File |
|---|---|---|---|
| 2 | `p2-plan-digest` Fingerprint a plan with SHA-256 | `plan_digest` | `changegate/plan_parser.py` |
| 2 | `p2-read-plan` Read a plan file safely | `read_plan_bytes` | `changegate/plan_parser.py` |
| 2 | `p2-decode-plan` Decode plan JSON with useful errors | `decode_plan` | `changegate/plan_parser.py` |
| 2 | `p2-check-format` Check the plan format version | `check_format` | `changegate/plan_parser.py` |
| 2 | `p2-canonical` Canonical JSON: same data, same bytes | `canonical_bytes`, `sha256_hex` | `changegate/canonical.py` |
| 2 | `p2-lists-and-blocks` Normalise messy Terraform values | `as_list`, `first_block` | `changegate/policies/helpers.py` |
| 2 | `p2-ports` Parse and compare port ranges | `parse_port_range`, `range_includes_any`, `covers_all_ports` | `changegate/policies/helpers.py` |
| 2 | `p2-json-documents` Read IAM policy documents | `load_json_document`, `statements`, `principal_is_public` | `changegate/policies/helpers.py` |
| 3 | `p3-action` The Action enum: decoding Terraform actions | `Action.from_terraform`, `Action.is_destructive`, `Action.changes_state` | `changegate/models.py` |
| 3 | `p3-severity` Ordered severities | `Severity.parse`, `Severity.escalate` | `changegate/models.py` |
| 3 | `p3-resource-change` ResourceChange: a frozen dataclass | `ResourceChange` | `changegate/models.py` |
| 3 | `p3-finding` Finding: one policy problem | `Finding` | `changegate/models.py` |
| 3 | `p3-evaluation` Evaluation: the result of a whole plan | `Evaluation` | `changegate/models.py` |
| 3 | `p3-providers` A provider registry | `provider_key`, `lookup`, `cloud_for`, `all_stateful_types` | `changegate/providers.py` |
| 3 | `p3-parse-change` Turn one JSON entry into a ResourceChange | `parse_change` | `changegate/plan_parser.py` |
| 3 | `p3-parse-plan` Parse a whole plan | `parse_plan`, `load_plan` | `changegate/plan_parser.py` |
| 4 | `p4-networks` Is this CIDR the whole internet? | `is_world`, `any_world` | `changegate/policies/helpers.py` |
| 4 | `p4-config-validation` Validate config values | `_reject_unknown`, `_severity`, `_str_list` | `changegate/config.py` |
| 4 | `p4-config-risk` Load the [risk] section | `_risk` | `changegate/config.py` |
| 4 | `p4-config-load` Find and load the config file | `resolve_path`, `load_config` | `changegate/config.py` |
| 4 | `p4-policy-base` The Policy base class | `Policy.applies_to`, `Policy.finding` | `changegate/policies/base.py` |
| 4 | `p4-registry` Discover policies with a decorator | `register`, `load_policies` | `changegate/policies/base.py` |
| 4 | `p4-run-policies` Run policies and fail closed | `run_policies` | `changegate/policies/base.py` |
| 4 | `p4-destroy-stateful` Policy: deleting data-holding resources | `DestroyStatefulResource.stateful_types`, `DestroyStatefulResource.check` | `changegate/policies/common.py` |
| 4 | `p4-required-tags` Policy: required tags and labels | `RequiredTags.check` | `changegate/policies/common.py` |
| 4 | `p4-open-ingress` Shared logic: open to the internet | `OpenIngressPolicy.judge` | `changegate/policies/network.py` |
| 4 | `p4-aws-s3` AWS policies: public S3 | `S3PublicAcl.check`, `S3PublicAccessBlock.check`, `S3PublicBucketPolicy.check` | `changegate/policies/aws.py` |
| 4 | `p4-aws-security-groups` AWS policy: security groups | `SecurityGroupOpenIngress.check`, `SecurityGroupOpenIngress._rule` | `changegate/policies/aws.py` |
| 4 | `p4-aws-storage` AWS policies: encryption and public databases | `UnencryptedStorage.check`, `RdsPubliclyAccessible.check` | `changegate/policies/aws.py` |
| 4 | `p4-aws-iam` AWS policy: wildcard IAM permissions | `IamWildcard.check` | `changegate/policies/aws.py` |
| 4 | `p4-gcp-storage` GCP policies: public buckets | `_members`, `_roles`, `GcsPublicIam.check`, `GcsUniformAccess.check` | `changegate/policies/gcp.py` |
| 4 | `p4-gcp-network` GCP policies: firewalls and Cloud SQL | `FirewallOpenIngress.check`, `SqlPublicNetwork.check` | `changegate/policies/gcp.py` |
| 4 | `p4-gcp-iam` GCP policy: basic roles and public grants | `IamPrimitiveOrPublicRole.check` | `changegate/policies/gcp.py` |
| 4 | `p4-risk` Classify risk and decide | `classify`, `decide` | `changegate/risk.py` |
| 4 | `p4-evaluator` The evaluation pipeline | `evaluate_changes`, `evaluate_bytes`, `evaluate_file` | `changegate/evaluator.py` |
| 5 | `p5-approval-format` Approvals as JSON, with timezones | `_iso`, `_parse_time`, `Approval.payload`, `Approval.to_dict`, `Approval.from_dict` | `changegate/approvals.py` |
| 5 | `p5-signatures` Keys and HMAC signatures | `load_key`, `compute_signature`, `sign`, `signature_valid` | `changegate/approvals.py` |
| 5 | `p5-create-approval` Create an approval | `create_approval` | `changegate/approvals.py` |
| 5 | `p5-approval-rules` The rules for a valid approval | `approval_problem` | `changegate/approvals.py` |
| 5 | `p5-check-approvals` Count valid approvals | `check_approvals` | `changegate/approvals.py` |
| 5 | `p5-approval-files` Save and load approval files | `write_approval`, `load_approvals` | `changegate/approvals.py` |
| 5 | `p5-audit-append` An append-only, hash-chained log | `record_hash`, `AuditLog.records`, `AuditLog.head`, `AuditLog.append` | `changegate/audit.py` |
| 5 | `p5-audit-verify` Verify the audit chain | `AuditLog.verify` | `changegate/audit.py` |
| 6 | `p6-report-text` Plain-text report | `final_outcome`, `render_text` | `changegate/report.py` |
| 6 | `p6-report-formats` JSON and Markdown reports | `render_json`, `render_markdown` | `changegate/report.py` |
| 6 | `p6-cli-parser` Command-line arguments with argparse | `build_parser` | `changegate/cli.py` |
| 6 | `p6-cli-commands` The CLI commands and exit codes | `exit_code_for`, `cmd_evaluate`, `cmd_approve`, `cmd_verify`, `cmd_audit` | `changegate/cli.py` |
| 6 | `p6-cli-main` main(): one place for errors | `main` | `changegate/cli.py` |
| 6 | `p6-capstone` Capstone: the full ChangeGate test suite | the full suite passes | - |

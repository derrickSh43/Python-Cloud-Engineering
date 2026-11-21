# Curriculum map: worked backward from ChangeGate

The curriculum was designed by starting from the finished tool and asking, for each component,
"what must a learner be able to do to write this themselves?" Every skill below is taught before the
exercise that needs it.

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
| CI (offline) | gate every PR | GitHub Actions, running tests and the gate in CI | 6A | 6A |
| Cloud (optional) | real plans | `terraform plan`/`show -json`, OIDC/Workload Identity, environments | 6B | 6B |

## Phase outcomes

- **Phase 0 - Orientation.** Use the app; describe ChangeGate.
- **Phase 1 - Python fundamentals.** Write small programs with variables, decisions, loops, collections and
  functions, using resource names, tags, ports and regions as the examples.
- **Phase 2 - Data and files.** Load and navigate a real Terraform plan; handle bad input with clear errors.
- **Phase 3 - Structure and testing.** Model plan data with dataclasses and enums; organise a package;
  write pytest tests.
- **Phase 4 - Policy engine.** Build pluggable policies for AWS and GCP, config loading, risk and decisions.
- **Phase 5 - Trust and accountability.** Sign and verify approvals; keep a hash-chained audit log; handle
  secrets and time correctly.
- **Phase 6A - Production automation.** Ship the CLI, reports, packaging and an offline CI gate.
  **The course is complete here.**
- **Phase 6B - Cloud deployment (optional).** Run the gate against real AWS/GCP plans in CI.

## Build exercises

Each "build" exercise gives the learner a stub file in `workspace/changegate/` with `TODO`s and a
focused test file. `python learn.py check <exercise>` runs just those tests against the learner's code.
At the end, the full suite in `tests/` runs against the learner's workspace
(`CHANGEGATE_SRC=workspace`) - the same tests the reference passes.

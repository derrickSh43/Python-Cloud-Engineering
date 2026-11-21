# Project 01 - Cloud Change Control

Learn Python from your first `print()` to **Cloud ChangeGate**: a tested command-line tool that reads
Terraform plans, enforces modular security policies for AWS and GCP, classifies risk, verifies signed
approvals and keeps a tamper-evident audit trail, ready to run as a gate in CI/CD.

Start it from the repository root with `python learn.py`.

## Layout

```
project.toml          project metadata for the platform
curriculum/           the lessons (phase00_orientation ... phase06_*)
reference/            the complete ChangeGate implementation (the destination - try first, peek later)
exercises/            48 build exercises: tasks + graduated hints (phaseN.toml) and focused tests (tests/)
workspace/            YOUR copy of ChangeGate, generated with every exercise as a TODO (git-ignored)
tests/                the full ChangeGate test suite (runs against reference/ or your workspace/)
sample_data/          sample AWS/GCP plans + example config (all placeholders)
docs/                 ARCHITECTURE, SECURITY, SETUP, VERIFICATION, CURRICULUM_MAP
```

Available now: Phases 0-2 (orientation, Python fundamentals, data and files). Coming next: the Phase 3-6
lessons that lead into the remaining build exercises,
`examples/aws` and `examples/gcp` Terraform, and CI templates.

## Try the finished tool

```
cd projects/01-cloud-change-control/reference
python -m changegate --config ../sample_data/changegate.example.toml evaluate ../sample_data/plans/gcp_risky.json
```

```
Cloud ChangeGate
  risk:      CRITICAL
  decision:  BLOCKED
Findings (6):
  [CRITICAL] GCP-FIREWALL-OPEN-INGRESS  google_compute_firewall.allow_everything
  [HIGH    ] GCP-FIREWALL-OPEN-INGRESS  google_compute_firewall.allow_ssh
  ...
```

See [docs/SETUP.md](docs/SETUP.md) for the approval workflow and configuration, and
[docs/CURRICULUM_MAP.md](docs/CURRICULUM_MAP.md) for how each part of the tool maps to the lessons.

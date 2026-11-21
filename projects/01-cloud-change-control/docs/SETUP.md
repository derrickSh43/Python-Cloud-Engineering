# Setup

## Requirements

- **Python 3.11 or newer** (the course uses `tomllib`, added in 3.11). Check with `python --version`.
- **git** to clone the repository.
- Terraform is **not** required for the course. It's only needed for the optional cloud phase (6B).

## Get started

```
git clone https://github.com/derrickSh43/Python-Cloud-Engineering.git
cd Python-Cloud-Engineering
python learn.py
```

On macOS/Linux use `python3` if `python` points to Python 2. Phases 0-2 need nothing else installed.

From Phase 3 onward you'll use a virtual environment and pytest (the course walks you through it):

```
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Your workspace and build exercises

From Phase 2 you build ChangeGate yourself in `projects/01-cloud-change-control/workspace/`. It's created
automatically the first time you reach a build exercise (or run `python learn.py workspace init`): a copy
of the tool with each piece you'll write replaced by `raise NotImplementedError("TODO(<exercise id>)")`.
Open it in any editor.

```
python learn.py exercises            # what's done, what's next
python learn.py show p2-read-plan    # the task, the file, the function names
python learn.py check                # test the next unfinished exercise against your code
python learn.py hint p2-read-plan    # next hint (three per exercise, gentle -> specific)
python learn.py solution p2-read-plan   # after all hints or 3 genuine failed attempts
python learn.py workspace reset changegate/plan_parser.py   # start a file over (a .bak keeps yours)
```

The workspace is git-ignored, so pulling course updates never conflicts with your code.

## Running the reference implementation

The finished ChangeGate lives in `reference/` so you can see the destination. Don't read it before
attempting the exercises - but do run it:

```
cd projects/01-cloud-change-control
pip install -e reference
changegate --config sample_data/changegate.example.toml evaluate sample_data/plans/aws_risky.json
```

Or without installing: `cd reference` then `python -m changegate ...`.

## Configuration: where every value comes from

Nothing environment-specific is written in code. When you connect real infrastructure later, you fill
in values in these places only:

| What | Where | Committed? |
|---|---|---|
| Policy thresholds, approvers, required tags, audit path | `changegate.toml` (copy `sample_data/changegate.example.toml`) | no |
| Path to the config file | `--config` or `$CHANGEGATE_CONFIG` | - |
| Approval signing key | env var named by `[approvals] key_env` (default `CHANGEGATE_HMAC_KEY`) | never |
| Change author / approver identity | `--author` / `--approver` or `$CHANGEGATE_AUTHOR` / `$CHANGEGATE_APPROVER` | - |
| Cloud account, project, region (Phase 6B) | Terraform `*.tfvars` (copy the `.tfvars.example`) | no |
| Terraform state backend (Phase 6B) | `backend.hcl` passed with `terraform init -backend-config=backend.hcl` | no |
| CI cloud identity (Phase 6B) | GitHub repository/environment variables and secrets | - |

## Running the tests

```
pytest                                   # platform tests + the ChangeGate suite against reference/
python learn.py selftest                 # validates every lesson and exercise
```

To run the ChangeGate suite against your own code (the capstone):

```
CHANGEGATE_SRC=workspace pytest projects/01-cloud-change-control/tests      # macOS/Linux
$env:CHANGEGATE_SRC="workspace"; pytest projects/01-cloud-change-control/tests   # PowerShell
```

## Resetting progress

`python learn.py reset` erases saved progress for the current project. Progress is stored in
`.progress/profile.json` (git-ignored); set `PCE_PROGRESS_DIR` to keep it elsewhere.

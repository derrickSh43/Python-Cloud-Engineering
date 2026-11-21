"""Guards the "nothing hard-coded" rule: no real-looking cloud identifiers or secrets in the repo.

Allowed placeholders: AWS account 123456789012 (the AWS documentation example), the GCP project
`example-project`, and names under example.com. Real values belong in git-ignored files
(changegate.toml, *.tfvars, backend.hcl) or in CI variables and secrets.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".progress", "my_programs", ".pytest_cache", ".terraform"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".tf", ".hcl", ".txt", ".example", ".sh", ".bat",
                 ".cfg", ".ini", ".tfvars"}
PLACEHOLDER_ACCOUNT = "123456789012"

PATTERNS = {
    "AWS access key id": re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    "GCP service account key": re.compile(r'"type"\s*:\s*"service_account"'),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b"),
}
ACCOUNT_IN_ARN = re.compile(r"arn:aws[\w-]*:[\w-]+:[\w-]*:(\d{12}):")


def repo_files():
    try:
        listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.split()
        candidates = [ROOT / name for name in listed]
    except (OSError, subprocess.CalledProcessError):
        candidates = list(ROOT.rglob("*"))
    for path in candidates:
        if path.is_file() and not (set(path.relative_to(ROOT).parts) & SKIP_DIRS) and \
                (path.suffix in TEXT_SUFFIXES or path.name.endswith(".example")):
            yield path


def test_no_secrets_or_real_account_ids():
    problems = []
    this_file = Path(__file__).resolve()
    for path in repo_files():
        if path.resolve() == this_file:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                problems.append("%s: looks like a %s" % (path.relative_to(ROOT), label))
        for account in ACCOUNT_IN_ARN.findall(text):
            if account != PLACEHOLDER_ACCOUNT:
                problems.append("%s: ARN with non-placeholder account %s" % (path.relative_to(ROOT), account))
    assert not problems, "\n".join(problems)


def test_local_config_files_are_gitignored():
    ignore = (ROOT / ".gitignore").read_text()
    for pattern in ("changegate.toml", "*.tfvars", "backend.hcl", ".progress/", "*.tfstate"):
        assert pattern in ignore, "add %s to .gitignore" % pattern


def test_no_source_file_is_gitignored():
    """A too-broad .gitignore pattern once hid changegate/report.py from the repository."""
    try:
        ignored = subprocess.run(["git", "ls-files", "--others", "--ignored", "--exclude-standard"], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return  # not a git checkout (e.g. a downloaded ZIP)
    hidden = [f for f in ignored if f.endswith((".py", ".toml", ".md", ".json"))
              and not (set(Path(f).parts) & (SKIP_DIRS | {"workspace"}))
              and not f.endswith("changegate-audit.jsonl")]
    assert not hidden, "these source files are ignored by .gitignore: %s" % hidden

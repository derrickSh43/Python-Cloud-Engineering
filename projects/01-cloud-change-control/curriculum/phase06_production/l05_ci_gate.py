from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p06l5", "ChangeGate as a CI/CD gate", [
    T("""
        **Where a gate belongs**

        ChangeGate is most useful when nobody has to remember to run it. In a typical Terraform pipeline:

        ```
        pull request ─► terraform plan ─► terraform show -json ─► changegate verify ─► (approved?) ─► terraform apply
                                                                     │
                                                              exit 1 or 2: stop
        ```

        Because CI fails a step on any non-zero exit code, `verify` returning 1 (blocked) or 2 (approval
        required) stops the pipeline before `apply`. This milestone of the course runs the gate **offline**
        against plan files in the repository; producing real plans from AWS and GCP is the optional final phase.
    """),
    T("""
        **GitHub Actions in five minutes**

        A workflow is a YAML file in `.github/workflows/`. It says **when** to run (`on: pull_request`), and
        defines **jobs** made of **steps** that run on a fresh virtual machine:

        ```
        name: changegate-gate
        on:
          pull_request:
        jobs:
          gate:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4          # get the repository's files
              - uses: actions/setup-python@v5      # install Python
                with:
                  python-version: "3.12"
              - run: python -m pip install ./projects/01-cloud-change-control/workspace
              - run: changegate verify plan.json --format markdown
        ```

        YAML uses **indentation** for structure (spaces, never tabs) - just like Python blocks.
    """),
    T("""
        **Variables and secrets, not hard-coded values**

        The same discipline as `changegate.toml`: anything environment-specific comes from the CI platform's
        settings, not the workflow file.

        - `${{ vars.NAME }}` - a repository **variable** (plain configuration: paths, plan lists)
        - `${{ secrets.NAME }}` - a **secret** (the signing key, later cloud credentials). GitHub masks secrets
          in logs and never shows them again after you save them.
        - `${{ vars.NAME || 'default' }}` - fall back to a default when the variable isn't set

        Exposed as environment variables, these reach ChangeGate exactly the way it already expects:
        `CHANGEGATE_CONFIG`, `CHANGEGATE_HMAC_KEY`, `CHANGEGATE_AUTHOR`.
    """),
    T("""
        **The template**

        The course ships a complete gate workflow:
        `projects/01-cloud-change-control/ci/github-actions/changegate-gate.yml`. It:

        - installs **your** ChangeGate from the workspace
        - runs `changegate verify` on every plan listed in `vars.CHANGEGATE_PLANS`
        - appends each Markdown report to the **job summary** (`$GITHUB_STEP_SUMMARY`), so reviewers see
          findings right on the pull request
        - sets `CHANGEGATE_AUTHOR` to the pull request's author, so authors can't approve their own changes
        - fails with the worst exit code across all plans

        **To use it** in your own fork: copy it to `.github/workflows/`, commit your workspace (it's
        git-ignored by default, so use `git add -f projects/01-cloud-change-control/workspace`), push a branch
        and open a pull request. Try adding `aws_risky.json` to `CHANGEGATE_PLANS` and watch the gate block it.
    """),
    T("""
        **Approvals in CI**

        Where do approvals come from in a pipeline? Two common designs:

        - **Approval files** in the repository or as artifacts: an approver runs `changegate approve` in a job
          that has the signing key, and `verify` checks the files.
        - **Protected environments**: GitHub can require named reviewers to approve a deployment job before it
          runs. The approval job - and only that job - holds `CHANGEGATE_HMAC_KEY`, and signs an approval for
          the exact plan hash.

        Either way the key must be available only to the approval step, never to the jobs or people whose
        changes are being approved - see `docs/SECURITY.md`.
    """),
    Q("In a workflow, what does `${{ secrets.CHANGEGATE_HMAC_KEY }}` provide?",
      "The value of a repository secret, masked in logs", "A newly generated random key",
      "The key hard-coded in changegate.toml", "Nothing until the workflow is approved"),
    Q("The gate step's worst exit code across all plans is 2. What happens?",
      "The job fails, so the pull request shows a failed check until approvals exist",
      "The job passes with a warning", "The plan is applied automatically", "GitHub retries the job"),
    C("""
        The gate loops over plans and keeps the **worst** exit code. Write `worst_code(codes)` that returns
        the highest code in the list, or `0` for an empty list, and `summary(code)` that returns:

        - `0` → `"All plans allowed."`
        - `1` → `"At least one plan is BLOCKED."`
        - `2` → `"At least one plan needs approval."`
        - anything else → `"ChangeGate reported an error."`
    """, '''def worst_code(codes):
    return max(codes, default=0)

MESSAGES = {0: "All plans allowed.", 1: "At least one plan is BLOCKED.", 2: "At least one plan needs approval."}

def summary(code):
    return MESSAGES.get(code, "ChangeGate reported an error.")''',
      check="""
        assert worst_code([0, 2, 1]) == 2 and worst_code([]) == 0 and worst_code([3, 0]) == 3
        assert summary(0) == "All plans allowed."
        assert summary(1) == "At least one plan is BLOCKED."
        assert summary(2) == "At least one plan needs approval."
        assert summary(3) == "ChangeGate reported an error." and summary(99) == "ChangeGate reported an error."
      """,
      hints=["max(codes, default=0) handles the empty list.",
             "A dict of messages with .get(code, fallback) avoids an if/elif chain."]),
], summary="""
    - Gate placement: plan → show -json → `changegate verify` → apply only on exit 0.
    - GitHub Actions: `.github/workflows/*.yml`, `on:`, `jobs:`, `steps:` with `uses:` / `run:`; YAML indentation.
    - `${{ vars.X || 'default' }}` for configuration, `${{ secrets.X }}` for secrets; pass them as env vars.
    - Template: `ci/github-actions/changegate-gate.yml` - installs your workspace, writes Markdown to the
      job summary, fails with the worst exit code. Commit your workspace with `git add -f`.
    - Only the approval step holds the signing key.
""")

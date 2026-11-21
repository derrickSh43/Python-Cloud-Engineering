from pce.lesson import T, Q, B, Lesson

LESSON = Lesson("p06l6", "Capstone: the full test suite", [
    T("""
        **The finish line**

        You've written every piece of Cloud ChangeGate: the parser, the models, 14 security policies across
        AWS and GCP, configuration, risk and decisions, signed approvals, the audit log, reports and the CLI.

        The capstone runs the project's **complete** test suite - the same 190+ tests the reference
        implementation passes - against your workspace. It covers every policy, the expected outcome of every
        sample plan, the whole approval workflow, audit tampering and the CLI end to end.

        It uses pytest, so your virtual environment needs to be active (Phase 3). If something fails, the test
        name tells you which component; re-run that exercise's own check for a focused view.
    """),
    B("p6-capstone"),
    T("""
        **What you've built**

        A dependency-free Python tool that can sit in any Terraform pipeline and:

        - parse `terraform show -json` output into typed objects
        - apply modular, configurable security policies for AWS and GCP, failing closed
        - classify risk and decide allow / approval / block, with reasons
        - verify HMAC-signed approvals bound to the exact plan, with expiry and separation of duties
        - keep a hash-chained audit trail
        - report as text, JSON or Markdown, with exit codes CI understands

        **Optional next step - real clouds.** Everything so far ran against sample plans. The repository's
        `docs/SETUP.md` and the optional cloud phase explain how to point the same gate at real AWS and GCP
        accounts: every value - account, project, region, roles - comes from your own `.tfvars` files and CI
        variables, so nothing in the code changes.
    """),
    Q("Your capstone run fails only in `test_policies_gcp.py`. Where should you look first?",
      "The Phase 4 GCP policy exercises - re-run their checks (python learn.py check p4-gcp-...)",
      "The plan parser", "The CLI", "The test file - it must be wrong"),
], summary="""
    - Capstone: `python learn.py check p6-capstone` runs the full suite against your workspace
      (`CHANGEGATE_SRC=workspace python -m pytest projects/01-cloud-change-control/tests`).
    - A failing test names the component; re-run that exercise's check.
    - Next: optional real AWS/GCP integration - all values from your own tfvars and CI variables.
""")

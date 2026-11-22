from pce.lesson import T, Ex, Q, C, Lesson

LESSON = Lesson("p06l5", "Running your tool from other programs", [
    T("""
        **Exit codes are how scripts talk to each other**

        Pipelines, shell scripts and other Python programs run ChangeGate and look at one thing: the exit
        code. In Python you do that with `subprocess.run`. It runs a command, waits for it, and gives you
        `returncode`. The command is a **list** of arguments, so no shell quoting is involved.
    """),
    Ex("""
        import subprocess, sys
        result = subprocess.run([sys.executable, "-c", "import sys; print('checked'); sys.exit(2)"],
                                capture_output=True, text=True)
        print("exit code:", result.returncode)
        print("output:", result.stdout.strip())
    """, note="`sys.executable` is the Python running this code, so the example works on any machine."),
    T("""
        **Checking several files and keeping the worst result**

        A wrapper that gates several plans runs the tool once per file and keeps the **highest** exit code:
        one blocked plan (1) or one that needs approval (2) fails the whole run.

        ```
        worst = 0
        for path in plans:
            code = subprocess.run(["changegate", "verify", path]).returncode
            worst = max(worst, code)
        sys.exit(worst)
        ```

        The repository's CI template (`ci/github-actions/changegate-gate.yml`) does exactly this in a few lines
        of shell. Its settings come from environment variables (`CHANGEGATE_CONFIG`, `CHANGEGATE_PLANS`,
        `CHANGEGATE_HMAC_KEY`), the same ones your Python code already reads.
    """),
    Q("What does this print?", "2", "1", "0", "3",
      code="""
        codes = [0, 2, 1, 0]
        worst = 0
        for code in codes:
            worst = max(worst, code)
        print(worst)
      """),
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
    - `subprocess.run([...], capture_output=True, text=True)` runs a command; `.returncode`, `.stdout`.
    - Pass the command as a list, not one string.
    - Gating several files: keep `max` of the exit codes and exit with it.
    - The CI template does the same in shell, configured through environment variables.
""")

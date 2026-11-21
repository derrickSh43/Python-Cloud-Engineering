"""Runs learner code safely in a child process with a time limit."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HARNESS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness.py")
MARK = "@@PCE_REPORT@@"
TIME_LIMIT = 4.0


class RunResult:
    def __init__(self, output="", error=None, check_error=None, timed_out=False, crashed=None):
        self.output = output
        self.error = error
        self.check_error = check_error
        self.timed_out = timed_out
        self.crashed = crashed

    @property
    def ok(self):
        return not (self.error or self.check_error or self.timed_out or self.crashed)


def run_code(code, inputs=(), check=None, files=None, echo=False, timeout=TIME_LIMIT):
    """Run `code` in a fresh interpreter inside an empty temp folder.

    inputs: answers fed to input() in order.   check: python run afterwards in the same namespace.
    files:  {filename: text} created in the folder first.   echo: show prompts/answers in output.
    """
    job = json.dumps({"code": code, "inputs": list(inputs), "check": check, "echo": echo})
    workdir = tempfile.mkdtemp(prefix="pce_")
    try:
        for name, text in (files or {}).items():
            with open(os.path.join(workdir, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        try:
            proc = subprocess.run(
                [sys.executable, "-X", "utf8", "-I", HARNESS],
                input=job, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout, cwd=workdir,
            )
        except subprocess.TimeoutExpired:
            return RunResult(timed_out=True)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if MARK not in proc.stdout:
        return RunResult(crashed=(proc.stderr or "The program stopped unexpectedly.")[-1500:])
    report = json.loads(proc.stdout.rsplit(MARK, 1)[1])
    return RunResult(report["output"], report["error"], report["check_error"])

"""Helpers shared by the per-exercise tests. Standard library only - these tests run before pytest
is introduced, and they are also valid pytest tests."""

import contextlib
import io
import os
import shutil
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
SAMPLES = PROJECT / "sample_data" / "plans"
EXAMPLE_CONFIG = PROJECT / "sample_data" / "changegate.example.toml"
TEST_KEY = "test-key-0123456789abcdef0123456789abcdef"   # test-only value
AWS = "registry.terraform.io/hashicorp/aws"
GOOGLE = "registry.terraform.io/hashicorp/google"
ACTIONS = {"create": ["create"], "update": ["update"], "delete": ["delete"], "replace": ["delete", "create"],
           "no-op": ["no-op"], "read": ["read"]}


def sample(name):
    return SAMPLES / name


def entry(resource_type, after=None, action="create", before=None, unknown=None, name="this"):
    """A raw `resource_changes` item, as it appears in plan JSON."""
    provider = GOOGLE if resource_type.startswith("google_") else AWS
    return {"address": "%s.%s" % (resource_type, name), "mode": "managed", "type": resource_type, "name": name,
            "provider_name": provider,
            "change": {"actions": ACTIONS[action], "before": before, "after": after, "after_unknown": unknown or {}}}


def make_change(resource_type, after=None, action="create", before=None, unknown=None, name="this"):
    """A ResourceChange built with your parse_change (available from exercise p3-parse-change)."""
    from changegate.plan_parser import parse_change
    return parse_change(entry(resource_type, after, action, before, unknown, name))


def raises(exc_type, fn, *args, **kwargs):
    """Call fn and return the exception it raised. Fails if it didn't raise exc_type."""
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        return e
    raise AssertionError("expected %s to raise %s, but it didn't" % (getattr(fn, "__name__", fn), exc_type.__name__))


def messages(findings):
    return [f.message for f in findings]


@contextlib.contextmanager
def temp_dir():
    path = Path(tempfile.mkdtemp(prefix="pce_ex_"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@contextlib.contextmanager
def env(**values):
    """Temporarily set (or with None, remove) environment variables."""
    old = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


@contextlib.contextmanager
def captured():
    """Capture stdout and stderr: `with captured() as out: ...; out.stdout, out.stderr`."""
    class Out:
        stdout = ""
        stderr = ""
    result, so, se = Out(), io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
        yield result
    result.stdout, result.stderr = so.getvalue(), se.getvalue()


@contextlib.contextmanager
def workdir():
    """A temp folder holding the sample plans (in plans/) and the example config as changegate.toml,
    made the current directory, with ChangeGate environment variables cleared."""
    with temp_dir() as tmp:
        shutil.copytree(SAMPLES, tmp / "plans")
        shutil.copy(EXAMPLE_CONFIG, tmp / "changegate.toml")
        with chdir(tmp), env(CHANGEGATE_CONFIG=None, CHANGEGATE_AUTHOR=None, CHANGEGATE_APPROVER=None):
            yield tmp

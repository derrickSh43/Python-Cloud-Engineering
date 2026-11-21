"""Shared fixtures for the ChangeGate test suite.

The suite tests whichever implementation CHANGEGATE_SRC points at:
  - unset (default): reference/   (the complete reference implementation)
  - CHANGEGATE_SRC=workspace       the learner's own code, for the capstone check
"""

import os
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent
_src = os.environ.get("CHANGEGATE_SRC", "reference")
SRC = (PROJECT / _src).resolve() if not os.path.isabs(_src) else Path(_src)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SAMPLES = PROJECT / "sample_data" / "plans"
EXAMPLE_CONFIG = PROJECT / "sample_data" / "changegate.example.toml"
TEST_KEY = "test-key-0123456789abcdef0123456789abcdef"  # test-only value, never used outside tests

PROVIDERS = {"aws": "registry.terraform.io/hashicorp/aws", "google": "registry.terraform.io/hashicorp/google"}


def pytest_report_header(config):
    return "changegate source: %s" % SRC


@pytest.fixture
def samples():
    return SAMPLES


@pytest.fixture
def example_config_path():
    return EXAMPLE_CONFIG


@pytest.fixture
def make_change():
    """Build a ResourceChange the same way the parser would, from minimal arguments."""
    from changegate.plan_parser import parse_change

    def factory(resource_type, after=None, action="create", before=None, unknown=None, name="this"):
        provider = "google" if resource_type.startswith("google_") else "aws"
        actions = {"create": ["create"], "update": ["update"], "delete": ["delete"],
                   "replace": ["delete", "create"], "no-op": ["no-op"], "read": ["read"]}[action]
        return parse_change({
            "address": "%s.%s" % (resource_type, name), "mode": "managed", "type": resource_type, "name": name,
            "provider_name": PROVIDERS[provider],
            "change": {"actions": actions, "before": before, "after": after, "after_unknown": unknown or {}},
        })

    return factory


@pytest.fixture
def key_env(monkeypatch):
    monkeypatch.setenv("CHANGEGATE_HMAC_KEY", TEST_KEY)
    return TEST_KEY

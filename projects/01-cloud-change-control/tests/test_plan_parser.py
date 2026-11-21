import hashlib
import json

import pytest

from changegate import plan_parser
from changegate.models import Action
from changegate.plan_parser import PlanError


def test_load_sample_plan(samples):
    raw, plan, changes = plan_parser.load_plan(samples / "aws_safe.json")
    assert plan["format_version"].startswith("1.")
    # the data source in the sample is skipped
    assert [c.address for c in changes] == [
        "aws_s3_bucket.logs", "aws_s3_bucket_public_access_block.logs", "aws_security_group.web", "aws_instance.app"]
    assert changes[0].action is Action.CREATE and changes[0].cloud == "aws" and changes[0].provider == "aws"
    assert changes[3].action is Action.UPDATE


def test_replace_and_gcp_provider(samples):
    _, _, changes = plan_parser.load_plan(samples / "aws_db_replace.json")
    assert changes[0].action is Action.REPLACE
    _, _, gcp = plan_parser.load_plan(samples / "gcp_safe.json")
    assert {c.cloud for c in gcp} == {"gcp"}


def test_data_sources_can_be_included(samples):
    plan = plan_parser.decode_plan((samples / "aws_safe.json").read_bytes())
    assert len(plan_parser.parse_plan(plan, include_data_sources=True)) == 5


def test_digest_is_sha256_of_exact_bytes():
    raw = b'{"format_version": "1.2"}'
    assert plan_parser.plan_digest(raw) == hashlib.sha256(raw).hexdigest()
    assert plan_parser.plan_digest(raw + b" ") != plan_parser.plan_digest(raw)


def test_empty_resource_changes():
    assert plan_parser.parse_plan({"format_version": "1.2"}) == []
    assert plan_parser.parse_plan({"format_version": "1.2", "resource_changes": None}) == []


@pytest.mark.parametrize("raw, message", [
    (b"not json", "not valid JSON"),
    (b"[1, 2]", "object at the top level"),
    (b'{"resource_changes": []}', "format_version"),
    (b'{"format_version": "2.0"}', "unsupported"),
    (b'{"format_version": "1.2", "resource_changes": {}}', "must be a list"),
    (b'{"format_version": "1.2", "resource_changes": [{"address": "x"}]}', "missing"),
    (b'{"format_version": "1.2", "resource_changes": [{"address": "x", "change": {"actions": ["boom"]}}]}', "x:"),
    (b"\xff\xfe\x00binary", "UTF-8"),
])
def test_bad_input_raises_plan_error(raw, message):
    with pytest.raises(PlanError, match=message):
        plan_parser.parse_plan(plan_parser.decode_plan(raw))


def test_missing_file(tmp_path):
    with pytest.raises(PlanError, match="not found"):
        plan_parser.read_plan_bytes(tmp_path / "nope.json")


def test_utf8_bom_is_accepted():
    raw = "﻿".encode() + json.dumps({"format_version": "1.2"}).encode()
    assert plan_parser.decode_plan(raw)["format_version"] == "1.2"


def test_unknown_provider_is_other():
    change = plan_parser.parse_change({"address": "azurerm_rg.x", "type": "azurerm_rg", "name": "x",
                                       "provider_name": "registry.terraform.io/hashicorp/azurerm",
                                       "change": {"actions": ["create"], "after": {}}})
    assert change.cloud == "other" and change.provider == "azurerm"

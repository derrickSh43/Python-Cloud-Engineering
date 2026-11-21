from changegate.models import Action, ResourceChange
from changegate.plan_parser import PlanError, parse_change
from support import entry, raises


def test_parses_an_aws_create():
    """a create entry becomes a ResourceChange with provider and cloud filled in"""
    change = parse_change(entry("aws_s3_bucket", {"bucket": "logs"}, unknown={"arn": True}, name="logs"))
    assert isinstance(change, ResourceChange)
    assert change.address == "aws_s3_bucket.logs" and change.type == "aws_s3_bucket" and change.name == "logs"
    assert change.provider == "aws" and change.cloud == "aws"
    assert change.action is Action.CREATE
    assert change.after == {"bucket": "logs"} and change.before is None
    assert change.after_unknown == {"arn": True}


def test_gcp_replace():
    """a google delete+create entry becomes a gcp REPLACE"""
    change = parse_change(entry("google_compute_disk", {"size": 20}, action="replace", before={"size": 10}))
    assert change.cloud == "gcp" and change.provider == "google"
    assert change.action is Action.REPLACE and change.before == {"size": 10}


def test_optional_parts():
    """missing provider_name, type, after_unknown (or null) and module all have defaults"""
    change = parse_change({"address": "x.y", "change": {"actions": ["no-op"], "after_unknown": None}})
    assert change.type == "" and change.name == "" and change.provider == "" and change.cloud == "other"
    assert change.after_unknown == {} and change.module is None
    with_module = parse_change({**entry("aws_s3_bucket", {}), "module_address": "module.storage"})
    assert with_module.module == "module.storage"


def test_missing_required_parts():
    """missing address/change/actions (or a non-dict) raises PlanError mentioning 'missing'"""
    for bad in ({"change": {"actions": ["create"]}}, {"address": "x"}, {"address": "x", "change": {}}, "text"):
        error = raises(PlanError, parse_change, bad)
        assert "missing" in str(error), "message was: %s" % error


def test_bad_actions():
    """unknown actions raise PlanError starting with the resource address"""
    error = raises(PlanError, parse_change, {"address": "aws_x.y", "change": {"actions": ["explode"]}})
    assert str(error).startswith("aws_x.y:"), "message was: %s" % error

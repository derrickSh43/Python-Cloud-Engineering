from changegate.models import Action
from changegate.plan_parser import PlanError, load_plan, parse_plan
from support import raises, sample


def test_load_sample_plan():
    """load_plan returns (bytes, dict, changes) and skips data sources"""
    raw, plan, changes = load_plan(sample("aws_safe.json"))
    assert raw == sample("aws_safe.json").read_bytes()
    assert plan["format_version"] == "1.2"
    assert [c.address for c in changes] == ["aws_s3_bucket.logs", "aws_s3_bucket_public_access_block.logs",
                                            "aws_security_group.web", "aws_instance.app"]


def test_include_data_sources():
    """include_data_sources=True keeps the data source entries"""
    _, plan, _ = load_plan(sample("aws_safe.json"))
    assert len(parse_plan(plan, include_data_sources=True)) == 5


def test_keeps_no_op_changes():
    """no-op changes are kept"""
    _, _, changes = load_plan(sample("no_changes.json"))
    assert [c.action for c in changes] == [Action.NO_OP]


def test_no_resource_changes():
    """a plan with no (or null) resource_changes has no changes"""
    assert parse_plan({"format_version": "1.2"}) == []
    assert parse_plan({"format_version": "1.2", "resource_changes": None}) == []


def test_resource_changes_must_be_a_list():
    """resource_changes of {} or a string raises PlanError('... must be a list')"""
    for bad in ({}, "nope"):
        error = raises(PlanError, parse_plan, {"format_version": "1.2", "resource_changes": bad})
        assert "must be a list" in str(error), "message was: %s" % error


def test_checks_format_first():
    """an unsupported format raises before anything is parsed"""
    raises(PlanError, parse_plan, {"format_version": "9.0", "resource_changes": []})

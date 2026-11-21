import json

from changegate.models import Severity
from changegate.policies.aws import IamWildcard
from support import make_change


def run(*statements, resource_type="aws_iam_policy"):
    policy = IamWildcard()
    change = make_change(resource_type, {"policy": json.dumps({"Statement": list(statements)})})
    return list(policy.check(change)) if policy.applies_to(change) else []


def test_star_action_is_critical():
    """Action '*' is CRITICAL and names the Sid"""
    found = run({"Sid": "Everything", "Effect": "Allow", "Action": "*", "Resource": "*"})
    assert [(f.severity, f.message) for f in found] == [
        (Severity.CRITICAL, "statement 'Everything' allows every action (\"*\")")]


def test_service_wildcard_on_every_resource():
    """'s3:*' on Resource '*' is HIGH; scoped resources are fine"""
    found = run({"Effect": "Allow", "Action": ["s3:*", "ec2:DescribeInstances"], "Resource": "*"},
                resource_type="aws_iam_role_policy")
    assert [(f.severity, f.message) for f in found] == [
        (Severity.HIGH, "statement '(no Sid)' allows s3:* on every resource")]
    assert run({"Effect": "Allow", "Action": "s3:*", "Resource": "arn:aws:s3:::example-bucket/*"}) == []


def test_not_action():
    """Allow + NotAction is reported"""
    found = run({"Effect": "Allow", "NotAction": "iam:*", "Resource": "*"})
    assert len(found) == 1 and "NotAction" in found[0].message


def test_deny_and_specific_actions_are_fine():
    """Deny statements and specific actions produce nothing"""
    assert run({"Effect": "Deny", "Action": "*", "Resource": "*"}) == []
    assert run({"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "*"}) == []


def test_unknown_and_invalid():
    """unknown policies are skipped; invalid JSON is reported"""
    policy = IamWildcard()
    assert list(policy.check(make_change("aws_iam_policy", {"policy": None}, unknown={"policy": True}))) == []
    found = list(policy.check(make_change("aws_iam_policy", {"policy": "not json"})))
    assert len(found) == 1 and "not valid JSON" in found[0].message

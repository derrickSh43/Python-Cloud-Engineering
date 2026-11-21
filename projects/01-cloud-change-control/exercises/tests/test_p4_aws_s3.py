import json

from changegate.models import Severity
from changegate.policies.aws import S3PublicAccessBlock, S3PublicAcl, S3PublicBucketPolicy
from support import make_change, messages


def run(policy, change):
    return list(policy.check(change)) if policy.applies_to(change) else []


def doc(*statements):
    return json.dumps({"Version": "2012-10-17", "Statement": list(statements)})


def test_acl_levels():
    """public-read is HIGH, public-read-write is CRITICAL, private is fine"""
    assert run(S3PublicAcl(), make_change("aws_s3_bucket_acl", {"acl": "private"})) == []
    found = run(S3PublicAcl(), make_change("aws_s3_bucket_acl", {"acl": "public-read"}))
    assert [(f.severity, f.message) for f in found] == [(Severity.HIGH, "bucket ACL is 'public-read'")]
    assert run(S3PublicAcl(), make_change("aws_s3_bucket_acl", {"acl": "public-read-write"}))[0].severity is Severity.CRITICAL


def test_public_access_block():
    """flags that aren't exactly True are listed in one finding"""
    all_on = dict.fromkeys(S3PublicAccessBlock.FLAGS, True)
    assert run(S3PublicAccessBlock(), make_change("aws_s3_bucket_public_access_block", all_on)) == []
    half = {**all_on, "block_public_acls": False, "restrict_public_buckets": None}
    assert messages(run(S3PublicAccessBlock(), make_change("aws_s3_bucket_public_access_block", half))) == [
        "public access protections disabled: block_public_acls, restrict_public_buckets"]


def test_public_access_block_unknown_flags():
    """unknown flags are not reported"""
    attrs = {**dict.fromkeys(S3PublicAccessBlock.FLAGS, True), "block_public_policy": None}
    change = make_change("aws_s3_bucket_public_access_block", attrs, unknown={"block_public_policy": True})
    assert run(S3PublicAccessBlock(), change) == []


def test_bucket_policy_public():
    """Allow + Principal '*' without a Condition is reported with its Sid"""
    policy = doc({"Sid": "PublicRead", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject"})
    found = run(S3PublicBucketPolicy(), make_change("aws_s3_bucket_policy", {"policy": policy}))
    assert len(found) == 1 and "PublicRead" in found[0].message


def test_bucket_policy_safe_cases():
    """specific principals, Conditions, Deny statements and unknown policies are fine"""
    for statement in ({"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123456789012:root"}},
                      {"Effect": "Allow", "Principal": "*", "Condition": {"Bool": {"aws:SecureTransport": "true"}}},
                      {"Effect": "Deny", "Principal": "*"}):
        assert run(S3PublicBucketPolicy(), make_change("aws_s3_bucket_policy", {"policy": doc(statement)})) == []
    unknown = make_change("aws_s3_bucket_policy", {"policy": None}, unknown={"policy": True})
    assert run(S3PublicBucketPolicy(), unknown) == []


def test_bucket_policy_bad_json():
    """an unparseable policy is reported, not crashed on"""
    found = run(S3PublicBucketPolicy(), make_change("aws_s3_bucket_policy", {"policy": "{nope"}))
    assert len(found) == 1 and "not valid JSON" in found[0].message

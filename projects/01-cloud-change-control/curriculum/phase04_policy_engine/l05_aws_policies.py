from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l5", "AWS security policies", [
    T("""
        **Public S3 buckets**

        Publicly readable S3 buckets are behind a long list of real data leaks. AWS has three overlapping
        ways to make a bucket public, and ChangeGate checks all three:

        - **ACLs** (`aws_s3_bucket_acl`): the canned ACLs `public-read` and `authenticated-read` let anyone
          read; `public-read-write` lets anyone **write** too (CRITICAL - attackers host malware in it).
        - **Public access block** (`aws_s3_bucket_public_access_block`): four switches that override ACLs and
          policies. All four should be `true`. Turning any off is a red flag.
        - **Bucket policies** (`aws_s3_bucket_policy`): a JSON policy; a statement that `Allow`s
          `Principal: "*"` without a `Condition` (like "only from our VPC endpoint") is public.

        Note: since 2023 new buckets block public access and encrypt objects by default - but Terraform can
        still turn those protections off, which is exactly what a plan review should catch.
    """),
    T("""
        **Security groups**

        A security group is a stateful firewall around EC2 instances, databases and load balancers. Terraform
        expresses ingress rules in three ways: inline `ingress` blocks on `aws_security_group`, separate
        `aws_security_group_rule` resources (with `type = "ingress"` or `"egress"`), and the newer
        `aws_vpc_security_group_ingress_rule` (one CIDR per rule, `cidr_ipv4` / `cidr_ipv6`).

        Protocol `"-1"` means **all protocols and ports**. A missing from/to port means the full range. Watch
        for `0` - it's a valid port number but falsy, so test `is not None`.
    """),
    P("""
        rule = {"from_port": 0, "to_port": 0, "protocol": "-1"}
        low = rule.get("from_port") or 22
        low_correct = rule.get("from_port") if rule.get("from_port") is not None else 22
        print(low, low_correct)
    """, explain="`or` treats 0 as missing and silently uses the fallback - a real bug in many scripts."),
    T("""
        **Encryption at rest**

        If a disk or database snapshot leaks, encryption is the last line of defence, and many compliance
        regimes require it. Each resource type names its flag differently - `aws_ebs_volume.encrypted`,
        `aws_db_instance.storage_encrypted`, `aws_efs_file_system.encrypted` - so the policy keeps a table
        mapping type → flag. EC2 instances have nested `root_block_device` and `ebs_block_device` blocks.

        Rule of thumb: treat a **missing** flag as unencrypted (the provider default may be off), but skip
        values that are **unknown** until apply.

        And `publicly_accessible = true` on an RDS database gives it a public IP - databases belong in private
        subnets.
    """),
    T("""
        **IAM wildcards**

        IAM policies decide what an identity can do. `"Action": "*"` with `"Resource": "*"` is full
        administrator access - if those credentials leak, everything is gone. ChangeGate flags:

        - `"Action": "*"` → CRITICAL
        - a service wildcard like `"s3:*"` on `"Resource": "*"` → HIGH (every action on every bucket)
        - `Allow` + `NotAction` → HIGH: "allow everything except X" grants every action AWS ever adds later

        `Deny` statements are never the problem - they only take permissions away. Remember that `Action` and
        `Resource` may each be a string or a list: normalise with `as_list` first.
    """),
    Ex("""
        import json
        policy = json.dumps({"Statement": [
            {"Sid": "Admin", "Effect": "Allow", "Action": "*", "Resource": "*"},
            {"Sid": "Logs", "Effect": "Allow", "Action": ["s3:*"], "Resource": "*"},
            {"Sid": "Guard", "Effect": "Deny", "Action": "*", "Resource": "*"},
        ]})
        for st in json.loads(policy)["Statement"]:
            actions = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
            if st["Effect"] != "Allow":
                continue
            if "*" in actions:
                print(st["Sid"], "-> CRITICAL: every action")
            elif "*" in [st["Resource"]] and any(a.endswith(":*") for a in actions):
                print(st["Sid"], "-> HIGH: service wildcard on every resource")
    """),
    Q("Which S3 ACL is CRITICAL rather than HIGH in ChangeGate?", "public-read-write", "public-read",
      "authenticated-read", "private", explain="Write access lets anyone upload content - and you pay to serve it."),
    Q("Why is `Allow` + `NotAction: [\"iam:*\"]` dangerous?",
      "It allows every action except IAM ones - including any added to AWS in the future",
      "It denies all IAM actions, locking admins out", "NotAction is invalid and ignored", "It only applies to the root user"),
    C("""
        Write `unencrypted(resource_type, attrs)` returning a list of messages:

        - for `"aws_ebs_volume"` check `attrs["encrypted"]`; for `"aws_db_instance"` check `attrs["storage_encrypted"]`
        - if the flag is not exactly `True` (False or missing), return `["<flag> is <value!r>"]`
        - any other type returns `[]`
    """, '''FLAGS = {"aws_ebs_volume": "encrypted", "aws_db_instance": "storage_encrypted"}

def unencrypted(resource_type, attrs):
    flag = FLAGS.get(resource_type)
    if flag is None:
        return []
    value = attrs.get(flag)
    if value is not True:
        return ["%s is %r" % (flag, value)]
    return []''',
      check="""
        assert unencrypted("aws_ebs_volume", {"encrypted": False}) == ["encrypted is False"]
        assert unencrypted("aws_ebs_volume", {}) == ["encrypted is None"], "a missing flag counts as unencrypted"
        assert unencrypted("aws_db_instance", {"storage_encrypted": True}) == []
        assert unencrypted("aws_s3_bucket", {"encrypted": False}) == []
      """,
      hints=["A dict mapping type to flag name keeps the code short.",
             '`value is not True` is False only for exactly True; `"%s is %r" % (flag, value)` formats the message.']),
    B("p4-aws-s3"),
    B("p4-aws-security-groups", intro="Three resource shapes, one judgement: use `self.judge(...)` from `OpenIngressPolicy`."),
    B("p4-aws-storage"),
    B("p4-aws-iam"),
], summary="""
    - S3 is public via ACLs (`public-read*`, `authenticated-read`), a disabled public access block, or a bucket
      policy allowing `Principal: "*"` without a Condition.
    - Security groups: inline `ingress`, `aws_security_group_rule`, `aws_vpc_security_group_ingress_rule`;
      protocol `"-1"` = everything; port 0 is falsy - use `is not None`.
    - Encryption: per-type flag names; missing = unencrypted, unknown = skip. Public RDS = HIGH.
    - IAM: `Action: "*"` CRITICAL, `svc:*` on `Resource: "*"` HIGH, `Allow` + `NotAction` HIGH; Deny is fine.
""")

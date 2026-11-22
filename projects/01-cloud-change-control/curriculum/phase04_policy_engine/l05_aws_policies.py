from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l5", "AWS rules: lookups, nested data and edge cases", [
    T("""
        **What the AWS rules check**

        Each rule is a small function over a dict of settings. You don't need to know AWS: here is the data.

        | resource type | key(s) to read | flag when |
        |---|---|---|
        | `aws_s3_bucket_acl` | `acl` (a string) | it's a key of a `PUBLIC` dict (the value is the severity) |
        | `aws_s3_bucket_public_access_block` | four boolean flags | any flag is not exactly `True` |
        | `aws_s3_bucket_policy` | `policy` (a JSON **string**) | a statement allows principal `"*"` with no `Condition` |
        | security group rules | `from_port`, `to_port`, `protocol`, CIDR lists | the shared `judge()` says so |
        | `aws_ebs_volume`, `aws_db_instance`... | an encryption flag (name differs per type) | not exactly `True` |
        | IAM policies | `policy` (JSON string) with `Action` / `Resource` | `"*"` wildcards in an `Allow` |

        The Python patterns repeat: dict lookups with a default, a table mapping type → key name, parsing a
        JSON string inside JSON, and values that can be a **string or a list**.
    """),
    T("""
        **The `0` trap**

        Port `0` is a valid value, but it's falsy. `rule.get("from_port") or 22` silently replaces it. Test
        `is not None` instead.
    """),
    P("""
        rule = {"from_port": 0, "to_port": 0, "protocol": "-1"}
        low = rule.get("from_port") or 22
        low_correct = rule.get("from_port") if rule.get("from_port") is not None else 22
        print(low, low_correct)
    """, explain="`or` treats 0 as missing and silently uses the fallback - a real bug in many scripts."),
    T("""
        **A table instead of an if/elif chain**

        Each type names its encryption flag differently. Keep a dict:

        ```
        FLAGS = {"aws_ebs_volume": "encrypted", "aws_db_instance": "storage_encrypted"}
        flag = FLAGS.get(change.type)      # None for types the rule doesn't cover
        ```

        Treat a **missing** flag as off (`attrs.get(flag) is not True`), but skip values marked unknown.
    """),
    T("""
        **String or list?**

        In an AWS policy document, `Action` may be `"s3:*"` or `["s3:GetObject", "s3:PutObject"]`. Normalise
        first with a helper like `as_list(value)`, then loop. Only `Allow` statements matter; skip `Deny`.
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
    Q("What does this print?", "['s3:*']", "['s', '3', ':', '*']", "s3:*", "An error",
      code="""
        def as_list(value):
            if value is None:
                return []
            return value if isinstance(value, list) else [value]

        print(as_list("s3:*"))
      """, explain="A lone string is wrapped in a list. Without the isinstance check, list(\"s3:*\") would split it into characters."),
    Q("What does this print?", "['public_acls']", "[]", "['public_acls', 'block_policy']", "An error",
      code="""
        FLAGS = ["block_policy", "public_acls"]
        attrs = {"block_policy": True, "public_acls": False}
        print([f for f in FLAGS if attrs.get(f) is not True])
      """, explain="Only values that are exactly True pass; False (and a missing flag, None) are reported."),
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
    - Each AWS rule is a dict lookup plus a condition; the exercise text gives the keys and the rule.
    - `x is not None` / `x is not True` instead of truthiness when 0 or a missing value matters.
    - A dict maps type → key name instead of an if/elif chain.
    - JSON strings inside JSON: `json.loads` again. Normalise string-or-list values with `as_list`.
""")

from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p04cp", "Security judgement", """
    Questions about the real-world reasons behind the policies, and a small policy written from scratch.
""", [
    Q("An S3 bucket policy statement has `\"Principal\": \"*\"` and no `Condition`. Who can use it?",
      "Anyone on the internet", "Only users in the same AWS account", "Only the bucket owner", "Nobody until a role is attached"),
    Q("Which GCP member grants access to anyone with any Google account?",
      "allAuthenticatedUsers", "allUsers", "domain:example.com", "projectViewer"),
    Q("Why is `roles/owner` on a project flagged even for a trusted employee?",
      "It grants far more than any one job needs: least privilege means granting only what's required",
      "Owner roles expire after 24 hours", "GCP charges extra for owners", "Owners can't use the console"),
    Q("A plan has five LOW-risk deletes of web servers. With the default threshold of 5, what's the risk?",
      "MEDIUM - many destructive changes raise risk one level", "LOW - the findings are all LOW",
      "CRITICAL - all deletes are critical", "HIGH - deletes are always high"),
    C("""
        Write a generator `public_snapshot_findings(change)` for a hypothetical rule. `change` is a dict with
        `type` and `after`. For `aws_db_snapshot` (and only that type), yield
        `("HIGH", "snapshot shared publicly")` when `after["shared_accounts"]` (a list, possibly missing or
        None) contains `"all"`, and `("MEDIUM", "snapshot shared with N account(s)")` when it lists other
        accounts but not `"all"`.
    """, '''def public_snapshot_findings(change):
    if change["type"] != "aws_db_snapshot":
        return
    shared = (change.get("after") or {}).get("shared_accounts") or []
    if "all" in shared:
        yield ("HIGH", "snapshot shared publicly")
    elif shared:
        yield ("MEDIUM", "snapshot shared with %d account(s)" % len(shared))''',
      check="""
        def f(t, after):
            return list(public_snapshot_findings({"type": t, "after": after}))
        assert f("aws_db_snapshot", {"shared_accounts": ["all"]}) == [("HIGH", "snapshot shared publicly")]
        assert f("aws_db_snapshot", {"shared_accounts": ["123456789012", "210987654321"]}) == [("MEDIUM", "snapshot shared with 2 account(s)")]
        assert f("aws_db_snapshot", {"shared_accounts": None}) == [] and f("aws_db_snapshot", {}) == []
        assert f("aws_db_snapshot", None) == [], "after may be None (e.g. for a delete)"
        assert f("aws_s3_bucket", {"shared_accounts": ["all"]}) == []
      """,
      require=["yield"],
      hints=["Return early for any other resource type.",
             '(change.get("after") or {}).get("shared_accounts") or [] copes with every missing case.',
             'if "all" in shared: yield (...)  elif shared: yield (...)']),
])

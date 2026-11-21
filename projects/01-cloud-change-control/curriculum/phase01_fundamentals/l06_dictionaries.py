from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l6", "Dictionaries and nested data", [
    T("""
        **Dictionaries: values by name**

        A **dictionary** (`dict`) maps **keys** to **values**, inside curly braces:

        ```
        tags = {"owner": "platform", "environment": "prod"}
        print(tags["owner"])          # platform
        tags["cost_center"] = "1234"  # add or change a key
        ```

        Cloud resources are naturally dictionaries: a bucket has a `name`, a `region`, `tags`... and
        Terraform's JSON output - the input to ChangeGate - is dictionaries all the way down.
    """),
    Ex("""
        bucket = {"name": "logs", "region": "eu-west-1", "versioning": True}
        print(bucket["name"], "in", bucket["region"])
        bucket["region"] = "eu-west-2"
        bucket["encrypted"] = True
        print(bucket)
        print(len(bucket), "keys")
    """),
    T("""
        **Missing keys**

        `tags["owner"]` raises a **KeyError** if there's no `"owner"` key. Two safe alternatives:

        - `"owner" in tags` - True if the key exists
        - `tags.get("owner")` - the value, or `None` if missing; `tags.get("owner", "unknown")` uses your default

        Real data is messy - resources often lack tags - so `.get` is your friend.
    """),
    Ex("""
        tags = {"environment": "dev"}
        print("owner" in tags)
        print(tags.get("owner"))
        print(tags.get("owner", "unassigned"))
        print(tags.get("environment", "unassigned"))
    """),
    Ex("""
        tags = {"environment": "dev"}
        print(tags["owner"])
    """, note="A KeyError names the missing key. Use `in` or `.get()` when a key might not exist.", error_ok=True),
    T("""
        **Looping over a dictionary**

        - `for key in d:` loops over keys
        - `for key, value in d.items():` loops over both
        - `d.keys()` and `d.values()` give just one side

        Dictionaries remember the order keys were added.
    """),
    Ex("""
        tags = {"owner": "platform", "environment": "prod", "service": "api"}
        for key, value in tags.items():
            print(f"{key} = {value}")
        print(list(tags.keys()))
    """),
    T("""
        **Counting with a dictionary**

        A dictionary makes an excellent counter. For each item, add 1 to its count, starting at 0 if it
        isn't there yet:

        ```
        counts = {}
        for action in actions:
            counts[action] = counts.get(action, 0) + 1
        ```
    """),
    P("""
        counts = {}
        for cloud in ["aws", "gcp", "aws", "aws"]:
            counts[cloud] = counts.get(cloud, 0) + 1
        print(counts)
    """),
    T("""
        **Nested data**

        Values can themselves be lists and dictionaries. Chain the lookups from the outside in:

        ```
        change = {
            "address": "aws_security_group.web",
            "change": {"actions": ["create"], "after": {"ingress": [{"from_port": 22}]}},
        }
        change["change"]["actions"][0]                       # "create"
        change["change"]["after"]["ingress"][0]["from_port"] # 22
        ```

        This is exactly the shape of a Terraform plan. Read the chain one step at a time: dict key, dict
        key, list index...
    """),
    P("""
        change = {"address": "aws_s3_bucket.logs",
                  "change": {"actions": ["delete", "create"], "after": {"tags": {"owner": "data"}}}}
        print(change["change"]["actions"])
        print(len(change["change"]["actions"]))
        print(change["change"]["after"]["tags"]["owner"])
    """),
    Q("`rule = {\"ports\": [22, 80]}` - how do you get 80?",
      'rule["ports"][1]', 'rule[1]', 'rule["ports"][80]', 'rule.ports[1]'),
    C("""
        A resource's tags are given: `tags = {"owner": "platform", "environment": "prod"}`.

        Print the value of the `"cost_center"` tag, or `MISSING` if it isn't set, using `.get`:

        ```output
        MISSING
        ```
    """, 'tags = {"owner": "platform", "environment": "prod"}\nprint(tags.get("cost_center", "MISSING"))',
      starter='tags = {"owner": "platform", "environment": "prod"}',
      require=[".get("],
      hints=[".get(key, default) returns the default when the key is missing.",
             'print(tags.get("cost_center", "MISSING"))']),
    C("""
        Count resources per cloud. Given
        `providers = ["aws", "google", "aws", "google", "aws"]`, build a dictionary `counts` and print it:

        ```output
        {'aws': 3, 'google': 2}
        ```
    """, 'providers = ["aws", "google", "aws", "google", "aws"]\ncounts = {}\nfor p in providers:\n    counts[p] = counts.get(p, 0) + 1\nprint(counts)',
      starter='providers = ["aws", "google", "aws", "google", "aws"]',
      check='assert counts == {"aws": 3, "google": 2}, "counts should be {\'aws\': 3, \'google\': 2}, got %r" % (counts,)',
      require=["for"],
      hints=["Start with counts = {} and loop over providers.",
             "counts[p] = counts.get(p, 0) + 1",
             "for p in providers:\n    counts[p] = counts.get(p, 0) + 1\nprint(counts)"]),
    C("""
        Here is one entry from a Terraform plan:

        ```
        entry = {
            "address": "aws_security_group.admin",
            "change": {
                "actions": ["create"],
                "after": {"ingress": [{"from_port": 443, "cidr_blocks": ["10.0.0.0/8"]},
                                      {"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]},
            },
        }
        ```

        Loop over the ingress rules and print the `from_port` of every rule whose `cidr_blocks` contains
        `"0.0.0.0/0"`:

        ```output
        22
        ```
    """, '''entry = {
    "address": "aws_security_group.admin",
    "change": {
        "actions": ["create"],
        "after": {"ingress": [{"from_port": 443, "cidr_blocks": ["10.0.0.0/8"]},
                              {"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]},
    },
}
for rule in entry["change"]["after"]["ingress"]:
    if "0.0.0.0/0" in rule["cidr_blocks"]:
        print(rule["from_port"])''',
      starter='''entry = {
    "address": "aws_security_group.admin",
    "change": {
        "actions": ["create"],
        "after": {"ingress": [{"from_port": 443, "cidr_blocks": ["10.0.0.0/8"]},
                              {"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]},
    },
}''',
      require=["for"], forbid=["print(22)"],
      hints=['The list of rules is entry["change"]["after"]["ingress"].',
             'Loop: for rule in entry["change"]["after"]["ingress"]:',
             'Inside: if "0.0.0.0/0" in rule["cidr_blocks"]: print(rule["from_port"])']),
], summary="""
    - `d = {"key": value}`; `d["key"]` reads (KeyError if missing); `d["key"] = v` adds/changes.
    - Safe reads: `"key" in d`, `d.get("key")`, `d.get("key", default)`.
    - Loops: `for k in d`, `for k, v in d.items()`; `d.keys()`, `d.values()`.
    - Counting: `counts[x] = counts.get(x, 0) + 1`.
    - Nested data: chain lookups outside-in: `plan["change"]["after"]["ingress"][0]["from_port"]`.
""")

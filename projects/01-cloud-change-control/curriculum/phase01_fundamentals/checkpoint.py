from pce.lesson import Q, P, C, Checkpoint

RESOURCES = '''resources = [
    {"address": "aws_s3_bucket.logs", "type": "aws_s3_bucket", "action": "create", "tags": {"owner": "platform"}},
    {"address": "aws_instance.web", "type": "aws_instance", "action": "update", "tags": {}},
    {"address": "aws_db_instance.orders", "type": "aws_db_instance", "action": "delete", "tags": {"owner": "data"}},
    {"address": "aws_instance.worker", "type": "aws_instance", "action": "create", "tags": {}},
]'''

CHECKPOINT = Checkpoint("p01cp", "Summarise a plan", """
    Put the whole phase together: you're given a simplified plan as a list of resource dictionaries -
    exactly the shape you'll build from real Terraform output in Phase 2. Answer questions about it with
    loops, conditions, dictionaries and functions.
""", [
    P(RESOURCES + '''
print(len(resources))
print(resources[2]["action"])
print(resources[0]["tags"].get("owner", "none"))
print(resources[1]["tags"].get("owner", "none"))
''', explain="len counts the list, [2] is the third resource, and .get returns the default when the key is missing."),
    C("""
        Using the `resources` list provided, print how many changes there are of each action, in this exact
        format and order:

        ```output
        create: 2
        update: 1
        delete: 1
        ```

        Count with a loop and a dictionary - your code must still work if the list changes.
    """, RESOURCES + '''
counts = {}
for resource in resources:
    action = resource["action"]
    counts[action] = counts.get(action, 0) + 1
for action, number in counts.items():
    print(f"{action}: {number}")''',
      starter=RESOURCES,
      check="""
        assert __output__.strip().splitlines() == ["create: 2", "update: 1", "delete: 1"], "print one line per action, in first-seen order"
        extra = [{"address": "x.y", "type": "x", "action": "delete", "tags": {}}]
        out = __capture__(exec, __source__.replace("resources = [", "resources = %r + [" % extra, 1), {})
        assert "delete: 2" in out and out.splitlines()[0] == "delete: 2", "your counts must come from the data, not be typed in"
      """,
      require=["for"],
      hints=["Start with an empty dict `counts = {}` and loop over `resources`.",
             "Inside the loop: counts[action] = counts.get(action, 0) + 1",
             'Then: for action, number in counts.items(): print(f"{action}: {number}")']),
    C("""
        Write a function `untagged(resources)` that **returns** a list of the addresses of resources whose
        `tags` dictionary has no `"owner"` key, in their original order.

        For the provided list it should return `["aws_instance.web", "aws_instance.worker"]`.
    """, RESOURCES + '''

def untagged(resources):
    result = []
    for resource in resources:
        if "owner" not in resource["tags"]:
            result.append(resource["address"])
    return result''',
      starter=RESOURCES,
      check="""
        assert untagged(resources) == ["aws_instance.web", "aws_instance.worker"], "got %r" % (untagged(resources),)
        assert untagged([]) == [], "an empty list should give []"
        assert untagged([{"address": "a.b", "tags": {"owner": "x"}}]) == []
      """,
      require=["def untagged", "return"],
      hints=["Create an empty list, loop, and append addresses that are missing the key.",
             '`"owner" not in resource["tags"]` checks for a missing key.',
             'def untagged(resources):\n    result = []\n    for resource in resources:\n        if "owner" not in resource["tags"]:\n            result.append(resource["address"])\n    return result']),
    C("""
        Write a function `risky_deletes(resources, stateful_types)` that returns the number of resources
        whose action is `"delete"` **and** whose type is in the `stateful_types` list.

        ```
        risky_deletes(resources, ["aws_db_instance", "aws_s3_bucket"])   # 1
        ```
    """, RESOURCES + '''

def risky_deletes(resources, stateful_types):
    count = 0
    for resource in resources:
        if resource["action"] == "delete" and resource["type"] in stateful_types:
            count += 1
    return count''',
      starter=RESOURCES,
      check="""
        assert risky_deletes(resources, ["aws_db_instance", "aws_s3_bucket"]) == 1
        assert risky_deletes(resources, ["aws_s3_bucket"]) == 0, "only deletes count"
        more = resources + [{"address": "aws_s3_bucket.old", "type": "aws_s3_bucket", "action": "delete", "tags": {}}]
        assert risky_deletes(more, ["aws_db_instance", "aws_s3_bucket"]) == 2
      """,
      require=["def risky_deletes", "return"],
      hints=["Keep a counter starting at 0 and add 1 when both conditions are true.",
             'if resource["action"] == "delete" and resource["type"] in stateful_types:',
             "count += 1 inside the if, and return count after the loop."]),
    Q("A function prints a value but has no `return`. What does calling it give back?",
      "None", "The printed value", "0", "An error",
      explain="Printing shows a value on screen; only return hands it back to the caller."),
])

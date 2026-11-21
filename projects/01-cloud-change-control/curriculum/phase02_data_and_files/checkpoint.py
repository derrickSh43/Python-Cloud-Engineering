from pce.lesson import Q, P, C, Checkpoint

PLAN = '''{
  "format_version": "1.2",
  "resource_changes": [
    {"address": "aws_s3_bucket.logs", "type": "aws_s3_bucket",
     "provider_name": "registry.terraform.io/hashicorp/aws", "mode": "managed",
     "change": {"actions": ["create"], "before": null, "after": {"bucket": "logs"}}},
    {"address": "data.aws_caller_identity.me", "type": "aws_caller_identity",
     "provider_name": "registry.terraform.io/hashicorp/aws", "mode": "data",
     "change": {"actions": ["read"], "before": null, "after": {}}},
    {"address": "google_sql_database_instance.main", "type": "google_sql_database_instance",
     "provider_name": "registry.terraform.io/hashicorp/google", "mode": "managed",
     "change": {"actions": ["delete"], "before": {"name": "main"}, "after": null}},
    {"address": "aws_instance.web", "type": "aws_instance",
     "provider_name": "registry.terraform.io/hashicorp/aws", "mode": "managed",
     "change": {"actions": ["delete", "create"], "before": {}, "after": {}}}
  ]
}'''

CHECKPOINT = Checkpoint("p02cp", "Read a real plan", """
    Combine files, JSON, exceptions, comprehensions and helper functions to answer questions about a plan
    file - the same job ChangeGate's parser does.
""", [
    Q("Which exception does `json.loads(\"{bad\")` raise?", "json.JSONDecodeError", "ValueError only", "KeyError",
      "FileNotFoundError", explain="JSONDecodeError is a subclass of ValueError, but the specific name is the one to catch."),
    P('''
import hashlib, json
a = json.dumps({"x": 1, "y": 2}, sort_keys=True, separators=(",", ":"))
b = json.dumps({"y": 2, "x": 1}, sort_keys=True, separators=(",", ":"))
print(a)
print(hashlib.sha256(a.encode()).hexdigest() == hashlib.sha256(b.encode()).hexdigest())
'''),
    C("""
        A file `plan.json` is in your folder. Write `managed_changes(path)` that loads it and **returns** a
        list of `(address, action)` tuples for every entry whose `mode` is `"managed"` (skip data
        sources). `action` is `"replace"` when the actions are delete+create in any order, otherwise the
        single action string.

        ```
        [("aws_s3_bucket.logs", "create"), ("google_sql_database_instance.main", "delete"),
         ("aws_instance.web", "replace")]
        ```
    """, '''import json
from pathlib import Path

def managed_changes(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    result = []
    for rc in plan["resource_changes"]:
        if rc["mode"] != "managed":
            continue
        actions = rc["change"]["actions"]
        action = "replace" if set(actions) == {"delete", "create"} else actions[0]
        result.append((rc["address"], action))
    return result''',
      files={"plan.json": PLAN},
      check="""
        expected = [("aws_s3_bucket.logs", "create"), ("google_sql_database_instance.main", "delete"),
                    ("aws_instance.web", "replace")]
        got = managed_changes("plan.json")
        assert got == expected, "got %r" % (got,)
      """,
      require=["def managed_changes", "return"],
      hints=['Load: json.loads(Path(path).read_text(encoding="utf-8")) and loop over plan["resource_changes"].',
             'Skip entries with `if rc["mode"] != "managed": continue`. Detect replace with set(actions) == {"delete", "create"}.',
             'result.append((rc["address"], action)) - note the double brackets: you append one tuple.']),
    C("""
        Write `load_plan_safely(path)` that returns the decoded plan dict, but raises
        `PlanError("plan file not found: <path>")` (from None) when the file doesn't exist and
        `PlanError("plan is not valid JSON")` (from None) when it can't be parsed.
        Define the `PlanError` class yourself.

        Files `plan.json` (valid) and `broken.json` (invalid) are in your folder; `absent.json` isn't.
    """, '''import json
from pathlib import Path

class PlanError(Exception):
    pass

def load_plan_safely(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PlanError("plan file not found: %s" % path) from None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise PlanError("plan is not valid JSON") from None''',
      files={"plan.json": PLAN, "broken.json": '{"format_version": '},
      check="""
        assert load_plan_safely("plan.json")["format_version"] == "1.2"
        for name, expected in (("absent.json", "plan file not found: absent.json"), ("broken.json", "plan is not valid JSON")):
            try:
                load_plan_safely(name)
            except PlanError as e:
                assert str(e) == expected, "for %s the message should be %r, got %r" % (name, expected, str(e))
                assert e.__suppress_context__, "use `raise ... from None`"
            else:
                raise AssertionError("load_plan_safely(%r) should raise PlanError" % name)
      """,
      require=["class PlanError", "from None"],
      hints=["Two separate try/except blocks: one around reading the file, one around json.loads.",
             "class PlanError(Exception):\n    pass",
             'except FileNotFoundError:\n    raise PlanError("plan file not found: %s" % path) from None']),
])

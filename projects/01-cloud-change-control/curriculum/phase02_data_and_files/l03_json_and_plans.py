from pce.lesson import T, Ex, Q, P, C, B, Lesson

MINI_PLAN = '''{
  "format_version": "1.2",
  "terraform_version": "1.9.5",
  "resource_changes": [
    {
      "address": "aws_s3_bucket.logs",
      "mode": "managed",
      "type": "aws_s3_bucket",
      "name": "logs",
      "provider_name": "registry.terraform.io/hashicorp/aws",
      "change": {
        "actions": ["create"],
        "before": null,
        "after": {"bucket": "example-app-logs", "tags": {"owner": "platform"}},
        "after_unknown": {"arn": true}
      }
    },
    {
      "address": "aws_db_instance.orders",
      "mode": "managed",
      "type": "aws_db_instance",
      "name": "orders",
      "provider_name": "registry.terraform.io/hashicorp/aws",
      "change": {
        "actions": ["delete", "create"],
        "before": {"engine_version": "15.4"},
        "after": {"engine_version": "16.1"},
        "after_unknown": {}
      }
    }
  ]
}'''

LESSON = Lesson("p02l3", "JSON and the Terraform plan format", [
    T("""
        **JSON**

        JSON is the most common format for exchanging data between programs. It maps neatly onto Python:

        | JSON | Python |
        |---|---|
        | object `{"a": 1}` | `dict` |
        | array `[1, 2]` | `list` |
        | string `"x"` | `str` |
        | number `1`, `1.5` | `int`, `float` |
        | `true` / `false` | `True` / `False` |
        | `null` | `None` |

        `json.loads(text)` parses a JSON string into Python values; `json.dumps(value)` goes the other way.
    """),
    Ex("""
        import json
        data = json.loads('{"bucket": "logs", "versioning": true, "tags": null, "ports": [22, 443]}')
        print(data)
        print(data["versioning"], data["tags"], data["ports"][1])
        print(json.dumps({"ok": True, "missing": None}))
        print(json.dumps({"b": 1, "a": 2}, indent=2))
    """),
    T("""
        **When JSON is broken**

        `json.loads` raises `json.JSONDecodeError` for invalid JSON. The exception object knows where the
        problem is: `.lineno`, `.colno` and `.msg`. Good tools report that location so the user can fix
        it quickly.
    """),
    Ex("""
        import json
        try:
            json.loads('{\\n  "a": 1,\\n  oops\\n}')
        except json.JSONDecodeError as e:
            print("line", e.lineno, "column", e.colno, "-", e.msg)
    """),
    T("""
        **Checking types with isinstance**

        Valid JSON isn't necessarily the *right shape*. `json.loads("[1, 2]")` is perfectly valid but
        gives a list, not the dict a plan should be. `isinstance(value, dict)` checks:

        ```
        isinstance({"a": 1}, dict)      # True
        isinstance([1, 2], dict)        # False
        isinstance(5, (int, float))     # True - a tuple of types means "any of these"
        ```
    """),
    P("""
        import json
        for text in ['{"a": 1}', '[1, 2]', '"plan"']:
            print(isinstance(json.loads(text), dict))
    """),
    T("""
        **Inside a Terraform plan**

        After `terraform plan -out=plan.tfplan`, the command `terraform show -json plan.tfplan > plan.json`
        writes JSON shaped like this (trimmed):

        ```
        {
          "format_version": "1.2",
          "resource_changes": [
            {
              "address": "aws_db_instance.orders",
              "type": "aws_db_instance",
              "provider_name": "registry.terraform.io/hashicorp/aws",
              "change": {
                "actions": ["delete", "create"],
                "before": {...},
                "after": {...},
                "after_unknown": {...}
              }
            }
          ]
        }
        ```

        - `format_version` - the version of this JSON layout. ChangeGate supports `1.x`.
        - `resource_changes` - one entry per resource.
        - `actions` - `["create"]`, `["update"]`, `["delete"]`, `["no-op"]`, or `["delete", "create"]`
          for a **replacement**.
        - `before` / `after` - the attributes before and after (`null` when the resource doesn't exist on
          that side). `after_unknown` marks values Terraform can't know until apply, like a new ARN.
    """),
    Ex("""
        import json
        from pathlib import Path
        plan = json.loads(Path("plan.json").read_text(encoding="utf-8"))
        print("format", plan["format_version"])
        for rc in plan["resource_changes"]:
            print(rc["address"], rc["change"]["actions"])
    """, files={"plan.json": MINI_PLAN}),
    Q("A plan entry has `\"actions\": [\"delete\", \"create\"]`. What will Terraform do?",
      "Destroy the resource and create a new one (a replacement)", "Nothing - they cancel out",
      "Update the resource in place", "Create it, then delete it again"),
    C("""
        A file `plan.json` is in your working folder. Load it, and for each resource change print its
        address and whether it is a replacement:

        ```output
        aws_s3_bucket.logs False
        aws_db_instance.orders True
        ```

        A replacement is when the set of actions is exactly `{"delete", "create"}`.
    """, 'import json\nfrom pathlib import Path\nplan = json.loads(Path("plan.json").read_text(encoding="utf-8"))\nfor rc in plan["resource_changes"]:\n    print(rc["address"], set(rc["change"]["actions"]) == {"delete", "create"})',
      files={"plan.json": MINI_PLAN},
      require=["json"],
      hints=['Load with json.loads(Path("plan.json").read_text(encoding="utf-8")).',
             'set(["delete", "create"]) == {"delete", "create"} is True regardless of order.',
             'for rc in plan["resource_changes"]:\n    print(rc["address"], set(rc["change"]["actions"]) == {"delete", "create"})']),
    B("p2-decode-plan", intro="This function turns the raw bytes from `read_plan_bytes` into a Python dict - "
                             "with a clear `PlanError` for each kind of bad input."),
    B("p2-check-format", intro="Before trusting a plan's contents, ChangeGate checks it's a format it understands."),
], summary="""
    - JSON ↔ Python: object/dict, array/list, string/str, number/int-float, true-false/True-False, null/None.
    - `json.loads(text)` parses; `json.dumps(value, indent=2)` writes. Errors: `json.JSONDecodeError`
      with `.lineno`, `.colno`, `.msg`.
    - `isinstance(value, dict)` checks shape; `isinstance(x, (int, float))` accepts several types.
    - A plan: `format_version`, `resource_changes[]` each with `address`, `type`, `provider_name`,
      `change.actions`, `change.before/after/after_unknown`. `["delete", "create"]` = replace.
""")

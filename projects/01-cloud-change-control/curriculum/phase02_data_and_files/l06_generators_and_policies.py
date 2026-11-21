from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p02l6", "JSON inside JSON, and generators", [
    T("""
        **Policies as strings**

        AWS IAM policies and GCP IAM policy data appear in a plan as **JSON text stored inside a JSON
        string**:

        ```
        "policy": "{\\"Version\\": \\"2012-10-17\\", \\"Statement\\": [{\\"Effect\\": \\"Allow\\", \\"Action\\": \\"*\\", \\"Resource\\": \\"*\\"}]}"
        ```

        The outer `json.loads` (of the whole plan) gives you a Python **string**. You need a second
        `json.loads` on that string to get the policy as a dict.
    """),
    Ex("""
        import json
        policy = {"Statement": [{"Effect": "Allow", "Action": "*"}]}
        attrs = {"policy": json.dumps(policy)}      # how Terraform stores it: a string
        plan_text = json.dumps(attrs)               # ...inside the plan's JSON
        print(plan_text)

        loaded = json.loads(plan_text)              # first parse: the plan
        print(type(loaded["policy"]))               # still a str!
        document = json.loads(loaded["policy"])     # second parse: the policy itself
        print(document["Statement"][0]["Action"])
    """, note="The backslashes in the output are JSON escaping the quote marks of the inner document."),
    T("""
        **IAM statements**

        An AWS policy document has a `Statement` that may be a single object **or** a list of them. Each
        statement has an `Effect` (`Allow` or `Deny`), an `Action`, a `Resource`, and for resource policies
        (like S3 bucket policies) a `Principal` - *who* is allowed.

        `"Principal": "*"` or `"Principal": {"AWS": "*"}` means **anyone on the internet** - one of the
        most common causes of data leaks.
    """),
    T("""
        **Generators: yield**

        A function that uses `yield` instead of `return` is a **generator**. Each `yield` hands out one
        value; the function pauses there and continues when the next value is requested. Loop over a
        generator like a list, or turn it into one with `list(...)`:

        ```
        def world_open(cidrs):
            for cidr in cidrs:
                if cidr in ("0.0.0.0/0", "::/0"):
                    yield cidr

        for cidr in world_open(["10.0.0.0/8", "0.0.0.0/0", "::/0"]):
            print(cidr)
        ```

        Generators are ideal when a function finds **zero or more** things - exactly what a security
        policy does. ChangeGate's policies are generators that yield their findings.
    """),
    Ex("""
        def world_open(cidrs):
            for cidr in cidrs:
                if cidr in ("0.0.0.0/0", "::/0"):
                    yield cidr

        found = world_open(["10.0.0.0/8", "0.0.0.0/0", "::/0"])
        print(found)
        print(list(found))
        print(list(world_open(["10.0.0.0/8"])))
    """, note="Calling a generator function doesn't run it yet - it returns a generator object. "
              "`list()` runs it to the end."),
    P("""
        def countdown(n):
            while n > 0:
                yield n
                n -= 1

        print(list(countdown(3)))
        print(sum(countdown(4)))
    """),
    Q("A generator function finishes without yielding anything. What does `list(...)` of it give?",
      "[]", "None", "An error", "[None]"),
    C("""
        Write a generator `allow_actions(document)` that yields the `Action` of every statement in
        `document["Statement"]` whose `Effect` is `"Allow"`.

        ```
        doc = {"Statement": [{"Effect": "Allow", "Action": "s3:GetObject"},
                             {"Effect": "Deny", "Action": "*"},
                             {"Effect": "Allow", "Action": "ec2:*"}]}
        list(allow_actions(doc))     # ["s3:GetObject", "ec2:*"]
        ```
    """, 'def allow_actions(document):\n    for statement in document["Statement"]:\n        if statement["Effect"] == "Allow":\n            yield statement["Action"]',
      check="""
        import types
        doc = {"Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}, {"Effect": "Deny", "Action": "*"},
                             {"Effect": "Allow", "Action": "ec2:*"}]}
        result = allow_actions(doc)
        assert isinstance(result, types.GeneratorType), "use yield to make allow_actions a generator"
        assert list(result) == ["s3:GetObject", "ec2:*"]
        assert list(allow_actions({"Statement": []})) == []
      """,
      require=["yield"],
      hints=["Loop over document[\"Statement\"] and check each statement's Effect.",
             'for statement in document["Statement"]:\n    if statement["Effect"] == "Allow":\n        yield statement["Action"]']),
    B("p2-json-documents", intro="The last three helpers for this phase. `statements` must be a generator - the "
                                "tests check."),
], summary="""
    - IAM policies arrive as JSON strings inside the plan: `json.loads` them a second time.
    - `Statement` may be one object or a list; `Principal: "*"` / `{"AWS": "*"}` means anyone.
    - Generators: a function with `yield` returns a generator; it produces values lazily. `list(gen)` collects
      them. Ideal for "find zero or more problems".
""")

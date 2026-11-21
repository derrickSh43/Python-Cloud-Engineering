from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l2", "Variables and types", [
    T("""
        **Naming values**

        A **variable** is a name for a value. You create one with `=`:

        ```
        region = "us-east-1"
        instance_count = 3
        print(region, instance_count)
        ```

        Read `=` as "now refers to", not "equals". The right side is worked out first, then the name on
        the left is attached to it. Use the name anywhere you'd use the value.
    """),
    Ex("""
        region = "us-east-1"
        instance_count = 3
        print("Deploying", instance_count, "instances to", region)
        instance_count = 5        # a variable can be changed
        print("Now", instance_count)
    """),
    T("""
        **Naming rules**

        - Letters, digits and underscores only, and not starting with a digit: `subnet_2` is fine, `2subnet` isn't.
        - Case matters: `Region` and `region` are different variables.
        - Python style is **snake_case**: lowercase words joined by underscores, like `bucket_name`.
        - Choose names that say what the value *means*: `max_instances`, not `x`.
    """),
    P("""
        count = 2
        count = count + 1
        print(count)
    """, explain="The right side `count + 1` is worked out first (2 + 1), then `count` refers to 3."),
    T("""
        **Types**

        Every value has a **type**:

        - `str` - text: `"t3.micro"`
        - `int` - whole numbers: `443`
        - `float` - decimals: `0.0116` (an hourly price, say)
        - `bool` - `True` or `False` (capital T and F, no quotes)
        - `None` - "no value": a special value you'll see often with Terraform data

        `type(value)` tells you the type.
    """),
    Ex("""
        print(type("t3.micro"))
        print(type(443))
        print(type(0.0116))
        print(type(True))
        print(type(None))
    """),
    Q("Which value is an `int`?", "22", '"22"', "22.0", "True",
      explain='"22" is a string because of the quotes, and 22.0 is a float.'),
    T("""
        **f-strings: putting values inside text**

        Put an `f` before the opening quote and write variables inside `{curly braces}`:

        ```
        name = "logs"
        region = "eu-west-1"
        print(f"bucket {name} in {region}")     # bucket logs in eu-west-1
        ```

        You can put small expressions inside the braces too: `f"{count + 1} instances"`.
        f-strings are the clearest way to build messages, and you'll use them constantly.
    """),
    Ex("""
        name = "web"
        port = 443
        hourly = 0.0116
        print(f"security group {name} allows port {port}")
        print(f"3 instances cost {3 * hourly} per hour")
    """),
    P("""
        env = "prod"
        replicas = 2
        print(f"{env} has {replicas * 2} pods")
    """),
    C("""
        Create a variable `resource_type` holding `"aws_s3_bucket"` and a variable `name` holding `"logs"`.
        Then use an f-string to print the Terraform address, which joins them with a dot:

        ```output
        aws_s3_bucket.logs
        ```
    """, 'resource_type = "aws_s3_bucket"\nname = "logs"\nprint(f"{resource_type}.{name}")',
      check="""
        assert resource_type == "aws_s3_bucket", "resource_type should be 'aws_s3_bucket'"
        assert name == "logs", "name should be 'logs'"
        assert __output__.strip() == "aws_s3_bucket.logs", "print the address: aws_s3_bucket.logs"
      """,
      require=[('f"', "f'")],
      hints=["Create both variables with = on separate lines first.",
             'Inside an f-string, write {resource_type}.{name} - the dot is just text between them.',
             'print(f"{resource_type}.{name}")']),
    C("""
        A plan adds `to_add = 3` resources and destroys `to_destroy = 1`. Create those two variables and
        print:

        ```output
        Plan: 3 to add, 1 to destroy, 4 total changes.
        ```

        Compute the total in your code - don't type the 4.
    """, 'to_add = 3\nto_destroy = 1\nprint(f"Plan: {to_add} to add, {to_destroy} to destroy, {to_add + to_destroy} total changes.")',
      check="""
        assert to_add == 3 and to_destroy == 1, "create to_add = 3 and to_destroy = 1"
        assert __output__.strip() == "Plan: 3 to add, 1 to destroy, 4 total changes.", "check the exact wording and punctuation"
      """,
      forbid=["4 total"],
      hints=["An f-string can contain an expression: {to_add + to_destroy}.",
             'print(f"Plan: {to_add} to add, {to_destroy} to destroy, {to_add + to_destroy} total changes.")']),
], summary="""
    - `name = value` creates or updates a variable. The right side is evaluated first.
    - Names: snake_case, letters/digits/underscores, case-sensitive, meaningful.
    - Types: `str`, `int`, `float`, `bool` (`True`/`False`), and `None` for "no value". `type(x)` shows it.
    - f-strings: `f"bucket {name} has {count + 1} objects"` puts values inside text.
""")

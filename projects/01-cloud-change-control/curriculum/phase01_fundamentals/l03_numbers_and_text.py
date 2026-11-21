from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l3", "Numbers and text", [
    T("""
        **Arithmetic**

        | operator | meaning | example | result |
        |---|---|---|---|
        | `+` `-` `*` | add, subtract, multiply | `3 * 4` | `12` |
        | `/` | divide (always a float) | `10 / 4` | `2.5` |
        | `//` | divide, rounding down | `10 // 4` | `2` |
        | `%` | remainder | `10 % 4` | `2` |
        | `**` | power | `2 ** 10` | `1024` |

        Brackets work as in maths: `(2 + 3) * 4` is 20.
    """),
    Ex("""
        hourly = 0.0116
        hours_per_month = 730
        print("monthly cost:", hourly * hours_per_month)
        print("rounded:", round(hourly * hours_per_month, 2))
        print("full days in 100 hours:", 100 // 24, "remainder", 100 % 24)
    """, note="`round(value, 2)` rounds to two decimal places."),
    P("""
        print(7 // 2)
        print(7 % 2)
        print(7 / 2)
    """),
    T("""
        **Converting between types**

        Values read from files and configuration often arrive as **text**, even when they look like
        numbers. Convert with `int()`, `float()` and `str()`:

        ```
        port_text = "8080"
        port = int(port_text)       # 8080, a number you can do maths with
        label = "port " + str(port) # back to text so it can be joined with +
        ```

        `+` joins two strings, but `"port " + 8080` is a **TypeError**: Python won't guess whether you
        meant text or maths.
    """),
    Ex("""
        print("443" + "1")      # joins text
        print(int("443") + 1)   # does maths
        print(float("0.5") * 2)
        print("port " + str(22))
    """),
    Ex("""
        print("port " + 22)
    """, note="Python refuses to add text and a number. Convert first with `str(22)`, or use an f-string.",
       error_ok=True),
    T("""
        **Strings have methods**

        A **method** is a function that belongs to a value, called with a dot: `text.upper()`.

        | method | example | result |
        |---|---|---|
        | `.lower()` / `.upper()` | `"PROD".lower()` | `"prod"` |
        | `.strip()` | `"  web  ".strip()` | `"web"` |
        | `.replace(a, b)` | `"t3.micro".replace("micro", "large")` | `"t3.large"` |
        | `.startswith(x)` / `.endswith(x)` | `"aws_s3_bucket".startswith("aws_")` | `True` |
        | `.split(sep)` | `"10.0.1.0/24".split("/")` | `["10.0.1.0", "24"]` |

        Methods return a **new** string; the original is unchanged (strings can't be modified).
        `len(text)` gives the number of characters.
    """),
    Ex("""
        provider = "registry.terraform.io/hashicorp/aws"
        print(provider.upper())
        print(provider.split("/"))
        print(provider.endswith("/aws"))
        print(len(provider))
        print("  t3.micro \\n".strip())
    """),
    T("""
        **Indexing and slicing**

        Characters are numbered from **0**. `text[0]` is the first, `text[-1]` the last.
        A **slice** `text[start:end]` takes characters from `start` up to, but **not including**, `end`.

        ```
        sha = "dc1f38524b760ba9"
        sha[0]      # "d"
        sha[:6]     # "dc1f38"  (first six)
        sha[-4:]    # "0ba9"    (last four)
        ```
    """),
    P("""
        region = "eu-west-2"
        print(region[0])
        print(region[:2])
        print(region[-1])
    """),
    Q("What is `\"aws_db_instance\".split(\"_\")[0]`?", '"aws"', '"db"', '["aws"]', '"a"',
      explain="split gives [\"aws\", \"db\", \"instance\"] and [0] takes the first item."),
    C("""
        A Terraform provider address is stored in `provider = "registry.terraform.io/hashicorp/google"`.

        Print just the last part after the final `/`:

        ```output
        google
        ```

        Use string methods - don't type the word `google` in your print.
    """, 'provider = "registry.terraform.io/hashicorp/google"\nprint(provider.split("/")[-1])',
      forbid=['print("google")', "print('google')"],
      hints=['.split("/") turns the address into a list of parts.',
             "Index -1 is the last item of a list.",
             'print(provider.split("/")[-1])']),
    C("""
        Instance sizes come in as messy text: `raw = "  T3.Micro "`. Clean it up so it prints
        lower-case with no surrounding spaces:

        ```output
        t3.micro
        ```
    """, 'raw = "  T3.Micro "\nprint(raw.strip().lower())',
      require=["raw"], forbid=['"t3.micro"', "'t3.micro'"],
      hints=["Two methods: one removes surrounding spaces, one makes text lower-case.",
             "Methods can be chained: raw.strip().lower()"]),
    C("""
        A security group rule arrives as text: `port_range = "8000-8080"`.

        Split it, convert both halves to numbers, and print how many ports the range covers (inclusive,
        so 8000-8080 is 81 ports):

        ```output
        81
        ```
    """, 'port_range = "8000-8080"\nparts = port_range.split("-")\nlow = int(parts[0])\nhigh = int(parts[1])\nprint(high - low + 1)',
      forbid=["81"],
      hints=['port_range.split("-") gives ["8000", "8080"] - two strings.',
             "int(...) turns each string into a number. Inclusive count = high - low + 1.",
             'parts = port_range.split("-")\nprint(int(parts[1]) - int(parts[0]) + 1)']),
], summary="""
    - Arithmetic: `+ - * /` (`/` gives a float), `//` floor divide, `%` remainder, `**` power, `round(x, 2)`.
    - Convert with `int()`, `float()`, `str()`. `"a" + 1` is a TypeError.
    - String methods return new strings: `.lower() .upper() .strip() .replace(a, b) .startswith(x) .split(sep)`.
    - `len(text)`; indexing from 0, `text[-1]` is last; slices `text[a:b]` exclude `b`.
""")

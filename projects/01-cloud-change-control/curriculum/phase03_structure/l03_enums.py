from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p03l3", "Enums: a fixed set of values", [
    T("""
        **The problem with plain strings**

        Terraform actions are one of a handful of words. If you pass them around as strings, nothing
        stops `"delet"` slipping through, and every function has to re-check the spelling. An **enum**
        defines the complete set of allowed values once:

        ```
        from enum import Enum

        class Action(Enum):
            CREATE = "create"
            UPDATE = "update"
            DELETE = "delete"
        ```

        Each **member** has a `.name` (`"CREATE"`) and a `.value` (`"create"`). Compare members with `is`
        or `==`: `action is Action.DELETE`.
    """),
    Ex("""
        from enum import Enum

        class Action(Enum):
            CREATE = "create"
            UPDATE = "update"
            DELETE = "delete"

        a = Action.DELETE
        print(a, a.name, a.value)
        print(Action("create"))        # look up by VALUE with ()
        print(Action["UPDATE"])        # look up by NAME with []
        print([m.value for m in Action])
    """),
    Ex("""
        from enum import Enum

        class Action(Enum):
            CREATE = "create"

        Action("explode")
    """, note="Looking up an unknown value raises ValueError; an unknown name with [] raises KeyError.",
       error_ok=True),
    T("""
        **str and int enums**

        - `class Action(str, Enum)` makes each member **also a string**, so `Action.CREATE == "create"` is
          True and it can go straight into JSON.
        - `IntEnum` members are **also integers**, so they can be compared and ordered. That's exactly
          what severities need:

        ```
        from enum import IntEnum

        class Severity(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        Severity.HIGH > Severity.MEDIUM                      # True
        max([Severity.LOW, Severity.CRITICAL])              # Severity.CRITICAL
        Severity(min(Severity.CRITICAL, Severity.HIGH + 2)) # Severity.CRITICAL
        ```
    """),
    Ex("""
        from enum import IntEnum

        class Severity(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        found = [Severity.MEDIUM, Severity.HIGH, Severity.LOW]
        print(max(found).name)
        print(sorted(found, reverse=True))
        print(Severity.HIGH + 1, Severity(Severity.HIGH + 1))
        print(Severity["high".upper()])
    """),
    T("""
        **Methods on enums**

        Enums are classes, so they can have methods, properties and class methods:

        ```
        class Action(str, Enum):
            ...
            @property
            def is_destructive(self):
                return self in (Action.DELETE, Action.REPLACE)

            @classmethod
            def from_terraform(cls, actions):     # ["delete", "create"] -> Action.REPLACE
                ...
        ```

        That's exactly what you're about to write.
    """),
    P("""
        from enum import IntEnum

        class Level(IntEnum):
            LOW = 1
            HIGH = 3

            def __str__(self):
                return self.name

        print(str(Level.HIGH), Level.HIGH > Level.LOW, Level.LOW == 1)
    """),
    Q("`class Severity(IntEnum)` with LOW=1 ... CRITICAL=4. What is `max(Severity.HIGH, Severity.LOW)`?",
      "Severity.HIGH", "3", "Severity.LOW", "An error: enums can't be compared",
      explain="IntEnum members compare as integers, but max returns the member itself."),
    C("""
        Define `class Cloud(str, Enum)` with members `AWS = "aws"`, `GCP = "gcp"` and `OTHER = "other"`,
        and a class method `from_provider(name)` that returns `AWS` for `"aws"`, `GCP` for `"google"` or
        `"google-beta"`, and `OTHER` for anything else.
    """, 'from enum import Enum\n\nclass Cloud(str, Enum):\n    AWS = "aws"\n    GCP = "gcp"\n    OTHER = "other"\n\n    @classmethod\n    def from_provider(cls, name):\n        if name == "aws":\n            return cls.AWS\n        if name in ("google", "google-beta"):\n            return cls.GCP\n        return cls.OTHER',
      check="""
        assert Cloud.AWS.value == "aws" and Cloud.GCP == "gcp", "members need the values aws/gcp/other and a str mixin"
        assert Cloud.from_provider("aws") is Cloud.AWS
        assert Cloud.from_provider("google-beta") is Cloud.GCP and Cloud.from_provider("google") is Cloud.GCP
        assert Cloud.from_provider("azurerm") is Cloud.OTHER
      """,
      require=["Enum", "@classmethod"],
      hints=["from enum import Enum, then class Cloud(str, Enum): with three members.",
             "from_provider is a @classmethod; return cls.AWS etc.",
             'if name == "aws": return cls.AWS\nif name in ("google", "google-beta"): return cls.GCP\nreturn cls.OTHER']),
    B("p3-action", intro="ChangeGate's `Action` members are already declared in `models.py`. Write its three methods."),
    B("p3-severity", intro="Same file. `Severity.parse` is what lets config files say `\"high\"` instead of a number."),
], summary="""
    - `class Action(Enum): CREATE = "create"` - members have `.name` and `.value`.
    - Look up by value `Action("create")` (ValueError if unknown) or by name `Action["CREATE"]` (KeyError).
    - `class X(str, Enum)` members are also strings; `IntEnum` members are also ints and can be ordered/max'd.
    - Enums can have methods, properties and class methods.
""")

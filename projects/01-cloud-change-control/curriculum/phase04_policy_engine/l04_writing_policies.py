from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l4", "Writing policies", [
    T("""
        **Anatomy of a policy**

        ```
        @register
        class DestroyStatefulResource(Policy):
            id = "CG-DESTROY-STATEFUL"
            title = "Deleting or replacing a resource that holds data"
            severity = Severity.HIGH
            actions = frozenset({Action.DELETE, Action.REPLACE})
            default_settings = {"extra_types": [], "ignore_types": []}

            def check(self, change):
                if change.type not in self.stateful_types():
                    return
                yield self.finding(change, "...", "remediation advice")
        ```

        - The class attributes say **when** it runs; `check` says **what's wrong**.
        - `check` is a generator: yield nothing for a clean change, one finding per problem otherwise.
        - Every finding carries **remediation** - telling someone their plan is blocked without saying how to
          fix it just makes them angry.
        - `default_settings` are overridable from config: `[policies.settings.CG-DESTROY-STATEFUL]`.
    """),
    T("""
        **Why destructive changes to data are special**

        Deleting a web server is usually fine: Terraform recreates it from code. Deleting a **database**,
        a **storage bucket** or a **disk** destroys data that no code can recreate. Worse, many harmless-looking
        edits *force a replacement*: changing a database's engine version or an EBS volume's type can
        appear in the plan as `["delete", "create"]`.

        ChangeGate asks each provider which resource types are **stateful** (they hold data) and flags any
        delete or replace of them as HIGH. Teams can add their own types or exclude some via settings.
    """),
    T("""
        **Tags and labels**

        Organisations rely on metadata on every resource - `owner`, `environment`, `cost-center` - for billing,
        incident response and clean-up. AWS calls it **tags** (and `tags_all` includes provider-wide
        `default_tags`); GCP calls it **labels**. The provider registry knows which attribute to read for each
        cloud, so one `RequiredTags` policy covers both.

        Two subtleties:

        - Some resource types don't support tags at all - if the attribute isn't present, skip it.
        - If Terraform can't know the tags until apply (`after_unknown`), don't guess - skip it.
    """),
    P("""
        required = ["owner", "environment"]
        tags = {"owner": "platform", "team": "core"}
        print([key for key in required if key not in tags])
    """),
    T("""
        **Sharing logic between policies: subclassing**

        "Open to the internet on a sensitive port" applies to AWS security groups *and* GCP firewalls. The
        resource shapes differ, but the judgement is identical:

        - all ports, or all protocols, open to the world → **CRITICAL**
        - a sensitive port (SSH 22, RDP 3389, databases 3306/5432/1433, Redis 6379...) open → **HIGH**
        - other ports (like 443 for a website) → fine

        So ChangeGate has an `OpenIngressPolicy` base class with a `judge()` method, and the AWS and GCP
        policies subclass it - each only translates its own resource shape into `judge(...)` calls. It isn't
        registered itself, only its subclasses are.
    """),
    Q("Why might `aws_db_instance` appear with actions `[\"delete\", \"create\"]` when nobody asked to delete it?",
      "Some attribute changes force Terraform to replace the resource", "Terraform always replaces databases on apply",
      "It's a bug in the plan file", "Delete-then-create is how Terraform updates tags"),
    C("""
        Write a generator function `judge(label, all_traffic, low, high, sensitive)` that mirrors
        ChangeGate's logic using plain strings:

        - if `all_traffic` or the range covers 0/1 to 65535: yield `"CRITICAL: <label> allows ALL ports"` and stop
        - else, if any sensitive ports fall within `low..high`: yield
          `"HIGH: <label> exposes 22, 3389"` (sorted, comma-separated)
    """, '''def judge(label, all_traffic, low, high, sensitive):
    if all_traffic or (low <= 1 and high >= 65535):
        yield "CRITICAL: %s allows ALL ports" % label
        return
    hits = sorted(p for p in sensitive if low <= p <= high)
    if hits:
        yield "HIGH: %s exposes %s" % (label, ", ".join(map(str, hits)))''',
      check="""
        S = [3389, 22, 5432]
        assert list(judge("rule 1", True, 22, 22, S)) == ["CRITICAL: rule 1 allows ALL ports"]
        assert list(judge("rule 1", False, 0, 65535, S)) == ["CRITICAL: rule 1 allows ALL ports"]
        assert list(judge("rule 2", False, 0, 4000, S)) == ["HIGH: rule 2 exposes 22, 3389"], "got %r" % (list(judge("rule 2", False, 0, 4000, S)),)
        assert list(judge("rule 3", False, 443, 443, S)) == []
      """,
      require=["yield"],
      hints=["Check the all-ports case first and `return` right after yielding.",
             "hits = sorted(p for p in sensitive if low <= p <= high)",
             '", ".join(map(str, hits)) turns [22, 3389] into "22, 3389".']),
    B("p4-destroy-stateful"),
    B("p4-required-tags"),
    B("p4-open-ingress", intro="The shared judgement for AWS security groups and GCP firewalls, in `policies/network.py`."),
], summary="""
    - A policy: class attributes (id, title, severity, resource_types, actions, default_settings) say when it
      runs; `check(change)` yields findings with remediation.
    - Stateful resources (databases, buckets, disks) hold data code can't recreate; flag delete/replace.
      Some edits force a replace.
    - Tags (AWS `tags_all`/`tags`) and labels (GCP) via the provider registry; skip untaggable and unknown.
    - Share judgement through a base class (`OpenIngressPolicy.judge`); subclasses adapt resource shapes.
""")

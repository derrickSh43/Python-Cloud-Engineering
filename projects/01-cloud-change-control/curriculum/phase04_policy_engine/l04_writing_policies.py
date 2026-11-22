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
        **The first two rules**

        - **Stateful deletes**: if a change deletes or replaces a resource whose type is in a set of
          "stateful" types (databases, buckets, disks), yield a HIGH finding. It's a set lookup plus an
          action check.
        - **Required tags**: read a dict of tags from the change's `after` settings and report the required
          keys that are missing. If the tags key isn't there at all, or its value is unknown, skip it. The
          provider registry tells you which key holds the tags (`tags_all` / `tags` for AWS, `labels` for GCP).
    """),
    P("""
        required = ["owner", "environment"]
        tags = {"owner": "platform", "team": "core"}
        print([key for key in required if key not in tags])
    """),
    T("""
        **Sharing logic between policies: subclassing**

        Two rules (one for AWS firewall rules, one for GCP) need the same check on a port range:

        - all ports open → **CRITICAL**
        - a port from a "sensitive" list (22, 3389, 5432...) inside the range → **HIGH**
        - otherwise → nothing

        Put that logic once in a base class method, `OpenIngressPolicy.judge()`. Each subclass only pulls the
        port range out of its own dict shape and calls `self.judge(...)`. The base class isn't registered,
        only its subclasses are.
    """),
    Q("What does this print?", "AWS: HIGH", "Base: HIGH", "HIGH", "An error",
      code="""
        class Base:
            name = "Base"
            def judge(self, port):
                return "%s: %s" % (self.name, "HIGH" if port == 22 else "ok")

        class AwsRule(Base):
            name = "AWS"

        print(AwsRule().judge(22))
      """, explain="AwsRule inherits judge(); inside it, self.name finds the subclass's own value first."),
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
    - Stateful deletes: a set lookup on the type plus an action check.
    - Required tags: missing keys from a dict; skip when the tags key is absent or unknown.
    - Share judgement through a base class (`OpenIngressPolicy.judge`); subclasses adapt resource shapes.
""")

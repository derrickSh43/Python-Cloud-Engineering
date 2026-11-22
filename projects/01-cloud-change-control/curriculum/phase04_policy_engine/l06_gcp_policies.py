from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l6", "GCP rules: one question, three data shapes", [
    T("""
        **The same data, three shapes**

        Google Cloud access grants come in three dict shapes, and a rule must handle all of them:

        | shape | where the members are |
        |---|---|
        | `{"role": ..., "member": "user:a@example.com"}` | one string |
        | `{"role": ..., "members": [...]}` | a list |
        | `{"policy_data": "<JSON string>"}` | `bindings[].members` inside a JSON string |

        Two member values mean "public": `allUsers` and `allAuthenticatedUsers`. Collect every member into
        one list first, then ask your question once.
    """),
    Ex("""
        import json
        member = {"role": "roles/storage.objectViewer", "member": "allUsers"}
        binding = {"role": "roles/storage.admin", "members": ["group:ops@example.com"]}
        policy = {"policy_data": json.dumps({"bindings": [{"role": "roles/owner", "members": ["user:a@example.com"]}]})}

        def members(attrs):
            found = []
            if "member" in attrs:
                found.append(attrs["member"])
            found += attrs.get("members", [])
            if attrs.get("policy_data"):
                for b in json.loads(attrs["policy_data"])["bindings"]:
                    found += b["members"]
            return found

        for attrs in (member, binding, policy):
            print(members(attrs))
    """),
    T("""
        **The other GCP rules**

        - **Buckets**: flag `uniform_bucket_level_access` set to `False`.
        - **Roles**: flag grants of `roles/owner` / `roles/editor`, and any role granted to `allUsers`.
        - **Firewalls**: `allow` is a list of dicts with `protocol` and an optional `ports` list of strings
          like `"22"` or `"8000-8090"`. Protocol `all`, or `tcp`/`udp` with no ports, means every port.
        - **Cloud SQL**: the setting you need is nested inside lists of one dict:
          `settings[0]["ip_configuration"][0]["authorized_networks"]`. A helper `first_block(attrs, key)`
          returns that first dict, or `{}` if it's missing.
    """),
    P("""
        allow = [{"protocol": "tcp", "ports": []}, {"protocol": "icmp"}, {"protocol": "tcp", "ports": ["22", "8000-8090"]}]
        for n, block in enumerate(allow, 1):
            protocol = block["protocol"]
            ports = block.get("ports") or []
            if protocol == "all" or (protocol in ("tcp", "udp", "sctp") and not ports):
                print(n, "every port")
            else:
                print(n, ports)
    """),
    Q("What does this print?", "8000 8090", "8000-8090", "['8000', '8090']", "An error",
      code="""
        text = "8000-8090"
        low, _, high = text.partition("-")
        print(int(low), int(high or low))
      """, explain="partition splits on the first '-' into three parts. For \"22\", high is \"\" so `high or low` reuses low."),
    Q("What does this print?", "{}", "None", "An error: list index out of range", "[]",
      code="""
        def first_block(attrs, key):
            blocks = attrs.get(key) or []
            return blocks[0] if blocks and isinstance(blocks[0], dict) else {}

        print(first_block({"settings": []}, "settings"))
      """, explain="The empty list is checked before indexing, so the helper returns {} instead of raising IndexError."),
    C("""
        Write `public_members(attrs)` that returns the **sorted** list of public members (`allUsers`,
        `allAuthenticatedUsers`) found in `attrs["member"]`, `attrs["members"]` and the bindings inside
        `attrs["policy_data"]` (a JSON string), each of which may be missing.
    """, '''import json

PUBLIC = {"allUsers", "allAuthenticatedUsers"}

def public_members(attrs):
    found = []
    if attrs.get("member"):
        found.append(attrs["member"])
    found += attrs.get("members") or []
    if attrs.get("policy_data"):
        for binding in json.loads(attrs["policy_data"]).get("bindings", []):
            found += binding.get("members", [])
    return sorted(PUBLIC & set(found))''',
      check="""
        import json
        assert public_members({"member": "allUsers"}) == ["allUsers"]
        assert public_members({"members": ["user:a@example.com", "allAuthenticatedUsers", "allUsers"]}) == ["allAuthenticatedUsers", "allUsers"]
        data = json.dumps({"bindings": [{"role": "r", "members": ["allUsers"]}, {"role": "s", "members": ["group:g@example.com"]}]})
        assert public_members({"policy_data": data}) == ["allUsers"]
        assert public_members({"member": "user:a@example.com"}) == [] and public_members({}) == []
      """,
      hints=["Collect every member into one list, then intersect with the public set.",
             'json.loads(attrs["policy_data"]).get("bindings", []) gives the bindings.',
             "return sorted(PUBLIC & set(found))"]),
    B("p4-gcp-storage"),
    B("p4-gcp-network", intro="Reuse `self.judge(...)` for the firewall; `first_block` twice for Cloud SQL."),
    B("p4-gcp-iam"),
], summary="""
    - Normalise several data shapes into one list, then apply the rule once.
    - Set intersection (`PUBLIC & set(found)`) answers "which of these appear?".
    - `str.partition("-")` parses `"22"` and `"8000-8090"` alike.
    - Guard nested `[0]` lookups with a helper that returns `{}` when the list is empty.
""")

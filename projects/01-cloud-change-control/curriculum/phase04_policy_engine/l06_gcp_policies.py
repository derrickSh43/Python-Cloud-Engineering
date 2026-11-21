from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l6", "Google Cloud security policies", [
    T("""
        **GCP IAM in three shapes**

        Google Cloud grants **roles** to **members** (`user:alice@example.com`, `group:ops@example.com`,
        `serviceAccount:...`). Terraform offers three resource styles for the same thing, and a policy must
        understand all of them:

        | resource | shape | behaviour |
        |---|---|---|
        | `*_iam_member` | `role`, `member` | adds one member to one role |
        | `*_iam_binding` | `role`, `members: [...]` | sets the full member list for one role |
        | `*_iam_policy` | `policy_data`: JSON string with `bindings: [{role, members}]` | replaces the whole policy |

        Two special members mean "the public": **`allUsers`** (anyone on the internet, no login) and
        **`allAuthenticatedUsers`** (anyone with *any* Google account - effectively also the public).
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
        **Buckets and uniform access**

        Cloud Storage buckets can control access with IAM alone (**uniform bucket-level access**) or also allow
        per-object ACLs. With per-object ACLs, any single object can be made public on its own, which is easy
        to miss. Google recommends `uniform_bucket_level_access = true` and
        `public_access_prevention = "enforced"`, which blocks public grants entirely. ChangeGate rates uniform
        access being off as MEDIUM, and notes whether public access prevention is enforced.
    """),
    T("""
        **Basic roles**

        `roles/owner` and `roles/editor` are GCP's **basic** (formerly "primitive") roles: they grant broad
        access to almost every service in a project. Granting them violates **least privilege** - give people
        and services only what their job needs, using predefined roles like `roles/storage.objectViewer`.
        Granting *any* role on a project, folder or organization to `allUsers` is CRITICAL.
    """),
    T("""
        **Firewalls and Cloud SQL**

        A `google_compute_firewall` has a `direction` (default `INGRESS`), `source_ranges`, and `allow` blocks,
        each with a `protocol` and optional `ports`. Protocol `all` - or `tcp`/`udp` with **no ports listed** -
        means every port. Ports may be single (`"22"`) or ranges (`"8000-8090"`). Disabled rules and egress
        rules are skipped.

        Cloud SQL instances nest their network settings two blocks deep:
        `settings[0].ip_configuration[0].authorized_networks`. An authorized network of `0.0.0.0/0` lets the
        whole internet attempt connections. Better: private IP and the Cloud SQL Auth Proxy.
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
    Q("A bucket grants `roles/storage.objectViewer` to `allAuthenticatedUsers`. Is that public?",
      "Effectively yes - anyone with any Google account can read it", "No - only users in your organization",
      "No - authenticated means approved by an admin", "Only if uniform access is off"),
    Q("What does a GCP firewall `allow` block of `{\"protocol\": \"tcp\"}` with no ports mean?",
      "All TCP ports", "No ports - the rule does nothing", "Only port 80", "Only well-known ports below 1024"),
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
    - GCP IAM resources: `*_iam_member` (member), `*_iam_binding` (members), `*_iam_policy` (policy_data JSON).
    - `allUsers` and `allAuthenticatedUsers` both mean public.
    - Buckets: prefer uniform bucket-level access + public access prevention "enforced".
    - Basic roles `roles/owner`/`roles/editor` break least privilege; any role to allUsers is CRITICAL.
    - Firewalls: `all`, or tcp/udp with no ports = every port; skip disabled/egress. Cloud SQL:
      `settings[0].ip_configuration[0].authorized_networks` containing 0.0.0.0/0 is public.
""")

from pce.lesson import T, Q, Lesson

LESSON = Lesson("p00l2", "What you'll build: Cloud ChangeGate", [
    T("""
        **The problem**

        Teams change cloud infrastructure with **Terraform**. Before applying a change, Terraform produces
        a **plan**: a list of resources it will create, update or delete. A single careless plan can open
        SSH to the whole internet, make a storage bucket public, or delete a production database.

        Code review helps, but reviewers get tired and plans get long. You'll build a tool that reads
        every plan automatically and enforces the rules before anything is applied.
    """),
    T("""
        **Cloud ChangeGate, step by step**

        1. **Parse** the Terraform plan (JSON) into Python objects.
        2. **Evaluate** each change against modular **security policies** for AWS and GCP.
        3. **Classify risk**: LOW, MEDIUM, HIGH or CRITICAL.
        4. **Decide**: allow it, require approval, or block it.
        5. **Verify approvals**: signed, tied to that exact plan, from authorised people, not expired.
        6. **Audit**: record every decision in a tamper-evident log.
        7. Run it all from a **command-line tool** that fits into a CI/CD pipeline.
    """),
    T("""
        **How you'll get there**

        - **Phase 1** - Python fundamentals with cloud-flavoured examples.
        - **Phase 2** - Data and files: reading real Terraform plan JSON.
        - **Phase 3** - Structure and testing: models, classes, packages and pytest.
        - **Phase 4** - The policy engine and risk classification.
        - **Phase 5** - Trust: hashing, signed approvals and the audit log.
        - **Phase 6** - Production: the CLI, reports, packaging and CI/CD.

        Everything runs on your machine against sample plans; no cloud account is needed. Connecting real
        AWS and GCP accounts is an optional final step once the tool is finished.
    """),
    Q("What does a Terraform plan describe?",
      "The changes Terraform will make to infrastructure if applied",
      "The bill for last month's cloud usage",
      "A list of every user in the cloud account",
      explain="A plan is a preview: create, update, replace or delete, resource by resource."),
    Q("A plan would delete a production database. What should ChangeGate do?",
      "Flag it as high risk and require approval (or block it)",
      "Apply it immediately - Terraform knows best",
      "Ignore it because deletes are always safe",
      explain="Destructive changes to stateful resources are exactly what change control exists for."),
], summary="""
    **Cloud ChangeGate** reads a Terraform plan and decides whether it can be applied.

    parse plan → evaluate policies (AWS + GCP) → classify risk → decide (allow / approval / block)
    → verify signed approvals → write a tamper-evident audit record → all from a CLI used in CI/CD.
""")

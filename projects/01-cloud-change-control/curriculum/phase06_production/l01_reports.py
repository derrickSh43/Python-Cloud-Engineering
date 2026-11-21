from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p06l1", "Reports for humans and machines", [
    T("""
        **One result, three audiences**

        - **People in a terminal** want aligned, scannable text.
        - **Other programs** (dashboards, bots, your own scripts) want JSON.
        - **Pull request reviewers** want Markdown - GitHub renders it as headings and tables in a comment or
          a job summary.

        ChangeGate keeps the evaluation separate from how it's shown: `report.py` has one function per
        format, all taking the same `Evaluation`, and a dict `RENDERERS` maps `"text"`, `"json"` and
        `"markdown"` to them. The CLI just picks one by name.
    """),
    T("""
        **Aligned text with format specs**

        Both `%`-formatting and f-strings can pad values to a width:

        ```
        "[%-8s]" % "HIGH"        # '[HIGH    ]'  - left-aligned in 8
        "[%8s]" % "HIGH"         # '[    HIGH]'  - right-aligned
        f"[{'HIGH':<8}]"         # '[HIGH    ]'
        f"{3:>4}"                # '   3'
        ```

        Building a report as a **list of lines** and joining with `"\\n"` at the end is clearer than adding
        strings together, and makes it easy to add sections conditionally.
    """),
    Ex("""
        findings = [("CRITICAL", "AWS-IAM-WILDCARD", "aws_iam_policy.deploy"),
                    ("HIGH", "AWS-SG-OPEN-INGRESS", "aws_security_group.admin")]
        lines = ["Cloud ChangeGate", "  risk:      CRITICAL", ""]
        if findings:
            lines.append("Findings (%d):" % len(findings))
            for level, policy, address in findings:
                lines.append("  [%-8s] %s  %s" % (level, policy, address))
        print("\\n".join(lines))
    """),
    T("""
        **JSON reports**

        For JSON, reuse the `to_dict()` methods you wrote in Phase 3, add any extra fields, and dump with
        `indent=2`. Ending output with a newline is a small courtesy that keeps terminals and `diff` tidy.
    """),
    T("""
        **Markdown tables and escaping**

        ```
        | Severity | Policy | Resource |
        |---|---|---|
        | HIGH | `AWS-SG-OPEN-INGRESS` | `aws_security_group.admin` |
        ```

        A `|` inside a cell would split it into two columns, so free text (messages, remediation) must
        escape it as `\\|`. Code-like values go in backticks so they render in monospace.
    """),
    Ex("""
        def md(text):
            return text.replace("|", "\\\\|")

        rows = [("HIGH", "AWS-SG-OPEN-INGRESS", "port 22 | 3389 open")]
        lines = ["| Severity | Policy | Problem |", "|---|---|---|"]
        for level, policy, message in rows:
            lines.append("| %s | `%s` | %s |" % (level, policy, md(message)))
        print("\\n".join(lines))
    """),
    Q("Why have a `RENDERERS` dict instead of an if/elif chain in the CLI?",
      "Adding a format means adding one entry, and the CLI's --format choices come straight from its keys",
      "Dicts are faster than if statements", "argparse requires a dict", "JSON must be produced by a dict"),
    C("""
        Write `render(rows, fmt)` where `rows` is a list of `(name, count)` tuples and `fmt` is `"text"`,
        `"json"` or `"markdown"`:

        - text: one line per row, the name left-aligned in 10 characters then the count: `"create    2"`
        - json: `json.dumps({name: count, ...})`
        - markdown: a header `| Action | Count |`, the separator `|---|---|`, then `| create | 2 |` rows

        Join lines with `"\\n"`. Use a dict of small functions to choose the format.
    """, '''import json

def _text(rows):
    return "\\n".join("%-10s%d" % (name, count) for name, count in rows)

def _json(rows):
    return json.dumps(dict(rows))

def _markdown(rows):
    return "\\n".join(["| Action | Count |", "|---|---|"] + ["| %s | %d |" % (n, c) for n, c in rows])

RENDERERS = {"text": _text, "json": _json, "markdown": _markdown}

def render(rows, fmt):
    return RENDERERS[fmt](rows)''',
      check="""
        import json as _j
        rows = [("create", 2), ("delete", 1)]
        assert render(rows, "text") == "create    2\\ndelete    1", repr(render(rows, "text"))
        assert _j.loads(render(rows, "json")) == {"create": 2, "delete": 1}
        assert render(rows, "markdown") == "| Action | Count |\\n|---|---|\\n| create | 2 |\\n| delete | 1 |", repr(render(rows, "markdown"))
      """,
      require=["{"],
      hints=['"%-10s%d" % (name, count) pads the name to 10 characters.',
             "dict(rows) turns a list of pairs into a dict for json.dumps.",
             'RENDERERS = {"text": _text, "json": _json, "markdown": _markdown} and return RENDERERS[fmt](rows)']),
    B("p6-report-text"),
    B("p6-report-formats"),
], summary="""
    - Separate results from presentation: one renderer per format, chosen via a `RENDERERS` dict.
    - Padding: `"%-8s" % x`, `f"{x:<8}"`, `f"{n:>4}"`. Build reports as a list of lines, `"\\n".join(lines)`.
    - JSON: `to_dict()` + extra keys, `json.dumps(data, indent=2) + "\\n"`.
    - Markdown tables: header, `|---|` separator, rows; escape `|` in free text; backticks for code values.
""")

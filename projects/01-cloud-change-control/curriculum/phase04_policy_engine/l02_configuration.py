from pce.lesson import T, Ex, Q, P, C, B, Lesson

TEAM_TOML = '''[risk]
approval_at = "medium"
block_at = "critical"
destructive_escalation_threshold = 5

[approvals]
approvers = ["alice", "bob"]
key_env = "CHANGEGATE_HMAC_KEY"
'''

LESSON = Lesson("p04l2", "Configuration without hard-coding", [
    T("""
        **Why configuration matters**

        Every team has different rules: who may approve, which tags are required, which ports are sensitive,
        how risky is too risky. If those choices are written in code, every team needs its own copy of the
        code. Instead, ChangeGate reads them from a **config file**, and reads anything secret or
        environment-specific from **environment variables**:

        | what | where | in git? |
        |---|---|---|
        | thresholds, approvers, required tags | `changegate.toml` | no (an `.example` is) |
        | which config file | `--config` or `$CHANGEGATE_CONFIG` | - |
        | the approval signing key | an env var named in the config | **never** |

        This is the same discipline you'll apply to cloud credentials and account IDs at the very end.
    """),
    T("""
        **TOML and tomllib**

        TOML is a simple config format with sections (`[risk]`), keys, strings, numbers, booleans and lists.
        Python 3.11+ reads it with the built-in `tomllib` - note it needs the file opened in **binary** mode:

        ```
        import tomllib
        with open("changegate.toml", "rb") as f:
            data = tomllib.load(f)        # a dict of dicts
        data["risk"]["approval_at"]       # "medium"
        ```

        `with open(...) as f:` opens a file and **guarantees** it's closed afterwards, even if an error
        happens. `tomllib.loads(text)` parses a string instead.
    """),
    Ex("""
        import tomllib
        with open("changegate.toml", "rb") as f:
            data = tomllib.load(f)
        print(data)
        print(data["approvals"]["approvers"], type(data["risk"]["destructive_escalation_threshold"]))
    """, files={"changegate.toml": TEAM_TOML}),
    T("""
        **Fail loudly on typos**

        Suppose someone writes `aproval_at = "critical"` (a typo). A lenient loader ignores the unknown key,
        quietly uses the default, and the team thinks they changed a rule when they didn't. For a security
        tool that's dangerous. ChangeGate **rejects unknown keys** with a message listing them:

        ```
        unknown = set(data) - allowed
        if unknown:
            raise ConfigError("unknown setting(s) in [risk]: " + ", ".join(sorted(unknown)))
        ```

        It also checks every value's type and range, so mistakes show up when the config is loaded, not
        halfway through a deployment.
    """),
    T("""
        **The bool-is-an-int trap**

        In Python, `True` and `False` are integers: `isinstance(True, int)` is `True` and `True + 1 == 2`.
        So a check like "must be a whole number >= 0" silently accepts `threshold = true`. Exclude bools
        explicitly:

        ```
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ConfigError("must be a whole number >= 0")
        ```
    """),
    P("""
        for value in (3, True, 2.5, "4"):
            print(value, isinstance(value, int), isinstance(value, int) and not isinstance(value, bool))
    """),
    T("""
        **Environment variables**

        `os.environ` is a dict-like view of the environment. Read with `os.environ.get("NAME")` (None if
        unset). For testability, functions can accept an `environ` argument that **defaults** to
        `os.environ` - tests then pass a plain dict instead of changing the real environment:

        ```
        def resolve_path(explicit=None, environ=None):
            environ = os.environ if environ is None else environ
            ...
        ```

        Why `environ is None` and not `environ or os.environ`? Because an empty dict `{}` is falsy - a test
        passing `{}` to mean "no variables set" would get the real environment instead.
    """),
    Ex("""
        import os
        def config_source(environ=None):
            environ = os.environ if environ is None else environ
            return environ.get("CHANGEGATE_CONFIG", "(not set)")

        print(config_source({"CHANGEGATE_CONFIG": "team.toml"}))
        print(config_source({}))
    """),
    Q("Why does tomllib.load need `open(path, \"rb\")`?",
      "tomllib reads bytes and handles the decoding itself", "TOML files are binary", "\"rb\" means read-backup",
      "It doesn't; \"r\" works the same"),
    C("""
        Write `load_ports(path)` that reads a TOML file and returns the list under `[network] sensitive_ports`.

        - Missing file → `ConfigError("config file not found: <path>")`
        - Missing `[network]` table or key → return the default `[22, 3389]`
        - If the value isn't a list of ints (bools don't count), raise `ConfigError("sensitive_ports must be a list of port numbers")`

        Define `ConfigError` yourself. `ports.toml` and `bad.toml` exist in your folder.
    """, '''import tomllib

class ConfigError(Exception):
    pass

def load_ports(path):
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError("config file not found: %s" % path) from None
    ports = data.get("network", {}).get("sensitive_ports", [22, 3389])
    if not isinstance(ports, list) or not all(isinstance(p, int) and not isinstance(p, bool) for p in ports):
        raise ConfigError("sensitive_ports must be a list of port numbers")
    return ports''',
      files={"ports.toml": "[network]\nsensitive_ports = [22, 5432]\n", "bad.toml": "[network]\nsensitive_ports = [22, true]\n",
             "empty.toml": "[risk]\napproval_at = \"high\"\n"},
      check="""
        assert load_ports("ports.toml") == [22, 5432]
        assert load_ports("empty.toml") == [22, 3389], "missing [network] should give the default"
        for name, text in (("bad.toml", "list of port numbers"), ("absent.toml", "not found")):
            try:
                load_ports(name)
            except ConfigError as e:
                assert text in str(e), "%s: got %r" % (name, str(e))
            else:
                raise AssertionError("load_ports(%r) should raise ConfigError" % name)
      """,
      require=["tomllib", "class ConfigError"],
      hints=['with open(path, "rb") as f: data = tomllib.load(f) - inside try/except FileNotFoundError.',
             'data.get("network", {}).get("sensitive_ports", [22, 3389]) handles both missing levels.',
             "all(isinstance(p, int) and not isinstance(p, bool) for p in ports)"]),
    B("p4-config-validation", intro="The building blocks of ChangeGate's strict config loader, in `config.py`."),
    B("p4-config-risk", intro="One full section: `[risk]`. The other sections follow the same pattern and are written for you."),
    B("p4-config-load", intro="Finding and loading the file: --config, then $CHANGEGATE_CONFIG, then ./changegate.toml."),
], summary="""
    - Team choices in `changegate.toml`; secrets and environment-specific values in environment variables.
    - `with open(path, "rb") as f: data = tomllib.load(f)` (binary mode). `with` always closes the file.
    - Reject unknown keys (`set(data) - allowed`) and validate types so typos fail loudly.
    - `True` is an int: exclude bools with `isinstance(v, bool)`.
    - `environ = os.environ if environ is None else environ` - testable, and `{}` still means "empty".
""")

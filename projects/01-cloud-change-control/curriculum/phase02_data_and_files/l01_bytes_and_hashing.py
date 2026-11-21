from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p02l1", "Bytes, modules and fingerprints", [
    T("""
        **Importing modules**

        Python ships with a large **standard library** of modules. Bring one in with `import`:

        ```
        import hashlib
        import json
        from pathlib import Path      # import one name from a module
        ```

        After `import hashlib`, use its contents with a dot: `hashlib.sha256(...)`. ChangeGate uses only
        the standard library - nothing to install.
    """),
    T("""
        **Text and bytes**

        Computers store everything as **bytes** - numbers from 0 to 255. A `str` is text (characters);
        `bytes` is raw data. You convert between them with an **encoding**, almost always UTF-8:

        ```
        text = "café"
        data = text.encode("utf-8")    # b'caf\\xc3\\xa9'  - 5 bytes for 4 characters
        back = data.decode("utf-8")    # "café"
        ```

        A bytes literal is written with a `b` prefix: `b"plan"`. Files on disk are bytes; reading them as
        text means decoding.
    """),
    Ex("""
        text = "café"
        data = text.encode("utf-8")
        print(data, len(text), "characters", len(data), "bytes")
        print(data.decode("utf-8"))
        print(type(text), type(data))
    """),
    Ex("""
        b"\\xff\\xfe".decode("utf-8")
    """, note="Not every sequence of bytes is valid UTF-8. A UnicodeDecodeError usually means you're reading "
              "a binary file as text.", error_ok=True),
    Q("Why might `\"abc\" == b\"abc\"` be False?",
      "A str and bytes are different types, even with the same characters",
      "Because of the b, Python reverses the bytes", "They're equal; it's True", "Strings are always longer"),
    T("""
        **Fingerprints: SHA-256**

        A **hash function** turns any amount of data into a short, fixed-size fingerprint. SHA-256 gives
        64 hex characters. Change one byte of the input and the fingerprint changes completely; you can't
        work backwards from the fingerprint to the data.

        ChangeGate fingerprints each plan. An approval says "I approve the plan whose SHA-256 is
        `dc1f...`" - so if anyone edits the plan afterwards, the approval no longer matches.

        ```
        import hashlib
        hashlib.sha256(b"some bytes").hexdigest()   # 64 hex characters
        ```

        Hash functions take **bytes**, not text - another reason the difference matters.
    """),
    Ex("""
        import hashlib
        print(hashlib.sha256(b"plan v1").hexdigest())
        print(hashlib.sha256(b"plan v2").hexdigest())
        print(len(hashlib.sha256(b"").hexdigest()))
    """),
    P("""
        import hashlib
        a = hashlib.sha256("approve".encode("utf-8")).hexdigest()
        b = hashlib.sha256(b"approve").hexdigest()
        print(a == b)
    """, explain="Encoding the text to UTF-8 gives exactly the bytes b'approve', so the fingerprints match."),
    C("""
        Print the first 12 characters of the SHA-256 hex digest of the bytes `b"terraform"`.
        (Short prefixes like this are handy in file names and logs.)
    """, 'import hashlib\nprint(hashlib.sha256(b"terraform").hexdigest()[:12])',
      require=["hashlib"],
      hints=["hashlib.sha256(b\"terraform\").hexdigest() gives the full 64-character string.",
             "Slice the first 12 characters with [:12]."]),
    T("""
        **Your workspace**

        Time to build. Your copy of ChangeGate lives in `projects/01-cloud-change-control/workspace/`.
        Every function you'll write is already there, with its name, parameters and description, but its
        body is just:

        ```
        raise NotImplementedError("TODO(p2-plan-digest): plan_digest")
        ```

        You replace that line with real code, in **your own editor** (VS Code is a great free choice;
        Notepad works too). Then run the exercise's checks - press **c** here, or run
        `python learn.py check` in a terminal. Read each failing check: it says what was expected.
    """),
    B("p2-plan-digest", intro="Your first piece of ChangeGate. Open the file shown below, find `plan_digest`, "
                             "and replace the `raise` line."),
], summary="""
    - `import module` / `from module import name`. ChangeGate uses only the standard library.
    - `str` is text, `bytes` is raw data. `text.encode("utf-8")` → bytes; `data.decode("utf-8")` → text.
      Bytes literals: `b"..."`. Bad bytes raise UnicodeDecodeError.
    - `hashlib.sha256(data).hexdigest()` - 64 hex chars; any change to the bytes changes it completely.
    - Build exercises: edit your workspace file in your editor, then check (`c` or `python learn.py check`).
""")

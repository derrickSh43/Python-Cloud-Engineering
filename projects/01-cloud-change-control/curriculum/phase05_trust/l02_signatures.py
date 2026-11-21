from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l2", "Secrets and signatures", [
    T("""
        **A hash isn't a signature**

        A SHA-256 fingerprint proves data hasn't changed - but anyone can compute one. If an approval file
        just contained "alice approves plan dc1f..." plus its hash, an attacker could write "mallory approves
        plan dc1f..." and compute a fresh hash.

        A **signature** needs a secret. **HMAC** (hash-based message authentication code) mixes a secret
        key into the hash. Without the key you can't produce a valid HMAC, and changing even one byte of the
        message makes the old one invalid.

        ```
        import hmac, hashlib
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        ```

        `key` and `message` are both **bytes**.
    """),
    Ex("""
        import hashlib
        import hmac
        key = b"k" * 32
        message = b'{"approver":"alice","plan":"dc1f"}'
        good = hmac.new(key, message, hashlib.sha256).hexdigest()
        print(good)
        print(hmac.new(b"wrong-key-wrong-key-wrong-key-xx", message, hashlib.sha256).hexdigest() == good)
        print(hmac.new(key, message.replace(b"alice", b"mallo"), hashlib.sha256).hexdigest() == good)
    """),
    T("""
        **Where the key lives**

        A signing key is a **secret**. It must never be written in code, config files, or git. ChangeGate
        reads it from an environment variable whose *name* is configurable (`[approvals] key_env`), so CI can
        inject it from its secret store. Generate a strong random key with the `secrets` module:

        ```
        python -c "import secrets; print(secrets.token_hex(32))"
        ```

        `secrets` is designed for security; the `random` module is **not** - its output can be predicted.
        ChangeGate also refuses keys shorter than 32 bytes.
    """),
    Ex("""
        import secrets
        key = secrets.token_hex(32)
        print(len(key), "hex characters =", len(key.encode()), "bytes when encoded")
        print(key[:8] + "...")
    """, note="Every run prints a different key. Never print a real one in full - logs are not secret."),
    T("""
        **Timing attacks and compare_digest**

        Comparing two strings with `==` stops at the **first** different character. That's measurably faster
        when the first character is wrong than when only the last one is. An attacker who can submit many
        guesses and time the responses can recover a valid signature one character at a time.

        `hmac.compare_digest(a, b)` takes the same time no matter where the strings differ. **Always** use it
        to compare signatures, tokens and other secrets.
    """),
    P("""
        import hmac
        print(hmac.compare_digest("abc123", "abc123"))
        print(hmac.compare_digest("abc123", "abc124"))
    """),
    T("""
        **What gets signed**

        ChangeGate signs the approval's **payload** - every field except the signature itself - turned into
        canonical JSON bytes with the `canonical_bytes` helper you wrote in Phase 2. Same data, same bytes,
        same signature, on any machine.

        Approvals are frozen dataclasses, so "adding" the signature means making a modified copy with
        `dataclasses.replace(approval, signature=...)`.

        Creating an approval also validates its inputs. A plan hash must be exactly 64 lowercase hex
        characters, which a **regular expression** checks neatly:

        ```
        import re
        re.fullmatch(r"[0-9a-f]{64}", text)     # a match object, or None
        ```

        `[0-9a-f]` means one character from that set, `{64}` means exactly 64 of them, and `fullmatch`
        requires the whole string to match.
    """),
    Ex("""
        import re
        for text in ["a" * 64, "A" * 64, "a" * 63, "g" * 64]:
            print(len(text), bool(re.fullmatch(r"[0-9a-f]{64}", text)))
    """),
    Q("Why use `hmac.compare_digest` instead of `==` for signatures?",
      "It takes the same time wherever the strings differ, so timing reveals nothing",
      "It's faster", "== doesn't work on hex strings", "It also checks the key"),
    Q("Where should ChangeGate's signing key be stored?",
      "In a secret store, injected as an environment variable", "In changegate.toml", "In the source code as a constant",
      "In the approval file next to the signature"),
    C("""
        Write `sign(message, key)` returning the HMAC-SHA256 hex digest of the bytes `message` with the bytes
        `key`, and `verify(message, key, signature)` returning whether `signature` matches, using
        `hmac.compare_digest`.
    """, 'import hashlib\nimport hmac\n\ndef sign(message, key):\n    return hmac.new(key, message, hashlib.sha256).hexdigest()\n\ndef verify(message, key, signature):\n    return hmac.compare_digest(signature, sign(message, key))',
      check="""
        import hashlib, hmac as _h
        k = b"k" * 32
        assert sign(b"hello", k) == _h.new(k, b"hello", hashlib.sha256).hexdigest()
        s = sign(b"approve plan", k)
        assert verify(b"approve plan", k, s) is True
        assert verify(b"approve plan!", k, s) is False
        assert verify(b"approve plan", b"x" * 32, s) is False
      """,
      require=["hmac.new", "compare_digest"],
      hints=["hmac.new(key, message, hashlib.sha256).hexdigest()",
             "verify computes a fresh signature and compares with hmac.compare_digest(signature, fresh)."]),
    B("p5-signatures"),
    B("p5-create-approval"),
], summary="""
    - Hashes prove integrity; **HMAC** (`hmac.new(key, msg, hashlib.sha256).hexdigest()`) proves the signer had the key.
    - Keys are secrets: environment variable / secret store, never code or git. Generate with `secrets.token_hex(32)`.
    - Compare secrets with `hmac.compare_digest`, never `==` (timing attacks).
    - Sign canonical bytes of the payload; add the signature with `dataclasses.replace`.
    - `re.fullmatch(r"[0-9a-f]{64}", text)` validates a whole string against a pattern.
""")

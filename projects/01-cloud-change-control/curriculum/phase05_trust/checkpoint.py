from pce.lesson import Q, C, Checkpoint

CHECKPOINT = Checkpoint("p05cp", "A signed, expiring token", """
    Combine time, canonical JSON and HMAC: build and verify a tiny signed token - the same ingredients
    as a ChangeGate approval.
""", [
    Q("What does this print?", "False", "True", "An error",
      code="""
        import hashlib
        a = hashlib.sha256(b'{"bucket": "logs"}').hexdigest()
        b = hashlib.sha256(b'{"bucket": "logs2"}').hexdigest()
        print(a == b)
      """, explain="Any change to the bytes gives a completely different SHA-256 digest."),
    Q("What does this print?", "True", "False", "An error",
      code="""
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        issued = now + timedelta(minutes=3)
        print(issued <= now + timedelta(minutes=5))
      """, explain="3 minutes ahead is inside the 5-minute tolerance."),
    C("""
        Write two functions:

        - `make_token(subject, key, now, ttl_minutes)` returns a dict
          `{"subject": ..., "expires": <ISO UTC with Z, to seconds>, "sig": <HMAC-SHA256 hex>}` where the
          signature covers the canonical JSON (sorted keys, separators `","` and `":"`) of
          `{"subject": ..., "expires": ...}`.
        - `check_token(token, key, now)` returns `"ok"`, `"bad signature"` or `"expired"` (signature checked
          first, with `hmac.compare_digest`; expired when `now >=` the expiry).
    """, '''import hashlib, hmac, json
from datetime import datetime, timedelta, timezone

def _payload(subject, expires):
    return json.dumps({"subject": subject, "expires": expires}, sort_keys=True, separators=(",", ":")).encode()

def make_token(subject, key, now, ttl_minutes):
    expires = (now + timedelta(minutes=ttl_minutes)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    sig = hmac.new(key, _payload(subject, expires), hashlib.sha256).hexdigest()
    return {"subject": subject, "expires": expires, "sig": sig}

def check_token(token, key, now):
    expected = hmac.new(key, _payload(token["subject"], token["expires"]), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token["sig"], expected):
        return "bad signature"
    if now >= datetime.fromisoformat(token["expires"].replace("Z", "+00:00")):
        return "expired"
    return "ok"''',
      check="""
        import hashlib, hmac as _h, json as _j
        from datetime import datetime, timedelta, timezone
        key = b"k" * 32
        now = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        t = make_token("plan-dc1f", key, now, 30)
        assert t["expires"] == "2026-03-01T12:30:00Z", "got %r" % t["expires"]
        expected = _h.new(key, _j.dumps({"subject": "plan-dc1f", "expires": t["expires"]}, sort_keys=True, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
        assert t["sig"] == expected, "sign the canonical JSON of subject and expires"
        assert check_token(t, key, now) == "ok"
        assert check_token(t, key, now + timedelta(minutes=30)) == "expired"
        assert check_token(dict(t, subject="plan-evil"), key, now) == "bad signature"
        assert check_token(dict(t, expires="2027-01-01T00:00:00Z"), key, now) == "bad signature", "edits to the expiry must break the signature"
        assert check_token(t, b"z" * 32, now) == "bad signature"
      """,
      require=["hmac", "compare_digest"],
      hints=["Write a helper that builds the canonical payload bytes from subject and expires; use it in both functions.",
             '(now + timedelta(minutes=ttl_minutes)).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")',
             "In check_token, verify the signature first; then parse the expiry with fromisoformat (replacing Z)."]),
])

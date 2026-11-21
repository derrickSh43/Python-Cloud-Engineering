from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l1", "Time done right", [
    T("""
        **Why time is tricky**

        An approval "valid for 24 hours" needs an exact moment it was issued and an exact moment it
        expires. "14:00" means nothing without a timezone: 14:00 in London and 14:00 in Sydney are eleven
        hours apart. Engineers who approve from different countries, CI runners in UTC, laptops in local time -
        the only safe rule is:

        **Store and compare times in UTC, and always attach the timezone.**
    """),
    T("""
        **Naive and aware datetimes**

        `datetime.now()` returns a **naive** datetime - no timezone attached, just "the local clock says...".
        `datetime.now(timezone.utc)` returns an **aware** one. Python refuses to compare naive and aware
        datetimes, which is a good thing.

        ```
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=24)
        expires > now          # True
        now.tzinfo             # datetime.timezone.utc
        ```

        `timedelta` represents a duration; adding one to a datetime gives a new datetime.
    """),
    Ex("""
        from datetime import datetime, timedelta, timezone
        issued = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        expires = issued + timedelta(hours=24)
        print(issued)
        print(expires)
        print(expires - issued, (expires - issued).total_seconds() / 3600, "hours")
        print(issued.tzinfo is not None)
    """),
    Ex("""
        from datetime import datetime, timezone
        naive = datetime(2026, 3, 1, 12, 0)
        aware = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        print(naive < aware)
    """, note="Mixing naive and aware datetimes is a TypeError - Python won't guess the timezone.", error_ok=True),
    T("""
        **ISO-8601 text**

        To store a time in JSON, write it as **ISO-8601** text: `2026-03-01T12:00:00+00:00`. UTC is
        often written with a `Z` ("Zulu") suffix instead: `2026-03-01T12:00:00Z`.

        - `moment.isoformat(timespec="seconds")` - text, to the second
        - `moment.astimezone(timezone.utc)` - the same instant expressed in UTC
        - `datetime.fromisoformat(text)` - parse it back (to be safe across Python versions, replace a trailing
          `Z` with `+00:00` first)
    """),
    Ex("""
        from datetime import datetime, timedelta, timezone
        plus_two = timezone(timedelta(hours=2))
        local = datetime(2026, 3, 1, 14, 0, 30, 123456, tzinfo=plus_two)
        utc = local.astimezone(timezone.utc)
        text = utc.isoformat(timespec="seconds").replace("+00:00", "Z")
        print(text)
        back = datetime.fromisoformat(text.replace("Z", "+00:00"))
        print(back == local, back.tzinfo)
    """, note="14:00:30 at UTC+2 is 12:00:30 UTC - the same instant, so `back == local` is True."),
    P("""
        from datetime import datetime, timedelta, timezone
        start = datetime(2026, 1, 31, 23, 30, tzinfo=timezone.utc)
        print((start + timedelta(minutes=45)).isoformat())
    """, explain="timedelta handles crossing midnight and month ends for you."),
    Q("Which call gives the current time with a timezone attached?",
      "datetime.now(timezone.utc)", "datetime.now()", "datetime.utcnow()", "time.time()",
      explain="datetime.utcnow() returns a NAIVE datetime holding UTC values - easy to misuse, and deprecated."),
    C("""
        Write `is_expired(expires_text, now)` where `expires_text` is ISO-8601 (possibly ending in `Z`) and
        `now` is an aware datetime. Return True if `now` is at or after the expiry. If the text has no
        timezone, raise `ValueError("timestamp must include a timezone")`.
    """, 'from datetime import datetime\n\ndef is_expired(expires_text, now):\n    expires = datetime.fromisoformat(expires_text.replace("Z", "+00:00"))\n    if expires.tzinfo is None:\n        raise ValueError("timestamp must include a timezone")\n    return now >= expires',
      check="""
        from datetime import datetime, timezone
        now = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
        assert is_expired("2026-03-01T11:59:59Z", now) is True
        assert is_expired("2026-03-01T12:00:00Z", now) is True, "exactly at the expiry counts as expired"
        assert is_expired("2026-03-01T14:00:01+02:00", now) is False, "14:00:01 at +02:00 is 12:00:01 UTC"
        try:
            is_expired("2026-03-01T12:00:00", now)
        except ValueError as e:
            assert "timezone" in str(e)
        else:
            raise AssertionError("a timestamp without a timezone should raise ValueError")
      """,
      require=["fromisoformat"],
      hints=['datetime.fromisoformat(expires_text.replace("Z", "+00:00")) parses it.',
             "Check `.tzinfo is None` before comparing.",
             "return now >= expires"]),
    B("p5-approval-format", intro="Approvals are stored as JSON with UTC timestamps. These functions convert in both "
                                 "directions and refuse anything ambiguous."),
], summary="""
    - Store and compare times in UTC, always timezone-aware: `datetime.now(timezone.utc)`.
    - Naive vs aware can't be compared (TypeError). `timedelta(hours=24)` is a duration.
    - ISO-8601: `moment.astimezone(timezone.utc).isoformat(timespec="seconds")`, `Z` = UTC;
      parse with `datetime.fromisoformat(text.replace("Z", "+00:00"))` and check `.tzinfo`.
""")

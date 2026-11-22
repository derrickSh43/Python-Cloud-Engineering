from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p05l5", "A tamper-evident audit log", [
    T("""
        **Why an audit log**

        After an incident, someone will ask: *who approved this, when, and what did ChangeGate decide?* An
        audit log answers that. But a plain log file can be edited by anyone with access - including someone
        covering their tracks. ChangeGate's log is **tamper-evident**: you can't change history without it
        showing.
    """),
    T("""
        **JSON Lines**

        The log is a **JSON Lines** file (`.jsonl`): one complete JSON object per line. Appending a record is
        just writing one more line, and a reader can process it line by line. Each record has a sequence
        number, a UTC timestamp, an event name (`evaluate`, `approve`, `verify`) and event data.
    """),
    T("""
        **Hash chains**

        Each record stores the **hash of the previous record**, and its own hash covers everything in it
        (including that previous hash):

        ```
        record 1: {seq: 1, ..., prev_hash: 000...000, hash: H1}
        record 2: {seq: 2, ..., prev_hash: H1,        hash: H2}
        record 3: {seq: 3, ..., prev_hash: H2,        hash: H3}
        ```

        - **Edit** record 2 → its recomputed hash no longer matches `hash`.
        - Edit it *and* fix its hash → record 3's `prev_hash` no longer matches.
        - **Delete** or **reorder** records → sequence numbers and links break.

        To rewrite history undetected you'd have to recompute every hash after the change - and if the
        latest hash (the **head**) has been recorded somewhere else, even that is caught. This is the same
        idea behind git commits and blockchains. The first record links to a "genesis" hash of 64 zeros.
    """),
    Ex("""
        import hashlib, json

        def h(record):
            body = {k: v for k, v in record.items() if k != "hash"}
            return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

        chain, prev = [], "0" * 64
        for seq, event in enumerate(["evaluate", "approve", "verify"], 1):
            record = {"seq": seq, "event": event, "prev_hash": prev}
            record["hash"] = h(record)
            chain.append(record)
            prev = record["hash"]

        for r in chain:
            print(r["seq"], r["event"], r["prev_hash"][:8], "->", r["hash"][:8])

        chain[1]["event"] = "nothing happened"
        print("record 2 intact?", h(chain[1]) == chain[1]["hash"])
    """),
    T("""
        **Append-only writes**

        Opening a file with `os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)` asks the operating
        system to put **every write at the end of the file**, even if two processes write at once - existing
        records are never overwritten. `|` combines the flags; `0o640` sets file permissions on Unix
        (owner read/write, group read). Write bytes with `os.write(fd, data)` and always `os.close(fd)` in a
        `finally` block.
    """),
    Q("What does this print?", "[2]", "[]", "[1, 2]", "An error",
      code="""
        chain = [{"seq": 1, "prev_hash": "000", "hash": "aaa"},
                 {"seq": 2, "prev_hash": "zzz", "hash": "bbb"}]
        prev = "000"
        broken = []
        for record in chain:
            if record["prev_hash"] != prev:
                broken.append(record["seq"])
            prev = record["hash"]
        print(broken)
      """, explain="Each record's prev_hash is compared with the previous record's hash; record 2 points at the wrong one."),
    Q("What does this print?", "3 1", "1 3", "3 3", "An error",
      code="""
        import json
        lines = ['{"seq": 1}', '{"seq": 2}', '{"seq": 3}']
        records = [json.loads(line) for line in lines]
        print(len(records), records[0]["seq"])
      """, explain="JSON Lines: one json.loads per line gives one dict per record."),
    C("""
        Write `verify_chain(records)` that checks a list of dicts with keys `seq`, `prev_hash` and `hash`,
        where each record's `hash` must equal `digest(record)` (provided below - it hashes everything except
        `hash`). Return a list of problem strings - empty if the chain is intact:

        - `"record N: bad sequence"` if `seq` isn't N (counting from 1)
        - `"record N: chain broken"` if `prev_hash` isn't the previous record's hash (`"0" * 64` for the first)
        - `"record N: modified"` if `hash` doesn't match `digest(record)`
    """, '''import hashlib, json

def digest(record):
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

def verify_chain(records):
    problems, prev = [], "0" * 64
    for n, record in enumerate(records, 1):
        if record.get("seq") != n:
            problems.append("record %d: bad sequence" % n)
        if record.get("prev_hash") != prev:
            problems.append("record %d: chain broken" % n)
        if record.get("hash") != digest(record):
            problems.append("record %d: modified" % n)
        prev = record.get("hash")
    return problems''',
      starter='''import hashlib, json

def digest(record):
    body = {k: v for k, v in record.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()''',
      check="""
        def build(n):
            out, prev = [], "0" * 64
            for i in range(1, n + 1):
                r = {"seq": i, "data": i, "prev_hash": prev}
                r["hash"] = digest(r)
                out.append(r)
                prev = r["hash"]
            return out
        good = build(3)
        assert verify_chain(good) == [], "an intact chain has no problems, got %r" % (verify_chain(good),)
        edited = build(3); edited[1]["data"] = 99
        assert verify_chain(edited) == ["record 2: modified"], verify_chain(edited)
        dropped = build(3); del dropped[1]
        assert "record 2: bad sequence" in verify_chain(dropped) and "record 2: chain broken" in verify_chain(dropped)
        assert verify_chain([]) == []
      """,
      require=["def verify_chain"],
      hints=["Keep `prev` starting at '0' * 64 and update it to each record's hash as you go.",
             "Three independent `if` checks per record.",
             'if record.get("prev_hash") != prev:\n    problems.append("record %d: chain broken" % n)']),
    B("p5-audit-append"),
    B("p5-audit-verify"),
], summary="""
    - Audit log = JSON Lines; each record: seq, UTC timestamp, event, data, prev_hash, hash.
    - Hash chain: each hash covers the record incl. prev_hash. Edits, deletions and reordering break it;
      genesis hash = 64 zeros.
    - Append-only: `os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)`, `os.write`, close in `finally`.
""")

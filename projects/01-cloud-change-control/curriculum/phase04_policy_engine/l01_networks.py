from pce.lesson import T, Ex, Q, P, C, B, Lesson

LESSON = Lesson("p04l1", "IP ranges and the whole internet", [
    T("""
        **CIDR notation**

        Firewalls describe sources as **CIDR ranges**: an address and a prefix length, like `10.0.0.0/8`.
        The prefix says how many leading bits are fixed:

        | CIDR | addresses | meaning |
        |---|---|---|
        | `203.0.113.7/32` | 1 | one host |
        | `10.0.1.0/24` | 256 | a typical subnet |
        | `10.0.0.0/8` | 16.7 million | a large private network |
        | `0.0.0.0/0` | all of IPv4 | **the entire internet** |
        | `::/0` | all of IPv6 | **the entire IPv6 internet** |

        A prefix length of **0** fixes no bits at all - every address matches. That's what "open to the
        world" means, and it's the single most common way cloud resources get exposed.
    """),
    T("""
        **The ipaddress module**

        Comparing strings (`cidr == "0.0.0.0/0"`) misses sloppy but equivalent forms like `" 0.0.0.0/0 "`
        or `"1.2.3.4/0"`. The standard `ipaddress` module understands networks properly:

        ```
        import ipaddress
        net = ipaddress.ip_network("10.0.1.0/24")
        net.prefixlen          # 24
        net.num_addresses      # 256
        ```

        `ip_network` is strict by default: `"1.2.3.4/0"` has host bits set and raises ValueError. Pass
        `strict=False` to accept it (it becomes `0.0.0.0/0`). Invalid text always raises `ValueError`.
    """),
    Ex("""
        import ipaddress
        for text in ["10.0.1.0/24", "0.0.0.0/0", "::/0", "1.2.3.4/0", "203.0.113.7/32"]:
            net = ipaddress.ip_network(text, strict=False)
            print(f"{text:16} prefix={net.prefixlen:<3} addresses={net.num_addresses}")
    """, note="`{text:16}` pads to 16 characters; `{n:<3}` left-aligns in 3. Handy for tables."),
    Ex("""
        import ipaddress
        try:
            ipaddress.ip_network("not-a-network")
        except ValueError as e:
            print("ValueError:", e)
        print(ipaddress.ip_address("10.0.1.5") in ipaddress.ip_network("10.0.0.0/8"))
    """),
    Q("Which of these is NOT open to the whole internet?", "0.0.0.0/1", "0.0.0.0/0", "::/0", "5.6.7.8/0",
      explain="/1 covers half of IPv4 - still huge, but not everything. Only prefix length 0 is the whole internet."),
    C("""
        Write `subnet_size(cidr)` that returns the number of addresses in the network, accepting host bits
        (`strict=False`), and returns `0` for invalid text instead of raising.

        ```
        subnet_size("10.0.1.0/24")   # 256
        subnet_size("10.0.1.9/30")   # 4
        subnet_size("banana")        # 0
        ```
    """, 'import ipaddress\n\ndef subnet_size(cidr):\n    try:\n        return ipaddress.ip_network(cidr, strict=False).num_addresses\n    except ValueError:\n        return 0',
      check="""
        assert subnet_size("10.0.1.0/24") == 256
        assert subnet_size("10.0.1.9/30") == 4, "use strict=False so host bits are accepted"
        assert subnet_size("banana") == 0
      """,
      require=["ipaddress"],
      hints=["ipaddress.ip_network(cidr, strict=False).num_addresses",
             "Wrap it in try/except ValueError and return 0 in the except."]),
    B("p4-networks", intro="ChangeGate's world-open check. Every firewall, security group and database-network "
                          "policy relies on it."),
], summary="""
    - CIDR `a.b.c.d/n`: n leading bits fixed. `/32` one host, `/0` everything. `0.0.0.0/0` and `::/0` = the internet.
    - `ipaddress.ip_network(text, strict=False)` parses (ValueError if invalid); `.prefixlen`, `.num_addresses`.
    - `ip_address(x) in ip_network(y)` tests membership.
    - Format specs: `f"{text:16}"` pads, `f"{n:<3}"` left-aligns.
""")

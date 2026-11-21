from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p01l1", "Your first program", [
    T("""
        **Programs are instructions**

        A Python program is a list of instructions that run **top to bottom**, one line at a time. The
        most basic instruction is `print()`, which shows something on the screen.

        ```
        print("Plan: 3 to add, 1 to change, 0 to destroy.")
        ```

        The text inside the quotes is called a **string**. Strings can use double quotes `"..."` or single
        quotes `'...'` - just be consistent within one string.
    """),
    Ex("""
        print("Plan: 3 to add, 1 to change, 0 to destroy.")
        print('Apply complete!')
    """, note="Each `print()` starts on a new line."),
    P("""
        print("terraform init")
        print("terraform plan")
        print("terraform apply")
    """, explain="Lines run in order, top to bottom."),
    T("""
        **Printing several things**

        Give `print()` several values separated by commas and it prints them with a space between:

        ```
        print("region:", "us-east-1")      # region: us-east-1
        print("instances:", 3)             # instances: 3
        ```

        Numbers don't need quotes. Anything after `#` on a line is a **comment**: Python ignores it.
        Comments are notes for humans.
    """),
    Ex("""
        # this line is a comment - Python skips it
        print("region:", "eu-west-1")
        print("instances:", 3, "of", 5)
        print()            # an empty print() prints a blank line
        print("done")
    """),
    Q("What does `print(\"zones:\", 3)` show?",
      "zones: 3", "zones:3", '"zones:" 3', "zones: \"3\"",
      explain="Commas separate values, and print() puts one space between them. Quotes are not printed."),
    C("""
        Print exactly these two lines:

        ```output
        Terraform plan
        3 to add
        ```
    """, 'print("Terraform plan")\nprint("3 to add")',
      hints=["You need two print() calls, one for each line.",
             'Line 1: print("Terraform plan")  Line 2: print("3 to add")']),
    T("""
        **When things go wrong**

        If Python can't understand a line, it stops and shows an **error**. Errors are normal - every
        programmer sees dozens a day. The app explains each one in plain English. The most common first
        error is a **SyntaxError**: a missing quote or bracket.
    """),
    Ex("""
        print("missing a closing quote)
    """, note="Read the error: it names the problem and the line. Here the string never ends.", error_ok=True),
    P("""
        print("a", "b", "c")
        print("a" "b")
    """, explain="With commas you get spaces. Two strings written side by side with no comma are glued "
                 "together into one string - a rarely used feature, but now you've seen it."),
    C("""
        Use **one** `print()` with commas to show:

        ```output
        bucket: logs created: True
        ```

        (`True` is a special value in Python - you'll meet it properly soon. Write it without quotes.)
    """, 'print("bucket:", "logs", "created:", True)',
      require=[","],
      hints=["Separate each piece with a comma inside a single print(...).",
             'print("bucket:", "logs", "created:", True)']),
], summary="""
    - Programs run top to bottom. `print(...)` shows values; each call starts a new line.
    - Strings are text in quotes: `"..."` or `'...'`.
    - `print(a, b, c)` prints the values separated by spaces. `print()` alone prints a blank line.
    - `#` starts a comment. Python ignores it.
    - A **SyntaxError** means Python couldn't read the line: check quotes and brackets.
""")

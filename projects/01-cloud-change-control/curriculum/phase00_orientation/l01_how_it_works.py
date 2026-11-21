from pce.lesson import T, Ex, Q, P, C, Lesson

LESSON = Lesson("p00l1", "How this course works", [
    T("""
        **Learning by doing**

        Every lesson is a short sequence of steps:

        - **Explanations** introduce one idea at a time.
        - **Examples** are real Python that runs right here; the output you see is genuine.
        - **Questions** and **"what will this print?"** puzzles check your understanding.
        - **Exercises** ask you to write code. The app runs it and tells you exactly what went wrong
          if it doesn't work yet.
    """),
    Ex("""
        print("Hello from Python")
        print(2 + 3)
    """, note="Press **x** on an example to open it in the Playground and experiment with it."),
    P("""
        print("plan")
        print("apply")
    """, explain="Python runs lines top to bottom, and each print() starts a new line."),
    T("""
        **Writing code in exercises**

        Type one line, press Enter, then the next line. When you're finished, type `run` on its own line.

        - `:fix 2` retypes line 2, `:undo` removes the last line, `:show` shows everything.
        - `:hint` reveals the next hint. Hints start gentle and get more specific.
        - The reference solution unlocks after you've seen every hint or made a few attempts.
    """),
    C("""
        Print exactly this line:

        ```output
        ChangeGate is ready
        ```
    """, 'print("ChangeGate is ready")',
      hints=["Use the print() function with the text inside quotes.",
             'Type: print("ChangeGate is ready") then type run on the next line.']),
    Q("When does the reference solution for an exercise become available?",
      "After you've seen every hint or made a few honest attempts",
      "Immediately, before you try anything",
      "Never - you must solve everything alone",
      explain="Trying first is where the learning happens, but you'll never be stuck forever."),
], summary="""
    - Lessons are steps: explanations, live examples, questions and exercises.
    - In exercises, type code line by line, then `run`. `:fix N`, `:undo`, `:show`, `:edit` help you edit.
    - `:hint` reveals graduated hints; the reference solution unlocks after all hints or a few attempts.
    - `:menu` saves and returns to the menu at any time.
""")

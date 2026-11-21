"""Turns Python's error messages into beginner-friendly explanations."""

import builtins
import re

from . import ui
from .ui import style

GENERAL = {
    "SyntaxError": "Python couldn't understand the *grammar* of this line. Look for a missing quote, "
                   "bracket or colon, or a typo, on or just before the line shown.",
    "IndentationError": "The spaces at the start of a line are off. Lines inside an if / for / while / def "
                        "must all be indented by the same amount (4 spaces is the standard).",
    "TabError": "You mixed tabs and spaces for indentation. Use only spaces (4 per level).",
    "NameError": "You used a name Python doesn't know (yet). Check the spelling, capital letters, and "
                 "that the variable was created *before* this line. Text needs quotes around it.",
    "TypeError": "You used a value of the wrong type for this operation, like adding text to a number. "
                 "Convert first with int(), float() or str().",
    "ValueError": "The type was right but the value wasn't, like int(\"hello\").",
    "ZeroDivisionError": "You divided by zero. Check the divisor before dividing.",
    "IndexError": "You asked for a position that doesn't exist. Counting starts at 0, so the last "
                  "position of something with length n is n - 1.",
    "KeyError": "That key isn't in the dictionary. Check its spelling, or use .get(key, default) for a "
                "safe lookup.",
    "AttributeError": "That value doesn't have the method or attribute you asked for. Check the spelling "
                      "and what type the value really is.",
    "ModuleNotFoundError": "Python can't find a module with that name. Check the spelling of the import.",
    "ImportError": "The import didn't work. Check the spelling of the module and the name inside it.",
    "RecursionError": "A function kept calling itself without stopping. Make sure there is a base case "
                      "that returns without calling the function again.",
    "UnboundLocalError": "You changed a variable inside a function before giving it a value there. "
                         "Create it inside the function, or pass it in as a parameter.",
    "FileNotFoundError": "That file doesn't exist (in this folder). Check the filename, or create it first "
                         "with mode \"w\".",
    "EOFError": "Your program called input() more times than this challenge expected. Check how many "
                "times you ask for input.",
    "OverflowError": "A number got too big to handle.",
    "StopIteration": "You called next() on something that had no more items.",
    "TooMuchOutput": "Your program printed a HUGE amount of text, which usually means an infinite loop. "
                     "Check that your loop's condition eventually becomes False.",
    "NotImplementedError": "This method exists but hasn't been written yet. A child class should "
                           "override it.",
    "AssertionError": "An assert statement failed: something you expected to be True was False.",
}


def specific_tip(etype, msg):
    """A tip tailored to the exact message, or None."""
    if etype == "NameError":
        m = re.search(r"name '(\w+)' is not defined", msg)
        if m:
            name = m.group(1)
            if name != name.lower() and name.lower() in dir(builtins):
                return "Python is case-sensitive: write `" + name.lower() + "`, not `" + name + "`."
            if name in ("true", "false", "none"):
                return "Write `" + name.capitalize() + "` with a capital first letter."
            return ("Python doesn't know `" + name + "`. If you meant text, put it in quotes: \"" + name
                    + "\". If it's a variable or function, check the spelling and that it was "
                    "created before this line.")
    if etype == "TypeError":
        if "can only concatenate str" in msg:
            return "You're joining text and a number with +. Convert the number with str(...) or use an f-string."
        if "unsupported operand" in msg and "'str'" in msg:
            return ("One side of the operation is text (str). If it came from input(), convert it with "
                    "int(...) or float(...) first.")
        if "not callable" in msg:
            return "You put ( ) after something that isn't a function. Did you reuse a function's name as a variable?"
        if "missing" in msg and "required positional argument" in msg:
            return "You called a function without giving it all the values it needs."
        if "positional argument" in msg and "given" in msg:
            return ("You gave a function the wrong number of values. (Inside a class, did you forget "
                    "`self` as the first parameter?)")
        if "not subscriptable" in msg:
            return "You used [ ] on something that isn't a list, string or dictionary."
        if "not iterable" in msg:
            return "You tried to loop over something that isn't a collection. Did you mean range(...)?"
        if "does not support item assignment" in msg:
            return "That value can't be changed in place. Strings and tuples are immutable — build a new one instead."
    if etype == "ValueError":
        if "invalid literal for int()" in msg:
            return ("int() only understands whole numbers written as text, like \"42\". Not words, not "
                    "decimals. For decimals use float().")
        if "could not convert string to float" in msg:
            return "float() only understands numbers written as text, like \"3.5\"."
        if "too many values to unpack" in msg or "not enough values to unpack" in msg:
            return "The number of variables on the left doesn't match the number of values on the right."
    if etype in ("SyntaxError", "IndentationError", "TabError"):
        if "expected ':'" in msg:
            return "Lines that start a block (if, elif, else, for, while, def, class, try...) must end with a colon `:`."
        if "unterminated string" in msg or "EOL while scanning" in msg:
            return "A string is missing its closing quote. Every \" needs a partner \"."
        if "was never closed" in msg or "unexpected EOF" in msg:
            return "A bracket ( [ or { was opened but never closed."
        if "unmatched" in msg or "does not match opening" in msg:
            return "There's a closing bracket that doesn't match an opening one."
        if "Perhaps you forgot a comma" in msg:
            return "Looks like two values are side by side without a comma between them."
        if "'=' instead of '=='" in msg or "Maybe you meant '=='" in msg:
            return "Use == to compare two things. A single = means 'store this value'."
        if "cannot assign to" in msg:
            return "The left side of = must be a variable name (the value goes on the right)."
        if "invalid character" in msg:
            return "There's an unusual character, often a curly quote copied from somewhere. Use plain \" or ' quotes."
        if "expected an indented block" in msg:
            return "After a line ending in `:`, the next line must be indented (4 spaces)."
        if "unexpected indent" in msg:
            return "This line is indented but it shouldn't be. Remove the spaces at its start."
        if "unindent does not match" in msg:
            return "This line's indentation doesn't line up with any line above it. Count the spaces."
        if "Missing parentheses in call to 'print'" in msg:
            return "In Python 3, print needs parentheses: print(\"hello\")."
        if "invalid decimal literal" in msg:
            return "Variable names can't start with a digit, and numbers can't contain letters."
    if etype == "AttributeError":
        if "'NoneType'" in msg:
            return ("This value is None. That often happens when a function didn't `return` anything, or "
                    "you saved the result of a method like .sort() or .append(), which return None.")
        m = re.search(r"'(\w+)' object has no attribute '(\w+)'", msg)
        if m:
            return ("A " + m.group(1) + " doesn't have `." + m.group(2) + "`. Check the spelling, and "
                    "whether the value is the type you think it is.")
    if etype == "IndexError" and "out of range" in msg:
        return "Counting starts at 0: the first item is [0] and the last is [len(x) - 1] or [-1]."
    if etype == "KeyError":
        return "The key " + msg + " isn't in the dictionary. Use `key in d` to check, or d.get(key, default)."
    return None


def explain_error(error, code="", indent=2):
    """Print an error report: type, line, offending code, the message and a friendly tip."""
    pad = " " * indent
    etype, msg, line = error.get("type", "Error"), error.get("message", ""), error.get("line")
    where = " on line " + str(line) if line else ""
    print(pad + style("✘ " + etype + where, "red", "bold"))
    lines = code.split("\n")
    if line and 1 <= line <= len(lines):
        print(pad + style("  " + str(line) + " │ ", "grey") + ui.highlight(lines[line - 1]))
    if msg:
        print(pad + style("  " + msg, "red"))
    tip = specific_tip(etype, msg) or GENERAL.get(etype)
    if tip:
        print()
        ui.render(style("Tip: ", "yellow", "bold") + tip, indent=indent + 1)

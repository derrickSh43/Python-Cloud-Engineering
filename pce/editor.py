"""A tiny line-by-line code editor that runs inside the terminal."""

import os
import shlex
import shutil
import subprocess
import sys
import tempfile

from . import ui
from .ui import style, BackToMenu

HELP = [
    ("run", "run your code"),
    (":show", "show all your code"),
    (":undo", "delete the last line"),
    (":fix N", "retype line N"),
    (":del N", "delete line N"),
    (":ins N", "insert a new line before line N"),
    (":clear", "erase everything, start over"),
    (":edit", "edit in Notepad / text editor"),
]


class Editor:
    indent_tips_left = 3  # how many more times to remind about indentation (Windows, no readline)

    def __init__(self, starter=""):
        self.lines = starter.split("\n") if starter.strip() else []
        self.arg = ""

    def text(self):
        return "\n".join(self.lines)

    def show(self, title="Your code"):
        if self.lines:
            ui.code_box(self.text(), title=title)
        else:
            print(style("  (no code yet - start typing!)", "grey", "italic"))

    def suggest_indent(self, upto=None):
        lines = self.lines if upto is None else self.lines[:upto]
        for line in reversed(lines):
            if line.strip():
                indent = line[: len(line) - len(line.lstrip())]
                return indent + "    " if line.rstrip().endswith(":") else indent
        return ""

    def _prompt(self, number):
        return style("  " + str(number).rjust(3) + "│ ", "blue", prompt=True)

    def _line_number(self, allow_end=False):
        try:
            n = int(self.arg)
        except ValueError:
            n = None
        top = len(self.lines) + (1 if allow_end else 0)
        if n is None or not 1 <= n <= top:
            print(style("  Give a line number between 1 and %d, e.g. :fix 2" % max(top, 1), "yellow"))
            return None
        return n

    def collect(self, commands):
        """Read code lines until the learner types a command from `commands`; return that command."""
        while True:
            raw = ui.read_code_line(self._prompt(len(self.lines) + 1), self.suggest_indent())
            stripped = raw.strip()
            if stripped in ("run", ":run") and "run" in commands:
                return "run"
            if stripped.startswith(":") and len(stripped) > 1 and stripped[1].isalpha():
                word, _, arg = stripped[1:].partition(" ")
                word, self.arg = word.lower(), arg.strip()
                if word in ("menu", "m", "quit", "q"):
                    raise BackToMenu()
                if word in commands:
                    return word
                self.command(word)
                continue
            self.lines.append(raw.replace("\t", "    ").rstrip())
            if ui.readline is None and raw.rstrip().endswith(":") and Editor.indent_tips_left > 0:
                Editor.indent_tips_left -= 1
                print(style("        ↳ the next line belongs inside this block: start it with 4 spaces", "grey"))

    def command(self, word):
        if word == "undo":
            if self.lines:
                removed = self.lines.pop()
                print(style("  removed line %d: %s" % (len(self.lines) + 1, removed.strip()), "grey"))
            else:
                print(style("  nothing to undo", "grey"))
        elif word == "show":
            self.show()
        elif word == "clear":
            self.lines = []
            print(style("  All clear. Start typing from line 1.", "grey"))
        elif word == "fix":
            n = self._line_number()
            if n:
                old = self.lines[n - 1]
                print(style("  line %d was: " % n, "grey") + ui.highlight(old))
                print(style("  type the new line (or press Enter to keep it):", "grey"))
                prefill = old if ui.readline else ""
                new = ui.read_code_line(self._prompt(n), prefill)
                if new.strip():
                    self.lines[n - 1] = new.replace("\t", "    ").rstrip()
                self.show()
        elif word == "del":
            n = self._line_number()
            if n:
                self.lines.pop(n - 1)
                self.show()
        elif word == "ins":
            n = self._line_number(allow_end=True)
            if n:
                new = ui.read_code_line(self._prompt(n), self.suggest_indent(n - 1))
                self.lines.insert(n - 1, new.replace("\t", "    ").rstrip())
                self.show()
        elif word == "edit":
            self.edit_external()
        elif word == "help":
            print_help()
        else:
            print(style("  Unknown command :%s  (type :help to see commands)" % word, "yellow"))

    def edit_external(self):
        path = os.path.join(tempfile.gettempdir(), "pce_code.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text() + "\n")
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        try:
            if editor:
                subprocess.call(shlex.split(editor, posix=os.name != "nt") + [path])
            elif os.name == "nt" or sys.platform == "darwin":
                cmd = ["notepad.exe", path] if os.name == "nt" else ["open", "-t", path]
                subprocess.Popen(cmd)
                print(style("  Your code is open in a text editor.", "cyan"))
                print(style("  Edit it, SAVE it (Ctrl+S / Cmd+S), then come back here.", "cyan"))
                ui.ask(style("  ▸ Press Enter here when you've saved ", "yellow", prompt=True))
            else:
                subprocess.call([shutil.which("nano") or "vi", path])
        except OSError as e:
            print(style("  Couldn't open an editor (%s). Set the EDITOR environment variable." % e, "red"))
            return
        with open(path, encoding="utf-8") as f:
            content = f.read().replace("\t", "    ").rstrip()
        self.lines = [l.rstrip() for l in content.split("\n")] if content else []
        self.show()
        print(style("  Type `run` to run it, or keep typing to add more lines.", "grey"))


def print_help(extra=()):
    rows = list(HELP) + list(extra)
    print(style("  Type your code one line at a time, then type ", "grey") + style("run", "cyan", "bold")
          + style(" on its own line.", "grey"))
    for i in range(0, len(rows), 2):
        pair = rows[i:i + 2]
        cells = [style(cmd.ljust(11), "cyan") + style(desc.ljust(31), "grey") for cmd, desc in pair]
        print("    " + "".join(cells))

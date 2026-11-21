"""Everything that draws on the terminal: colours, boxes, wrapped text, code highlighting, input."""

import builtins
import keyword
import os
import re
import shutil
import sys
import textwrap

try:
    import readline  # arrow-key editing + auto-indent on macOS / Linux
except ImportError:  # Windows has no readline; plain input() still works fine
    readline = None

if os.name == "nt":
    os.system("")  # switches classic Windows consoles into ANSI-colour mode

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


class BackToMenu(Exception):
    """Raised when the learner types :menu so we can unwind to the main menu."""


class QuitApp(Exception):
    """Raised on Ctrl+C / end of input so the app can save and exit cleanly."""


_CODES = {
    "reset": "0", "bold": "1", "dim": "2", "italic": "3", "under": "4",
    "red": "91", "green": "92", "yellow": "93", "blue": "94", "magenta": "95",
    "cyan": "96", "white": "97", "grey": "90",
    "orange": "38;5;208", "gold": "38;5;220", "pink": "38;5;213", "teal": "38;5;44",
    "purple": "38;5;141", "lime": "38;5;154",
}


def style(text, *names, prompt=False):
    """Wrap text in ANSI colour codes. prompt=True makes it safe inside input() with readline."""
    text = str(text)
    if not COLOR or not names:
        return text
    start = "\033[" + ";".join(_CODES[n] for n in names) + "m"
    end = "\033[0m"
    if prompt and readline is not None:
        start, end = "\001" + start + "\002", "\001" + end + "\002"
    return start + text + end


_ANSI = re.compile(r"\033\[[0-9;]*m")


def visible_len(text):
    return len(_ANSI.sub("", text))


def width():
    cols = shutil.get_terminal_size((90, 30)).columns
    return max(50, min(cols - 2, 96))


def clear():
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")
    else:
        print("\n" + "-" * 40)


def rule(color="grey", char="─"):
    print(style(char * width(), color))


def banner(title, color="gold", char="═"):
    w = width()
    print(style(char * w, color))
    print(style(title.center(w), "bold", color))
    print(style(char * w, color))


def bar(fraction, length=20, color="green"):
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * length))
    return style("█" * filled, color) + style("░" * (length - filled), "grey")


def boxed(lines, color="gold", indent=2):
    """Draw a box around already-formatted lines."""
    inner = max(visible_len(l) for l in lines) if lines else 0
    pad = " " * indent
    print(pad + style("╔" + "═" * (inner + 2) + "╗", color))
    for line in lines:
        gap = inner - visible_len(line)
        print(pad + style("║ ", color) + line + " " * gap + style(" ║", color))
    print(pad + style("╚" + "═" * (inner + 2) + "╝", color))


# ---------------------------------------------------------------- code highlighting

_TOKEN = re.compile(
    r"(?P<comment>#.*$)"
    r"|(?P<string>(?<![\w])[rRbBfFuU]{0,2}(?:\"(?:\\.|[^\"\\])*\"?|'(?:\\.|[^'\\])*'?))"
    r"|(?P<number>\b\d[\d_]*(?:\.\d+)?\b)"
    r"|(?P<name>\b[A-Za-z_]\w*\b)"
)
_BUILTINS = set(dir(builtins))
_CONSTANTS = {"True", "False", "None"}


def highlight(line):
    if not COLOR:
        return line

    def paint(m):
        kind, text = m.lastgroup, m.group()
        if kind == "comment":
            return style(text, "grey", "italic")
        if kind == "string":
            return style(text, "lime")
        if kind == "number":
            return style(text, "yellow")
        if text in _CONSTANTS:
            return style(text, "orange")
        if keyword.iskeyword(text):
            return style(text, "magenta")
        if text in _BUILTINS:
            return style(text, "cyan")
        return text

    return _TOKEN.sub(paint, line)


def code_box(code, title=None, color="blue", numbered=True, indent=2):
    pad = " " * indent
    lines = code.split("\n") if code else [""]
    head = "┌─ " + title + " " if title else "┌"
    print(pad + style(head + "─" * max(4, 44 - len(head)), color))
    digits = len(str(len(lines)))
    for n, line in enumerate(lines, 1):
        num = style(str(n).rjust(digits) + " ", "grey") if numbered else ""
        print(pad + style("│ ", color) + num + highlight(line))
    print(pad + style("└" + "─" * 44, color))


def output_box(text, title="Output", color="green", indent=2, max_lines=40):
    pad = " " * indent
    print(pad + style("┌─ " + title + " " + "─" * max(4, 40 - len(title)), color))
    if text.strip("\n") == "":
        print(pad + style("│ ", color) + style("(nothing was printed)", "grey", "italic"))
    else:
        lines = text.rstrip("\n").split("\n")
        for line in lines[:max_lines]:
            print(pad + style("│ ", color) + line[:300])
        if len(lines) > max_lines:
            print(pad + style("│ ", color) + style("... (%d more lines)" % (len(lines) - max_lines), "grey", "italic"))
    print(pad + style("└" + "─" * 44, color))


# ---------------------------------------------------------------- prose rendering

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])")
_KEEP = "\x00"  # stands in for spaces that must not be wrapped


def _by_code_spans(text, on_code, on_prose):
    """Apply on_code to `code spans` and on_prose to everything else, so markup inside code is left alone."""
    parts = re.split(r"(`[^`]+`)", text)
    return "".join(on_code(p[1:-1]) if i % 2 else on_prose(p) for i, p in enumerate(parts))


def _protect(text):
    def prose(p):
        p = _BOLD.sub(lambda m: "**" + m.group(1).replace(" ", _KEEP) + "**", p)
        return _ITALIC.sub(lambda m: "*" + m.group(1).replace(" ", _KEEP) + "*", p)
    return _by_code_spans(text, lambda c: "`" + c.replace(" ", _KEEP) + "`", prose)


def _inline(line):
    if COLOR:
        def prose(p):
            p = _BOLD.sub(lambda m: style(m.group(1), "bold", "white"), p)
            return _ITALIC.sub(lambda m: style(m.group(1), "italic"), p)
        line = _by_code_spans(line, lambda c: style(c, "cyan"), prose)
    else:
        def prose(p):
            p = _BOLD.sub(lambda m: m.group(1), p)
            return _ITALIC.sub(lambda m: m.group(1), p)
        line = _by_code_spans(line, lambda c: "`" + c + "`", prose)
    return line.replace(_KEEP, " ")


def render(text, indent=2):
    """Print lesson prose: wraps paragraphs, supports `code`, **bold**, - bullets and ``` blocks."""
    pad = " " * indent
    w = width() - indent
    para = []

    def flush():
        if para:
            joined = " ".join(p.strip() for p in para)
            for wrapped in textwrap.wrap(_protect(joined), w):
                print(pad + _inline(wrapped))
            para.clear()

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            tag = stripped[3:].strip()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            body = textwrap.dedent("\n".join(block))
            if tag == "output":
                output_box(body, title="Expected output", color="lime", indent=indent + 1)
            else:
                code_box(body, indent=indent + 1)
        elif stripped == "":
            flush()
            print()
        else:
            bullet = re.match(r"(\s*)([-*]|\d+[.)])\s+(.*)", line)
            if bullet:
                flush()
                lead = pad + bullet.group(1)
                mark = "•" if bullet.group(2) in "-*" else bullet.group(2)
                first = lead + style(mark, "gold") + " "
                rest = lead + " " * (len(mark) + 1)
                wrapped = textwrap.wrap(_protect(bullet.group(3)), w - len(rest) + len(pad)) or [""]
                print(first + _inline(wrapped[0]))
                for extra in wrapped[1:]:
                    print(rest + _inline(extra))
            else:
                para.append(line)
        i += 1
    flush()


def note(text, label="Note"):
    """A highlighted aside: tips, warnings, real-world context."""
    print("  " + style(label, "bold", "teal"))
    render(text, indent=4)


# ---------------------------------------------------------------- input

def ask(prompt="", menu=True):
    try:
        answer = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise QuitApp()
    if menu and answer.strip().lower() in (":menu", ":m", ":quit", ":q"):
        raise BackToMenu()
    return answer


def pause(label="continue"):
    ask(style("  ▸ Press Enter to " + label + " ", "grey", prompt=True))


def choose(prompt, valid, menu=True):
    """Ask until the answer is one of `valid` (case-insensitive). Returns the lower-cased answer."""
    valid = [v.lower() for v in valid]
    while True:
        answer = ask(prompt, menu=menu).strip().lower()
        if answer in valid:
            return answer
        print(style("  Please type one of: " + ", ".join(v if v else "Enter" for v in valid), "grey"))


def confirm(prompt, default=False):
    hint = " [Y/n] " if default else " [y/N] "
    answer = ask(style("  " + prompt + hint, "yellow", prompt=True)).strip().lower()
    if not answer:
        return default
    return answer.startswith("y")


def read_code_line(prompt, prefill=""):
    """Read one line of code. With readline, the suggested indentation is pre-typed."""
    if readline is not None and prefill:
        def hook():
            readline.insert_text(prefill)
            readline.redisplay()
        readline.set_pre_input_hook(hook)
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise QuitApp()
    finally:
        if readline is not None:
            readline.set_pre_input_hook(None)

"""The interactive learning app: menus, lessons, exercises, checkpoints, review, reference cards,
the playground and the progress screen."""

import datetime
import os
import random
import re
import subprocess
import sys

from . import ui
from .editor import Editor, print_help
from .errors import explain_error
from .grader import grade, describe_output_difference, normalize
from .progress import Profile
from .projects import ROOT, discover
from .runner import run_code
from .ui import BackToMenu, QuitApp, style

PROGRAMS_DIR = os.path.join(ROOT, "my_programs")
SOLUTION_AFTER_FAILS = 3  # the reference solution unlocks after this many failed runs (or all hints)

LOGO = r"""
   ___       _   _               ___ _             _   ___           _
  | _ \_  _ | |_| |_  ___ _ _   / __| |___ _  _ __| | | __|_ _  __ _(_)_ _  ___ ___ _ _(_)_ _  __ _
  |  _/ || ||  _| ' \/ _ \ ' \ | (__| / _ \ || / _` | | _|| ' \/ _` | | ' \/ -_) -_) '_| | ' \/ _` |
  |_|  \_, | \__|_||_\___/_||_| \___|_\___/\_,_\__,_| |___|_||_\__, |_|_||_\___\___|_| |_|_||_\__, |
       |__/                                                    |___/                          |___/
"""

PRAISE = ["Correct.", "That's right.", "Exactly.", "Nicely done.", "Spot on."]


class App:
    def __init__(self, project=None, unlock_all=False):
        self.unlock_all = unlock_all
        self.requested_project = project
        self.profile = Profile.load()
        self.project = None
        self.mistakes = 0  # mistakes in the lesson / checkpoint being worked on

    @property
    def phases(self):
        return self.project.phases

    @property
    def prog(self):
        return self.profile.project(self.project.id)

    # ================================================================ start / menus
    def run(self):
        try:
            if self.profile is None:
                self.first_run()
            self.profile.touch_day()
            self.select_project(initial=True)
            self.profile.save()
            self.main_menu()
        except QuitApp:
            pass
        finally:
            if self.profile:
                self.profile.save()
                print(style("\n  Progress saved.\n", "lime"))

    def first_run(self):
        ui.clear()
        print(style(LOGO, "teal", "bold"))
        ui.render("""
Welcome. This is a hands-on course in Python for cloud engineering. You'll write real code in every
lesson. The app runs it, checks it, and explains errors in plain English. Your progress is saved
automatically, so you can stop and come back at any time.
""")
        print()
        name = ui.ask(style("  What should I call you? (Enter to skip) ", "yellow", prompt=True), menu=False).strip()
        self.profile = Profile(name[:30])
        self.profile.save()
        print()
        self.how_it_works(pause=False)
        ui.pause("start")

    def select_project(self, initial=False):
        projects = discover()
        if not projects:
            raise SystemExit("No projects found in the projects/ folder.")
        wanted = self.requested_project if initial else None
        if initial and not wanted:
            wanted = self.profile.current_project
        chosen = next((p for p in projects if wanted in (p.id, os.path.basename(p.path))), None)
        if chosen is None and len(projects) == 1:
            chosen = projects[0]
        while chosen is None:
            ui.clear()
            ui.banner("CHOOSE A PROJECT", color="teal")
            print()
            for n, p in enumerate(projects, 1):
                print("   " + style("[%d]" % n, "cyan", "bold") + " " + style(p.title, "bold", "white"))
                ui.render(p.summary, indent=7)
            print()
            answer = ui.ask(style("  Project number: ", "yellow", prompt=True), menu=False).strip()
            if answer.isdigit() and 1 <= int(answer) <= len(projects):
                chosen = projects[int(answer) - 1]
        self.project = chosen
        self.profile.current_project = chosen.id
        self.profile.save()

    def main_menu(self):
        while True:
            ui.clear()
            print(style(LOGO, "teal"))
            self.status_line()
            print()
            dest = self.next_destination()
            if dest[0] == "lesson":
                label = "Continue: " + self.phases[dest[1]]["lessons"][dest[2]]["title"]
            elif dest[0] == "checkpoint":
                label = "Continue: Phase %d checkpoint" % self.phases[dest[1]]["number"]
            else:
                label = "Course complete - see what's next"
            options = [
                ("1", label, "gold"), ("2", "Course map (open any unlocked lesson)", "white"),
                ("3", "Reference cards (summaries of finished lessons)", "white"),
                ("4", "Review practice (mixed questions from finished lessons)", "white"),
                ("5", "Playground (write and run any code)", "white"), ("6", "Your progress", "white"),
                ("7", "How it works", "white"),
            ]
            if len(discover()) > 1:
                options.append(("8", "Switch project", "white"))
            options.append(("0", "Save & quit", "grey"))
            for key, text, color in options:
                print("   " + style("[" + key + "]", "cyan", "bold") + " " + style(text, color))
            print()
            choice = ui.choose(style("  Choose: ", "yellow", prompt=True), [k for k, _, _ in options], menu=False)
            try:
                if choice == "1":
                    self.continue_course()
                elif choice == "2":
                    self.course_map()
                elif choice == "3":
                    self.reference_cards()
                elif choice == "4":
                    self.review()
                elif choice == "5":
                    self.playground()
                elif choice == "6":
                    self.progress_screen()
                elif choice == "7":
                    ui.clear()
                    self.how_it_works()
                elif choice == "8":
                    self.select_project()
                elif choice == "0":
                    return
            except BackToMenu:
                pass
            self.profile.save()

    def status_line(self):
        total = len(self.project.lessons())
        done = sum(1 for _, lesson in self.project.lessons() if lesson["id"] in self.prog.completed_lessons)
        parts = [style("  " + self.project.title, "bold", "white")]
        if self.profile.name:
            parts.append(style(self.profile.name, "grey"))
        parts.append(ui.bar(done / total if total else 0, 20, "teal") + style(" %d/%d lessons" % (done, total), "teal"))
        if self.profile.streak >= 2:
            parts.append(style("%d in a row" % self.profile.streak, "orange", "bold"))
        print("   ".join(parts))

    def how_it_works(self, pause=True):
        ui.render("""
- The course is split into **phases**. Each phase has short **lessons** and ends with a **checkpoint**.
  Pass the checkpoint to unlock the next phase.
- Lessons mix explanations, **live examples**, **quizzes**, **"what will this print?"** questions and
  **coding exercises**. In exercises you write real Python; the app runs it and checks the result.
- **Hints are graduated**: each `:hint` reveals a little more. The reference solution unlocks after
  you've used every hint or made %d honest attempts. Try first - that's where the learning happens.
- Every finished lesson adds a **reference card** you can look back at any time.
- **Review practice** mixes questions from lessons you've finished so they stick.
- The **Playground** runs anything you like and can save your programs to `my_programs/`.

**Writing code:** type one line, press Enter, type the next... then type `run` on its own line.
`:fix 2` retypes line 2, `:undo` removes the last line, `:edit` opens your code in a text editor.
Type `:menu` at any time to save and go back to the menu.

Errors are information, not failure. Read them - the app explains each one.
""" % SOLUTION_AFTER_FAILS)
        if pause:
            ui.pause("go back")

    # ================================================================ progress helpers
    def lesson_done(self, pi, li):
        return self.phases[pi]["lessons"][li]["id"] in self.prog.completed_lessons

    def checkpoint_passed(self, pi):
        return self.phases[pi]["checkpoint"]["id"] in self.prog.checkpoints

    def phase_unlocked(self, pi):
        return self.unlock_all or pi == 0 or self.checkpoint_passed(pi - 1)

    def lesson_unlocked(self, pi, li):
        return self.phase_unlocked(pi) and (self.unlock_all or li == 0 or self.lesson_done(pi, li - 1))

    def checkpoint_unlocked(self, pi):
        lessons = self.phases[pi]["lessons"]
        return self.phase_unlocked(pi) and (
            self.unlock_all or all(self.lesson_done(pi, li) for li in range(len(lessons))))

    def next_destination(self):
        for pi, phase in enumerate(self.phases):
            for li in range(len(phase["lessons"])):
                if not self.lesson_done(pi, li):
                    return ("lesson", pi, li)
            if not self.checkpoint_passed(pi):
                return ("checkpoint", pi)
        return ("done",)

    def continue_course(self):
        while True:
            dest = self.next_destination()
            if dest[0] == "done":
                self.course_complete()
                return
            if dest[0] == "lesson":
                self.play_lesson(dest[1], dest[2])
            elif not self.run_checkpoint(dest[1]):
                return
            if self.next_destination()[0] == "done":
                self.course_complete()
                return
            if not ui.confirm("Continue to the next lesson?", default=True):
                return

    # ================================================================ course map
    def course_map(self):
        while True:
            ui.clear()
            ui.banner("COURSE MAP · " + self.project.title.upper(), color="teal")
            for pi, phase in enumerate(self.phases):
                total = len(phase["lessons"])
                done = sum(self.lesson_done(pi, li) for li in range(total))
                if self.checkpoint_passed(pi):
                    mark, color = "✔", "lime"
                elif self.phase_unlocked(pi):
                    mark, color = "▸", "yellow"
                else:
                    mark, color = "·", "grey"
                print("  %s %s %s %s %s" % (
                    style(mark, color, "bold"), style(str(phase["number"]).rjust(2) + ".", color),
                    style(phase["title"].ljust(30), color, "bold" if color != "grey" else "dim"),
                    style(phase["topic"][:38].ljust(38), "white" if color != "grey" else "grey"),
                    style("%d/%d" % (done, total), "cyan")))
            print()
            answer = ui.ask(style("  Phase number to open (Enter to go back): ", "yellow", prompt=True)).strip()
            if not answer:
                return
            pi = next((i for i, ph in enumerate(self.phases) if str(ph["number"]) == answer), None)
            if pi is None:
                continue
            if not self.phase_unlocked(pi):
                print(style("  Pass the previous phase's checkpoint to unlock this phase.", "grey"))
                ui.pause()
                continue
            self.phase_screen(pi)

    def phase_screen(self, pi):
        phase = self.phases[pi]
        while True:
            ui.clear()
            ui.banner("Phase %d · %s" % (phase["number"], phase["title"]), color="teal")
            ui.render(phase["overview"])
            print()
            for li, lesson in enumerate(phase["lessons"]):
                if self.lesson_done(pi, li):
                    mark = style("✔", "lime")
                elif self.lesson_unlocked(pi, li):
                    mark = style("▸", "yellow")
                else:
                    mark = style("·", "grey")
                print("   %s %s %s" % (mark, style("[" + str(li + 1) + "]", "cyan"), lesson["title"]))
            passed = self.checkpoint_passed(pi)
            mark = style("✔", "lime") if passed else (
                style("▸", "yellow") if self.checkpoint_unlocked(pi) else style("·", "grey"))
            print("   %s %s Checkpoint: %s%s" % (mark, style("[c]", "cyan", "bold"), phase["checkpoint"]["title"],
                                                style(" (passed - retake any time)", "grey") if passed else ""))
            print()
            answer = ui.ask(style("  Lesson number, c for the checkpoint, Enter to go back: ", "yellow",
                                  prompt=True)).strip().lower()
            if not answer:
                return
            if answer == "c":
                if self.checkpoint_unlocked(pi):
                    self.run_checkpoint(pi)
                else:
                    print(style("  Finish every lesson in this phase first.", "grey"))
                    ui.pause()
            elif answer.isdigit() and 1 <= int(answer) <= len(phase["lessons"]):
                li = int(answer) - 1
                if self.lesson_unlocked(pi, li):
                    self.play_lesson(pi, li)
                else:
                    print(style("  Finish the earlier lessons first.", "grey"))
                    ui.pause()

    # ================================================================ lessons
    def show_overview(self, phase):
        if phase["id"] in self.prog.seen_overviews:
            return
        ui.clear()
        ui.banner("PHASE %d · %s" % (phase["number"], phase["title"].upper()), color="teal")
        print()
        ui.render(phase["overview"])
        if phase["outcomes"]:
            print()
            print(style("  By the end of this phase you will be able to:", "bold", "white"))
            for outcome in phase["outcomes"]:
                ui.render("- " + outcome, indent=4)
        print()
        self.prog.seen_overviews.append(phase["id"])
        self.profile.save()
        ui.pause("start the phase")

    def play_lesson(self, pi, li):
        phase = self.phases[pi]
        lesson = phase["lessons"][li]
        steps = lesson["steps"]
        if li == 0:
            self.show_overview(phase)
        idx = self.prog.position.get(lesson["id"], 0)
        if idx >= len(steps):
            idx = 0
        if idx == 0:
            self.mistakes = 0
        while idx < len(steps):
            ui.clear()
            self.lesson_header(phase, lesson, idx)
            ctx = {"mode": "lesson", "key": "%s:%d" % (lesson["id"], idx), "can_back": idx > 0}
            result = self.do_step(steps[idx], ctx)
            if result == "back":
                idx -= 1
            elif result != "stay":
                idx += 1
            self.prog.position[lesson["id"]] = idx
            self.profile.save()
        self.finish_lesson(pi, li)

    def lesson_header(self, phase, lesson, idx):
        total = len(lesson["steps"])
        print(style("  Phase %d · %s  ›  %s" % (phase["number"], phase["title"], lesson["title"]), "bold", "gold"))
        line = "  " + ui.bar(idx / total, 24) + style(" step %d/%d" % (idx + 1, total), "grey")
        if self.profile.streak >= 2:
            line += style("    %d in a row" % self.profile.streak, "orange", "bold")
        print(line)
        ui.rule()

    def finish_lesson(self, pi, li):
        phase = self.phases[pi]
        lesson = phase["lessons"][li]
        if lesson["id"] not in self.prog.completed_lessons:
            self.prog.completed_lessons.append(lesson["id"])
        ui.clear()
        ui.banner("LESSON COMPLETE: " + lesson["title"].upper(), color="lime")
        print()
        graded = any(s["type"] in ("quiz", "predict", "code") for s in lesson["steps"])
        if graded and self.mistakes == 0:
            print(style("  No mistakes in this lesson.", "lime", "bold"))
            print()
        print(style("  Reference card", "teal", "bold"))
        ui.rule("teal")
        ui.render(lesson["summary"])
        ui.rule("teal")
        self.profile.save()
        if li == len(phase["lessons"]) - 1 and not self.checkpoint_passed(pi):
            print()
            print(style("  That was the last lesson in this phase. Next: the phase checkpoint.", "yellow", "bold"))
        print()
        ui.pause()

    # ================================================================ steps
    def do_step(self, step, ctx):
        handler = {"text": self.step_text, "example": self.step_example, "quiz": self.step_quiz,
                   "predict": self.step_predict, "code": self.step_code}[step["type"]]
        return handler(step, ctx)

    def nav(self, ctx, extra=""):
        parts = ["Enter ▸ next"]
        if extra:
            parts.append(extra)
        if ctx.get("can_back"):
            parts.append("b ▸ back")
        parts.append(":menu ▸ save & exit")
        return ui.ask(style("  " + "    ".join(parts) + " ", "grey", prompt=True)).strip().lower()

    def step_text(self, step, ctx):
        print()
        ui.render(step["text"])
        print()
        return "back" if self.nav(ctx) == "b" and ctx.get("can_back") else "next"

    def step_example(self, step, ctx):
        print()
        ui.code_box(step["code"], title="Example")
        result = run_code(step["code"], step["inputs"], files=step["files"], echo=True)
        if step["inputs"]:
            print(style("  (typed for you: " + ", ".join(step["inputs"]) + ")", "grey"))
        ui.output_box(result.output, title="Output when it runs")
        if result.error:
            explain_error(result.error, step["code"])
        if result.timed_out:
            print(style("  (this example was stopped because it ran too long)", "grey"))
        if step["note"]:
            print()
            ui.render(step["note"])
        print()
        answer = self.nav(ctx, "x ▸ experiment with this code")
        if answer == "x":
            self.playground(starter=step["code"], embedded=True)
            return "stay"
        return "back" if answer == "b" and ctx.get("can_back") else "next"

    def step_quiz(self, step, ctx):
        print()
        print(style("  ? QUESTION", "magenta", "bold"))
        if step["code"]:
            ui.code_box(step["code"])
        ui.render(step["question"])
        options = [step["correct"]] + step["wrong"]
        random.shuffle(options)
        letters = "abcdefg"[: len(options)]
        crossed = set()
        first_try = True
        while True:
            print()
            for i, option in enumerate(options):
                if i in crossed:
                    print("    " + style(letters[i] + ") " + option, "grey", "dim"))
                else:
                    ui.render(style(letters[i] + ")", "cyan", "bold") + " " + option, indent=4)
            answer = ui.ask(style("  Your answer (letter): ", "yellow", prompt=True)).strip().lower()
            if len(answer) != 1 or answer not in letters or letters.index(answer) in crossed:
                print(style("  Type one of the letters shown.", "grey"))
                continue
            i = letters.index(answer)
            if options[i] == step["correct"]:
                print(style("  ✔ " + random.choice(PRAISE), "lime", "bold"))
                break
            crossed.add(i)
            first_try = False
            print(style("  ✘ Not quite. Have another look and try again.", "red"))
            self.fail(ctx)
        if step["explain"]:
            print()
            ui.render(step["explain"], indent=4)
        self.record(ctx, "quiz", first_try)
        print()
        ui.pause()
        return "next"

    def step_predict(self, step, ctx):
        print()
        print(style("  ? WHAT WILL THIS PRINT?", "magenta", "bold"))
        ui.code_box(step["code"], title="Read carefully")
        if step["inputs"]:
            print(style("  When it runs, the user types: ", "grey")
                  + ", ".join(style(v, "yellow") for v in step["inputs"]))
        result = run_code(step["code"], step["inputs"], files=step["files"])
        expected = normalize(result.output)
        lines = expected.split("\n")
        if len(lines) > 1:
            print(style("  It prints %d lines. Type them one at a time." % len(lines), "grey"))
        else:
            print(style("  Type exactly what appears on the screen.", "grey"))
        first_try = True
        for attempt in (1, 2):
            guess = []
            for n in range(len(lines)):
                label = "  line %d › " % (n + 1) if len(lines) > 1 else "  › "
                guess.append(ui.ask(style(label, "cyan", prompt=True)).strip())
            if [g.strip() for g in guess] == [l.strip() for l in lines]:
                print(style("  ✔ Exactly right.", "lime", "bold"))
                break
            first_try = False
            self.fail(ctx)
            joined = "\n".join(guess)
            if joined.replace('"', "").replace("'", "") == expected.replace('"', "").replace("'", ""):
                tip = "Close. print() shows text WITHOUT the quote marks around it."
            elif joined.lower() == expected.lower():
                tip = "Close. Check your capital letters."
            elif joined.replace(" ", "") == expected.replace(" ", ""):
                tip = "Close. Check the spaces."
            else:
                tip = "Not quite. Trace through the code line by line, top to bottom."
            print(style("  ✘ " + tip, "red"))
            if attempt == 1:
                print(style("  One more try.", "yellow"))
        ui.output_box(result.output, title="Actual output")
        if step["explain"]:
            ui.render(step["explain"], indent=4)
        self.record(ctx, "predict", first_try)
        print()
        ui.pause()
        return "next"

    def step_code(self, step, ctx):
        key = ctx.get("key")
        prog = self.prog
        print()
        print(style("  ✎ " + step["title"].upper(), "orange", "bold"))
        ui.render(step["task"])
        if step["cases"]:
            print(style("  Your program is tested several times. Each time these answers are typed for input():", "grey"))
            for case in step["cases"]:
                print(style("     • " + (", ".join(repr(v) for v in case) or "(nothing)"), "grey"))
        elif step["inputs"]:
            print(style("  These answers will be typed for your input() calls: "
                        + ", ".join(repr(v) for v in step["inputs"]), "grey"))
        editor = Editor(step["starter"])
        print()
        if step["starter"]:
            editor.show("Starter code (already typed in for you)")
        extra = [(":hint", "reveal the next hint"), (":solution", "reference solution (when unlocked)")]
        print_help(extra)
        print()
        hints_used = prog.hints.get(key, 0) if key else 0
        fails = prog.attempts.get(key, 0) if key else 0
        total_hints = len(step["hints"])
        for n in range(hints_used):
            print(style("  Hint %d/%d (seen before): " % (n + 1, total_hints), "yellow"))
            ui.render(step["hints"][n], indent=4)
        while True:
            command = editor.collect({"run", "hint", "solution", "help"})
            if command == "help":
                print_help(extra)
                continue
            if command == "hint":
                if hints_used < total_hints:
                    hints_used += 1
                    prog.stats["hints"] += 1
                    if key:
                        prog.hints[key] = hints_used
                    print(style("  Hint %d/%d: " % (hints_used, total_hints), "yellow", "bold"))
                    ui.render(step["hints"][hints_used - 1], indent=4)
                    self.profile.save()
                else:
                    print(style("  No more hints. The reference solution is now available with :solution.", "grey"))
                continue
            if command == "solution":
                if hints_used < total_hints and fails < SOLUTION_AFTER_FAILS:
                    print(style("  The reference solution unlocks after you've seen every hint (%d/%d so far) "
                                "or made %d attempts (%d so far)." % (
                                    hints_used, total_hints, SOLUTION_AFTER_FAILS, fails), "grey"))
                    continue
                if self.reveal_solution(step, ctx):
                    return "next"
                continue
            code = editor.text()
            print(style("  ⚙ running your code...", "grey"))
            prog.stats["runs"] += 1
            verdict = grade(step, code)
            if verdict.passed:
                break
            fails += 1
            if key:
                prog.attempts[key] = fails
            print()
            self.show_verdict(verdict, code)
            print()
            self.fail(ctx)
            self.profile.save()
            if fails >= 2 and hints_used < total_hints:
                print(style("  Stuck? Type :hint for a nudge.", "yellow"))
            print(style("  Fix your code and type run again.  (:show  :fix N  :undo  :clear  :edit)", "grey"))
        print()
        print(style("  ✔ EXERCISE COMPLETE", "lime", "bold"))
        self.record(ctx, "code", fails == 0, hints_used)
        print()
        answer = ui.ask(style("  Enter ▸ continue    s ▸ compare with the reference solution ", "grey",
                              prompt=True)).strip().lower()
        if answer == "s":
            ui.code_box(step["solution"], title="Reference solution", color="purple")
            print(style("  (There is usually more than one correct way to solve a problem.)", "grey"))
            ui.pause()
        return "next"

    def reveal_solution(self, step, ctx):
        prompt = "Show the reference solution and move on?"
        if ctx["mode"] == "checkpoint":
            prompt += " (Your checkpoint will be marked as assisted.)"
        if not ui.confirm(prompt):
            return False
        self.fail(ctx)
        ctx["assisted"] = True
        self.prog.stats["solutions"] += 1
        if ctx.get("key") and ctx["key"] not in self.prog.solutions_viewed:
            self.prog.solutions_viewed.append(ctx["key"])
        ui.code_box(step["solution"], title="Reference solution", color="purple")
        ui.render("Read it line by line and make sure you understand **why** it works. Then try writing it "
                  "again yourself in the Playground - retyping builds memory.", indent=4)
        ui.pause()
        return True

    def show_verdict(self, verdict, code):
        v, info = verdict.kind, verdict.info
        if info.get("inputs"):
            print(style("  (test run with input(): " + ", ".join(repr(x) for x in info["inputs"]) + ")", "grey"))
        if v == "empty":
            print(style("  You haven't written any code yet. Type some lines, then run.", "yellow"))
        elif v == "require":
            print(style("  ✘ Your code runs, but this exercise wants you to practise using ", "yellow")
                  + style(" or ".join(info["needed"]), "cyan", "bold") + style(".", "yellow"))
        elif v == "forbid":
            print(style("  ✘ For this exercise, don't use ", "yellow") + style(info["bad"], "cyan", "bold")
                  + style(" - do it the long way for practice.", "yellow"))
        elif v == "error":
            self.prog.note_error(info["error"]["type"])
            if info.get("output"):
                ui.output_box(info["output"], title="Printed before the error", color="grey")
            explain_error(info["error"], code)
        elif v == "timeout":
            self.prog.stats["timeouts"] += 1
            self.prog.note_error("Timeout")
            print(style("  ⏳ Your program was still running after a few seconds, so it was stopped.", "red", "bold"))
            ui.render("This almost always means an **infinite loop**: a `while` loop whose condition never "
                      "becomes False. Make sure something inside the loop changes so the loop can end.", indent=4)
        elif v == "output":
            print(style("  ✘ Your program ran, but its output isn't what was expected.", "red", "bold"))
            ui.output_box(info["expected"], title="Expected output", color="lime")
            ui.output_box(info["got"], title="Your output", color="red")
            print(style("  " + describe_output_difference(info["expected"], info["got"]), "yellow"))
        elif v == "check":
            print(style("  ✘ Not quite yet:", "red", "bold"))
            ui.render(info["message"], indent=4)
            if info.get("output"):
                ui.output_box(info["output"], title="Your program printed", color="grey")
        elif v == "crash":
            print(style("  Something went wrong running your code:", "red"))
            print(style(info["detail"], "grey"))

    # ================================================================ feedback bookkeeping
    def fail(self, ctx):
        self.mistakes += 1
        ctx["failed"] = True

    def record(self, ctx, kind, first_try, hints=0):
        s = self.prog.stats
        if kind == "code":
            s["solved"] += 1
            s["first_try"] += first_try
            s["without_hints"] += hints == 0
        else:
            s[kind + "_total"] += 1
            s[kind + "_right"] += first_try
        clean = first_try and hints == 0
        self.profile.record_answer(clean)
        if ctx.get("key"):
            self.prog.done_steps.add(ctx["key"])
        if clean and self.profile.streak >= 5 and self.profile.streak % 5 == 0:
            print(style("  %d right in a row." % self.profile.streak, "orange", "bold"))

    # ================================================================ checkpoints
    def run_checkpoint(self, pi):
        """Work through a phase checkpoint. Returns True when it was completed."""
        phase = self.phases[pi]
        cp = phase["checkpoint"]
        ui.clear()
        ui.banner("PHASE %d CHECKPOINT: %s" % (phase["number"], cp["title"].upper()), color="gold")
        print()
        ui.render(cp["intro"])
        print()
        ui.render("Complete every task to pass. Hints are available; using the reference solution marks the "
                  "checkpoint as *assisted* (it still unlocks the next phase, and you can retake it any time).")
        print()
        ui.pause("begin")
        self.mistakes = 0
        assisted = False
        steps = cp["steps"]
        for i, step in enumerate(steps):
            ui.clear()
            print(style("  Phase %d checkpoint · %s" % (phase["number"], cp["title"]), "bold", "gold"))
            print("  " + ui.bar(i / len(steps), 24, "gold") + style(" task %d/%d" % (i + 1, len(steps)), "grey"))
            ui.rule("gold")
            ctx = {"mode": "checkpoint", "key": "%s:%d" % (cp["id"], i)}
            self.do_step(step, ctx)
            assisted = assisted or ctx.get("assisted", False)
        first = cp["id"] not in self.prog.checkpoints
        previous = self.prog.checkpoints.get(cp["id"])
        record = {"mistakes": self.mistakes, "assisted": assisted, "date": datetime.date.today().isoformat()}
        if previous is None or (not assisted and (previous["assisted"] or self.mistakes <= previous["mistakes"])):
            self.prog.checkpoints[cp["id"]] = record
        self.profile.save()
        ui.clear()
        ui.banner("CHECKPOINT PASSED: PHASE %d" % phase["number"], color="lime")
        print()
        print(style("  Mistakes along the way: %d%s" % (self.mistakes, "   (assisted)" if assisted else ""), "white"))
        if first and pi + 1 < len(self.phases):
            nxt = self.phases[pi + 1]
            print(style("  Unlocked: Phase %d · %s" % (nxt["number"], nxt["title"]), "cyan", "bold"))
        print()
        ui.pause()
        return True

    # ================================================================ completion
    def course_complete(self):
        ui.clear()
        ui.banner("COURSE COMPLETE · " + self.project.title.upper(), color="gold")
        print()
        ui.render("You've worked through every phase and checkpoint in this project. Open the project's "
                  "README for next steps, and keep using Review practice to keep your skills sharp.")
        print()
        s = self.prog.stats
        print(style("  %d exercises solved · %d first try · %d hints · %d reference solutions viewed" % (
            s["solved"], s["first_try"], s["hints"], s["solutions"]), "cyan", "bold"))
        print()
        ui.pause("return to the menu")

    # ================================================================ reference cards
    def reference_cards(self):
        entries = [(phase, lesson) for phase, lesson in self.project.lessons()
                   if lesson["id"] in self.prog.completed_lessons]
        while True:
            ui.clear()
            ui.banner("REFERENCE CARDS", color="teal")
            if not entries:
                print(style("  Empty for now. Every lesson you finish adds a card.", "grey"))
                ui.pause("go back")
                return
            current = None
            for n, (phase, lesson) in enumerate(entries, 1):
                if phase is not current:
                    current = phase
                    print(style("  Phase %d · %s" % (phase["number"], phase["title"]), "gold", "bold"))
                print("    " + style(str(n).rjust(2) + ".", "cyan") + " " + lesson["title"])
            print()
            answer = ui.ask(style("  Card number to read (Enter to go back): ", "yellow", prompt=True)).strip()
            if not answer:
                return
            if answer.isdigit() and 1 <= int(answer) <= len(entries):
                _, lesson = entries[int(answer) - 1]
                ui.clear()
                ui.banner(lesson["title"], color="teal")
                print()
                ui.render(lesson["summary"])
                print()
                ui.pause("go back")

    # ================================================================ review practice
    def review(self):
        pool = [step for _, lesson in self.project.lessons() if lesson["id"] in self.prog.completed_lessons
                for step in lesson["steps"] if step["type"] in ("quiz", "predict", "code")]
        ui.clear()
        ui.banner("REVIEW PRACTICE", color="orange")
        ui.render("\nRandom questions from lessons you've finished. Coming back to old material is what makes "
                  "it stick.\n")
        quick = [s for s in pool if s["type"] != "code"]
        drills = [s for s in pool if s["type"] == "code"]
        if len(quick) < 3:
            print(style("  Finish a couple of lessons first, then come back.", "grey"))
            ui.pause("go back")
            return
        print("   " + style("[1]", "cyan", "bold") + " Quick round - 6 questions")
        print("   " + style("[2]", "cyan", "bold") + " Coding round - 3 exercises" +
              ("" if len(drills) >= 3 else style(" (needs more finished lessons)", "grey")))
        print("   " + style("[Enter]", "cyan") + " back")
        choice = ui.choose(style("  Choose: ", "yellow", prompt=True), ["1", "2", ""])
        if choice == "" or (choice == "2" and len(drills) < 3):
            return
        rounds = random.sample(quick, min(6, len(quick))) if choice == "1" else random.sample(drills, 3)
        score = 0
        for n, step in enumerate(rounds, 1):
            ui.clear()
            print(style("  REVIEW  ·  question %d of %d  ·  %d right so far" % (n, len(rounds), score), "orange", "bold"))
            ui.rule("orange")
            ctx = {"mode": "review"}
            self.do_step(step, ctx)
            if not ctx.get("failed"):
                score += 1
        self.prog.stats["review_rounds"] += 1
        ui.clear()
        ui.banner("REVIEW RESULT: %d / %d" % (score, len(rounds)), color="orange")
        if score < len(rounds):
            print(style("\n  The ones you missed are worth re-reading on their reference cards.", "grey"))
        print()
        ui.pause()

    # ================================================================ playground
    def playground(self, starter="", embedded=False):
        ui.clear()
        ui.banner("PLAYGROUND", color="teal")
        ui.render("""
Write **any** Python and run it for real. Here `input()` really asks *you*, and if a program runs
forever, press **Ctrl+C** to stop it.
""")
        extra = [(":save NAME", "save to my_programs/NAME.py"), (":load NAME", "load a saved program"),
                 (":list", "list saved programs"), (":back", "leave the playground")]
        print_help(extra)
        print()
        editor = Editor(starter)
        if starter:
            editor.show("Experiment: change it, then type run")
        while True:
            command = editor.collect({"run", "save", "load", "list", "back", "help"})
            if command == "back":
                return
            if command == "help":
                print_help(extra)
            elif command == "run":
                self.run_interactive(editor.text())
            elif command == "list":
                files = sorted(f for f in os.listdir(PROGRAMS_DIR) if f.endswith(".py") and not f.startswith("_")) \
                    if os.path.isdir(PROGRAMS_DIR) else []
                print(style("  Saved programs: " + (", ".join(f[:-3] for f in files) or "(none yet)"), "cyan"))
            elif command in ("save", "load"):
                name = re.sub(r"[^\w-]", "", editor.arg or ui.ask(style("  Program name: ", "yellow", prompt=True)))
                if not name:
                    continue
                path = os.path.join(PROGRAMS_DIR, name + ".py")
                if command == "save":
                    os.makedirs(PROGRAMS_DIR, exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(editor.text() + "\n")
                    print(style("  Saved to " + path, "lime"))
                    print(style("  Run it outside the app with:  python \"" + path + "\"", "grey"))
                elif os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        editor.lines = f.read().rstrip().split("\n")
                    editor.show(name + ".py")
                else:
                    print(style("  No program called " + name, "red"))

    def run_interactive(self, code):
        if not code.strip():
            print(style("  Nothing to run yet.", "grey"))
            return
        os.makedirs(PROGRAMS_DIR, exist_ok=True)
        path = os.path.join(PROGRAMS_DIR, "_playground_run.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code + "\n")
        print(style("  ── running ── (Ctrl+C stops it) ──", "teal"))
        sys.stdout.flush()
        stderr = ""
        try:
            proc = subprocess.run([sys.executable, "-X", "utf8", path], cwd=PROGRAMS_DIR,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            stderr = proc.stderr
        except KeyboardInterrupt:
            print(style("\n  (stopped)", "yellow"))
        print(style("  ── finished ──", "teal"))
        self.prog.stats["playground_runs"] += 1
        if stderr.strip():
            last = stderr.strip().split("\n")[-1]
            etype, _, msg = last.partition(":")
            lines = re.findall(r'_playground_run\.py", line (\d+)', stderr)
            error = {"type": etype.strip().split(".")[-1], "message": msg.strip(),
                     "line": int(lines[-1]) if lines else None}
            self.prog.note_error(error["type"])
            explain_error(error, code)

    # ================================================================ progress screen
    def progress_screen(self):
        prog, s = self.prog, self.prog.stats
        ui.clear()
        ui.banner("YOUR PROGRESS · " + self.project.title.upper(), color="cyan")
        print()
        for pi, phase in enumerate(self.phases):
            total = len(phase["lessons"])
            done = sum(self.lesson_done(pi, li) for li in range(total))
            cp = prog.checkpoints.get(phase["checkpoint"]["id"])
            cp_text = ("checkpoint ✔" + (" (assisted)" if cp["assisted"] else "")) if cp else "checkpoint ·"
            print("  %s %s %s  %s" % (style(("Phase %d" % phase["number"]).ljust(8), "bold", "white"),
                                      ui.bar(done / total if total else 0, 16, "teal"),
                                      style("%d/%d lessons" % (done, total), "teal"),
                                      style(cp_text, "lime" if cp else "grey")))
        print()

        def pct(a, b):
            return "%d%%" % round(100 * a / b) if b else "-"

        print("  Exercises solved %d   first try %s   without hints %s" % (
            s["solved"], pct(s["first_try"], s["solved"]), pct(s["without_hints"], s["solved"])))
        print("  Questions right first time: quizzes %s   predictions %s" % (
            pct(s["quiz_right"], s["quiz_total"]), pct(s["predict_right"], s["predict_total"])))
        print("  Hints used %d   reference solutions viewed %d   code runs %d" % (s["hints"], s["solutions"], s["runs"]))
        print("  Errors met %d (%d kinds: %s)" % (s["errors"], len(s["error_types"]),
                                                ", ".join(s["error_types"][:8]) or "none yet"))
        print("  Best run of first-time answers %d   days in a row %d" % (self.profile.best_streak,
                                                                          self.profile.day_streak))
        print()
        if ui.ask(style("  Enter ▸ back    reset ▸ erase progress for this project ", "grey",
                        prompt=True)).strip().lower() == "reset":
            if ui.confirm("Really erase all progress for %s? This cannot be undone." % self.project.title):
                self.profile.reset_project(self.project.id)
                self.profile.save()
                print(style("  Progress for this project erased.", "yellow"))
                ui.pause()

"""Python Cloud Engineering - hands-on Python for cloud engineers, in your terminal.

    python learn.py                        start (or continue) the course
    python learn.py --project ID           open a specific project
    python learn.py --unlock-all           open every phase (for instructors / reviewers)
    python learn.py list                   list available projects
    python learn.py reset                  erase saved progress for a project
    python learn.py selftest [--phase N]   validate every lesson and exercise

Build exercises (you write parts of a real application in your workspace):

    python learn.py exercises              list exercises and your progress
    python learn.py show ID                read an exercise's task
    python learn.py check [ID]             run an exercise's tests (default: the next unfinished one)
    python learn.py hint ID                reveal the next graduated hint
    python learn.py solution ID            reference solution (after all hints or 3 failed checks)
    python learn.py workspace init         create your workspace (done automatically when needed)
    python learn.py workspace reset FILE   restore one workspace file to its starting state
"""

import sys

if sys.version_info < (3, 11):
    print("This course needs Python 3.11 or newer. You have " + sys.version.split()[0] + ".")
    print("Download the latest Python from https://www.python.org/downloads/")
    sys.exit(1)

import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog="learn.py", description="Python Cloud Engineering")
    parser.add_argument("--project", help="project id (see `learn.py list`)")
    parser.add_argument("--unlock-all", action="store_true", help="open every phase")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="list available projects")
    st = sub.add_parser("selftest", help="validate lessons and exercises")
    st.add_argument("--phase", type=int, help="only check this phase's lessons")
    st.add_argument("--no-exercises", action="store_true", help="skip the build-exercise checks")
    sub.add_parser("reset", help="erase saved progress for a project")
    sub.add_parser("exercises", help="list build exercises and progress")
    for name, text in (("show", "read an exercise's task"), ("hint", "reveal the next hint"),
                       ("solution", "show the reference solution (when unlocked)")):
        sub.add_parser(name, help=text).add_argument("id")
    sub.add_parser("check", help="run an exercise's tests").add_argument("id", nargs="?")
    ws = sub.add_parser("workspace", help="manage your workspace")
    ws.add_argument("action", choices=["init", "reset", "path"])
    ws.add_argument("file", nargs="?", help="for reset: e.g. changegate/plan_parser.py")
    return parser


def session_for(args):
    from pce import exercise_cli, projects
    from pce.progress import Profile

    profile = Profile.load() or Profile()
    if args.project:
        project = projects.find(args.project)
    elif profile.current_project:
        project = projects.find(profile.current_project)
    else:
        found = projects.discover()
        if len(found) != 1:
            raise SystemExit("Use --project to choose a project (see `python learn.py list`).")
        project = found[0]
    profile.current_project = project.id
    return exercise_cli.Session(project, profile)


def exercise_command(args):
    from pce import ui
    from pce.exercises import ExerciseError

    try:
        session = session_for(args)
        if args.command == "exercises":
            session.listing()
            return 0
        if args.command == "workspace":
            if args.action == "path":
                print(session.workspace)
            elif args.action == "init":
                if not session.ensure_workspace():
                    print("Your workspace already exists: " + session.workspace)
            else:
                if not args.file:
                    print("Say which file to reset, e.g. python learn.py workspace reset changegate/plan_parser.py")
                    return 3
                session.ensure_workspace(quiet=True)
                target, backup, reopened = session.reset_file(args.file)
                print("Restored %s%s" % (target, (" (your version saved as %s)" % backup) if backup else ""))
                if reopened:
                    print("These exercises are back to TODO and need checking again: " + ", ".join(reopened))
            return 0
        if args.command == "check" and not args.id:
            exercise = session.next_unfinished()
            if exercise is None:
                print("Every exercise is complete.")
                return 0
        else:
            exercise = session.ex_set.get(args.id)
        if args.command == "show":
            session.ensure_workspace()
            session.show(exercise)
        elif args.command == "check":
            return 0 if session.check(exercise) else 1
        elif args.command == "hint":
            session.hint(exercise)
        elif args.command == "solution":
            session.solution(exercise, confirm=ui.confirm if sys.stdin.isatty() else None)
        return 0
    except ExerciseError as e:
        print(e)
        return 3


def main(argv=None):
    args = build_parser().parse_args(argv)

    from pce import projects as proj

    if args.command == "list":
        for p in proj.discover():
            print("%-28s %s" % (p.id, p.title))
            if p.summary:
                print("%-28s %s" % ("", p.summary))
        return 0

    if args.command == "selftest":
        from pce import selftest
        chosen = [proj.find(args.project)] if args.project else proj.discover()
        return 1 if selftest.run(chosen, only_phase=args.phase, exercises=not args.no_exercises) else 0

    if args.command == "reset":
        from pce.progress import Profile
        profile = Profile.load()
        if profile is None:
            print("No saved progress yet.")
            return 0
        project_id = proj.find(args.project).id if args.project else profile.current_project
        if not project_id:
            print("Use --project to choose which project to reset.")
            return 1
        answer = input("Erase ALL saved progress for %s? Type yes to confirm: " % project_id)
        if answer.strip().lower() == "yes":
            profile.reset_project(project_id)
            profile.save()
            print("Progress erased. (Your workspace files are untouched.)")
        return 0

    if args.command in ("exercises", "show", "check", "hint", "solution", "workspace"):
        return exercise_command(args)

    from pce.engine import App
    App(project=args.project, unlock_all=args.unlock_all).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

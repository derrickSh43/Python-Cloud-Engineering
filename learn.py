"""Python Cloud Engineering - hands-on Python for cloud engineers, in your terminal.

    python learn.py                        start (or continue) the course
    python learn.py --project ID           open a specific project
    python learn.py --unlock-all           open every phase (for instructors / reviewers)
    python learn.py list                   list available projects
    python learn.py selftest [--phase N]   validate every lesson and exercise
    python learn.py reset                  erase saved progress for a project
"""

import sys

if sys.version_info < (3, 11):
    print("This course needs Python 3.11 or newer. You have " + sys.version.split()[0] + ".")
    print("Download the latest Python from https://www.python.org/downloads/")
    sys.exit(1)

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(prog="learn.py", description="Python Cloud Engineering")
    parser.add_argument("--project", help="project id (see `learn.py list`)")
    parser.add_argument("--unlock-all", action="store_true", help="open every phase")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="list available projects")
    st = sub.add_parser("selftest", help="validate lessons and exercises")
    st.add_argument("--phase", type=int, help="only check this phase number")
    sub.add_parser("reset", help="erase saved progress for a project")
    args = parser.parse_args(argv)

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
        return 1 if selftest.run(chosen, only_phase=args.phase) else 0

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
            print("Progress erased.")
        return 0

    from pce.engine import App
    App(project=args.project, unlock_all=args.unlock_all).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

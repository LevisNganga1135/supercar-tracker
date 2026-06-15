# main.py
# ENTRY POINT — wires argparse subcommands to functions in cli/commands.py.
# Loads data from store.json on startup, saves it after any command
# that modifies data.

import argparse
import sys

from models.user import User
from utils.file_io import load_data, save_data
from utils.display import print_banner, print_error, console
from cli import commands


def build_parser() -> argparse.ArgumentParser:
    """
    Build the full argparse CLI structure.
    Each subcommand gets its own parser with --flags and help text.
    """
    parser = argparse.ArgumentParser(
        prog="supercar-tracker",
        description="🏎️  Supercar Dealership Project Management CLI"
    )

    # subparsers = the different commands (add-user, list-projects, etc.)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---------------------------------------------------------- #
    #  USER COMMANDS                                               #
    # ---------------------------------------------------------- #

    # add-user --name "Alex" --role manager --email "alex@dealer.com"
    p = subparsers.add_parser("add-user", help="Create a new staff member")
    p.add_argument("--name", required=True, help="Full name of the staff member")
    p.add_argument(
        "--role", default="sales_rep",
        choices=User.VALID_ROLES,
        help="Staff role (default: sales_rep)"
    )
    p.add_argument("--email", help="Email address (optional)")
    p.set_defaults(func=commands.add_user)

    # list-users
    p = subparsers.add_parser("list-users", help="List all staff members")
    p.set_defaults(func=commands.list_users)

    # view-user --user "Alex"
    p = subparsers.add_parser("view-user", help="Show details for one staff member")
    p.add_argument("--user", required=True, help="User name or ID")
    p.set_defaults(func=commands.view_user)

    # delete-user --user-id 3
    p = subparsers.add_parser("delete-user", help="Delete a staff member and all their data")
    p.add_argument("--user-id", required=True, type=int, help="ID of the user to delete")
    p.set_defaults(func=commands.delete_user)

    # ---------------------------------------------------------- #
    #  PROJECT COMMANDS                                            #
    # ---------------------------------------------------------- #

    # add-project --user "Alex" --title "Ferrari 488 Delivery Prep" --car-model "Ferrari 488" --description "..."
    p = subparsers.add_parser("add-project", help="Add a new project to a user")
    p.add_argument("--user", required=True, help="User name or ID who owns this project")
    p.add_argument("--title", required=True, help="Project title")
    p.add_argument("--car-model", dest="car_model", default="", help="Supercar model (e.g. 'Ferrari 488')")
    p.add_argument("--description", default="", help="Short project description")
    p.set_defaults(func=commands.add_project)

    # list-projects [--user "Alex"]
    p = subparsers.add_parser("list-projects", help="List projects (optionally for one user)")
    p.add_argument("--user", help="Filter to a specific user's projects (name or ID)")
    p.set_defaults(func=commands.list_projects)

    # search-projects --keyword "Ferrari"
    p = subparsers.add_parser("search-projects", help="Search projects by title or car model")
    p.add_argument("--keyword", required=True, help="Search term")
    p.set_defaults(func=commands.search_projects)

    # ---------------------------------------------------------- #
    #  TASK COMMANDS                                               #
    # ---------------------------------------------------------- #

    # add-task --project "Ferrari 488 Delivery Prep" --title "Polish exterior" --priority high --due-date 2025-12-01
    p = subparsers.add_parser("add-task", help="Add a new task to a project")
    p.add_argument("--project", required=True, help="Project title to add the task to")
    p.add_argument("--title", required=True, help="Task title")
    p.add_argument(
        "--priority", default="medium",
        choices=["low", "medium", "high"],
        help="Task priority (default: medium)"
    )
    p.add_argument("--due-date", dest="due_date", help="Due date, e.g. 2025-12-01 (optional)")
    p.set_defaults(func=commands.add_task)

    # list-tasks --project "Ferrari 488 Delivery Prep" [--status pending]
    p = subparsers.add_parser("list-tasks", help="List tasks for a project")
    p.add_argument("--project", required=True, help="Project title")
    p.add_argument(
        "--status", choices=["pending", "in_progress", "complete"],
        help="Filter by task status (optional)"
    )
    p.set_defaults(func=commands.list_tasks)

    # complete-task --project "Ferrari 488 Delivery Prep" --task-id 2
    p = subparsers.add_parser("complete-task", help="Mark a task as complete")
    p.add_argument("--project", required=True, help="Project title")
    p.add_argument("--task-id", required=True, type=int, help="ID of the task to complete")
    p.set_defaults(func=commands.complete_task)

    # assign-task --project "Ferrari 488 Delivery Prep" --task-id 2 --user "Alex"
    p = subparsers.add_parser("assign-task", help="Assign a staff member to a task (contributor)")
    p.add_argument("--project", required=True, help="Project title")
    p.add_argument("--task-id", required=True, type=int, help="ID of the task")
    p.add_argument("--user", required=True, help="User name or ID to assign")
    p.set_defaults(func=commands.assign_task)

    return parser


def main():
    """
    Application entry point.
    1. Show banner
    2. Load existing data from store.json
    3. Parse CLI args and run the matching command
    4. Save data back to disk if the command modified anything
    """
    print_banner()

    # Load all users (and their nested projects/tasks) from disk
    users = load_data()

    parser = build_parser()
    args = parser.parse_args()

    try:
        # Run the matching command function (e.g. commands.add_user)
        needs_save = args.func(args, users)
    except Exception as e:
        # Catch-all so a single bad command doesn't crash with a raw traceback
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

    # Persist changes only if the command actually modified data
    if needs_save:
        save_data(users)

    console.print()  # trailing blank line for readability


if __name__ == "__main__":
    main()
    
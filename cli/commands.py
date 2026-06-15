# cli/commands.py
# All CLI subcommands live here.
# Each function: receives parsed args + the in-memory user list,
# does its job, then returns whether data needs to be saved.

from models.user import User
from models.project import Project
from models.task import Task
from utils.display import (
    console,
    print_users_table,
    print_user_detail,
    print_projects_table,
    print_tasks_table,
    print_success,
    print_error,
)


# ------------------------------------------------------------------ #
#  USER COMMANDS                                                       #
# ------------------------------------------------------------------ #

def add_user(args, users: list) -> bool:
    """
    Create a new User and add them to the in-memory list.
    Returns True if a save is needed.
    """
    # Guard: prevent duplicate names (case-insensitive)
    if User.find_by_name(users, args.name):
        print_error(f"A user named '{args.name}' already exists.")
        return False

    # Validate role BEFORE construction (User has no role setter at init time)
    if args.role.lower() not in User.VALID_ROLES:
        print_error(f"Invalid role '{args.role}'. Choose from: {User.VALID_ROLES}")
        return False

    user = User(name=args.name, role=args.role, email=args.email or "")
    users.append(user)
    print_success(f"User '{user.name}' created with ID #{user.id}.")
    return True


def list_users(args, users: list) -> bool:
    """Display all users in a rich table. No save needed."""
    if not users:
        print_error("No users found. Use 'add-user' to create one.")
        return False

    print_users_table(users)
    return False


def view_user(args, users: list) -> bool:
    """Show a detailed panel for one user (by name or ID)."""
    user = _resolve_user(users, args.user)
    if not user:
        print_error(f"No user found matching '{args.user}'.")
        return False

    print_user_detail(user)
    return False


def delete_user(args, users: list) -> bool:
    """
    Remove a user (and all their projects/tasks) by ID.
    Returns True if a save is needed.
    """
    user = User.find_by_id(users, args.user_id)
    if not user:
        print_error(f"No user found with ID #{args.user_id}.")
        return False

    users.remove(user)
    print_success(f"User '{user.name}' (#{user.id}) and all their data was deleted.")
    return True


# ------------------------------------------------------------------ #
#  PROJECT COMMANDS                                                    #
# ------------------------------------------------------------------ #

def add_project(args, users: list) -> bool:
    """
    Create a new Project and assign it to a user.
    Looks up the user by name (or ID, if --user is numeric).
    """
    user = _resolve_user(users, args.user)
    if not user:
        print_error(f"No user found matching '{args.user}'.")
        return False

    project = Project(
        title=args.title,
        description=args.description or "",
        car_model=args.car_model or "",
    )

    try:
        user.add_project(project)
    except ValueError as e:
        # Duplicate project title for this user
        print_error(str(e))
        return False

    print_success(
        f"Project '{project.title}' (#{project.id}) added to {user.name}."
    )
    return True


def list_projects(args, users: list) -> bool:
    """
    Display projects.
    If --user is given, show only that user's projects.
    Otherwise show every project across every user, one table per user.
    """
    if args.user:
        user = _resolve_user(users, args.user)
        if not user:
            print_error(f"No user found matching '{args.user}'.")
            return False

        if not user.projects:
            print_error(f"{user.name} has no projects yet.")
            return False

        print_projects_table(user.projects, owner_name=user.name)
        return False

    # No --user: print one table per user that has projects
    any_found = False
    for user in users:
        if user.projects:
            any_found = True
            print_projects_table(user.projects, owner_name=user.name)

    if not any_found:
        print_error("No projects found. Use 'add-project' to create one.")

    return False


def search_projects(args, users: list) -> bool:
    """
    Search projects by a keyword in the title or car model,
    across ALL users. Read-only command.
    """
    keyword = args.keyword.lower()
    any_found = False

    for user in users:
        matches = [
            p for p in user.projects
            if keyword in p.title.lower() or keyword in p.car_model.lower()
        ]
        if matches:
            any_found = True
            print_projects_table(matches, owner_name=user.name)

    if not any_found:
        print_error(f"No projects matched '{args.keyword}'.")

    return False


# ------------------------------------------------------------------ #
#  TASK COMMANDS                                                       #
# ------------------------------------------------------------------ #

def add_task(args, users: list) -> bool:
    """
    Add a new Task to a project.
    Project is found by title across ALL users.
    """
    project, _owner = _find_project_anywhere(users, args.project)
    if not project:
        print_error(f"No project found with title '{args.project}'.")
        return False

    try:
        task = Task(title=args.title, priority=args.priority, due_date=args.due_date)
    except ValueError as e:
        print_error(str(e))
        return False

    project.add_task(task)
    print_success(
        f"Task '{task.title}' (#{task.id}) added to project '{project.title}'."
    )
    return True


def list_tasks(args, users: list) -> bool:
    """
    Display tasks for a given project (by title).
    Optionally filter by --status.
    """
    project, owner_name = _find_project_anywhere(users, args.project)
    if not project:
        print_error(f"No project found with title '{args.project}'.")
        return False

    tasks = project.tasks
    if args.status:
        if args.status not in Task.VALID_STATUSES:
            print_error(
                f"Invalid status '{args.status}'. Choose from: {Task.VALID_STATUSES}"
            )
            return False
        tasks = [t for t in tasks if t.status == args.status]

    if not tasks:
        console.print(f"[yellow]No tasks found for project '{project.title}'.[/yellow]")
        return False

    console.print(f"\n[bold]Owner:[/bold] {owner_name}")
    print_tasks_table(tasks, project_title=project.title)
    return False


def complete_task(args, users: list) -> bool:
    """
    Mark a task as complete.
    Finds the project by title, then the task by ID within it.
    """
    project, _owner = _find_project_anywhere(users, args.project)
    if not project:
        print_error(f"No project found with title '{args.project}'.")
        return False

    try:
        task = project.complete_task(args.task_id)
    except ValueError as e:
        print_error(str(e))
        return False

    print_success(f"Task '{task.title}' (#{task.id}) marked as complete.")
    return True


def assign_task(args, users: list) -> bool:
    """
    Assign a user as a contributor to a task (many-to-many relationship).
    Finds the project by title, the task by ID, and the user by name/ID.
    """
    project, _owner = _find_project_anywhere(users, args.project)
    if not project:
        print_error(f"No project found with title '{args.project}'.")
        return False

    task = project.get_task_by_id(args.task_id)
    if not task:
        print_error(f"No task with ID #{args.task_id} found in project '{project.title}'.")
        return False

    contributor = _resolve_user(users, args.user)
    if not contributor:
        print_error(f"No user found matching '{args.user}'.")
        return False

    try:
        task.add_contributor(contributor.id)
    except TypeError as e:
        print_error(str(e))
        return False

    print_success(
        f"{contributor.name} assigned to task '{task.title}' (#{task.id})."
    )
    return True


# ------------------------------------------------------------------ #
#  INTERNAL HELPER FUNCTIONS — not exposed as CLI commands             #
# ------------------------------------------------------------------ #

def _resolve_user(users: list, identifier: str):
    """
    Find a user by either numeric ID or name.
    Lets the CLI accept --user "Alex" OR --user 3.
    """
    if identifier is None:
        return None

    # Try numeric ID first
    if identifier.isdigit():
        user = User.find_by_id(users, int(identifier))
        if user:
            return user

    # Fall back to name lookup
    return User.find_by_name(users, identifier)


def _find_project_anywhere(users: list, title: str):
    """
    Search every user's project list for a matching title (case-insensitive).
    Returns (project, owner_name) or (None, None) if not found.
    """
    for user in users:
        project = user.get_project_by_title(title)
        if project:
            return project, user.name
    return None, None

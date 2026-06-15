# utils/display.py
# DISPLAY ENGINE — all rich terminal output lives here.
# Uses the 'rich' library for beautiful tables, panels, and colored badges.
# Nothing in this file touches data — it only PRESENTS it.

from rich.console import Console        # the main rich output engine
from rich.table import Table            # for drawing tables in the terminal
from rich.panel import Panel            # for bordered info boxes
from rich.text import Text              # for inline colored text
from rich.progress import BarColumn, Progress, TextColumn  # progress bars
from rich import box                    # table border styles


# One shared Console instance used by all functions in this file
# Think of it like a configured printer — we set it up once and reuse it
console = Console()


# ------------------------------------------------------------------ #
#  COLOUR HELPERS                                                      #
# ------------------------------------------------------------------ #

def status_color(status: str) -> str:
    """
    Map a status string to a rich color name.
    Used to color-code status badges consistently across all tables.

    Rich color syntax: "[color]text[/color]"
    """
    colors = {
        # Task statuses
        "pending":     "yellow",
        "in_progress": "cyan",
        "complete":    "green",
        # Project statuses
        "active":      "bright_green",
        "on_hold":     "yellow",
        "completed":   "green",
    }
    # Default to white if status is unrecognised
    return colors.get(status, "white")


def priority_color(priority: str) -> str:
    """Map a priority string to a rich color."""
    colors = {
        "low":    "dim white",
        "medium": "yellow",
        "high":   "bold red",
    }
    return colors.get(priority, "white")


def role_color(role: str) -> str:
    """Map a user role to a rich color."""
    colors = {
        "manager":   "bold magenta",
        "sales_rep": "cyan",
        "mechanic":  "yellow",
        "admin":     "bold blue",
    }
    return colors.get(role, "white")


# ------------------------------------------------------------------ #
#  BANNER                                                              #
# ------------------------------------------------------------------ #

def print_banner():
    """
    Print the app welcome banner.
    Called once at startup in main.py.
    Panel wraps content in a styled border box.
    """
    banner = Text()
    banner.append("🏎️  SUPERCAR DEALERSHIP", style="bold red")
    banner.append("  |  ", style="dim white")
    banner.append("Project Management CLI", style="bold white")
    console.print(Panel(banner, border_style="red", padding=(1, 4)))


# ------------------------------------------------------------------ #
#  USER DISPLAY                                                        #
# ------------------------------------------------------------------ #

def print_users_table(users: list):
    """
    Display all users in a formatted rich Table.
    Each row = one User object.
    """
    if not users:
        console.print("[yellow]No users found. Add one with: add-user --name 'Alex'[/yellow]")
        return

    # Create the table with a styled title and border
    table = Table(
        title="👥  Dealership Staff",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        show_lines=True         # horizontal lines between rows
    )

    # Define columns — ratio controls relative width
    table.add_column("ID",       style="dim",          width=5)
    table.add_column("Name",     style="bold white",   min_width=15)
    table.add_column("Role",     min_width=12)
    table.add_column("Email",    style="dim",          min_width=20)
    table.add_column("Projects", justify="center",     width=10)

    # Add one row per user
    for user in users:
        role_text = f"[{role_color(user.role)}]{user.role}[/{role_color(user.role)}]"
        table.add_row(
            str(user.id),
            user.name,
            role_text,
            user.email or "—",
            str(user.total_projects)
        )

    console.print(table)


def print_user_detail(user):
    """
    Print a detailed panel for a single user including their projects.
    Called by the view-user command.
    """
    info = (
        f"[bold]ID:[/bold]       {user.id}\n"
        f"[bold]Name:[/bold]     {user.name}\n"
        f"[bold]Role:[/bold]     [{role_color(user.role)}]{user.role}[/{role_color(user.role)}]\n"
        f"[bold]Email:[/bold]    {user.email or '—'}\n"
        f"[bold]Projects:[/bold] {user.total_projects}"
    )
    console.print(Panel(info, title=f"[bold red]👤 {user.name}[/bold red]",
                        border_style="red", padding=(1, 2)))


# ------------------------------------------------------------------ #
#  PROJECT DISPLAY                                                     #
# ------------------------------------------------------------------ #

def print_projects_table(projects: list, owner_name: str = ""):
    """
    Display a list of projects in a rich table.
    Optionally show whose projects these are via owner_name.
    """
    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        return

    title = f"📁  Projects" + (f" — {owner_name}" if owner_name else "")

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="magenta",
        header_style="bold magenta",
        show_lines=True
    )

    table.add_column("ID",          style="dim",        width=5)
    table.add_column("Title",       style="bold white", min_width=20)
    table.add_column("Car Model",   style="italic",     min_width=18)
    table.add_column("Status",      min_width=12)
    table.add_column("Progress",    justify="center",   min_width=14)
    table.add_column("Tasks",       justify="center",   width=8)
    table.add_column("Created",     style="dim",        min_width=14)

    for project in projects:
        s_color = status_color(project.status)
        status_text = f"[{s_color}]{project.status}[/{s_color}]"

        progress_text = (
            f"[green]{project.progress}%[/green] "
            f"[dim]({project.completed_tasks}/{project.total_tasks})[/dim]"
        )

        table.add_row(
            str(project.id),
            project.title,
            project.car_model or "—",
            status_text,
            progress_text,
            str(project.total_tasks),
            project.created_at
        )

    console.print(table)


def print_project_detail(project):
    """
    Print a detailed panel for one project including all its tasks.
    Called by the view-project command.
    """
    s_color = status_color(project.status)
    info = (
        f"[bold]ID:[/bold]          {project.id}\n"
        f"[bold]Title:[/bold]       {project.title}\n"
        f"[bold]Car Model:[/bold]   {project.car_model or '—'}\n"
        f"[bold]Description:[/bold] {project.description or '—'}\n"
        f"[bold]Status:[/bold]      [{s_color}]{project.status}[/{s_color}]\n"
        f"[bold]Progress:[/bold]    {project.progress}% "
        f"({project.completed_tasks}/{project.total_tasks} tasks done)\n"
        f"[bold]Created:[/bold]     {project.created_at}"
    )
    console.print(Panel(
        info,
        title=f"[bold magenta]📁 {project.title}[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    ))

    if project.tasks:
        print_tasks_table(project.tasks)
    else:
        console.print("[dim]  No tasks yet. Add one with: add-task --project '...' --title '...'[/dim]")


# ------------------------------------------------------------------ #
#  TASK DISPLAY                                                        #
# ------------------------------------------------------------------ #

def print_tasks_table(tasks: list, project_title: str = ""):
    """
    Display tasks in a rich table.
    Color-codes status and priority for quick scanning.
    """
    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    title = f"✅  Tasks" + (f" — {project_title}" if project_title else "")

    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold cyan",
        show_lines=True
    )

    table.add_column("ID",         style="dim",      width=5)
    table.add_column("Title",      style="bold",     min_width=25)
    table.add_column("Status",     min_width=12)
    table.add_column("Priority",   min_width=10)
    table.add_column("Due Date",   style="dim",      min_width=12)
    table.add_column("Completed",  style="dim",      min_width=16)

    for task in tasks:
        s_color = status_color(task.status)
        status_text = f"[{s_color}]{task.status}[/{s_color}]"

        p_color = priority_color(task.priority)
        priority_text = f"[{p_color}]{task.priority}[/{p_color}]"

        table.add_row(
            str(task.id),
            task.title,
            status_text,
            priority_text,
            task.due_date or "—",
            task.completed_at or "—"
        )

    console.print(table)


# ------------------------------------------------------------------ #
#  SUCCESS / ERROR MESSAGES                                            #
# ------------------------------------------------------------------ #

def print_success(message: str):
    """Green success message with a checkmark."""
    console.print(f"[bold green]✅  {message}[/bold green]")


def print_error(message: str):
    """Red error message with an X."""
    console.print(f"[bold red]❌  {message}[/bold red]")


def print_info(message: str):
    """Dimmed info message for neutral feedback."""
    console.print(f"[dim cyan]ℹ️   {message}[/dim cyan]")


def print_warning(message: str):
    """Yellow warning message."""
    console.print(f"[bold yellow]⚠️   {message}[/bold yellow]")
    
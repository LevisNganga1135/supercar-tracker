# 🏎️ Supercar Dealership Project Management CLI

A command-line project management tool built for a supercar dealership.
Track staff, projects (car-related jobs), and tasks — all from the terminal,
with persistent JSON storage and rich-formatted output.

---

## Features

- **Users** — staff members (managers, sales reps, mechanics, admins)
- **Projects** — car-related jobs (e.g. "Ferrari 488 Delivery Prep"), owned by a user
- **Tasks** — steps within a project (e.g. "Polish exterior"), with status, priority, due dates, and **contributors** (many-to-many: multiple staff can be assigned to one task)
- **Persistence** — all data saved to `data/store.json`, loaded automatically on startup
- **Rich terminal output** — colored tables, panels, and status badges via the [`rich`](https://github.com/Textualize/rich) library
- **Full test suite** — 93 unit tests covering models and CLI commands (`pytest`)

---

## Project Structure
---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd supercar-tracker
```

### 2. Install dependencies

This project uses [`rich`](https://pypi.org/project/rich/) for terminal output and [`python-dateutil`](https://pypi.org/project/python-dateutil/) for date handling.

```bash
pip3 install -r requirements.txt --break-system-packages
```

> If you prefer an isolated environment, use a virtual environment instead:
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

### 3. Run the CLI

```bash
python3 main.py --help
```

---

## Usage

### User commands

```bash
# Create a staff member
python3 main.py add-user --name "Alex" --role manager --email "alex@dealer.com"

# List all staff
python3 main.py list-users

# View one staff member's details
python3 main.py view-user --user "Alex"

# Delete a staff member (and all their data)
python3 main.py delete-user --user-id 1
```

Valid roles: `manager`, `sales_rep`, `mechanic`, `admin`

### Project commands

```bash
# Add a project to a user
python3 main.py add-project --user "Alex" --title "Ferrari 488 Delivery Prep" --car-model "Ferrari 488" --description "Prepare for client delivery"

# List a specific user's projects
python3 main.py list-projects --user "Alex"

# List all projects across all users
python3 main.py list-projects

# Search projects by title or car model
python3 main.py search-projects --keyword "Ferrari"
```

### Task commands

```bash
# Add a task to a project
python3 main.py add-task --project "Ferrari 488 Delivery Prep" --title "Polish exterior" --priority high --due-date 2025-12-01

# List tasks for a project
python3 main.py list-tasks --project "Ferrari 488 Delivery Prep"

# Filter tasks by status
python3 main.py list-tasks --project "Ferrari 488 Delivery Prep" --status pending

# Mark a task complete
python3 main.py complete-task --project "Ferrari 488 Delivery Prep" --task-id 1

# Assign a staff member to a task (contributor)
python3 main.py assign-task --project "Ferrari 488 Delivery Prep" --task-id 1 --user "Alex"
```

Valid priorities: `low`, `medium`, `high`
Valid task statuses: `pending`, `in_progress`, `complete`

---

## Data Model & Relationships
- A **User** owns multiple **Projects**.
- A **Project** owns multiple **Tasks**.
- A **Task** can have multiple **contributors** (user IDs), and a **User** can contribute to many tasks across different projects — this is the many-to-many relationship.

All data is serialized to/from `data/store.json` via `to_dict()` / `from_dict()` methods on each model.

---

## Running Tests

```bash
pip3 install pytest --break-system-packages
pytest -v
```

The test suite covers:
- Model logic: ID counters, validation (`@property` setters), relationships, serialization round-trips, computed properties (`progress`, `total_tasks`)
- CLI commands: success and failure paths for every subcommand, including duplicate guards and many-to-many contributor assignment

---

## Error Handling

- Missing or corrupted `data/store.json` is detected and reset gracefully (with a warning) rather than crashing.
- Invalid input (bad roles, statuses, priorities, emails, empty titles) is rejected with clear error messages via `argparse` `choices` and model property setters.
- All CLI commands catch unexpected exceptions in `main.py` and print a friendly error instead of a raw traceback.

---

## Tech Stack

- Python 3.10+
- [`argparse`](https://docs.python.org/3/library/argparse.html) — CLI structure
- [`json`](https://docs.python.org/3/library/json.html) — data persistence
- [`rich`](https://pypi.org/project/rich/) — terminal tables, panels, colors
- [`python-dateutil`](https://pypi.org/project/python-dateutil/) — date handling
- [`pytest`](https://pypi.org/project/pytest/) — testing
# models/task.py
# TASK — the smallest unit of work in our system.
# Example: "Polish Ferrari exterior", "Check engine oil", "Process paperwork"

from datetime import datetime  # built-in: for timestamps

class Task:
    """
    Represents a single task inside a project.
    Each task has a title, status, priority, due date, timestamps,
    and a list of contributors (user IDs) — a many-to-many relationship
    between Task and User.
    """

    # Class attribute — shared ID counter across ALL Task instances
    _id_counter = 0

    # Valid status values — prevents typos like "complet" or "DONE"
    VALID_STATUSES = ["pending", "in_progress", "complete"]

    # Valid priority levels for a task
    VALID_PRIORITIES = ["low", "medium", "high"]

    def __init__(self, title: str, priority: str = "medium", due_date: str = None):
        # Auto-increment the class-level ID counter
        Task._id_counter += 1
        self._id = Task._id_counter

        # Private attributes — accessed via @property below
        self._title = title.strip()
        self._status = "pending"      # all tasks start as pending
        self._priority = priority.lower()
        self._due_date = due_date       # optional string like "2025-12-01"

        # Many-to-many: list of user IDs assigned to (contributing to) this task
        self._contributors = []

        # Timestamps — recorded automatically on creation
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._completed_at = None       # set only when task is marked complete

    # ------------------------------------------------------------------ #
    #  PROPERTIES — controlled read access to private attributes          #
    # ------------------------------------------------------------------ #

    @property
    def id(self):
        """Read-only ID — no setter so it can never be changed."""
        return self._id

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        """Validate before updating the title."""
        if not value or not isinstance(value, str):
            raise ValueError("Task title must be a non-empty string.")
        self._title = value.strip()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value: str):
        """
        Only allow valid status values.
        If someone tries task.status = 'done' it raises an error.
        """
        if value not in Task.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. Choose from: {Task.VALID_STATUSES}"
            )
        self._status = value
        # If marked complete, record the completion timestamp automatically
        if value == "complete":
            self._completed_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, value: str):
        """Validate priority level."""
        if value.lower() not in Task.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{value}'. Choose from: {Task.VALID_PRIORITIES}"
            )
        self._priority = value.lower()

    @property
    def due_date(self):
        return self._due_date

    @property
    def created_at(self):
        return self._created_at

    @property
    def completed_at(self):
        return self._completed_at

    @property
    def contributors(self):
        """
        Returns the list of user IDs assigned to this task.
        Returned as a copy so callers can't mutate the internal list directly.
        """
        return list(self._contributors)

    # ------------------------------------------------------------------ #
    #  INSTANCE METHODS                                                    #
    # ------------------------------------------------------------------ #

    def mark_complete(self):
        """Convenience method to mark this task as complete."""
        self.status = "complete"  # uses the setter above (auto-sets timestamp)

    def mark_in_progress(self):
        """Convenience method to move task to in_progress."""
        self.status = "in_progress"

    def is_complete(self) -> bool:
        """Returns True if the task is done — useful for filtering."""
        return self._status == "complete"

    def add_contributor(self, user_id: int):
        """
        Assign a user (by ID) to this task.
        Many-to-many: a task can have multiple contributors,
        and a user can contribute to multiple tasks.
        """
        if not isinstance(user_id, int):
            raise TypeError("user_id must be an integer.")
        if user_id not in self._contributors:
            self._contributors.append(user_id)

    def remove_contributor(self, user_id: int):
        """Unassign a user (by ID) from this task."""
        if user_id in self._contributors:
            self._contributors.remove(user_id)

    def has_contributor(self, user_id: int) -> bool:
        """Check if a given user is assigned to this task."""
        return user_id in self._contributors

    # ------------------------------------------------------------------ #
    #  STRING REPRESENTATIONS                                              #
    # ------------------------------------------------------------------ #

    def __str__(self):
        """Clean readable output when you print(task)."""
        contributors_str = (
            ", ".join(f"User#{uid}" for uid in self._contributors)
            if self._contributors else "Unassigned"
        )
        return (
            f"[Task #{self._id}] {self._title} | "
            f"Status: {self._status} | Priority: {self._priority} | "
            f"Due: {self._due_date or 'N/A'} | Contributors: {contributors_str}"
        )

    def __repr__(self):
        """Technical output for debugging."""
        return (
            f"Task(id={self._id}, title='{self._title}', "
            f"status='{self._status}', contributors={self._contributors})"
        )

    # ------------------------------------------------------------------ #
    #  FILE I/O HELPERS                                                    #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """
        Serialize task to a dictionary for JSON storage.
        Called when saving data to store.json.
        """
        return {
            "id": self._id,
            "title": self._title,
            "status": self._status,
            "priority": self._priority,
            "due_date": self._due_date,
            "contributors": self._contributors,
            "created_at": self._created_at,
            "completed_at": self._completed_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Rebuild a Task object from a dictionary (loaded from JSON).
        @classmethod means we call it on the CLASS not an instance:
        task = Task.from_dict({"title": "Polish car", ...})
        """
        # Create the task with core fields
        task = cls(
            title=data["title"],
            priority=data.get("priority", "medium"),
            due_date=data.get("due_date")
        )
        # Restore the saved ID, status, and contributors exactly as they were
        task._id = data["id"]
        task._status = data.get("status", "pending")
        task._contributors = data.get("contributors", [])
        task._created_at = data.get("created_at", task._created_at)
        task._completed_at = data.get("completed_at")
        return task
    
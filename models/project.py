# models/project.py
# PROJECT — a car-related job assigned to a user.
# Example: "Ferrari 488 Delivery Prep", "Lamborghini Huracan Service"
# One project holds MANY tasks — this is a one-to-many relationship.

from datetime import datetime       # built-in: for timestamps
from models.task import Task        # import Task so Project can own Tasks


class Project:
    """
    Represents a project at the supercar dealership.
    A project belongs to one User and contains many Tasks.
    """

    # Class attribute — shared ID counter across ALL Project instances
    _id_counter = 0

    # Valid project status values
    VALID_STATUSES = ["active", "on_hold", "completed"]

    def __init__(self, title: str, description: str = "", car_model: str = ""):
        # Auto-increment the shared project ID counter
        Project._id_counter += 1
        self._id = Project._id_counter

        # Core attributes — private, accessed via @property
        self._title = title.strip()
        self._description = description.strip()
        self._car_model = car_model.strip()   # e.g. "Ferrari 488", "McLaren 720S"
        self._status = "active"               # projects start as active

        # Tasks list — this project OWNS these task objects (one-to-many)
        self._tasks = []

        # Timestamp
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ------------------------------------------------------------------ #
    #  PROPERTIES                                                          #
    # ------------------------------------------------------------------ #

    @property
    def id(self):
        """Read-only unique ID."""
        return self._id

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        """Validate and update the project title."""
        if not value or not isinstance(value, str):
            raise ValueError("Project title must be a non-empty string.")
        self._title = value.strip()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value.strip()

    @property
    def car_model(self):
        return self._car_model

    @car_model.setter
    def car_model(self, value: str):
        """Update which supercar this project is about."""
        self._car_model = value.strip()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value: str):
        """Only allow valid status transitions."""
        if value not in Project.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{value}'. Choose from: {Project.VALID_STATUSES}"
            )
        self._status = value

    @property
    def tasks(self):
        """Return a copy of the tasks list — protects internal list."""
        return list(self._tasks)

    @property
    def created_at(self):
        return self._created_at

    # ------------------------------------------------------------------ #
    #  TASK MANAGEMENT METHODS                                             #
    # ------------------------------------------------------------------ #

    def add_task(self, task: Task):
        """
        Add a Task object to this project.
        We type-check to make sure only Task objects are added.
        """
        if not isinstance(task, Task):
            raise TypeError("Only Task objects can be added to a project.")
        self._tasks.append(task)

    def remove_task(self, task_id: int):
        """
        Remove a task by its ID.
        Uses a list comprehension to filter it out.
        """
        original_count = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.id != task_id]

        # Let the caller know if nothing was removed
        if len(self._tasks) == original_count:
            raise ValueError(f"No task with ID {task_id} found in this project.")

    def get_task_by_id(self, task_id: int):
        """
        Find and return a single task by its ID.
        Returns None if not found — caller must handle that case.
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_status(self, status: str):
        """
        Filter tasks by status.
        Example: project.get_tasks_by_status("pending")
        """
        return [t for t in self._tasks if t.status == status]

    def complete_task(self, task_id: int):
        """
        Find a task by ID and mark it complete.
        Raises an error if the task doesn't exist.
        """
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"Task #{task_id} not found in project '{self._title}'.")
        task.mark_complete()
        return task

    # ------------------------------------------------------------------ #
    #  COMPUTED PROPERTIES — calculated on the fly, not stored            #
    # ------------------------------------------------------------------ #

    @property
    def total_tasks(self):
        """How many tasks does this project have?"""
        return len(self._tasks)

    @property
    def completed_tasks(self):
        """How many tasks are marked complete?"""
        return sum(1 for t in self._tasks if t.is_complete())

    @property
    def progress(self):
        """
        Return completion percentage as an integer (0-100).
        Avoids division by zero if no tasks exist yet.
        """
        if self.total_tasks == 0:
            return 0
        return int((self.completed_tasks / self.total_tasks) * 100)

    # ------------------------------------------------------------------ #
    #  CLASS METHODS                                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def find_by_title(cls, projects: list, title: str):
        """
        Search a list of projects by title (case-insensitive).
        Usage: Project.find_by_title(all_projects, "Ferrari 488")
        """
        title_lower = title.lower()
        for project in projects:
            if project.title.lower() == title_lower:
                return project
        return None

    # ------------------------------------------------------------------ #
    #  STRING REPRESENTATIONS                                              #
    # ------------------------------------------------------------------ #

    def __str__(self):
        """Clean readable summary when you print(project)."""
        return (
            f"[Project #{self._id}] {self._title} | "
            f"Car: {self._car_model or 'N/A'} | "
            f"Status: {self._status} | "
            f"Progress: {self.progress}% ({self.completed_tasks}/{self.total_tasks} tasks)"
        )

    def __repr__(self):
        """Technical output for debugging."""
        return (
            f"Project(id={self._id}, title='{self._title}', "
            f"status='{self._status}', tasks={self.total_tasks})"
        )

    # ------------------------------------------------------------------ #
    #  FILE I/O HELPERS                                                    #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """
        Serialize this project (and all its tasks) to a dictionary.
        Notice we call task.to_dict() for each task — nested serialization.
        """
        return {
            "id": self._id,
            "title": self._title,
            "description": self._description,
            "car_model": self._car_model,
            "status": self._status,
            "created_at": self._created_at,
            "tasks": [task.to_dict() for task in self._tasks]  # nested!
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Rebuild a Project object (and its tasks) from saved JSON data.
        This is the reverse of to_dict().
        """
        project = cls(
            title=data["title"],
            description=data.get("description", ""),
            car_model=data.get("car_model", "")
        )
        # Restore saved ID and status
        project._id = data["id"]
        project._status = data.get("status", "active")
        project._created_at = data.get("created_at", project._created_at)

        # Rebuild each task from its saved dictionary
        for task_data in data.get("tasks", []):
            project._tasks.append(Task.from_dict(task_data))

        return project
    
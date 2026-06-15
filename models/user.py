# models/user.py
# USER — a staff member at the supercar dealership.
# Inherits from Person (gets name + id for free).
# Owns many Projects — this is the top of our data hierarchy.

from models.base import Person          # import the parent class
from models.project import Project      # import Project so User can own them


class User(Person):
    """
    Represents a dealership staff member.
    Inherits name and id from Person.
    Adds role, email, and a list of projects.

    Hierarchy: Person --> User --> owns Projects --> owns Tasks
    """

    # Valid roles at our supercar dealership
    VALID_ROLES = ["manager", "sales_rep", "mechanic", "admin"]

    # Class-level registry of ALL users ever created
    # Useful for lookups without passing lists around
    _all_users = []

    def __init__(self, name: str, role: str = "sales_rep", email: str = ""):
        # Call the PARENT __init__ first — this sets up _id and _name
        # super() refers to the Person class above us in the hierarchy
        super().__init__(name)

        # User-specific private attributes
        self._role = role.lower()
        self._email = email.strip()

        # Projects list — this user OWNS these project objects
        self._projects = []

        # Register this user in the class-level list
        User._all_users.append(self)

    # ------------------------------------------------------------------ #
    #  PROPERTIES                                                          #
    # ------------------------------------------------------------------ #

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value: str):
        """Only allow valid dealership roles."""
        if value.lower() not in User.VALID_ROLES:
            raise ValueError(
                f"Invalid role '{value}'. Choose from: {User.VALID_ROLES}"
            )
        self._role = value.lower()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value: str):
        """Basic email validation."""
        if value and "@" not in value:
            raise ValueError("Invalid email address — must contain '@'.")
        self._email = value.strip()

    @property
    def projects(self):
        """Return a copy of the projects list — protects internal state."""
        return list(self._projects)

    # ------------------------------------------------------------------ #
    #  PROJECT MANAGEMENT METHODS                                          #
    # ------------------------------------------------------------------ #

    def add_project(self, project: Project):
        """
        Assign a Project to this user.
        Type-checks to ensure only Project objects are added.
        """
        if not isinstance(project, Project):
            raise TypeError("Only Project objects can be added to a user.")

        # Prevent duplicate project titles for the same user
        for p in self._projects:
            if p.title.lower() == project.title.lower():
                raise ValueError(
                    f"User '{self.name}' already has a project called '{project.title}'."
                )
        self._projects.append(project)

    def remove_project(self, project_id: int):
        """Remove a project from this user by project ID."""
        original_count = len(self._projects)
        self._projects = [p for p in self._projects if p.id != project_id]

        if len(self._projects) == original_count:
            raise ValueError(f"No project with ID {project_id} found for '{self.name}'.")

    def get_project_by_title(self, title: str):
        """
        Find one of this user's projects by title (case-insensitive).
        Returns None if not found.
        """
        for project in self._projects:
            if project.title.lower() == title.lower():
                return project
        return None

    def get_project_by_id(self, project_id: int):
        """Find one of this user's projects by ID."""
        for project in self._projects:
            if project.id == project_id:
                return project
        return None

    def get_active_projects(self):
        """Return only projects with 'active' status."""
        return [p for p in self._projects if p.status == "active"]

    # ------------------------------------------------------------------ #
    #  COMPUTED PROPERTIES                                                 #
    # ------------------------------------------------------------------ #

    @property
    def total_projects(self):
        """How many projects does this user have?"""
        return len(self._projects)

    @property
    def is_manager(self):
        """Quick boolean check — useful in conditionals."""
        return self._role == "manager"

    # ------------------------------------------------------------------ #
    #  CLASS METHODS — operate on the class, not a single instance        #
    # ------------------------------------------------------------------ #

    @classmethod
    def find_by_name(cls, users: list, name: str):
        """
        Search a list of users by name (case-insensitive).
        Usage: User.find_by_name(all_users, "Alex")
        Returns the user object or None.
        """
        for user in users:
            if user.name.lower() == name.lower():
                return user
        return None

    @classmethod
    def find_by_id(cls, users: list, user_id: int):
        """Search a list of users by their ID."""
        for user in users:
            if user.id == user_id:
                return user
        return None

    @classmethod
    def get_all(cls):
        """
        Return the class-level registry of all users.
        Usage: User.get_all()
        """
        return list(cls._all_users)

    @classmethod
    def clear_all(cls):
        """
        Clear the registry — mainly used in tests to reset state.
        Without this, tests would bleed into each other.
        """
        cls._all_users = []

    # ------------------------------------------------------------------ #
    #  STRING REPRESENTATIONS                                              #
    # ------------------------------------------------------------------ #

    def __str__(self):
        """
        Overrides Person.__str__() with richer User info.
        This is METHOD OVERRIDING — a key OOP concept.
        """
        return (
            f"[User #{self.id}] {self.name} | "
            f"Role: {self._role} | "
            f"Email: {self._email or 'N/A'} | "
            f"Projects: {self.total_projects}"
        )

    def __repr__(self):
        return (
            f"User(id={self.id}, name='{self.name}', "
            f"role='{self._role}', projects={self.total_projects})"
        )

    # ------------------------------------------------------------------ #
    #  FILE I/O HELPERS                                                    #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """
        Serialize user + all their projects to a dictionary.
        Extends Person.to_dict() with extra User fields.
        """
        base = super().to_dict()        # get {"id": ..., "name": ...} from Person
        base.update({                   # add User-specific fields on top
            "role": self._role,
            "email": self._email,
            "projects": [p.to_dict() for p in self._projects]  # nested!
        })
        return base

    @classmethod
    def from_dict(cls, data: dict):
        """
        Rebuild a User (and all their projects/tasks) from saved JSON.
        Called when loading store.json at startup.
        """
        user = cls(
            name=data["name"],
            role=data.get("role", "sales_rep"),
            email=data.get("email", "")
        )
        # Restore the exact saved ID
        user._id = data["id"]

        # Rebuild each project from its saved dictionary
        for project_data in data.get("projects", []):
            user._projects.append(Project.from_dict(project_data))

        return user
    
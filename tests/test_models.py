# tests/test_models.py
# Unit tests for User, Project, Task, and Person (base class).
# Run with: pytest tests/test_models.py -v

import pytest

from models.base import Person
from models.user import User
from models.project import Project
from models.task import Task


@pytest.fixture(autouse=True)
def reset_state():
    """
    Runs automatically before EVERY test in this file.
    Class-level ID counters and registries are shared across instances,
    so we reset them here to keep tests fully independent of each other.
    Person._id_counter is reset too, since User.__init__ calls
    super().__init__() which increments it for every User as well.
    """
    Person._id_counter = 0
    User.clear_all()
    User._id_counter = 0
    Project._id_counter = 0
    Task._id_counter = 0
    yield


# ------------------------------------------------------------------ #
#  PERSON (base class)                                                 #
# ------------------------------------------------------------------ #

class TestPerson:
    def test_person_has_id_and_name(self):
        p = Person("Sam")
        assert p.name == "Sam"
        assert p.id == 1

    def test_person_ids_increment(self):
        p1 = Person("Sam")
        p2 = Person("Jordan")
        assert p2.id == p1.id + 1

    def test_person_to_dict(self):
        p = Person("Sam")
        data = p.to_dict()
        assert data["id"] == 1
        assert data["name"] == "Sam"


# ------------------------------------------------------------------ #
#  USER                                                                #
# ------------------------------------------------------------------ #

class TestUser:
    def test_user_inherits_person(self):
        """User should get id/name behavior from Person via inheritance."""
        u = User("Alex", role="manager")
        assert isinstance(u, Person)
        assert u.name == "Alex"
        assert u.id == 1

    def test_user_default_role(self):
        u = User("Alex")
        assert u.role == "sales_rep"

    def test_user_role_setter_valid(self):
        u = User("Alex")
        u.role = "mechanic"
        assert u.role == "mechanic"

    def test_user_role_setter_invalid_raises(self):
        u = User("Alex")
        with pytest.raises(ValueError):
            u.role = "ceo"

    def test_user_email_setter_invalid_raises(self):
        u = User("Alex")
        with pytest.raises(ValueError):
            u.email = "not-an-email"

    def test_user_email_setter_valid(self):
        u = User("Alex")
        u.email = "alex@dealer.com"
        assert u.email == "alex@dealer.com"

    def test_add_project_success(self):
        u = User("Alex")
        proj = Project("Ferrari 488 Delivery Prep", car_model="Ferrari 488")
        u.add_project(proj)
        assert u.total_projects == 1
        assert u.projects[0].title == "Ferrari 488 Delivery Prep"

    def test_add_project_rejects_non_project(self):
        u = User("Alex")
        with pytest.raises(TypeError):
            u.add_project("not a project")

    def test_add_project_duplicate_title_raises(self):
        u = User("Alex")
        u.add_project(Project("Ferrari 488 Delivery Prep"))
        with pytest.raises(ValueError):
            u.add_project(Project("Ferrari 488 Delivery Prep"))

    def test_remove_project(self):
        u = User("Alex")
        proj = Project("Ferrari 488 Delivery Prep")
        u.add_project(proj)
        u.remove_project(proj.id)
        assert u.total_projects == 0

    def test_remove_project_missing_raises(self):
        u = User("Alex")
        with pytest.raises(ValueError):
            u.remove_project(999)

    def test_get_project_by_title_case_insensitive(self):
        u = User("Alex")
        u.add_project(Project("Ferrari 488 Delivery Prep"))
        found = u.get_project_by_title("ferrari 488 delivery prep")
        assert found is not None
        assert found.title == "Ferrari 488 Delivery Prep"

    def test_get_project_by_title_not_found(self):
        u = User("Alex")
        assert u.get_project_by_title("Nonexistent") is None

    def test_is_manager_property(self):
        manager = User("Alex", role="manager")
        rep = User("Jordan", role="sales_rep")
        assert manager.is_manager is True
        assert rep.is_manager is False

    def test_find_by_name(self):
        u1 = User("Alex")
        User("Jordan")
        found = User.find_by_name(User.get_all(), "alex")  # case-insensitive
        assert found is u1

    def test_find_by_name_not_found(self):
        User("Alex")
        assert User.find_by_name(User.get_all(), "Nobody") is None

    def test_find_by_id(self):
        u1 = User("Alex")
        found = User.find_by_id(User.get_all(), u1.id)
        assert found is u1

    def test_get_all_registry(self):
        User("Alex")
        User("Jordan")
        assert len(User.get_all()) == 2

    def test_clear_all_resets_registry(self):
        User("Alex")
        User.clear_all()
        assert User.get_all() == []

    def test_user_to_dict_and_from_dict_round_trip(self):
        u = User("Alex", role="manager", email="alex@dealer.com")
        proj = Project("Ferrari 488 Delivery Prep", car_model="Ferrari 488")
        proj.add_task(Task("Polish exterior", priority="high"))
        u.add_project(proj)

        data = u.to_dict()
        rebuilt = User.from_dict(data)

        assert rebuilt.id == u.id
        assert rebuilt.name == "Alex"
        assert rebuilt.role == "manager"
        assert rebuilt.email == "alex@dealer.com"
        assert rebuilt.total_projects == 1
        assert rebuilt.projects[0].title == "Ferrari 488 Delivery Prep"
        assert rebuilt.projects[0].tasks[0].title == "Polish exterior"


# ------------------------------------------------------------------ #
#  PROJECT                                                             #
# ------------------------------------------------------------------ #

class TestProject:
    def test_project_creation_defaults(self):
        proj = Project("Ferrari 488 Delivery Prep")
        assert proj.title == "Ferrari 488 Delivery Prep"
        assert proj.status == "active"
        assert proj.total_tasks == 0

    def test_project_ids_increment(self):
        p1 = Project("Project A")
        p2 = Project("Project B")
        assert p2.id == p1.id + 1

    def test_title_setter_invalid_raises(self):
        proj = Project("Valid Title")
        with pytest.raises(ValueError):
            proj.title = ""

    def test_status_setter_valid(self):
        proj = Project("Ferrari 488 Delivery Prep")
        proj.status = "on_hold"
        assert proj.status == "on_hold"

    def test_status_setter_invalid_raises(self):
        proj = Project("Ferrari 488 Delivery Prep")
        with pytest.raises(ValueError):
            proj.status = "cancelled"

    def test_add_task_success(self):
        proj = Project("Ferrari 488 Delivery Prep")
        task = Task("Polish exterior")
        proj.add_task(task)
        assert proj.total_tasks == 1

    def test_add_task_rejects_non_task(self):
        proj = Project("Ferrari 488 Delivery Prep")
        with pytest.raises(TypeError):
            proj.add_task("not a task")

    def test_remove_task(self):
        proj = Project("Ferrari 488 Delivery Prep")
        task = Task("Polish exterior")
        proj.add_task(task)
        proj.remove_task(task.id)
        assert proj.total_tasks == 0

    def test_remove_task_missing_raises(self):
        proj = Project("Ferrari 488 Delivery Prep")
        with pytest.raises(ValueError):
            proj.remove_task(999)

    def test_get_task_by_id(self):
        proj = Project("Ferrari 488 Delivery Prep")
        task = Task("Polish exterior")
        proj.add_task(task)
        assert proj.get_task_by_id(task.id) is task

    def test_get_tasks_by_status(self):
        proj = Project("Ferrari 488 Delivery Prep")
        t1 = Task("Polish exterior")
        t2 = Task("Check engine")
        t2.mark_complete()
        proj.add_task(t1)
        proj.add_task(t2)
        pending = proj.get_tasks_by_status("pending")
        complete = proj.get_tasks_by_status("complete")
        assert pending == [t1]
        assert complete == [t2]

    def test_complete_task(self):
        proj = Project("Ferrari 488 Delivery Prep")
        task = Task("Polish exterior")
        proj.add_task(task)
        proj.complete_task(task.id)
        assert task.is_complete() is True

    def test_complete_task_missing_raises(self):
        proj = Project("Ferrari 488 Delivery Prep")
        with pytest.raises(ValueError):
            proj.complete_task(999)

    def test_progress_zero_when_no_tasks(self):
        proj = Project("Ferrari 488 Delivery Prep")
        assert proj.progress == 0

    def test_progress_calculation(self):
        proj = Project("Ferrari 488 Delivery Prep")
        t1 = Task("Polish exterior")
        t2 = Task("Check engine")
        proj.add_task(t1)
        proj.add_task(t2)
        proj.complete_task(t1.id)
        assert proj.progress == 50
        assert proj.completed_tasks == 1
        assert proj.total_tasks == 2

    def test_find_by_title(self):
        p1 = Project("Ferrari 488 Delivery Prep")
        p2 = Project("Lamborghini Service")
        found = Project.find_by_title([p1, p2], "lamborghini service")  # case-insensitive
        assert found is p2

    def test_find_by_title_not_found(self):
        p1 = Project("Ferrari 488 Delivery Prep")
        assert Project.find_by_title([p1], "Nonexistent") is None

    def test_project_to_dict_and_from_dict_round_trip(self):
        proj = Project("Ferrari 488 Delivery Prep", description="Get it ready", car_model="Ferrari 488")
        proj.add_task(Task("Polish exterior", priority="high", due_date="2025-12-01"))
        proj.status = "on_hold"

        data = proj.to_dict()
        rebuilt = Project.from_dict(data)

        assert rebuilt.id == proj.id
        assert rebuilt.title == "Ferrari 488 Delivery Prep"
        assert rebuilt.car_model == "Ferrari 488"
        assert rebuilt.status == "on_hold"
        assert rebuilt.total_tasks == 1
        assert rebuilt.tasks[0].title == "Polish exterior"
        assert rebuilt.tasks[0].priority == "high"
        assert rebuilt.tasks[0].due_date == "2025-12-01"


# ------------------------------------------------------------------ #
#  TASK                                                                #
# ------------------------------------------------------------------ #

class TestTask:
    def test_task_creation_defaults(self):
        task = Task("Polish exterior")
        assert task.title == "Polish exterior"
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.completed_at is None
        assert task.contributors == []

    def test_task_ids_increment(self):
        t1 = Task("Task A")
        t2 = Task("Task B")
        assert t2.id == t1.id + 1

    def test_title_setter_invalid_raises(self):
        task = Task("Valid title")
        with pytest.raises(ValueError):
            task.title = ""

    def test_status_setter_valid(self):
        task = Task("Polish exterior")
        task.status = "in_progress"
        assert task.status == "in_progress"

    def test_status_setter_invalid_raises(self):
        task = Task("Polish exterior")
        with pytest.raises(ValueError):
            task.status = "done"

    def test_mark_complete_sets_timestamp(self):
        task = Task("Polish exterior")
        assert task.completed_at is None
        task.mark_complete()
        assert task.status == "complete"
        assert task.completed_at is not None

    def test_mark_in_progress(self):
        task = Task("Polish exterior")
        task.mark_in_progress()
        assert task.status == "in_progress"

    def test_is_complete(self):
        task = Task("Polish exterior")
        assert task.is_complete() is False
        task.mark_complete()
        assert task.is_complete() is True

    def test_priority_setter_valid(self):
        task = Task("Polish exterior")
        task.priority = "high"
        assert task.priority == "high"

    def test_priority_setter_invalid_raises(self):
        task = Task("Polish exterior")
        with pytest.raises(ValueError):
            task.priority = "urgent"

    def test_add_contributor(self):
        task = Task("Polish exterior")
        task.add_contributor(1)
        assert task.contributors == [1]

    def test_add_contributor_no_duplicates(self):
        task = Task("Polish exterior")
        task.add_contributor(1)
        task.add_contributor(1)
        assert task.contributors == [1]

    def test_add_contributor_multiple_users(self):
        """Many-to-many: a task can have multiple contributors."""
        task = Task("Polish exterior")
        task.add_contributor(1)
        task.add_contributor(2)
        assert task.contributors == [1, 2]

    def test_add_contributor_invalid_type_raises(self):
        task = Task("Polish exterior")
        with pytest.raises(TypeError):
            task.add_contributor("not-an-id")

    def test_remove_contributor(self):
        task = Task("Polish exterior")
        task.add_contributor(1)
        task.remove_contributor(1)
        assert task.contributors == []

    def test_remove_contributor_not_present_is_noop(self):
        task = Task("Polish exterior")
        task.remove_contributor(999)  # should not raise
        assert task.contributors == []

    def test_has_contributor(self):
        task = Task("Polish exterior")
        task.add_contributor(1)
        assert task.has_contributor(1) is True
        assert task.has_contributor(2) is False

    def test_contributors_returns_copy(self):
        """Mutating the returned list should not affect internal state."""
        task = Task("Polish exterior")
        task.add_contributor(1)
        contributors = task.contributors
        contributors.append(99)
        assert task.contributors == [1]

    def test_task_to_dict_and_from_dict_round_trip(self):
        task = Task("Polish exterior", priority="high", due_date="2025-12-01")
        task.add_contributor(1)
        task.add_contributor(2)
        task.mark_complete()

        data = task.to_dict()
        rebuilt = Task.from_dict(data)

        assert rebuilt.id == task.id
        assert rebuilt.title == "Polish exterior"
        assert rebuilt.priority == "high"
        assert rebuilt.due_date == "2025-12-01"
        assert rebuilt.status == "complete"
        assert rebuilt.completed_at == task.completed_at
        assert rebuilt.contributors == [1, 2]
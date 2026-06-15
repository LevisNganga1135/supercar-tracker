# tests/test_commands.py
# Unit tests for cli/commands.py — tests CLI command functions directly
# by simulating argparse Namespace objects, without spawning subprocesses.
# Run with: pytest tests/test_commands.py -v

import pytest
from argparse import Namespace

from models.base import Person
from models.user import User
from models.project import Project
from models.task import Task
from cli import commands


@pytest.fixture(autouse=True)
def reset_state():
    """
    Reset all class-level registries/counters before every test.
    Person._id_counter is reset too, since User.__init__ calls
    super().__init__() which increments it for every User as well.
    """
    Person._id_counter = 0
    User.clear_all()
    User._id_counter = 0
    Project._id_counter = 0
    Task._id_counter = 0
    yield


@pytest.fixture
def users():
    """A fresh empty user list — the in-memory 'database' passed to commands."""
    return []


def ns(**kwargs):
    """
    Shorthand for building an argparse.Namespace.
    Lets tests write ns(name="Alex", role="manager", email=None)
    instead of Namespace(name="Alex", role="manager", email=None).
    """
    return Namespace(**kwargs)


# ------------------------------------------------------------------ #
#  add_user                                                            #
# ------------------------------------------------------------------ #

class TestAddUser:
    def test_add_user_success(self, users):
        args = ns(name="Alex", role="manager", email="alex@dealer.com")
        result = commands.add_user(args, users)
        assert result is True
        assert len(users) == 1
        assert users[0].name == "Alex"
        assert users[0].role == "manager"

    def test_add_user_duplicate_name_rejected(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        result = commands.add_user(ns(name="Alex", role="sales_rep", email=None), users)
        assert result is False
        assert len(users) == 1  # second add did NOT happen

    def test_add_user_invalid_role_rejected(self, users):
        args = ns(name="Alex", role="ceo", email=None)
        result = commands.add_user(args, users)
        assert result is False
        assert len(users) == 0


# ------------------------------------------------------------------ #
#  list_users / view_user / delete_user                                #
# ------------------------------------------------------------------ #

class TestUserListing:
    def test_list_users_empty_returns_false(self, users):
        result = commands.list_users(ns(), users)
        assert result is False

    def test_list_users_with_data(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        result = commands.list_users(ns(), users)
        assert result is False  # listing never triggers a save

    def test_view_user_found(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        result = commands.view_user(ns(user="Alex"), users)
        assert result is False

    def test_view_user_not_found(self, users):
        result = commands.view_user(ns(user="Nobody"), users)
        assert result is False

    def test_delete_user_success(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        user_id = users[0].id
        result = commands.delete_user(ns(user_id=user_id), users)
        assert result is True
        assert len(users) == 0

    def test_delete_user_not_found(self, users):
        result = commands.delete_user(ns(user_id=999), users)
        assert result is False


# ------------------------------------------------------------------ #
#  add_project / list_projects / search_projects                      #
# ------------------------------------------------------------------ #

class TestProjectCommands:
    def test_add_project_success(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        args = ns(user="Alex", title="Ferrari 488 Delivery Prep",
                   car_model="Ferrari 488", description="Get it ready")
        result = commands.add_project(args, users)
        assert result is True
        assert users[0].total_projects == 1
        assert users[0].projects[0].title == "Ferrari 488 Delivery Prep"

    def test_add_project_user_not_found(self, users):
        args = ns(user="Nobody", title="Ferrari 488 Delivery Prep",
                   car_model="", description="")
        result = commands.add_project(args, users)
        assert result is False

    def test_add_project_resolves_user_by_id(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        user_id = users[0].id
        args = ns(user=str(user_id), title="Ferrari 488 Delivery Prep",
                   car_model="", description="")
        result = commands.add_project(args, users)
        assert result is True
        assert users[0].total_projects == 1

    def test_add_project_duplicate_title_rejected(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        args = ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="", description="")
        commands.add_project(args, users)
        result = commands.add_project(args, users)
        assert result is False
        assert users[0].total_projects == 1

    def test_list_projects_for_specific_user(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        commands.add_project(
            ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="", description=""),
            users
        )
        result = commands.list_projects(ns(user="Alex"), users)
        assert result is False

    def test_list_projects_user_not_found(self, users):
        result = commands.list_projects(ns(user="Nobody"), users)
        assert result is False

    def test_list_projects_no_filter_shows_all(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        commands.add_project(
            ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="", description=""),
            users
        )
        result = commands.list_projects(ns(user=None), users)
        assert result is False

    def test_list_projects_empty_overall(self, users):
        result = commands.list_projects(ns(user=None), users)
        assert result is False

    def test_search_projects_finds_match(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        commands.add_project(
            ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="Ferrari 488", description=""),
            users
        )
        result = commands.search_projects(ns(keyword="ferrari"), users)
        assert result is False

    def test_search_projects_no_match(self, users):
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        commands.add_project(
            ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="Ferrari 488", description=""),
            users
        )
        result = commands.search_projects(ns(keyword="lamborghini"), users)
        assert result is False


# ------------------------------------------------------------------ #
#  add_task / list_tasks / complete_task / assign_task                #
# ------------------------------------------------------------------ #

class TestTaskCommands:
    def _setup_project(self, users):
        """Helper: create a user with one project, return the project title."""
        commands.add_user(ns(name="Alex", role="manager", email=None), users)
        commands.add_project(
            ns(user="Alex", title="Ferrari 488 Delivery Prep", car_model="Ferrari 488", description=""),
            users
        )
        return "Ferrari 488 Delivery Prep"

    def test_add_task_success(self, users):
        title = self._setup_project(users)
        args = ns(project=title, title="Polish exterior", priority="high", due_date=None)
        result = commands.add_task(args, users)
        assert result is True

        project = users[0].get_project_by_title(title)
        assert project.total_tasks == 1
        assert project.tasks[0].title == "Polish exterior"
        assert project.tasks[0].priority == "high"

    def test_add_task_project_not_found(self, users):
        args = ns(project="Nonexistent", title="Polish exterior", priority="medium", due_date=None)
        result = commands.add_task(args, users)
        assert result is False

    def test_list_tasks_for_project(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)
        result = commands.list_tasks(ns(project=title, status=None), users)
        assert result is False

    def test_list_tasks_project_not_found(self, users):
        result = commands.list_tasks(ns(project="Nonexistent", status=None), users)
        assert result is False

    def test_list_tasks_filtered_by_status(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)
        commands.add_task(ns(project=title, title="Check engine", priority="medium", due_date=None), users)

        project = users[0].get_project_by_title(title)
        project.tasks[0].mark_complete()  # complete the first task

        result = commands.list_tasks(ns(project=title, status="complete"), users)
        assert result is False

    def test_list_tasks_invalid_status_rejected(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)
        result = commands.list_tasks(ns(project=title, status="urgent"), users)
        assert result is False

    def test_complete_task_success(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)

        project = users[0].get_project_by_title(title)
        task_id = project.tasks[0].id

        result = commands.complete_task(ns(project=title, task_id=task_id), users)
        assert result is True
        assert project.tasks[0].is_complete() is True

    def test_complete_task_missing_task_id(self, users):
        title = self._setup_project(users)
        result = commands.complete_task(ns(project=title, task_id=999), users)
        assert result is False

    def test_complete_task_project_not_found(self, users):
        result = commands.complete_task(ns(project="Nonexistent", task_id=1), users)
        assert result is False

    def test_assign_task_success(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)

        project = users[0].get_project_by_title(title)
        task_id = project.tasks[0].id

        result = commands.assign_task(ns(project=title, task_id=task_id, user="Alex"), users)
        assert result is True

        task = project.get_task_by_id(task_id)
        assert task.has_contributor(users[0].id) is True

    def test_assign_task_project_not_found(self, users):
        result = commands.assign_task(ns(project="Nonexistent", task_id=1, user="Alex"), users)
        assert result is False

    def test_assign_task_missing_task_id(self, users):
        title = self._setup_project(users)
        result = commands.assign_task(ns(project=title, task_id=999, user="Alex"), users)
        assert result is False

    def test_assign_task_user_not_found(self, users):
        title = self._setup_project(users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)

        project = users[0].get_project_by_title(title)
        task_id = project.tasks[0].id

        result = commands.assign_task(ns(project=title, task_id=task_id, user="Nobody"), users)
        assert result is False

    def test_assign_task_multiple_contributors(self, users):
        """Many-to-many: multiple users can be assigned to the same task."""
        title = self._setup_project(users)
        commands.add_user(ns(name="Jordan", role="mechanic", email=None), users)
        commands.add_task(ns(project=title, title="Polish exterior", priority="high", due_date=None), users)

        project = users[0].get_project_by_title(title)
        task_id = project.tasks[0].id

        commands.assign_task(ns(project=title, task_id=task_id, user="Alex"), users)
        commands.assign_task(ns(project=title, task_id=task_id, user="Jordan"), users)

        task = project.get_task_by_id(task_id)
        assert len(task.contributors) == 2
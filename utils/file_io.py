# utils/file_io.py
# FILE I/O ENGINE — handles all saving and loading of data.
# All data lives in data/store.json as a nested JSON structure.
# This module is the only place that touches the file system.

import json                         # built-in: read/write JSON
import os                           # built-in: check if file/folder exists

from models.base import Person      # needed to sync the Person ID counter (drives user.id)
from models.user import User        # needed to rebuild User objects from JSON
from models.task import Task        # needed to sync ID counters after loading
from models.project import Project  # needed to sync ID counters after loading


# ------------------------------------------------------------------ #
#  PATH CONFIGURATION                                                  #
# ------------------------------------------------------------------ #

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "store.json")


# ------------------------------------------------------------------ #
#  SAVE                                                                #
# ------------------------------------------------------------------ #

def save_data(users: list):
    """
    Serialize all users (and their projects/tasks) to JSON and write
    to data/store.json.

    Flow:
      User objects --> to_dict() --> Python dict --> json.dump --> file

    Args:
        users: list of User objects to persist
    """
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    data = {
        "users": [user.to_dict() for user in users],

        # Save ID counters so they don't reset on next load.
        # NOTE: user.id is driven by Person._id_counter (User inherits
        # from Person and never overrides _id), so we save THAT —
        # not User._id_counter, which is never incremented or read.
        "meta": {
            "person_id_counter": Person._id_counter,
            "project_id_counter": Project._id_counter,
            "task_id_counter": Task._id_counter
        }
    }

    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        raise OSError(f"Failed to save data to '{DATA_FILE}': {e}")


# ------------------------------------------------------------------ #
#  LOAD                                                                #
# ------------------------------------------------------------------ #

def load_data() -> list:
    """
    Read data/store.json and rebuild all User objects
    (with their nested Projects and Tasks).

    Flow:
      file --> json.load --> Python dict --> from_dict() --> User objects

    Returns:
        list of User objects, or empty list if no file exists yet
    """

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

    except json.JSONDecodeError as e:
        print(f"Warning: store.json is corrupted and will be reset. ({e})")
        return []

    except OSError as e:
        raise OSError(f"Failed to read data from '{DATA_FILE}': {e}")

    # Rebuild each User object (which rebuilds its Projects and Tasks).
    # NOTE: each from_dict() call constructs objects via __init__, which
    # increments the relevant _id_counter even though the saved ID is
    # restored afterward — so the counters get "polluted" during loading.
    # We fix this below by recomputing counters from the actual data.
    users = []
    for user_data in data.get("users", []):
        try:
            user = User.from_dict(user_data)
            users.append(user)
        except (KeyError, ValueError) as e:
            print(f"Warning: Skipping corrupted user record: {e}")

    # ------------------------------------------------------------ #
    # Recompute ID counters from the ACTUAL loaded data, ignoring
    # whatever from_dict() left the counters at. This self-heals
    # any inflation caused by object construction during loading,
    # and guarantees the next new object gets a fresh, non-colliding ID.
    # ------------------------------------------------------------ #
    max_person_id = 0
    max_project_id = 0
    max_task_id = 0

    for user in users:
        max_person_id = max(max_person_id, user.id)
        for project in user.projects:
            max_project_id = max(max_project_id, project.id)
            for task in project.tasks:
                max_task_id = max(max_task_id, task.id)

    # Also consider the saved meta counters, in case there are IDs
    # referenced (e.g. by deleted users) that are no longer present
    # in the data but should still not be reused.
    meta = data.get("meta", {})
    max_person_id = max(max_person_id, meta.get("person_id_counter", 0))
    max_project_id = max(max_project_id, meta.get("project_id_counter", 0))
    max_task_id = max(max_task_id, meta.get("task_id_counter", 0))

    Person._id_counter  = max_person_id
    Project._id_counter = max_project_id
    Task._id_counter    = max_task_id

    return users


# ------------------------------------------------------------------ #
#  HELPERS                                                             #
# ------------------------------------------------------------------ #

def file_exists() -> bool:
    """Quick check — does the data file exist yet?"""
    return os.path.exists(DATA_FILE)


def reset_data():
    """
    Wipe all saved data by writing an empty structure.
    Used in tests to get a clean slate.
    WARNING: destructive — all data will be lost.
    """
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [], "meta": {}}, f, indent=2)

    # Also reset in-memory ID counters
    Person._id_counter  = 0
    Project._id_counter = 0
    Task._id_counter    = 0
    
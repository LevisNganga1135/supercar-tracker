# models/base.py
# BASE CLASS — a blueprint that other classes inherit from.


class Person:
    """
    Base class representing a generic person.
    User will inherit from this — this is OOP inheritance in action.
    """

    # Class attribute: shared counter across ALL Person instances
    # Every time a new Person (or User) is created, this number goes up
    _id_counter = 0

    def __init__(self, name: str):
        # Increment the shared counter first
        Person._id_counter += 1

        # Give this instance a unique ID (private by convention: _prefix)
        self._id = Person._id_counter

        # Store name privately — access is controlled via @property below
        self._name = name

    # --- PROPERTY: controlled READ access to _name ---
    @property
    def name(self):
        """Getter — allows: person.name"""
        return self._name

    # --- SETTER: controlled WRITE access to _name ---
    @name.setter
    def name(self, value: str):
        """Setter — allows: person.name = 'New Name' with validation"""
        if not value or not isinstance(value, str):
            raise ValueError("Name must be a non-empty string.")
        self._name = value.strip()  # strip removes accidental whitespace

    # --- PROPERTY: read-only ID (no setter = cannot be changed after creation) ---
    @property
    def id(self):
        """Getter — allows: person.id (read only, no setter)"""
        return self._id

    def __str__(self):
        """
        Called when you print(person).
        Makes CLI output clean and readable.
        """
        return f"Person #{self._id}: {self._name}"

    def __repr__(self):
        """
        Called in lists/debugger — more technical version.
        Useful when you're inspecting a list of objects.
        """
        return f"Person(id={self._id}, name='{self._name}')"

    def to_dict(self):
        """
        Convert this object to a plain dictionary.
        JSON can't store Python objects directly — this bridges that gap.
        """
        return {
            "id": self._id,
            "name": self._name
        }
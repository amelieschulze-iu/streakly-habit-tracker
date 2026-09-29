"""Application logic of Streakly.

:class:`HabitTracker` is the single entry point for the user interface. It
works with :class:`~streakly.habit.Habit` objects, enforces the rules of the
application (e.g. unique habit names) and delegates storage to the
:class:`~streakly.database.HabitRepository`. Because the CLI only talks to this
class, the interface could later be replaced, e.g. by a web front end.
"""

from __future__ import annotations

from datetime import datetime

from streakly.database import HabitRepository
from streakly.exceptions import HabitAlreadyExistsError, HabitNotFoundError
from streakly.habit import Habit, create_habit
from streakly.sample_data import sample_habits


class HabitTracker:
    """Creates, checks off, deletes and provides habits.

    Args:
        repository: Repository used to persist the habits.
    """

    def __init__(self, repository: HabitRepository) -> None:
        self.repository = repository

    def get_habits(self) -> list[Habit]:
        """Return all stored habits (freshly loaded from the database)."""
        return self.repository.load_habits()

    def get_habit(self, name: str) -> Habit:
        """Return the habit with the given name (case-insensitive).

        Raises:
            HabitNotFoundError: If no habit with this name exists.
        """
        matches = [habit for habit in self.get_habits() if habit.name.lower() == name.strip().lower()]
        if not matches:
            raise HabitNotFoundError(f"There is no habit called '{name.strip()}'.")
        return matches[0]

    def create_habit(self, name: str, task: str, periodicity: str) -> Habit:
        """Create and store a new habit.

        Args:
            name: Unique name of the habit.
            task: Description of the task.
            periodicity: ``"daily"`` or ``"weekly"``.

        Raises:
            HabitAlreadyExistsError: If a habit with this name already exists.
            ValueError: If name, task or periodicity are invalid.
        """
        if any(habit.name.lower() == name.strip().lower() for habit in self.get_habits()):
            raise HabitAlreadyExistsError(f"A habit called '{name.strip()}' already exists.")
        habit = create_habit(periodicity, name=name, task=task)
        self.repository.add_habit(habit)
        return habit

    def check_off(self, name: str, moment: datetime | None = None) -> Habit:
        """Check off the habit with the given name at ``moment`` (default: now).

        Returns:
            The updated habit, e.g. to show the new streak.

        Raises:
            HabitNotFoundError: If the habit does not exist.
            InvalidCheckOffError: If the moment is in the future or before creation.
        """
        habit = self.get_habit(name)
        stored = habit.check_off(moment)
        self.repository.add_completion(habit.habit_id, stored)
        return habit

    def delete_habit(self, name: str) -> None:
        """Delete the habit with the given name and all its check-offs.

        Raises:
            HabitNotFoundError: If the habit does not exist.
        """
        self.repository.delete_habit(self.get_habit(name).habit_id)

    def load_sample_data(self) -> int:
        """Store the five predefined habits; existing names are skipped.

        Returns:
            The number of habits that were added.
        """
        existing = {habit.name.lower() for habit in self.get_habits()}
        new_habits = [habit for habit in sample_habits() if habit.name.lower() not in existing]
        for habit in new_habits:
            self.repository.add_habit(habit)
        return len(new_habits)

    def is_empty(self) -> bool:
        """Return ``True`` if no habit has been created yet."""
        return self.repository.is_empty()

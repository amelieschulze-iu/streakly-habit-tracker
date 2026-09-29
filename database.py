"""Persistence layer of Streakly based on SQLite.

:class:`HabitRepository` is the only place in the application that contains
SQL. It translates between database rows and :class:`~streakly.habit.Habit`
objects in both directions. Two tables are used::

    habits(id, name, task, periodicity, created_at)
    completions(id, habit_id -> habits.id, completed_at)

Deleting a habit also deletes its check-offs (``ON DELETE CASCADE``).
Timestamps are stored as ISO 8601 strings.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from streakly.habit import Habit, create_habit

SCHEMA = """
CREATE TABLE IF NOT EXISTS habits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    task        TEXT NOT NULL,
    periodicity TEXT NOT NULL CHECK (periodicity IN ('daily', 'weekly')),
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS completions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id     INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    completed_at TEXT NOT NULL
);
"""


class HabitRepository:
    """Stores and loads habits in an SQLite database.

    Args:
        db_path: Path to the database file. ``":memory:"`` creates a temporary
            in-memory database, which is used by the test suite.
    """

    def __init__(self, db_path: str = "habits.db") -> None:
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    # ------------------------------------------------------------------ writing
    def add_habit(self, habit: Habit) -> int:
        """Insert a habit including its existing check-offs and return its new id.

        The id is also stored in ``habit.habit_id``.
        """
        with self.connection:  # commits automatically, rolls back on errors
            cursor = self.connection.execute(
                "INSERT INTO habits (name, task, periodicity, created_at) VALUES (?, ?, ?, ?)",
                (habit.name, habit.task, habit.periodicity, habit.created_at.isoformat()))
            habit.habit_id = cursor.lastrowid
            self.connection.executemany(
                "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?)",
                [(habit.habit_id, moment.isoformat()) for moment in habit.completions])
        return habit.habit_id

    def add_completion(self, habit_id: int, moment: datetime) -> None:
        """Store a single check-off of the habit with the given id."""
        with self.connection:
            self.connection.execute(
                "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?)",
                (habit_id, moment.isoformat()))

    def delete_habit(self, habit_id: int) -> None:
        """Delete a habit together with all its check-offs."""
        with self.connection:
            self.connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))

    # ------------------------------------------------------------------ reading
    def load_habits(self) -> list[Habit]:
        """Load all habits with their check-offs as ``DailyHabit``/``WeeklyHabit`` objects."""
        completions: dict[int, list[datetime]] = {}
        for habit_id, completed_at in self.connection.execute(
                "SELECT habit_id, completed_at FROM completions ORDER BY completed_at"):
            completions.setdefault(habit_id, []).append(datetime.fromisoformat(completed_at))

        rows = self.connection.execute(
            "SELECT id, name, task, periodicity, created_at FROM habits ORDER BY id").fetchall()
        return [create_habit(periodicity, name=name, task=task,
                             created_at=datetime.fromisoformat(created_at),
                             completions=completions.get(habit_id, []), habit_id=habit_id)
                for habit_id, name, task, periodicity, created_at in rows]

    def is_empty(self) -> bool:
        """Return ``True`` if no habit is stored yet."""
        return self.connection.execute("SELECT COUNT(*) FROM habits").fetchone()[0] == 0

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

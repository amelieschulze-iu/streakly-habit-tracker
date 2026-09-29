"""Tests for the SQLite persistence layer (streakly.database)."""

import sqlite3
from datetime import datetime

import pytest

from streakly.database import HabitRepository
from streakly.habit import DailyHabit, WeeklyHabit


def test_new_database_is_empty(repository):
    assert repository.is_empty()
    assert repository.load_habits() == []


def test_habits_are_stored_and_loaded_with_all_data(repository, habits):
    for habit in habits:
        repository.add_habit(habit)
    loaded = {habit.name: habit for habit in repository.load_habits()}
    assert len(loaded) == 5
    for original in habits:
        copy = loaded[original.name]
        assert type(copy) is type(original)
        assert (copy.task, copy.created_at, copy.completions) == \
            (original.task, original.created_at, original.completions)


def test_add_habit_sets_the_id(repository):
    habit = DailyHabit("Test", "Task")
    habit_id = repository.add_habit(habit)
    assert habit.habit_id == habit_id is not None


def test_add_completion_is_persisted(repository):
    habit = WeeklyHabit("Test", "Task", created_at=datetime(2026, 8, 1))
    repository.add_habit(habit)
    repository.add_completion(habit.habit_id, datetime(2026, 8, 5, 9, 15))
    assert repository.load_habits()[0].completions == [datetime(2026, 8, 5, 9, 15)]


def test_delete_removes_habit_and_its_completions(repository, habits):
    repository.add_habit(habits[0])
    repository.delete_habit(habits[0].habit_id)
    assert repository.is_empty()
    count = repository.connection.execute("SELECT COUNT(*) FROM completions").fetchone()[0]
    assert count == 0


def test_habit_names_are_unique(repository):
    repository.add_habit(DailyHabit("Test", "Task"))
    with pytest.raises(sqlite3.IntegrityError):
        repository.add_habit(DailyHabit("Test", "Another task"))


def test_database_rejects_names_differing_only_in_case(repository):
    repository.add_habit(DailyHabit("Read", "Task"))
    with pytest.raises(sqlite3.IntegrityError):
        repository.add_habit(DailyHabit("READ", "Task"))


def test_foreign_keys_are_enforced(repository):
    with pytest.raises(sqlite3.IntegrityError):
        repository.add_completion(999, datetime(2026, 8, 5, 9, 0))


def test_data_persists_between_sessions(tmp_path):
    path = str(tmp_path / "habits.db")
    first_session = HabitRepository(path)
    first_session.add_habit(DailyHabit("Test", "Task", created_at=datetime(2026, 8, 1, 8, 0)))
    first_session.close()

    second_session = HabitRepository(path)
    assert [habit.name for habit in second_session.load_habits()] == ["Test"]
    second_session.close()

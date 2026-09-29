"""Shared pytest fixtures (test fixtures) for the Streakly test suite."""

import pytest

from streakly.database import HabitRepository
from streakly.sample_data import sample_habits
from streakly.tracker import HabitTracker


@pytest.fixture
def habits():
    """The five predefined habits with four weeks of example data."""
    return sample_habits()


@pytest.fixture
def habit_by_name(habits):
    """Dictionary that maps habit names to the sample habits."""
    return {habit.name: habit for habit in habits}


@pytest.fixture
def repository():
    """A fresh in-memory database that is closed after the test."""
    repo = HabitRepository(":memory:")
    yield repo
    repo.close()


@pytest.fixture
def tracker(repository):
    """A habit tracker with an empty in-memory database."""
    return HabitTracker(repository)


@pytest.fixture
def seeded_tracker(tracker):
    """A habit tracker whose database contains the sample habits."""
    tracker.load_sample_data()
    return tracker

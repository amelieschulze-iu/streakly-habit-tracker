"""Tests for the object-oriented domain model (streakly.habit)."""

from datetime import date, datetime, timedelta

import pytest

from streakly.exceptions import InvalidCheckOffError
from streakly.habit import DailyHabit, Habit, WeeklyHabit, create_habit


def test_habit_is_abstract():
    with pytest.raises(TypeError):
        Habit("Test", "Task")


@pytest.mark.parametrize("periodicity, expected_class", [("daily", DailyHabit), ("weekly", WeeklyHabit),
                                                         (" Weekly ", WeeklyHabit)])
def test_factory_creates_matching_subclass(periodicity, expected_class):
    habit = create_habit(periodicity, name="Test", task="Do something")
    assert isinstance(habit, expected_class)


def test_factory_rejects_unknown_periodicity():
    with pytest.raises(ValueError):
        create_habit("monthly", name="Test", task="Do something")


@pytest.mark.parametrize("name, task", [("", "Task"), ("   ", "Task"), ("Name", "")])
def test_empty_name_or_task_is_rejected(name, task):
    with pytest.raises(ValueError):
        DailyHabit(name, task)


def test_new_habit_stores_creation_time():
    before = datetime.now().replace(microsecond=0)
    habit = DailyHabit("Meditate", "Meditate for 10 minutes")
    assert before <= habit.created_at <= datetime.now()
    assert habit.completions == []


def test_daily_period_is_the_calendar_day():
    habit = DailyHabit("Test", "Task")
    assert habit.period_start(datetime(2026, 8, 12, 23, 59)) == date(2026, 8, 12)


@pytest.mark.parametrize("moment, monday", [(datetime(2026, 8, 24, 0, 1), date(2026, 8, 24)),   # Monday
                                            (datetime(2026, 8, 27, 12, 0), date(2026, 8, 24)),  # Thursday
                                            (datetime(2026, 8, 30, 23, 59), date(2026, 8, 24)),  # Sunday
                                            (date(2026, 8, 31), date(2026, 8, 31))])            # next Monday
def test_weekly_period_starts_on_monday(moment, monday):
    assert WeeklyHabit("Test", "Task").period_start(moment) == monday


def test_check_off_stores_date_and_time():
    habit = DailyHabit("Test", "Task", created_at=datetime(2026, 8, 1, 8, 0))
    moment = datetime(2026, 8, 2, 7, 45)
    assert habit.check_off(moment) == moment
    assert habit.completions == [moment]


def test_check_off_defaults_to_now():
    habit = DailyHabit("Test", "Task", created_at=datetime.now() - timedelta(hours=1))
    stored = habit.check_off()
    assert abs(datetime.now() - stored) < timedelta(seconds=5)


def test_several_check_offs_in_one_period_count_once():
    habit = DailyHabit("Test", "Task", created_at=datetime(2026, 8, 1, 6, 0))
    habit.check_off(datetime(2026, 8, 2, 7, 0))
    habit.check_off(datetime(2026, 8, 2, 21, 0))
    assert len(habit.completions) == 2
    assert habit.completed_periods() == [date(2026, 8, 2)]
    assert habit.is_completed_in(date(2026, 8, 2))
    assert not habit.is_completed_in(date(2026, 8, 3))


def test_check_off_in_the_future_is_rejected():
    habit = DailyHabit("Test", "Task")
    with pytest.raises(InvalidCheckOffError):
        habit.check_off(datetime.now() + timedelta(days=1))


def test_check_off_before_creation_is_rejected():
    habit = DailyHabit("Test", "Task", created_at=datetime(2026, 8, 10, 12, 0))
    with pytest.raises(InvalidCheckOffError):
        habit.check_off(datetime(2026, 8, 9, 12, 0))


def test_string_representation_contains_name_and_periodicity():
    assert str(WeeklyHabit("Jogging", "Run 5 km")) == "Jogging (weekly): Run 5 km"

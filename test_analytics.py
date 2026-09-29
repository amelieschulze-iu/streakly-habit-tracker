"""Tests for the functional analytics module (streakly.analytics) with the sample fixture."""

import copy
from datetime import date, datetime

import pytest

from streakly import analytics
from streakly.habit import DailyHabit, WeeklyHabit

START, END = date(2026, 8, 3), date(2026, 8, 30)
TODAY = date(2026, 9, 29)  # fixed "today" -> results do not depend on when the tests run


def test_list_habits_returns_all_habits_sorted(habits):
    names = [habit.name for habit in analytics.list_habits(habits)]
    assert names == ["Brush teeth", "Call the family", "Clean the apartment", "Drink water", "Read"]


@pytest.mark.parametrize("periodicity, expected", [
    ("daily", ["Brush teeth", "Drink water", "Read"]),
    ("weekly", ["Call the family", "Clean the apartment"]),
])
def test_filter_by_periodicity(habits, periodicity, expected):
    assert [habit.name for habit in analytics.filter_by_periodicity(habits, periodicity)] == expected


@pytest.mark.parametrize("name, expected", [("Brush teeth", 14), ("Drink water", 28), ("Read", 6),
                                            ("Clean the apartment", 2), ("Call the family", 4)])
def test_longest_streak_of_a_given_habit(habit_by_name, name, expected):
    assert analytics.longest_streak(habit_by_name[name]) == expected


def test_longest_streak_of_all_habits(habits):
    result = analytics.longest_streak_overall(habits)
    assert (result.habit_name, result.streak, result.periodicity) == ("Drink water", 28, "daily")


def test_longest_streak_overall_without_habits():
    assert analytics.longest_streak_overall([]) is None


def test_longest_streak_without_check_offs_is_zero():
    assert analytics.longest_streak(DailyHabit("New", "Task")) == 0


def test_weekly_streak_is_counted_in_weeks():
    habit = WeeklyHabit("Test", "Task", created_at=datetime(2026, 8, 3),
                        completions=[datetime(2026, 8, 3), datetime(2026, 8, 16),   # weeks 32 and 33
                                     datetime(2026, 8, 17), datetime(2026, 8, 23)])  # both in week 34
    assert analytics.longest_streak(habit) == 3


def test_streaks_of_all_is_sorted_by_streak(habits):
    assert [r.streak for r in analytics.streaks_of_all(habits)] == [28, 14, 6, 4, 2]


@pytest.mark.parametrize("name, today, expected", [
    ("Drink water", date(2026, 8, 30), 28),  # running day already completed
    ("Read", date(2026, 8, 30), 1),          # 30 Aug not done yet -> streak up to 29 Aug
    ("Read", date(2026, 8, 31), 0),          # 30 Aug has ended without check-off
    ("Brush teeth", date(2026, 8, 30), 13),  # since the missed 17 August
    ("Clean the apartment", date(2026, 8, 30), 1),
])
def test_current_streak(habit_by_name, name, today, expected):
    assert analytics.current_streak(habit_by_name[name], today) == expected


def test_missed_periods_of_daily_habit(habit_by_name):
    missed = analytics.missed_periods(habit_by_name["Read"], START, END, TODAY)
    assert missed == [date(2026, 8, day) for day in (6, 9, 16, 17, 20, 22, 23, 28, 30)]


def test_missed_periods_of_weekly_habit(habit_by_name):
    assert analytics.missed_periods(habit_by_name["Clean the apartment"], START, END, TODAY) == [date(2026, 8, 17)]


def test_running_period_is_not_counted_as_missed(habit_by_name):
    # the week 24-30 August has not ended on Thursday 27 August
    assert analytics.elapsed_periods(habit_by_name["Call the family"], START, date(2026, 8, 27), TODAY) == \
        [date(2026, 8, 3), date(2026, 8, 10), date(2026, 8, 17)]


def test_running_day_is_not_counted_as_missed(habit_by_name):
    # on 18 August the running day is not over yet -> only 3-17 August are evaluated
    elapsed = analytics.elapsed_periods(habit_by_name["Read"], START, date(2026, 8, 18), today=date(2026, 8, 18))
    assert elapsed[-1] == date(2026, 8, 17)
    assert len(elapsed) == 15


def test_running_week_is_not_counted_as_missed():
    habit = WeeklyHabit("Test", "Task", created_at=datetime(2026, 8, 3))
    # Wednesday of the second week: only the first week (3-9 August) is over
    assert analytics.missed_periods(habit, START, END, today=date(2026, 8, 12)) == [date(2026, 8, 3)]


def test_periods_before_creation_are_ignored(habit_by_name):
    # the time span starts before the habits were created (3 August)
    assert len(analytics.elapsed_periods(habit_by_name["Drink water"], date(2026, 7, 1), END, TODAY)) == 28


def test_struggled_most_skips_habits_without_elapsed_periods():
    new_habit = DailyHabit("New", "Task", created_at=datetime(2026, 9, 29, 8, 0))
    assert analytics.struggled_most([new_habit], START, TODAY, today=TODAY) == []


def test_struggled_most_ranks_by_miss_rate(habits):
    results = analytics.struggled_most(habits, START, END, TODAY)
    assert [r.habit_name for r in results[:3]] == ["Read", "Clean the apartment", "Brush teeth"]
    assert (results[0].missed, results[0].total) == (9, 28)
    assert results[0].miss_rate == pytest.approx(9 / 28)


def test_analytics_functions_do_not_modify_their_input(habits):
    snapshot = copy.deepcopy([(h.name, list(h.completions)) for h in habits])
    analytics.list_habits(habits)
    analytics.filter_by_periodicity(habits, "daily")
    analytics.longest_streak_overall(habits)
    analytics.struggled_most(habits, START, END, TODAY)
    assert [(h.name, list(h.completions)) for h in habits] == snapshot

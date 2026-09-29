"""Analytics module of Streakly – implemented in the functional programming style.

Every function in this module is a *pure function*: it only depends on its
arguments, returns a new value and never modifies its input, prints anything or
accesses the database. The functions are built from higher-order functions
(``map``, ``filter``, ``functools.reduce``, ``sorted``/``max`` with key
functions) and lambda expressions. Results with several values are returned as
immutable named tuples.

Functions that depend on the current date accept an optional ``today`` argument.
The CLI omits it (today's date is used), while the tests pass a fixed date, so
the results are reproducible no matter when the tests are run.
"""

from __future__ import annotations

from collections import namedtuple
from datetime import date, timedelta
from functools import reduce
from itertools import count, takewhile

from streakly.habit import Habit

#: Result of a streak analysis.
StreakResult = namedtuple("StreakResult", ["habit_name", "periodicity", "streak"])
#: Result of a struggle analysis for one habit within a time span.
StruggleResult = namedtuple("StruggleResult", ["habit_name", "periodicity", "missed", "total", "miss_rate"])


# ---------------------------------------------------------------- required analyses
def list_habits(habits: list[Habit]) -> list[Habit]:
    """Return all currently tracked habits, sorted alphabetically by name."""
    return sorted(habits, key=lambda habit: habit.name.lower())


def filter_by_periodicity(habits: list[Habit], periodicity: str) -> list[Habit]:
    """Return all habits with the given periodicity (``"daily"`` or ``"weekly"``)."""
    return list_habits(list(filter(lambda habit: habit.periodicity == periodicity.lower(), habits)))


def longest_streak(habit: Habit) -> int:
    """Return the longest run of consecutive completed periods of one habit.

    The sorted period start dates are folded with ``reduce`` into a triple
    ``(previous period, current run, longest run)``. A run continues if the
    distance to the previous period is exactly one period length.
    """
    def step(state: tuple, period: date) -> tuple:
        """Extend the current run or start a new one, and keep the best run so far."""
        previous, run, best = state
        run = run + 1 if previous is not None and period - previous == habit.period_length else 1
        return period, run, max(best, run)

    return reduce(step, habit.completed_periods(), (None, 0, 0))[2]


def longest_streak_overall(habits: list[Habit]) -> StreakResult | None:
    """Return the habit with the longest streak of all habits (``None`` if there are no habits)."""
    return max(streaks_of_all(habits), key=lambda result: result.streak, default=None)


# ---------------------------------------------------------------- additional analyses
def streaks_of_all(habits: list[Habit]) -> list[StreakResult]:
    """Return the longest streak of every habit, best streak first."""
    results = map(lambda habit: StreakResult(habit.name, habit.periodicity, longest_streak(habit)), habits)
    return sorted(results, key=lambda result: (-result.streak, result.habit_name.lower()))


def current_streak(habit: Habit, today: date | None = None) -> int:
    """Return the number of consecutive completed periods up to today.

    The running period is included if it is already completed. If not, the
    streak is counted up to the previous period, because the running period
    is not over yet and therefore does not break the streak.
    """
    today = today or date.today()
    completed = set(habit.completed_periods())
    running = habit.period_start(today)
    start = running if running in completed else running - habit.period_length
    periods_backwards = map(lambda i: start - i * habit.period_length, count())
    return sum(1 for _ in takewhile(lambda period: period in completed, periods_backwards))


def elapsed_periods(habit: Habit, start: date, end: date, today: date | None = None) -> list[date]:
    """Return the start dates of all periods that lie completely within ``start``–``end``.

    A period counts if it begins on or after ``start``, has ended by ``end``
    (inclusive), does not lie before the period in which the habit was created
    and is already over. The running period (containing ``today``) is never
    counted, because the user can still complete it.

    Args:
        habit: The habit to evaluate.
        start: First day of the time span.
        end: Last day of the time span (inclusive).
        today: Current date (default: today); injectable for deterministic tests.
    """
    last_day = min(end, (today or date.today()) - timedelta(days=1))
    aligned = habit.period_start(start)
    first_in_window = aligned if aligned >= start else aligned + habit.period_length
    first = max(first_in_window, habit.period_start(habit.created_at))
    candidates = map(lambda i: first + i * habit.period_length, count())
    return list(takewhile(lambda period: period + habit.period_length - timedelta(days=1) <= last_day,
                          candidates))


def missed_periods(habit: Habit, start: date, end: date, today: date | None = None) -> list[date]:
    """Return the start dates of all elapsed periods in ``start``–``end`` without a check-off."""
    completed = set(habit.completed_periods())
    return list(filter(lambda period: period not in completed, elapsed_periods(habit, start, end, today)))


def struggled_most(habits: list[Habit], start: date, end: date,
                   today: date | None = None) -> list[StruggleResult]:
    """Rank habits by the share of missed periods in ``start``–``end`` (worst first).

    Using the share instead of the absolute number keeps daily and weekly habits
    comparable. Habits without any elapsed period in the time span are skipped.
    """
    def evaluate(habit: Habit) -> StruggleResult:
        """Count the elapsed and the missed periods of one habit."""
        total = len(elapsed_periods(habit, start, end, today))
        missed = len(missed_periods(habit, start, end, today))
        return StruggleResult(habit.name, habit.periodicity, missed, total, missed / total if total else 0.0)

    results = filter(lambda result: result.total > 0, map(evaluate, habits))
    return sorted(results, key=lambda result: (-result.miss_rate, -result.missed, result.habit_name.lower()))

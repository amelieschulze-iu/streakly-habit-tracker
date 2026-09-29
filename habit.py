"""Object-oriented domain model of Streakly.

A habit is a clearly defined task that has to be completed periodically.
The abstract base class :class:`Habit` holds the data and behaviour that all
habits share. The periodicity is modelled through inheritance:
:class:`DailyHabit` and :class:`WeeklyHabit` only define how a point in time is
mapped to the start of its period. All other code works with the base class
(polymorphism), so a new periodicity only needs one new subclass.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta

from streakly.exceptions import InvalidCheckOffError


def _as_date(moment: date | datetime) -> date:
    """Return the calendar date of ``moment`` (works for dates and datetimes)."""
    return moment.date() if isinstance(moment, datetime) else moment


def now() -> datetime:
    """Return the current local time without microseconds."""
    return datetime.now().replace(microsecond=0)


class Habit(ABC):
    """Abstract base class for all habits.

    Attributes:
        name: Unique, human-readable name of the habit, e.g. ``"Brush teeth"``.
        task: Specification of the task that has to be completed.
        created_at: Date and time the habit was created.
        completions: Sorted list with the date and time of every check-off.
        habit_id: Primary key in the database (``None`` until the habit is saved).
    """

    #: Name of the periodicity as stored in the database (set by subclasses).
    periodicity: str = ""
    #: Length of one period (set by subclasses).
    period_length: timedelta = timedelta(0)

    def __init__(self, name: str, task: str, created_at: datetime | None = None,
                 completions: list[datetime] | None = None, habit_id: int | None = None) -> None:
        """Create a habit.

        Args:
            name: Name of the habit; must not be empty.
            task: Description of the task; must not be empty.
            created_at: Creation time, defaults to now.
            completions: Existing check-offs, e.g. when loading from the database.
            habit_id: Database id, if the habit has already been stored.

        Raises:
            ValueError: If the name or task is empty.
        """
        if not name or not name.strip():
            raise ValueError("The name of a habit must not be empty.")
        if not task or not task.strip():
            raise ValueError("The task of a habit must not be empty.")
        self.name = name.strip()
        self.task = task.strip()
        self.created_at = created_at or now()
        self.completions = sorted(completions or [])
        self.habit_id = habit_id

    # ------------------------------------------------------------------ behaviour
    @abstractmethod
    def period_start(self, moment: date | datetime) -> date:
        """Return the first day of the period that contains ``moment``."""

    def check_off(self, moment: datetime | None = None) -> datetime:
        """Mark the task as completed at ``moment`` (default: now).

        Several check-offs within the same period are allowed; for streaks
        they count only once.

        Args:
            moment: Date and time of the completion.

        Returns:
            The stored timestamp.

        Raises:
            InvalidCheckOffError: If the moment lies in the future or before
                the creation of the habit.
        """
        moment = moment or now()
        if moment > now():
            raise InvalidCheckOffError("A habit cannot be checked off in the future.")
        if moment < self.created_at:
            raise InvalidCheckOffError(
                f"'{self.name}' was created on {self.created_at:%Y-%m-%d %H:%M}; "
                "earlier check-offs are not possible.")
        self.completions.append(moment)
        self.completions.sort()
        return moment

    def completed_periods(self) -> list[date]:
        """Return the sorted start dates of all periods with at least one check-off."""
        return sorted(set(map(self.period_start, self.completions)))

    def is_completed_in(self, moment: date | datetime) -> bool:
        """Return ``True`` if the period containing ``moment`` has been completed."""
        return self.period_start(moment) in self.completed_periods()

    def last_completion(self) -> datetime | None:
        """Return the most recent check-off or ``None`` if there is none."""
        return self.completions[-1] if self.completions else None

    # ------------------------------------------------------------------ representation
    def __str__(self) -> str:
        return f"{self.name} ({self.periodicity}): {self.task}"

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(name={self.name!r}, task={self.task!r}, "
                f"created_at={self.created_at!r}, completions={len(self.completions)})")


class DailyHabit(Habit):
    """A habit that has to be completed at least once per calendar day."""

    periodicity = "daily"
    period_length = timedelta(days=1)

    def period_start(self, moment: date | datetime) -> date:
        """A daily period starts at the calendar day of ``moment``."""
        return _as_date(moment)


class WeeklyHabit(Habit):
    """A habit that has to be completed at least once per ISO week (Monday–Sunday)."""

    periodicity = "weekly"
    period_length = timedelta(days=7)

    def period_start(self, moment: date | datetime) -> date:
        """A weekly period starts on the Monday of the week containing ``moment``."""
        day = _as_date(moment)
        return day - timedelta(days=day.weekday())


#: Maps the periodicity names used in the CLI and database to their classes.
HABIT_TYPES: dict[str, type[Habit]] = {"daily": DailyHabit, "weekly": WeeklyHabit}


def create_habit(periodicity: str, **kwargs) -> Habit:
    """Factory function that creates a habit of the given periodicity.

    Args:
        periodicity: ``"daily"`` or ``"weekly"``.
        **kwargs: Arguments passed on to the habit constructor.

    Raises:
        ValueError: If the periodicity is unknown.
    """
    try:
        habit_class = HABIT_TYPES[periodicity.strip().lower()]
    except KeyError:
        raise ValueError(f"Unknown periodicity '{periodicity}'. Use one of: "
                         f"{', '.join(HABIT_TYPES)}.") from None
    return habit_class(**kwargs)

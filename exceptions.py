"""Custom exceptions used by Streakly.

All exceptions inherit from :class:`StreaklyError`, so the CLI can catch every
expected problem with a single ``except`` clause and show a friendly message.
"""


class StreaklyError(Exception):
    """Base class for all expected errors in Streakly."""


class HabitNotFoundError(StreaklyError):
    """Raised when a habit with the given name does not exist."""


class HabitAlreadyExistsError(StreaklyError):
    """Raised when a habit with the same name has already been created."""


class InvalidCheckOffError(StreaklyError):
    """Raised when a check-off lies in the future or before the habit was created."""

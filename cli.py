"""Interactive command-line interface (CLI) of Streakly.

The CLI is a simple menu loop based on the built-in :func:`input` function, so
users do not need to learn any command syntax. It only reads input, calls the
:class:`~streakly.tracker.HabitTracker` or the functions of
:mod:`streakly.analytics` and prints the results. Expected errors are caught
and shown as messages, so wrong input never crashes the program.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta

from streakly import analytics
from streakly.database import HabitRepository
from streakly.exceptions import StreaklyError
from streakly.habit import HABIT_TYPES, Habit
from streakly.tracker import HabitTracker

LINE = "-" * 62
UNIT = {"daily": "day", "weekly": "week"}


# ---------------------------------------------------------------- output helpers
def plural(number: int, periodicity: str) -> str:
    """Return e.g. ``'1 day'``, ``'14 days'`` or ``'2 weeks'``."""
    unit = UNIT.get(periodicity, "period")
    return f"{number} {unit}{'' if number == 1 else 's'}"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print rows as a simple left-aligned text table."""
    widths = [max(map(len, column)) for column in zip(headers, *rows)]
    print("  " + "  ".join(title.ljust(width) for title, width in zip(headers, widths)))
    print("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        print("  " + "  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def shorten(text: str, width: int) -> str:
    """Shorten ``text`` to ``width`` characters, marking cut text with '...'."""
    return text if len(text) <= width else text[:width - 3].rstrip() + "..."


def ask(prompt: str) -> str:
    """Read a line from the user (stripped)."""
    return input(prompt).strip()


def ask_date(prompt: str, default: date) -> date:
    """Ask for a date in the format YYYY-MM-DD; an empty input returns ``default``.

    Raises:
        ValueError: If the input is not a valid date.
    """
    text = ask(f"{prompt} [{default.isoformat()}]: ")
    if not text:
        return default
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"'{text}' is not a valid date. Please use the format YYYY-MM-DD.") from None


def parse_moment(text: str, today: date | None = None) -> datetime | None:
    """Convert user input into the moment of a check-off.

    Accepted formats are ``YYYY-MM-DD HH:MM`` and ``YYYY-MM-DD``. A date without
    time counts as the current time if it is today and as noon on any other day,
    so that entering today's date in the morning is never rejected as "future".

    Args:
        text: User input; an empty text returns ``None`` (= now).
        today: Current date (injectable for tests).

    Raises:
        ValueError: If the text matches none of the formats.
    """
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        pass
    try:
        day = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Please use the format YYYY-MM-DD or YYYY-MM-DD HH:MM.") from None
    if day == (today or date.today()):
        return datetime.now().replace(microsecond=0)
    return datetime.combine(day, time(12, 0))


def stored_moment(habit: Habit, moment: datetime | None) -> datetime:
    """Return the moment of the check-off just made (the latest one if ``moment`` is ``None``)."""
    return moment if moment is not None else habit.last_completion()


def select_habit(habits: list[Habit]) -> Habit | None:
    """Show a numbered list of habits and return the chosen one (``None`` = cancel)."""
    if not habits:
        print("  No habits yet - create one first.")
        return None
    for number, habit in enumerate(habits, start=1):
        print(f"  {number:>2}  {habit.name} ({habit.periodicity})")
    choice = ask("  Number of the habit (Enter = cancel): ")
    if not choice:
        return None
    if not choice.isdigit() or not 1 <= int(choice) <= len(habits):
        raise ValueError(f"Please enter a number between 1 and {len(habits)}.")
    return habits[int(choice) - 1]


# ---------------------------------------------------------------- menu actions
def handle_create(tracker: HabitTracker) -> None:
    """Create a new habit from user input."""
    print("\nCREATE A HABIT")
    name = ask("  Name (e.g. 'Go jogging'): ")
    task = ask("  Task (what exactly do you want to do?): ")
    periodicity = ask(f"  Periodicity ({' / '.join(HABIT_TYPES)}): ")
    habit = tracker.create_habit(name, task, periodicity)
    print(f"\n  [OK] '{habit.name}' was created as a {habit.periodicity} habit.")


def handle_check_off(tracker: HabitTracker) -> None:
    """Check off a habit now or at an entered date/time."""
    print("\nCHECK OFF A HABIT")
    habit = select_habit(analytics.list_habits(tracker.get_habits()))
    if habit is None:
        return
    moment = parse_moment(ask("  When? Enter = now, or YYYY-MM-DD [HH:MM]: "))
    habit = tracker.check_off(habit.name, moment)
    streak = analytics.current_streak(habit)
    print(f"\n  [OK] '{habit.name}' checked off at {stored_moment(habit, moment):%Y-%m-%d %H:%M}.")
    print(f"       Current streak: {plural(streak, habit.periodicity)}."
          + (" Keep it up!" if streak else ""))


def handle_delete(tracker: HabitTracker) -> None:
    """Delete a habit after confirmation."""
    print("\nDELETE A HABIT")
    habit = select_habit(analytics.list_habits(tracker.get_habits()))
    if habit is None:
        return
    if ask(f"  Delete '{habit.name}' and all its check-offs? Type 'yes' to confirm: ").lower() == "yes":
        tracker.delete_habit(habit.name)
        print(f"\n  [OK] '{habit.name}' was deleted.")
    else:
        print("  Nothing was deleted.")


def show_habit_table(habits: list[Habit]) -> None:
    """Print name, periodicity, task, last check-off and current streak of the habits."""
    if not habits:
        print("  No habits found.")
        return
    rows = [[habit.name, habit.periodicity, shorten(habit.task, 30),
             f"{habit.last_completion():%Y-%m-%d}" if habit.last_completion() else "-",
             plural(analytics.current_streak(habit), habit.periodicity)] for habit in habits]
    print_table(["Habit", "Period", "Task", "Last done", "Current streak"], rows)


def handle_show(tracker: HabitTracker) -> None:
    """Show all habits or the habits of one periodicity."""
    print("\nSHOW HABITS\n  1  All habits\n  2  Daily habits\n  3  Weekly habits")
    choice = ask("  Your choice: ")
    habits = tracker.get_habits()
    selection = {"1": lambda: analytics.list_habits(habits),
                 "2": lambda: analytics.filter_by_periodicity(habits, "daily"),
                 "3": lambda: analytics.filter_by_periodicity(habits, "weekly")}
    if choice not in selection:
        raise ValueError("Please choose 1, 2 or 3.")
    print()
    show_habit_table(selection[choice]())


def handle_analyse(tracker: HabitTracker) -> None:
    """Offer the analyses of the analytics module."""
    print("\nANALYSE HABITS\n  1  Longest streak of all habits\n  2  Longest streak of one habit"
          "\n  3  Streak overview of all habits\n  4  Habits I struggled with most")
    choice = ask("  Your choice: ")
    habits = tracker.get_habits()
    if choice == "1":
        best = analytics.longest_streak_overall(habits)
        print("\n  No habits yet." if best is None else
              f"\n  Your longest streak: {plural(best.streak, best.periodicity)} of '{best.habit_name}'.")
    elif choice == "2":
        habit = select_habit(analytics.list_habits(habits))
        if habit:
            print(f"\n  Longest streak of '{habit.name}': "
                  f"{plural(analytics.longest_streak(habit), habit.periodicity)}.")
    elif choice == "3":
        print()
        print_table(["Habit", "Period", "Longest streak"],
                    [[r.habit_name, r.periodicity, plural(r.streak, r.periodicity)]
                     for r in analytics.streaks_of_all(habits)])
    elif choice == "4":
        today = date.today()
        start = ask_date("  From", today - timedelta(days=28))
        end = ask_date("  To  ", today)
        if start > end:
            raise ValueError("The start date must not be after the end date.")
        results = analytics.struggled_most(habits, start, end)
        print()
        if not results:
            print("  No completed periods in this time span.")
            return
        print_table(["Habit", "Period", "Missed", "Miss rate"],
                    [[r.habit_name, r.periodicity, f"{r.missed} of {r.total}", f"{r.miss_rate:.0%}"]
                     for r in results])
        print(f"\n  You struggled most with '{results[0].habit_name}'.")
    else:
        raise ValueError("Please choose 1, 2, 3 or 4.")


MENU = {
    "1": ("Create a habit", handle_create),
    "2": ("Check off a habit", handle_check_off),
    "3": ("Delete a habit", handle_delete),
    "4": ("Show habits", handle_show),
    "5": ("Analyse habits", handle_analyse),
}


def show_main_menu() -> None:
    """Print the main menu."""
    print(f"\n{LINE}\n  STREAKLY - your habit tracker\n{LINE}")
    for key, (title, _) in MENU.items():
        print(f"  {key}  {title}")
    print("  0  Exit")


def run(tracker: HabitTracker) -> None:
    """Run the menu loop until the user chooses 'Exit'."""
    if tracker.is_empty():
        answer = ask("Welcome to Streakly! Load 5 sample habits with 4 weeks of data? [y/n]: ")
        if answer.lower().startswith("y"):
            print(f"  [OK] {tracker.load_sample_data()} sample habits loaded.")
    while True:
        show_main_menu()
        choice = ask("Your choice: ")
        if choice == "0":
            print("Goodbye - see you tomorrow!")
            return
        if choice not in MENU:
            print("  [!] Please enter a number from the menu.")
            continue
        try:
            MENU[choice][1](tracker)
        except (StreaklyError, ValueError) as error:
            print(f"\n  [!] {error}")


def main(argv: list[str] | None = None) -> None:
    """Start Streakly. Use ``--db`` to choose another database file."""
    parser = argparse.ArgumentParser(description="Streakly - a command-line habit tracker.")
    parser.add_argument("--db", default="habits.db", help="path to the SQLite database (default: habits.db)")
    args = parser.parse_args(argv)
    repository = HabitRepository(args.db)
    try:
        run(HabitTracker(repository))
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
    finally:
        repository.close()

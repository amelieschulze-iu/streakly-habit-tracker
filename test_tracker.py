"""Tests for the application logic (streakly.tracker) and the CLI."""

from datetime import date, datetime

import pytest

from streakly import analytics, cli
from streakly.exceptions import HabitAlreadyExistsError, HabitNotFoundError, InvalidCheckOffError
from streakly.habit import WeeklyHabit


def test_create_habit_is_stored(tracker):
    habit = tracker.create_habit("Go jogging", "Run at least 5 km", "weekly")
    assert isinstance(habit, WeeklyHabit)
    assert [h.name for h in tracker.get_habits()] == ["Go jogging"]


def test_duplicate_names_are_rejected_case_insensitively(tracker):
    tracker.create_habit("Go jogging", "Run", "weekly")
    with pytest.raises(HabitAlreadyExistsError):
        tracker.create_habit("go JOGGING", "Run again", "daily")


def test_check_off_is_persisted(seeded_tracker):
    habit = seeded_tracker.check_off("drink water", datetime(2026, 8, 31, 19, 0))
    assert habit.last_completion() == datetime(2026, 8, 31, 19, 0)
    assert seeded_tracker.get_habit("Drink water").last_completion() == datetime(2026, 8, 31, 19, 0)


def test_check_off_of_unknown_habit_raises(seeded_tracker):
    with pytest.raises(HabitNotFoundError):
        seeded_tracker.check_off("Fly to the moon")


def test_invalid_check_off_is_not_stored(seeded_tracker):
    with pytest.raises(InvalidCheckOffError):
        seeded_tracker.check_off("Read", datetime(2020, 1, 1))
    assert seeded_tracker.get_habit("Read").last_completion() == datetime(2026, 8, 29, 21, 30)


def test_delete_habit(seeded_tracker):
    seeded_tracker.delete_habit("Read")
    assert "Read" not in [habit.name for habit in seeded_tracker.get_habits()]
    with pytest.raises(HabitNotFoundError):
        seeded_tracker.delete_habit("Read")


def test_sample_data_is_loaded_only_once(tracker):
    assert tracker.is_empty()
    assert tracker.load_sample_data() == 5
    assert tracker.load_sample_data() == 0
    assert len(tracker.get_habits()) == 5


def test_parse_moment():
    assert cli.parse_moment("") is None
    assert cli.parse_moment("2026-08-31 07:15") == datetime(2026, 8, 31, 7, 15)
    assert cli.parse_moment("2026-08-31", today=date(2026, 9, 29)) == datetime(2026, 8, 31, 12, 0)
    with pytest.raises(ValueError):
        cli.parse_moment("31.08.2026")


def test_todays_date_is_never_rejected_as_future(seeded_tracker):
    moment = cli.parse_moment(date.today().isoformat())
    assert moment <= datetime.now()
    seeded_tracker.check_off("Read", moment)  # must not raise InvalidCheckOffError


def test_cli_rejects_invalid_time_span(seeded_tracker, monkeypatch, capsys):
    answers = iter(["5", "4", "2026-08-30", "2026-08-03", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.run(seeded_tracker)
    assert "[!] The start date must not be after the end date." in capsys.readouterr().out


def test_cli_rejects_invalid_date(seeded_tracker, monkeypatch, capsys):
    answers = iter(["5", "4", "03.08.2026", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.run(seeded_tracker)
    assert "is not a valid date" in capsys.readouterr().out


def test_cli_creates_a_habit_via_the_menu(tracker, monkeypatch, capsys):
    answers = iter(["n", "1", "Go jogging", "Run 5 km", "weekly", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.run(tracker)
    assert "'Go jogging' was created as a weekly habit" in capsys.readouterr().out
    assert tracker.get_habit("Go jogging").periodicity == "weekly"


def test_cli_shows_error_instead_of_crashing(seeded_tracker, monkeypatch, capsys):
    answers = iter(["1", "Read", "Read more", "daily", "0"])  # duplicate name
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.run(seeded_tracker)
    assert "[!] A habit called 'Read' already exists." in capsys.readouterr().out


def test_backdated_check_off_reports_its_own_date(seeded_tracker, monkeypatch, capsys):
    # "Read" is the 5th habit in alphabetical order; 30 August was missed in the sample data
    answers = iter(["2", "5", "2026-08-30 21:00", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.run(seeded_tracker)
    output = capsys.readouterr().out
    assert "'Read' checked off at 2026-08-30 21:00." in output
    assert analytics.longest_streak(seeded_tracker.get_habit("Read")) == 6


def test_main_uses_the_given_database_file(tmp_path, monkeypatch, capsys):
    answers = iter(["y", "0"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    cli.main(["--db", str(tmp_path / "test.db")])
    assert "5 sample habits loaded" in capsys.readouterr().out
    assert (tmp_path / "test.db").exists()


def test_shorten_marks_cut_text():
    assert cli.shorten("Short", 10) == "Short"
    assert cli.shorten("Vacuum and tidy up the whole apartment", 20) == "Vacuum and tidy u..."

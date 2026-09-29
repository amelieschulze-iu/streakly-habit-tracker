"""Five predefined habits with example data for four full weeks.

The data cover the ISO weeks 32–35 of 2026 (Monday 3 August to Sunday
30 August 2026). They contain deliberate gaps so that streaks and struggles
can be demonstrated, and they serve as the fixture of the test suite.

Expected results (used in the tests):

=====================  ========  ==============  =====================
Habit                  Period    Longest streak  Missed (3–30 Aug)
=====================  ========  ==============  =====================
Brush teeth            daily     14              1 of 28
Drink water            daily     28              0 of 28
Read                   daily     6               9 of 28
Clean the apartment    weekly    2               1 of 4
Call the family        weekly    4               0 of 4
=====================  ========  ==============  =====================
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from streakly.habit import DailyHabit, Habit, WeeklyHabit

#: First and last day of the example data.
SAMPLE_START = date(2026, 8, 3)
SAMPLE_END = date(2026, 8, 30)
#: All habits were created shortly before the first check-off.
SAMPLE_CREATED_AT = datetime(2026, 8, 3, 6, 0)


def _days_of_august(*days: int) -> list[date]:
    """Return the given days of August 2026 as date objects."""
    return [date(2026, 8, day) for day in days]


def _at(days: list[date], *times: time) -> list[datetime]:
    """Combine every day with every given time of day."""
    return [datetime.combine(day, moment) for day in days for moment in times]


def sample_habits() -> list[Habit]:
    """Return five new habit objects (three daily, two weekly) with four weeks of check-offs."""
    all_days = [SAMPLE_START + timedelta(days=offset) for offset in range(28)]
    return [
        DailyHabit("Brush teeth", "Brush your teeth in the morning and in the evening",
                   created_at=SAMPLE_CREATED_AT,
                   # two check-offs per day; 17 August was missed
                   completions=_at([day for day in all_days if day != date(2026, 8, 17)],
                                   time(7, 30), time(22, 0))),
        DailyHabit("Drink water", "Drink at least two litres of water",
                   created_at=SAMPLE_CREATED_AT,
                   completions=_at(all_days, time(20, 0))),
        DailyHabit("Read", "Read a book for at least 20 minutes",
                   created_at=SAMPLE_CREATED_AT,
                   completions=_at(_days_of_august(3, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15,
                                                   18, 19, 21, 24, 25, 26, 27, 29), time(21, 30))),
        WeeklyHabit("Clean the apartment", "Vacuum and tidy up the whole apartment",
                    created_at=SAMPLE_CREATED_AT,
                    # week 34 (17–23 August) was missed
                    completions=[datetime(2026, 8, 8, 10, 0), datetime(2026, 8, 16, 11, 0),
                                 datetime(2026, 8, 29, 10, 30)]),
        WeeklyHabit("Call the family", "Call your parents or siblings",
                    created_at=SAMPLE_CREATED_AT,
                    completions=_at(_days_of_august(9, 16, 23, 30), time(18, 0))),
    ]

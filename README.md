# Streakly – a command-line habit tracker

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests: 72 passed](https://img.shields.io/badge/tests-72%20passed-brightgreen)
![Dependencies: standard library only](https://img.shields.io/badge/dependencies-standard%20library%20only-lightgrey)

Streakly is the Python backend of a habit tracking app. Users define **daily** and **weekly**
habits, check them off at any time and analyse their progress – for example their longest streak
or the habits they struggled with most. All data are stored in a local SQLite database, so nothing
is lost between sessions.

The project was created for the portfolio course *Object Oriented and Functional Programming with
Python* (DLBDSOOFPP01) at IU International University of Applied Sciences.

- **Object-oriented core:** a habit is a class (`Habit` with the subclasses `DailyHabit` and `WeeklyHabit`).
- **Functional analytics:** all analyses are pure functions built with `map`, `filter` and `reduce`.
- **Persistent:** habits and every check-off (date and time) are stored with `sqlite3`.
- **Tested:** 72 unit tests (pytest) with five predefined habits as test fixture.

---

## Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Starting the app](#starting-the-app)
4. [How to use Streakly](#how-to-use-streakly)
5. [Key definitions](#key-definitions)
6. [Predefined habits (sample data)](#predefined-habits-sample-data)
7. [Running the tests](#running-the-tests)
8. [Project structure](#project-structure)
9. [Design](#design)

---

## Features

- **Create habits** with a unique name, a task specification and a periodicity (`daily` or `weekly`)
- **Check off habits** right now or at an earlier date and time, e.g. to catch up on a forgotten entry
- **Delete habits** after a confirmation – together with their whole history
- **Show habits:** all habits or only the daily/weekly ones, with task, last check-off and current streak
- **Analyse habits:**
  - longest streak of all habits
  - longest streak of one habit
  - streak overview of all habits
  - habits you struggled with most in a chosen time span
- **Immediate feedback:** your current streak is shown after every check-off
- **Five predefined habits** with four weeks of example data to explore the app right away
- **Robust input handling:** wrong input (unknown menu option, invalid date, date in the future,
  duplicate name, …) leads to a clear message instead of a crash

## Installation

**Requirements:** Python **3.10 or later**. Streakly itself only uses the Python standard library
(`sqlite3`, `datetime`, `functools`, `itertools`, `collections`, `abc`, `argparse`).
`pytest` is only needed to run the tests.

```bash
# 1. Get the code
git clone https://github.com/amelieschulze-iu/streakly-habit-tracker.git
cd streakly-habit-tracker
#    (alternatively: download the ZIP on GitHub via "Code" -> "Download ZIP" and unzip it)

# 2. Optional but recommended: create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the test tool
pip install -r requirements.txt
```

> On some systems the Python command is called `python3` instead of `python`.

## Starting the app

Run the following command inside the project folder:

```bash
python main.py                     # uses the database file habits.db in the current folder
python main.py --db demo.db        # uses another database file
python -m streakly                 # alternative way to start the app
```

On the **first start** the database is still empty and Streakly offers to load the five predefined
habits. Type `y` to explore the app with the example data or `n` to start from scratch.

```
Welcome to Streakly! Load 5 sample habits with 4 weeks of data? [y/n]: y
  [OK] 5 sample habits loaded.

--------------------------------------------------------------
  STREAKLY - your habit tracker
--------------------------------------------------------------
  1  Create a habit
  2  Check off a habit
  3  Delete a habit
  4  Show habits
  5  Analyse habits
  0  Exit
Your choice:
```

## How to use Streakly

Streakly is operated with a numbered menu: type the number of an option and press Enter.
After every action you return to the main menu. Choose `0` to exit – all data are saved
automatically after every change.

### 1 – Create a habit

Enter a unique name, the task and the periodicity (`daily` or `weekly`):

```
CREATE A HABIT
  Name (e.g. 'Go jogging'): Go jogging
  Task (what exactly do you want to do?): Run at least 5 km
  Periodicity (daily / weekly): weekly

  [OK] 'Go jogging' was created as a weekly habit.
```

Streakly stores the date and time when the habit was created.

### 2 – Complete a task (check off a habit)

Choose the habit by its number. Then

- press **Enter** to record the completion **now**, or
- type a **date** (`YYYY-MM-DD`) or **date and time** (`YYYY-MM-DD HH:MM`) to record a completion
  in the past, e.g. if you forgot to check off yesterday.

```
CHECK OFF A HABIT
   1  Brush teeth (daily)
   2  Call the family (weekly)
   3  Clean the apartment (weekly)
   4  Drink water (daily)
   5  Go jogging (weekly)
   6  Read (daily)
  Number of the habit (Enter = cancel): 5
  When? Enter = now, or YYYY-MM-DD [HH:MM]:

  [OK] 'Go jogging' checked off at 2026-09-29 17:26.
       Current streak: 1 week. Keep it up!
```

A habit has to be checked off **at least once per period** – once per calendar day for daily
habits and once per week (Monday to Sunday) for weekly habits. You can check off a habit several
times within one period (e.g. brushing your teeth in the morning and in the evening); for streaks
it counts only once. Check-offs in the future or before the habit was created are rejected.

### 3 – Delete a habit

Choose the habit and confirm with `yes`. The habit and all its check-offs are removed.

### 4 – Show habits

Choose whether to list all habits, only the daily or only the weekly habits. The table shows the
task, the date of the last check-off and the current streak of each habit.

### 5 – Analyse habits

| Option | Result |
|---|---|
| 1 Longest streak of all habits | habit with the longest run of consecutive completed periods |
| 2 Longest streak of one habit | longest streak of a habit you choose |
| 3 Streak overview of all habits | longest streak of every habit, best first |
| 4 Habits I struggled with most | share of missed periods per habit in a time span (Enter = last 4 weeks) |

Example for option 4 with the predefined habits:

```
  From [2026-09-01]: 2026-08-03
  To   [2026-09-29]: 2026-08-30

  Habit                Period  Missed   Miss rate
  -------------------  ------  -------  ---------
  Read                 daily   9 of 28  32%
  Clean the apartment  weekly  1 of 4   25%
  Brush teeth          daily   1 of 28  4%
  Call the family      weekly  0 of 4   0%
  Drink water          daily   0 of 28  0%

  You struggled most with 'Read'.
```

The ranking uses the **share** of missed periods, so daily and weekly habits stay comparable.

## Key definitions

- **Period:** a calendar day (daily habits) or an ISO week from Monday to Sunday (weekly habits).
- **Broken habit:** a period that has ended without a check-off.
- **Streak:** a run of consecutive completed periods.
- **Running period:** the current day or week is never counted as missed, because it is not over
  yet. So an unfinished day does not reset your current streak, and it does not appear as a
  struggle in the analysis.

## Predefined habits (sample data)

Streakly comes with five predefined habits (three daily, two weekly) and example check-offs for
four full weeks from **Monday, 3 August to Sunday, 30 August 2026**. They are defined in
[`streakly/sample_data.py`](streakly/sample_data.py), can be loaded on the first start and serve
as the test fixture of the unit tests.

| Habit | Periodicity | Task | Longest streak | Missed periods (3–30 Aug 2026) |
|---|---|---|---|---|
| Brush teeth | daily | Brush your teeth in the morning and in the evening | 14 days | 1 of 28 |
| Drink water | daily | Drink at least two litres of water | 28 days | 0 of 28 |
| Read | daily | Read a book for at least 20 minutes | 6 days | 9 of 28 |
| Clean the apartment | weekly | Vacuum and tidy up the whole apartment | 2 weeks | 1 of 4 |
| Call the family | weekly | Call your parents or siblings | 4 weeks | 0 of 4 |

Because the example data lie in the past, their **current** streaks are 0 today. To analyse the
example period with menu 5 → 4, enter the time span `2026-08-03` to `2026-08-30`.

## Running the tests

Run the test suite from the project folder:

```bash
python -m pytest            # short summary
python -m pytest -v         # every single test
```

```
tests/test_analytics.py ...........................        [ 37%]
tests/test_database.py .........                           [ 50%]
tests/test_habit.py ....................                   [ 77%]
tests/test_tracker.py ................                     [100%]
72 passed
```

The tests cover the habit classes (periods, check-off validation), every analytics function
(against the sample data with known expected results), the SQLite repository and the most
important CLI flows. They use an in-memory database and a fixed "today", so they never touch your
own `habits.db` and always produce the same results, no matter when they are run.

## Project structure

```
streakly-habit-tracker/
├── main.py                 # start script: python main.py
├── requirements.txt        # pytest (only needed for the tests)
├── README.md
├── docs/
│   ├── class_diagram.png   # UML class diagram
│   └── user_flow.png       # user flow of the CLI
├── streakly/
│   ├── __init__.py
│   ├── __main__.py         # allows: python -m streakly
│   ├── habit.py            # OOP domain model: Habit, DailyHabit, WeeklyHabit
│   ├── database.py         # HabitRepository: SQLite persistence
│   ├── tracker.py          # HabitTracker: application logic
│   ├── analytics.py        # pure functions for all analyses (functional programming)
│   ├── cli.py              # interactive command-line interface
│   ├── sample_data.py      # five predefined habits with four weeks of data
│   └── exceptions.py       # custom exceptions
└── tests/                  # pytest test suite (72 tests)
    ├── conftest.py         # fixtures: sample habits, in-memory database
    ├── test_habit.py
    ├── test_analytics.py
    ├── test_database.py
    └── test_tracker.py
```

## Design

Streakly is divided into layers with clearly separated responsibilities. Each layer only talks to
the layer below it, so single parts can be changed or replaced – for example the command-line menu
by a graphical front end – without touching the rest.

![UML class diagram of Streakly](docs/class_diagram.png)

- **Object-oriented core (`habit.py`):** the abstract class `Habit` holds name, task, creation time
  and all check-offs and validates new check-offs. `DailyHabit` and `WeeklyHabit` only define how a
  timestamp is mapped to the start of its period (`period_start`). Thanks to this polymorphism, no
  other code has to distinguish between them, and a monthly habit would only need one new subclass.
- **Persistence (`database.py`):** `HabitRepository` is the only class that contains SQL. It uses
  two tables (`habits`, `completions`) linked by a foreign key with `ON DELETE CASCADE` and converts
  database rows into habit objects and back. Every change is committed immediately.
- **Application logic (`tracker.py`):** `HabitTracker` is the single entry point for the user
  interface. It enforces rules such as unique habit names and raises custom exceptions
  (`HabitNotFoundError`, `HabitAlreadyExistsError`, `InvalidCheckOffError`).
- **Functional analytics (`analytics.py`):** pure functions that receive a list of habits and return
  new values (lists, numbers, named tuples) without printing, accessing the database or modifying
  their input. They are built with `map`, `filter`, `functools.reduce`, `itertools.takewhile`,
  lambdas and key functions. The longest streak, for example, is computed by folding the sorted
  period start dates with `reduce`.
- **Command-line interface (`cli.py`):** a numbered menu based on `input()` that needs no command
  syntax. It only reads input, calls the tracker or the analytics functions and formats the output;
  expected errors are caught centrally and shown as messages.

The user flow of the command-line interface:

![User flow of the CLI](docs/user_flow.png)

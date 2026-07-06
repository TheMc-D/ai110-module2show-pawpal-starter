# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

What's actually implemented in `pawpal_system.py`, connected to the Streamlit UI in `app.py`:

- **Owner & pet profiles** — track multiple pets per owner, each with their own independent task list.
- **Task tracking** — record a title, category, duration, priority, and an optional preferred time for every care task.
- **Priority-based scheduling** — `Scheduler.build_schedule()` builds a daily plan tier by tier, so a higher-priority task is never dropped to make room for a lower-priority one.
- **Time-budget packing** — within a priority tier, a best-fit search (`Scheduler._best_fit_subset()`) picks whichever combination of tasks uses the most of the remaining time, instead of wasting minutes on a fixed greedy order.
- **Sorting by priority** — `Scheduler.sort_by_priority()` orders tasks highest priority first, breaking ties by shorter duration.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks chronologically by preferred time, with untimed tasks sorting last.
- **Filtering** — `Owner.filter_tasks()` narrows the task list by pet name and/or completion status, independently or combined.
- **Conflict warnings** — `Scheduler.detect_conflicts()` flags any pair of same-day tasks whose preferred times overlap, even across different pets, and surfaces them automatically whenever a schedule is built.
- **Daily & weekly recurrence** — completing a `daily` or `weekly` task automatically spawns its next occurrence (respecting a weekly `days_of_week` pattern, e.g. Mon/Wed/Fri), so recurring care never has to be re-entered by hand.
- **Plan explanations** — `Scheduler.explain()` gives a human-readable reason for why each task made it onto the schedule.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output from running `python main.py`:

```
Today's Schedule
Daily plan for Jordan's pets — 2026-07-06
  08:00-08:10 — Feeding (Mochi, high priority)
  08:10-08:40 — Morning walk (Mochi, high priority)
  08:40-08:55 — Litter box cleaning (Biscuit, medium priority)
Not scheduled (ran out of time):
  Playtime (Biscuit, 45 min)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with verbose output:
python -m pytest -v

# Run with coverage:
pytest --cov
```

The suite (41 tests across `test_pawpal_system.py` and `tests/test_pawpal.py`) covers:

- **Sorting** — priority ordering (with duration as a tiebreaker) and chronological time ordering, including untimed tasks sorting last.
- **Recurrence** — daily and weekly tasks spawn a fresh, incomplete task for their next due date on completion (respecting `days_of_week` patterns), while one-time tasks never recur.
- **Filtering** — narrowing an owner's tasks by pet name and/or completion status, independently and combined.
- **Conflict detection** — overlapping preferred times are flagged (including tasks scheduled at the exact same time and across different pets), while back-to-back and untimed tasks are correctly left alone.
- **Time-budget scheduling** — higher-priority tasks are never dropped for lower-priority ones, and the best-fit packing minimizes wasted time within a priority tier.
- **Edge cases** — a pet with no tasks, an owner with no pets, an empty daily plan when nothing is due, and invalid task durations (zero/negative) being rejected at creation.

Sample test output:

```
============================= test session starts =============================
collected 41 items

test_pawpal_system.py ....................                               [ 48%]
tests\test_pawpal.py .....................                               [100%]

============================= 41 passed in 0.06s ==============================
```

### Confidence Level: ★★★★☆ (4/5)

The core scheduling behaviors — sorting, recurrence, filtering, conflict detection, and time-budget packing — are covered by passing tests, including boundary cases like same-time conflicts, back-to-back tasks, and empty pets/owners. One star held back because the suite is unit-level only: it doesn't yet exercise the Streamlit UI (`app.py`) end-to-end, and multi-week/multi-month recurrence chains beyond a single "complete → next occurrence" step haven't been stress-tested.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by priority | `Scheduler.sort_by_priority()` | Sorts highest priority first, breaking ties by shorter duration. Used internally by `build_schedule()` to decide scheduling order. |
| Sorting by time | `Scheduler.sort_by_time()` | Sorts tasks by their `preferred_time` ("HH:MM"); tasks with no preferred time sort last. Exposed in the Streamlit UI as a "Sort by preferred time" toggle on the task table. |
| Filtering by pet / status | `Owner.filter_tasks(pet_name=None, completed=None)` | Narrows the owner's tasks by pet name and/or completion status, either independently or combined. Exposed in the Streamlit UI as "Filter by pet" / "Filter by status" dropdowns. |
| Conflict detection | `Scheduler.detect_conflicts()` | Lightweight pairwise scan of same-day tasks with a `preferred_time`: computes each task's end time and flags any pair whose windows overlap (same pet or different pets), returning warning strings instead of raising an error. Wired into `build_schedule()` (surfaced in the plan's "Warnings" section) and into a standalone "Check for time conflicts" button in the UI. |
| Recurring tasks | `Task.is_due_today()`, `Task.mark_complete()`, `Task._create_next_occurrence()`, `Task._next_matching_weekday()` | Completing a `daily` or `weekly` task doesn't just flip a flag — `mark_complete()` spawns a fresh, incomplete `Task` for the next due date (`today + 1 day` for daily; the next matching weekday, or `+7 days` if there's no day-of-week pattern, for weekly) and attaches it to the same pet, so the recurrence continues on its own. |
| Time-budget packing | `Scheduler.filter_by_time()`, `Scheduler._best_fit_subset()` | Processes tasks tier by tier in strict priority order (a lower-priority tier can never bump a higher one), but within each tier runs a small subset-sum search to pick whichever combination of that tier's tasks uses the most of the remaining time — rather than a fixed duration-order greedy pass that can leave minutes unused. |

## 📸 Demo Walkthrough

### Main UI features

The Streamlit app (`app.py`) is organized top-to-bottom in the order you'd actually use it:

- **Owner & Pets** — set the owner's name and add one or more pets (name + species).
- **Scheduling preferences** — set the daily time budget (minutes) and the schedule's start time; these feed every scheduling action below.
- **Tasks** — add a care task to a selected pet (title, category, duration, priority, optional preferred time), then view all tasks in a table with:
  - **Filter by pet** / **Filter by status** dropdowns
  - A **Sort by** dropdown (Default / Priority / Preferred time)
  - A **Check for time conflicts** button that flags overlapping preferred times with `st.warning`
- **Build Schedule** — a **Generate schedule** button that runs the full scheduler and displays the result: conflict warnings (if any), the scheduled tasks as a table with an explanation caption per task, and any tasks that didn't fit in the time budget.

### Example workflow

1. Enter the owner's name and add a pet, e.g. "Mochi" (dog).
2. Add a task for Mochi: "Morning walk," 30 minutes, high priority, preferred time `08:00`.
3. Add a second task: "Feeding," 10 minutes, high priority, preferred time `08:00` (deliberately overlapping, to see conflict detection).
4. Click **Check for time conflicts** — a warning appears calling out that "Morning walk" and "Feeding" overlap.
5. Fix the time on one task, then click **Generate schedule** — today's plan appears as a table (start/end time, pet, task, priority), each row followed by a one-line explanation of why it was scheduled.
6. Add more tasks than the time budget allows — generating the schedule again shows the lower-priority tasks moved into the "didn't fit in today's time budget" table instead of being scheduled.

### Key Scheduler behaviors shown

- **Sorting** — switching the task table's "Sort by" dropdown to "Priority" or "Preferred time" reorders it live using `Scheduler.sort_by_priority()` / `sort_by_time()`.
- **Conflict warnings** — two tasks with the same or overlapping preferred times always produce a warning, whether checked manually or surfaced automatically when a schedule is generated.
- **Priority-aware, time-budget-aware packing** — the generated schedule always keeps higher-priority tasks over lower-priority ones, and best-fits whichever combination of same-priority tasks uses the most of the remaining budget.
- **Recurrence** — marking a `daily` or `weekly` task complete (exercised in `main.py`, not yet wired to a UI button) spawns its next occurrence automatically.

### Sample CLI output

`main.py` exercises the same backend without the UI — sorting, filtering, recurrence, conflict detection, and a final generated schedule:

```bash
python main.py
```

```
=== Sorting: all tasks by preferred time ===
  08:00  Morning walk (Mochi)
  08:30  Feeding (Mochi)
  09:00  Litter box cleaning (Biscuit)
  09:30  Playtime (Biscuit)
  18:00  Evening walk (Mochi)

=== Filtering: only Mochi's tasks ===
  Evening walk (completed=False)
  Feeding (completed=False)
  Morning walk (completed=False)

=== Filtering: completed tasks (should be none yet) ===
  []

=== Recurring tasks: completing 'Morning walk' should spawn tomorrow's occurrence ===
  Evening walk: completed=False, due_date=n/a
  Feeding: completed=False, due_date=n/a
  Morning walk: completed=True, due_date=n/a
  Morning walk: completed=False, due_date=2026-07-07

=== Filtering: completed tasks (after marking one complete) ===
  ['Morning walk']

=== Conflict detection: two tasks scheduled at the same time ===
  WARNING: 'Vet checkup' (Mochi, 08:00-08:20) overlaps 'Grooming appointment' (Biscuit, 08:10-08:25)

Today's Schedule
Daily plan for Jordan's pets — 2026-07-06
  08:00-08:10 — Feeding (Mochi, high priority)
  08:10-08:30 — Vet checkup (Mochi, high priority)
  08:30-08:45 — Litter box cleaning (Biscuit, medium priority)
  08:45-09:00 — Grooming appointment (Biscuit, medium priority)
  09:00-09:30 — Evening walk (Mochi, medium priority)
Not scheduled (ran out of time):
  Playtime (Biscuit, 45 min)
Warnings:
  'Vet checkup' (Mochi, 08:00-08:20) overlaps 'Grooming appointment' (Biscuit, 08:10-08:25)
```
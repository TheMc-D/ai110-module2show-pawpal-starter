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
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

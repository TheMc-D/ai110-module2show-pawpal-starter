# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Based on the scenario in the README, a user of PawPal+ should be able to:

- Enter basic owner and pet information (e.g., pet name, breed, and any relevant details about the owner) so the app knows who and what it's planning for.
- Add and edit pet care tasks (walks, feeding, meds, grooming, enrichment, etc.), specifying at least a duration and a priority for each one.
- Set the constraints and preferences the schedule should respect, such as how much time is available in the day and any owner preferences.
- Generate a daily plan/schedule that fits the tasks into the available time based on their priorities and constraints.
- View the generated plan clearly, ideally with an explanation of why tasks were scheduled the way they were.

**a. Initial design**

My initial UML design splits the system into six classes, separating data from behavior:

- **Owner** — holds the pet owner's `name` and `preferences` (e.g., preferred start time, max daily care time). It's mostly a data holder, with an `add_pet()` method to associate pets with an owner.
- **Pet** — holds `name`, `species`, `breed`, and a reference back to its `Owner`. Like Owner, it's primarily a data holder, with an `add_task()` method for attaching care tasks to a specific pet.
- **Task** — represents a single pet care task (walk, feeding, meds, grooming, enrichment) with `title`, `category`, `duration_minutes`, `priority`, `recurrence`, and an optional `preferred_time`. It owns logic that's intrinsic to a single task, like `conflicts_with()` (time overlap) and `is_due_today()` (recurrence check).
- **ScheduledTask** — a thin wrapper around a `Task` once it's been placed on the calendar, adding `start_time` and `end_time`, plus an `overlaps_with()` method to check against other scheduled tasks.
- **Scheduler** — the "brain" of the system. It holds the constraints (`available_time_minutes`, `start_time`, `constraints` dict) and is responsible for turning a list of `Task` objects into a `DailyPlan` via `build_schedule()`, using helper methods like `sort_by_priority()`, `filter_by_time()`, and `explain()` to justify its choices.
- **DailyPlan** — the output of scheduling: a `date`, the `Pet` it's for, the list of `scheduled_tasks`, any `dropped_tasks` that didn't fit, and the `total_duration` used. It's responsible for presenting the result (`to_display()`) rather than deciding it.

The core responsibility split is: **Owner/Pet/Task** describe *what exists*, **Scheduler** decides *what happens*, and **DailyPlan/ScheduledTask** describe *what was decided*. Keeping the scheduling logic isolated in `Scheduler` (rather than spreading it across `Task` or `Pet`) was a deliberate choice so the scheduling algorithm could change without touching the data classes.

**b. Design changes**

Once I translated the UML into an actual `pawpal_system.py` skeleton, a self-review surfaced a few gaps between the diagram and the code, so I made these changes:

- **Added `Owner.pets` and `Pet.tasks` list attributes.** The original design gave `Owner.add_pet()` and `Pet.add_task()` methods but no collection to add into — the one-to-many relationships implied by the UML weren't actually represented in the data. I added the missing lists and had `add_pet()`/`add_task()` append to them (and `add_pet()` now also sets the pet's `owner` back-reference).
- **Gave `Scheduler.build_schedule()` a `pet` and `date` parameter.** It originally only took `tasks`, but `DailyPlan` requires a `pet` and `date` to be constructed. Without them, `Scheduler` had no way to actually produce a valid `DailyPlan`.
- **Moved conflict detection off `Task` and onto `ScheduledTask`.** `Task.conflicts_with()` had no start/end time to compare against — only `ScheduledTask` carries `start_time`/`end_time`. I removed `conflicts_with()` from `Task` and implemented `ScheduledTask.overlaps_with()` instead, since that's the class that actually has the information needed to detect a real time conflict.
- **Dropped the stored `total_duration` field on `DailyPlan`.** Having both a stored field and a `total_time_used()` method risked the two drifting out of sync every time a task was added. I removed the field and made `total_time_used()` compute the sum from `scheduled_tasks` directly, so there's a single source of truth.
- **Typed `priority` and `recurrence` as `Literal` types**, and added a `days_of_week` field to `Task`, since a plain `str` allowed invalid values and gave `recurrence="weekly"` no way to say *which* day.

The common thread is that the first UML pass got the classes and their broad responsibilities right, but under-specified the actual data needed to wire those responsibilities together — most of these fixes were about making relationships and computed values concrete rather than changing the overall class structure.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: a hard time budget (`available_time_minutes`), task priority (`high`/`medium`/`low`), and each task's `preferred_time`. `Owner.preferences` exists as a dict for future owner-level preferences, but nothing in `Scheduler` reads it yet — it's a placeholder, not an active constraint.

Priority is the dominant constraint because it stands in for something that matters more than the clock: giving medication versus extra playtime aren't interchangeable just because they take the same number of minutes. The time budget is the one true hard constraint — a day only has so many minutes, so it decides what gets dropped once priority order is fixed. `preferred_time` is deliberately advisory rather than a hard scheduling constraint: it's used to order tasks and detect conflicts, but `build_schedule()` still packs tasks back-to-back from `start_time` rather than pinning each one to its preferred slot — a scheduler that rigidly enforced preferred times would generate far more "not scheduled" tasks than one that treats them as a hint plus a conflict check.

**b. Tradeoffs**

`Scheduler.filter_by_time()` processes tasks tier by tier in strict priority order — `high`, then `medium`, then `low` — and a lower tier is never allowed to displace a higher one, even when doing so would leave less of the time budget unused. For example, if a single 25-minute high-priority task and two 15-minute medium-priority tasks are competing for a 30-minute budget, the scheduler keeps the high-priority task and drops both medium ones, even though scheduling the two medium tasks instead would use the full 30 minutes with none wasted. Within a tier, the scheduler does search for the best-filling combination of that tier's own tasks (`_best_fit_subset()`), but it will never trade a higher-priority task away to improve overall time utilization.

This tradeoff is reasonable for pet care specifically because priority tiers aren't just a sorting convenience — they stand in for things like "give medication" versus "extra playtime," where skipping the former to fit more of the latter into the day would be a bad outcome regardless of how well it uses the clock. Optimizing for minimal wasted time across the whole day would occasionally sacrifice a health- or safety-critical task to pack in more low-stakes ones, which defeats the purpose of having priorities at all. The cost is that the total schedule isn't always time-optimal in the aggregate — but that's the correct choice when "optimal" and "safe" pull in different directions.

---

## 3. AI Collaboration

**a. Most effective AI assistant features**

The most useful capability wasn't code generation itself — it was the assistant reading the actual current state of a file before touching it, then making a scoped edit against exact lines instead of proposing a full-file rewrite. That kept every change reviewable: I could see precisely what was added to `pawpal_system.py` or `app.py` rather than having to diff a wholesale rewrite by eye. Just as important, the assistant actually *ran* things — `pytest` after every test change, `python main.py` to capture real sample output for the README — so claims like "41 passed" were verified facts, not descriptions of intent.

**b. An AI suggestion I rejected or modified**

When a new test (`duration_minutes=0`) failed, the AI's first proposed fix was to patch `Scheduler._best_fit_subset()`'s internal tie-breaking logic so the subset-sum search would tolerate a zero-duration task. I rejected that: it would have added defensive complexity to an already-subtle algorithm just to accommodate an input that should never legally exist. I pushed back and asked for validation at the boundary instead. The fix that shipped was a `Task.__post_init__` check that rejects any `duration_minutes < 1` at construction time — simpler, matches the constraint the Streamlit form (`min_value=1`) already enforces, and leaves the scheduling algorithm itself untouched.

**c. Using separate chat sessions**

I split the work across three chat sessions on purpose: one to keep algorithmic planning (working out the UML design and the scheduling approach — priority tiers, best-fit time-budget packing, recurrence rules) separate from the session where I actually built the core implementation, and a third session dedicated only to testing. Keeping planning separate from implementation meant design decisions got made deliberately rather than being improvised mid-code, and giving testing its own session meant it got treated as its own pass over the finished system — including a whole class of edge cases (empty pets, exact-same-time conflicts, invalid durations) that's easy to skip if testing is squeezed in at the tail end of a build session instead of run as a focused pass.

**d. Being the "lead architect"**

The AI can produce a plausible, working fix quickly — but "plausible" and "correct for this system" aren't the same thing. The zero-duration bug is the clearest example: the first fix worked (tests passed) but put the complexity in the wrong layer. Being the lead architect meant continuing to ask "why here and not at the boundary" instead of accepting the first green test run, and deciding what belonged in each artifact — a Features list that names real methods instead of aspirational copy, a Confidence Level that's earned by what the tests actually cover rather than inflated for the README. The AI moves fast once given direction; the judgment calls about where a fix belongs and whether a claim is actually verified stayed mine to make.

---

## 4. Testing and Verification

**a. What you tested**

The dedicated testing session produced 41 automated tests covering sorting (priority ordering with duration as a tiebreaker; chronological time ordering with untimed tasks sorting last), recurrence (daily/weekly tasks spawning a correctly-dated next occurrence, including the `days_of_week` pattern advancing to the next matching weekday rather than jumping a full week), filtering (by pet, by completion status, and both combined), conflict detection (overlapping preferred times flagged — including the exact-same-time case and conflicts across different pets — while back-to-back and untimed tasks are confirmed to never be falsely flagged), time-budget packing (higher-priority tasks never dropped for lower-priority ones, best-fit minimizing wasted time within a tier), and edge cases (a pet with no tasks, an owner with no pets, an empty daily plan, and invalid non-positive durations rejected at creation).

Beyond the automated suite, I also manually tested the app itself — running `python main.py` and reading through its printed output, and clicking through the Streamlit UI directly (adding pets/tasks, generating schedules, checking conflict warnings) to confirm the backend's behavior actually looks right to a user, not just correct in isolation against an assertion. These behaviors matter because they're exactly what a pet owner would notice going wrong: a missed medication because of a silent scheduling bug, or a false conflict warning that erodes trust in the tool, is worse than the app doing nothing at all.

**b. Confidence**

I rated this a 4 out of 5 in the README. The core algorithms are covered by passing tests, including boundary cases, and I've confirmed the same behaviors hold up when driving the actual UI and CLI by hand. The star held back is for what's still unit-level or manually spot-checked rather than exhaustively tested: long recurrence chains (many consecutive completions of a weekly multi-day task, to make sure `due_date` advancement doesn't drift over weeks), a much larger number of tasks in one day (to see how the best-fit subset-sum search performs as task count grows, since it's combinatorial rather than linear), and duplicate/near-duplicate task titles across pets.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the recurrence logic and the time-budget best-fit packing, since both required real algorithmic thought instead of just glue code — `mark_complete()` correctly spawning the next occurrence for a weekly task with a multi-day `days_of_week` pattern (advancing to the next matching weekday rather than jumping a full week), and `_best_fit_subset()` finding the combination of same-priority tasks that fills the remaining time budget best instead of just greedily taking tasks in a fixed order.

**b. What you would improve**

If I had another iteration, I'd wire a "mark complete" button into the Streamlit UI so recurrence is actually demoable there instead of only being exercised through `main.py`. I'd also make `Owner.preferences` an active constraint the scheduler reads (e.g. a preferred start time or a blackout window) instead of an inert dict that exists in the data model but does nothing yet.

**c. Key takeaway**

Keeping the data classes (`Task`/`Pet`/`Owner`) separate from the class that makes decisions (`Scheduler`) made every later addition — conflict detection, then recurrence, then time-budget packing — additive instead of requiring a redesign. The Phase 1 split held up even though almost every method's signature changed by the end. Splitting the AI collaboration itself into planning, implementation, and testing sessions reinforced the same lesson at the process level: deciding the design before writing code, and testing as its own deliberate pass rather than an afterthought, produced a more coherent system than doing everything in one continuous, improvised session would have.

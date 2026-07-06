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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

`Scheduler.filter_by_time()` processes tasks tier by tier in strict priority order — `high`, then `medium`, then `low` — and a lower tier is never allowed to displace a higher one, even when doing so would leave less of the time budget unused. For example, if a single 25-minute high-priority task and two 15-minute medium-priority tasks are competing for a 30-minute budget, the scheduler keeps the high-priority task and drops both medium ones, even though scheduling the two medium tasks instead would use the full 30 minutes with none wasted. Within a tier, the scheduler does search for the best-filling combination of that tier's own tasks (`_best_fit_subset()`), but it will never trade a higher-priority task away to improve overall time utilization.

This tradeoff is reasonable for pet care specifically because priority tiers aren't just a sorting convenience — they stand in for things like "give medication" versus "extra playtime," where skipping the former to fit more of the latter into the day would be a bad outcome regardless of how well it uses the clock. Optimizing for minimal wasted time across the whole day would occasionally sacrifice a health- or safety-critical task to pack in more low-stakes ones, which defeats the purpose of having priorities at all. The cost is that the total schedule isn't always time-optimal in the aggregate — but that's the correct choice when "optimal" and "safe" pull in different directions.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

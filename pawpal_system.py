from dataclasses import dataclass, field
from datetime import date as date_type, datetime, timedelta
from itertools import groupby
from typing import List, Literal, Optional, Tuple

Priority = Literal["low", "medium", "high"]
Recurrence = Literal["one-time", "daily", "weekly"]

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _add_minutes(time_str: str, minutes: int) -> str:
    start = datetime.strptime(time_str, "%H:%M")
    return (start + timedelta(minutes=minutes)).strftime("%H:%M")


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: Priority
    recurrence: Recurrence = "one-time"
    days_of_week: Optional[List[int]] = None
    preferred_time: Optional[str] = None
    due_date: Optional[date_type] = None
    completed: bool = False
    pet: Optional["Pet"] = None

    def __post_init__(self) -> None:
        if self.duration_minutes < 1:
            raise ValueError(
                f"duration_minutes must be at least 1 minute, got {self.duration_minutes}. "
                "Please enter a duration within the approved range."
            )

    def is_due_today(self, today: date_type) -> bool:
        """Return True if this task should appear on today's schedule.

        `due_date` (set automatically once a recurring task has been completed at least
        once, see `_create_next_occurrence`) always wins when present, since it pins this
        specific instance to one exact date. Only a task that has never been completed
        falls back to the more general `days_of_week` pattern check for `weekly` tasks,
        or is treated as due every day for `daily`/`one-time` tasks.
        """
        if self.completed:
            return False
        if self.due_date is not None:
            return self.due_date == today
        if self.recurrence == "weekly":
            return self.days_of_week is not None and today.weekday() in self.days_of_week
        return True

    def mark_complete(self, today: Optional[date_type] = None) -> None:
        """Mark this task as completed, spawning the next occurrence if it recurs.

        `daily`/`weekly` tasks never reset themselves back to due — instead, completing
        one instance creates a brand-new, incomplete `Task` for the next due date and
        attaches it to the same pet, so the recurrence continues automatically.
        """
        self.completed = True
        next_task = self._create_next_occurrence(today or date_type.today())
        if next_task is not None and self.pet is not None:
            self.pet.add_task(next_task)

    def mark_incomplete(self) -> None:
        """Mark this task as not completed."""
        self.completed = False

    def _create_next_occurrence(self, today: date_type) -> Optional["Task"]:
        """Return a fresh, incomplete Task for this task's next due date, or None if it doesn't recur.

        `daily` always steps forward exactly one day. `weekly` steps forward exactly
        seven days when there's no `days_of_week` pattern to honor, but when one is set
        (e.g. `[0, 2, 4]` for Mon/Wed/Fri) it instead advances to whichever of those
        weekdays comes next — otherwise completing a Monday occurrence would jump
        straight to next Monday and silently drop the Wednesday/Friday occurrences.
        """
        base = self.due_date or today
        if self.recurrence == "daily":
            next_due = base + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_due = self._next_matching_weekday(base) if self.days_of_week else base + timedelta(days=7)
        else:
            return None
        return Task(
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            days_of_week=self.days_of_week,
            preferred_time=self.preferred_time,
            due_date=next_due,
        )

    def _next_matching_weekday(self, after: date_type) -> date_type:
        """Return the next date after `after` whose weekday is in `days_of_week`.

        Checks the 7 days following `after` one at a time and returns the first match —
        a full week always contains at least one match as long as `days_of_week` is
        non-empty, so this never has to look further than 7 days ahead. The trailing
        `+7 days` return is an unreachable safety fallback, not part of the normal path.
        """
        for offset in range(1, 8):
            candidate = after + timedelta(days=offset)
            if candidate.weekday() in self.days_of_week:
                return candidate
        return after + timedelta(days=7)


@dataclass
class Pet:
    name: str
    species: str
    breed: Optional[str] = None
    owner: Optional["Owner"] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and link it back to the pet."""
        task.pet = self
        self.tasks.append(task)

    def get_tasks_due_today(self, today: date_type) -> List[Task]:
        """Return this pet's tasks that are due on the given date."""
        return [task for task in self.tasks if task.is_due_today(today)]


@dataclass
class Owner:
    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner and link it back to the owner."""
        pet.owner = self
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_tasks_due_today(self, today: date_type) -> List[Task]:
        """Return every task across all pets that is due on the given date."""
        return [task for pet in self.pets for task in pet.get_tasks_due_today(today)]

    def filter_tasks(self, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[Task]:
        """Return this owner's tasks, optionally narrowed by pet name and/or completion status.

        Each filter is applied only when its argument isn't `None`, and both can be
        combined (e.g. `pet_name="Mochi", completed=False` for Mochi's open tasks).
        """
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [task for task in tasks if task.pet is not None and task.pet.name == pet_name]
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
        return tasks


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    end_time: str

    def overlaps_with(self, other: "ScheduledTask") -> bool:
        """Return True if this scheduled task's time range overlaps another's."""
        return self.start_time < other.end_time and other.start_time < self.end_time


@dataclass
class DailyPlan:
    date: str
    owner: Owner
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    dropped_tasks: List[Task] = field(default_factory=list)
    conflict_warnings: List[str] = field(default_factory=list)

    def add_scheduled_task(self, task: Task, start_time: str, end_time: str) -> None:
        """Wrap a task with a start/end time and add it to this plan."""
        self.scheduled_tasks.append(ScheduledTask(task=task, start_time=start_time, end_time=end_time))

    def total_time_used(self) -> int:
        """Return the total minutes used by all scheduled tasks in this plan."""
        return sum(scheduled.task.duration_minutes for scheduled in self.scheduled_tasks)

    def to_display(self) -> str:
        """Render this plan as a human-readable, multi-line string."""
        lines = [f"Daily plan for {self.owner.name}'s pets — {self.date}"]
        for scheduled in self.scheduled_tasks:
            pet_name = scheduled.task.pet.name if scheduled.task.pet else "Unknown pet"
            lines.append(
                f"  {scheduled.start_time}-{scheduled.end_time} — {scheduled.task.title} "
                f"({pet_name}, {scheduled.task.priority} priority)"
            )
        if self.dropped_tasks:
            lines.append("Not scheduled (ran out of time):")
            for task in self.dropped_tasks:
                pet_name = task.pet.name if task.pet else "Unknown pet"
                lines.append(f"  {task.title} ({pet_name}, {task.duration_minutes} min)")
        if self.conflict_warnings:
            lines.append("Warnings:")
            for warning in self.conflict_warnings:
                lines.append(f"  {warning}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    available_time_minutes: int
    start_time: str
    constraints: dict = field(default_factory=dict)

    def build_schedule(self, owner: Owner, today: date_type) -> DailyPlan:
        """Build a DailyPlan for the owner's due tasks, honoring the time budget."""
        due_tasks = owner.get_tasks_due_today(today)
        conflict_warnings = self.detect_conflicts(due_tasks)
        ordered_tasks = self.sort_by_priority(due_tasks)
        selected_tasks, dropped_tasks = self.filter_by_time(ordered_tasks, self.available_time_minutes)

        plan = DailyPlan(
            date=today.isoformat(),
            owner=owner,
            dropped_tasks=dropped_tasks,
            conflict_warnings=conflict_warnings,
        )
        current_time = self.start_time
        for task in selected_tasks:
            end_time = _add_minutes(current_time, task.duration_minutes)
            plan.add_scheduled_task(task, start_time=current_time, end_time=end_time)
            current_time = end_time
        return plan

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks highest priority first, breaking ties by shorter duration."""
        return sorted(tasks, key=lambda task: (_PRIORITY_ORDER[task.priority], task.duration_minutes))

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by their preferred_time ("HH:MM"); tasks with no preferred time sort last.

        Zero-padded "HH:MM" strings compare in the same order as their clock times, so a
        plain string sort works without parsing them into actual time objects. "24:00" is
        used as a sentinel key for untimed tasks since it sorts after every valid time.
        """
        return sorted(tasks, key=lambda task: task.preferred_time or "24:00")

    def detect_conflicts(self, tasks: List[Task]) -> List[str]:
        """Lightweight pairwise scan for tasks with overlapping preferred times.

        Compares every pair of timed tasks (same pet or different pets) and returns
        a human-readable warning for each overlap, instead of raising an error, so a
        scheduling conflict never crashes the program — it's surfaced for the owner
        to resolve.
        """
        warnings: List[str] = []
        timed_tasks = [task for task in tasks if task.preferred_time]
        for i, task_a in enumerate(timed_tasks):
            start_a, end_a = task_a.preferred_time, _add_minutes(task_a.preferred_time, task_a.duration_minutes)
            for task_b in timed_tasks[i + 1:]:
                start_b, end_b = task_b.preferred_time, _add_minutes(task_b.preferred_time, task_b.duration_minutes)
                if start_a < end_b and start_b < end_a:
                    pet_a = task_a.pet.name if task_a.pet else "Unknown pet"
                    pet_b = task_b.pet.name if task_b.pet else "Unknown pet"
                    warnings.append(
                        f"'{task_a.title}' ({pet_a}, {start_a}-{end_a}) overlaps "
                        f"'{task_b.title}' ({pet_b}, {start_b}-{end_b})"
                    )
        return warnings

    def filter_by_time(self, tasks: List[Task], budget: int) -> Tuple[List[Task], List[Task]]:
        """Select tasks tier by tier, best-filling each priority tier's share of the budget.

        `tasks` must already be sorted by priority (as `sort_by_priority` does), so tasks
        of the same priority are contiguous. Processing tier by tier guarantees a lower
        priority tier can never bump a higher one, but within a tier we pick whichever
        combination of tasks uses the most of the remaining time — a fixed duration-order
        greedy can leave minutes unused that a different combination would have filled.
        """
        selected: List[Task] = []
        dropped: List[Task] = []
        remaining = budget
        for _, tier in groupby(tasks, key=lambda task: task.priority):
            tier_tasks = list(tier)
            tier_selected = self._best_fit_subset(tier_tasks, remaining)
            selected_ids = {id(task) for task in tier_selected}
            selected.extend(tier_selected)
            dropped.extend(task for task in tier_tasks if id(task) not in selected_ids)
            remaining -= sum(task.duration_minutes for task in tier_selected)
        return selected, dropped

    def _best_fit_subset(self, tasks: List[Task], budget: int) -> List[Task]:
        """Return the subset of tasks whose combined duration is the largest possible within budget.

        This is a 0/1 subset-sum search: `reachable` maps every total duration that can
        be built from the tasks seen so far to one task combination that achieves it.
        Each task either gets added on top of an existing total (if it still fits in
        `budget`) or left out, so by the end `reachable` holds every achievable total,
        and the largest one is the best possible use of the budget. This is more
        thorough than a single fixed-order pass (e.g. always taking the shortest task
        first), which can lock in a combination that wastes more time than an
        alternative one would have. Runs in O(tasks * distinct achievable totals), which
        stays small for a day's worth of pet care tasks.
        """
        reachable: dict = {0: []}
        for task in tasks:
            for total in list(reachable):
                new_total = total + task.duration_minutes
                if new_total <= budget and new_total not in reachable:
                    reachable[new_total] = reachable[total] + [task]
        return reachable[max(reachable)]

    def explain(self, task: Task) -> str:
        """Return a human-readable reason why this task was scheduled."""
        return (
            f"'{task.title}' was scheduled because it has {task.priority} priority "
            f"and its {task.duration_minutes}-minute duration fit within the remaining time budget."
        )

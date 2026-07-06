from dataclasses import dataclass, field
from datetime import date as date_type, datetime, timedelta
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
    completed: bool = False
    pet: Optional["Pet"] = None

    def is_due_today(self, today: date_type) -> bool:
        """Return True if this task should appear on today's schedule."""
        if self.completed:
            return False
        if self.recurrence == "weekly":
            return self.days_of_week is not None and today.weekday() in self.days_of_week
        return True

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not completed."""
        self.completed = False


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
        return "\n".join(lines)


@dataclass
class Scheduler:
    available_time_minutes: int
    start_time: str
    constraints: dict = field(default_factory=dict)

    def build_schedule(self, owner: Owner, today: date_type) -> DailyPlan:
        """Build a DailyPlan for the owner's due tasks, honoring the time budget."""
        due_tasks = owner.get_tasks_due_today(today)
        ordered_tasks = self.sort_by_priority(due_tasks)
        selected_tasks, dropped_tasks = self.filter_by_time(ordered_tasks, self.available_time_minutes)

        plan = DailyPlan(date=today.isoformat(), owner=owner, dropped_tasks=dropped_tasks)
        current_time = self.start_time
        for task in selected_tasks:
            end_time = _add_minutes(current_time, task.duration_minutes)
            plan.add_scheduled_task(task, start_time=current_time, end_time=end_time)
            current_time = end_time
        return plan

    def sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks highest priority first, breaking ties by shorter duration."""
        return sorted(tasks, key=lambda task: (_PRIORITY_ORDER[task.priority], task.duration_minutes))

    def filter_by_time(self, tasks: List[Task], budget: int) -> Tuple[List[Task], List[Task]]:
        """Split tasks into those that fit the time budget and those that don't."""
        selected: List[Task] = []
        dropped: List[Task] = []
        remaining = budget
        for task in tasks:
            if task.duration_minutes <= remaining:
                selected.append(task)
                remaining -= task.duration_minutes
            else:
                dropped.append(task)
        return selected, dropped

    def explain(self, task: Task) -> str:
        """Return a human-readable reason why this task was scheduled."""
        return (
            f"'{task.title}' was scheduled because it has {task.priority} priority "
            f"and its {task.duration_minutes}-minute duration fit within the remaining time budget."
        )

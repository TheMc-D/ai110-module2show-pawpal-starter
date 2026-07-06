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
        if self.completed:
            return False
        if self.recurrence == "weekly":
            return self.days_of_week is not None and today.weekday() in self.days_of_week
        return True

    def mark_complete(self) -> None:
        self.completed = True

    def mark_incomplete(self) -> None:
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    breed: Optional[str] = None
    owner: Optional["Owner"] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        task.pet = self
        self.tasks.append(task)

    def get_tasks_due_today(self, today: date_type) -> List[Task]:
        return [task for task in self.tasks if task.is_due_today(today)]


@dataclass
class Owner:
    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pet.owner = self
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        return [task for pet in self.pets for task in pet.tasks]

    def get_tasks_due_today(self, today: date_type) -> List[Task]:
        return [task for pet in self.pets for task in pet.get_tasks_due_today(today)]


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    end_time: str

    def overlaps_with(self, other: "ScheduledTask") -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time


@dataclass
class DailyPlan:
    date: str
    owner: Owner
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    dropped_tasks: List[Task] = field(default_factory=list)

    def add_scheduled_task(self, task: Task, start_time: str, end_time: str) -> None:
        self.scheduled_tasks.append(ScheduledTask(task=task, start_time=start_time, end_time=end_time))

    def total_time_used(self) -> int:
        return sum(scheduled.task.duration_minutes for scheduled in self.scheduled_tasks)

    def to_display(self) -> str:
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
        return sorted(tasks, key=lambda task: (_PRIORITY_ORDER[task.priority], task.duration_minutes))

    def filter_by_time(self, tasks: List[Task], budget: int) -> Tuple[List[Task], List[Task]]:
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
        return (
            f"'{task.title}' was scheduled because it has {task.priority} priority "
            f"and its {task.duration_minutes}-minute duration fit within the remaining time budget."
        )

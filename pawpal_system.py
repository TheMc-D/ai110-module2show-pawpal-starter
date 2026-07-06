from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Owner:
    name: str
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: "Pet") -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: Optional[str] = None
    owner: Optional[Owner] = None

    def add_task(self, task: "Task") -> None:
        pass


@dataclass
class Task:
    title: str
    category: str
    duration_minutes: int
    priority: str
    recurrence: str = "one-time"
    preferred_time: Optional[str] = None

    def conflicts_with(self, other: "Task") -> bool:
        pass

    def is_due_today(self) -> bool:
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    end_time: str

    def overlaps_with(self, other: "ScheduledTask") -> bool:
        pass


@dataclass
class DailyPlan:
    date: str
    pet: Pet
    scheduled_tasks: list = field(default_factory=list)
    dropped_tasks: list = field(default_factory=list)
    total_duration: int = 0

    def add_scheduled_task(self, task: Task, start_time: str) -> None:
        pass

    def total_time_used(self) -> int:
        pass

    def to_display(self) -> str:
        pass


@dataclass
class Scheduler:
    available_time_minutes: int
    start_time: str
    constraints: dict = field(default_factory=dict)

    def build_schedule(self, tasks: list) -> DailyPlan:
        pass

    def sort_by_priority(self, tasks: list) -> list:
        pass

    def filter_by_time(self, tasks: list, budget: int) -> list:
        pass

    def explain(self, task: Task) -> str:
        pass

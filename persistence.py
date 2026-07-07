import json
from datetime import date
from pathlib import Path
from typing import Any, Dict

from pawpal_system import Owner, Pet, Task


def _task_to_dict(task: Task) -> Dict[str, Any]:
    return {
        "title": task.title,
        "category": task.category,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "recurrence": task.recurrence,
        "days_of_week": task.days_of_week,
        "preferred_time": task.preferred_time,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "completed": task.completed,
    }


def _task_from_dict(data: Dict[str, Any]) -> Task:
    due_date = data.get("due_date")
    return Task(
        title=data["title"],
        category=data["category"],
        duration_minutes=data["duration_minutes"],
        priority=data["priority"],
        recurrence=data.get("recurrence", "one-time"),
        days_of_week=data.get("days_of_week"),
        preferred_time=data.get("preferred_time"),
        due_date=date.fromisoformat(due_date) if due_date else None,
        completed=data.get("completed", False),
    )


def _pet_to_dict(pet: Pet) -> Dict[str, Any]:
    return {
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "tasks": [_task_to_dict(task) for task in pet.tasks],
    }


def _pet_from_dict(data: Dict[str, Any]) -> Pet:
    pet = Pet(name=data["name"], species=data["species"], breed=data.get("breed"))
    for task_data in data.get("tasks", []):
        pet.add_task(_task_from_dict(task_data))
    return pet


def owner_to_dict(owner: Owner) -> Dict[str, Any]:
    """Convert an Owner (and all their pets/tasks) into a JSON-serializable dict.

    Back-references (`Pet.owner`, `Task.pet`) are intentionally omitted — they're
    reconstructed on load via `add_pet()`/`add_task()`, which set them automatically.
    """
    return {
        "name": owner.name,
        "preferences": owner.preferences,
        "pets": [_pet_to_dict(pet) for pet in owner.pets],
    }


def owner_from_dict(data: Dict[str, Any]) -> Owner:
    """Rebuild an Owner (and all their pets/tasks) from a dict produced by `owner_to_dict()`."""
    owner = Owner(name=data["name"], preferences=data.get("preferences", {}))
    for pet_data in data.get("pets", []):
        owner.add_pet(_pet_from_dict(pet_data))
    return owner


def save_owner(owner: Owner, path: str) -> None:
    """Save an owner (and all their pets/tasks) to a JSON file at `path`."""
    Path(path).write_text(json.dumps(owner_to_dict(owner), indent=2), encoding="utf-8")


def load_owner(path: str) -> Owner:
    """Load an owner (and all their pets/tasks) from the JSON file at `path`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return owner_from_dict(data)

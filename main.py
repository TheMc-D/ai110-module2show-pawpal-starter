from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler

owner = Owner(name="Jordan")

dog = Pet(name="Mochi", species="dog", breed="Shiba Inu")
cat = Pet(name="Biscuit", species="cat", breed="Tabby")
owner.add_pet(dog)
owner.add_pet(cat)

# Tasks are added out of preferred-time order on purpose, to prove sort_by_time() works.
dog.add_task(Task(title="Evening walk", category="walk", duration_minutes=30, priority="medium",
                   preferred_time="18:00", recurrence="daily"))
dog.add_task(Task(title="Feeding", category="feeding", duration_minutes=10, priority="high", preferred_time="08:30"))
dog.add_task(Task(title="Morning walk", category="walk", duration_minutes=30, priority="high",
                   preferred_time="08:00", recurrence="daily"))
cat.add_task(Task(title="Playtime", category="enrichment", duration_minutes=45, priority="low", preferred_time="09:30"))
cat.add_task(Task(title="Litter box cleaning", category="grooming", duration_minutes=15, priority="medium",
                   preferred_time="09:00"))

scheduler = Scheduler(available_time_minutes=90, start_time="08:00")

print("=== Sorting: all tasks by preferred time ===")
for task in scheduler.sort_by_time(owner.get_all_tasks()):
    pet_name = task.pet.name if task.pet else "Unknown pet"
    print(f"  {task.preferred_time or '--:--'}  {task.title} ({pet_name})")

print("\n=== Filtering: only Mochi's tasks ===")
for task in owner.filter_tasks(pet_name="Mochi"):
    print(f"  {task.title} (completed={task.completed})")

print("\n=== Filtering: completed tasks (should be none yet) ===")
print(f"  {[task.title for task in owner.filter_tasks(completed=True)]}")

print("\n=== Recurring tasks: completing 'Morning walk' should spawn tomorrow's occurrence ===")
morning_walk = next(task for task in dog.tasks if task.title == "Morning walk")
morning_walk.mark_complete()
for task in dog.tasks:
    due = task.due_date.isoformat() if task.due_date else "n/a"
    print(f"  {task.title}: completed={task.completed}, due_date={due}")

print("\n=== Filtering: completed tasks (after marking one complete) ===")
print(f"  {[task.title for task in owner.filter_tasks(completed=True)]}")

print("\n=== Conflict detection: two tasks scheduled at the same time ===")
dog.add_task(Task(title="Vet checkup", category="medication", duration_minutes=20, priority="high",
                   preferred_time="08:00"))
cat.add_task(Task(title="Grooming appointment", category="grooming", duration_minutes=15, priority="medium",
                   preferred_time="08:10"))
conflicts = scheduler.detect_conflicts(owner.get_tasks_due_today(date.today()))
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts detected.")

print("\nToday's Schedule")
plan = scheduler.build_schedule(owner, date.today())
print(plan.to_display())
